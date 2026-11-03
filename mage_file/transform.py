import pandas as pd

if "transformer" not in globals():
    from mage_ai.data_preparation.decorators import transformer

if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(df, *args, **kwargs):
    """
    Transform raw Uber trip records into one fact table and seven
    dimension tables (Star Schema).

    Returns a dictionary of pandas DataFrames for the Mage Data Exporter.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"Expected a pandas DataFrame from the upstream block, got {type(df).__name__}."
        )

    if df.empty:
        raise ValueError("Input data is empty.")

    required_columns = [
        "VendorID",
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "passenger_count",
        "trip_distance",
        "pickup_longitude",
        "pickup_latitude",
        "RatecodeID",
        "store_and_fwd_flag",
        "dropoff_longitude",
        "dropoff_latitude",
        "payment_type",
        "fare_amount",
        "extra",
        "mta_tax",
        "tip_amount",
        "tolls_amount",
        "improvement_surcharge",
        "total_amount",
    ]

    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Work on a copy so the upstream DataFrame is not modified.
    df = df[required_columns].copy()

    # Parse timestamps and remove records with invalid pickup/dropoff times.
    df["tpep_pickup_datetime"] = pd.to_datetime(
        df["tpep_pickup_datetime"], errors="coerce"
    )
    df["tpep_dropoff_datetime"] = pd.to_datetime(
        df["tpep_dropoff_datetime"], errors="coerce"
    )
    df = df.dropna(
        subset=["tpep_pickup_datetime", "tpep_dropoff_datetime"]
    ).copy()

    if df.empty:
        raise ValueError("No rows remain after validating pickup/dropoff timestamps.")

    # 1. Datetime dimension
    datetime_dim = (
        df[["tpep_pickup_datetime", "tpep_dropoff_datetime"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    pickup = datetime_dim["tpep_pickup_datetime"]
    dropoff = datetime_dim["tpep_dropoff_datetime"]

    datetime_dim["pick_hour"] = pickup.dt.hour
    datetime_dim["pick_day"] = pickup.dt.day
    datetime_dim["pick_month"] = pickup.dt.month
    datetime_dim["pick_year"] = pickup.dt.year
    datetime_dim["pick_weekday"] = pickup.dt.weekday

    datetime_dim["drop_hour"] = dropoff.dt.hour
    datetime_dim["drop_day"] = dropoff.dt.day
    datetime_dim["drop_month"] = dropoff.dt.month
    datetime_dim["drop_year"] = dropoff.dt.year
    datetime_dim["drop_weekday"] = dropoff.dt.weekday

    datetime_dim.insert(0, "datetime_id", range(len(datetime_dim)))

    datetime_dim = datetime_dim[
        [
            "datetime_id",
            "tpep_pickup_datetime",
            "pick_hour",
            "pick_day",
            "pick_month",
            "pick_year",
            "pick_weekday",
            "tpep_dropoff_datetime",
            "drop_hour",
            "drop_day",
            "drop_month",
            "drop_year",
            "drop_weekday",
        ]
    ]

    # 2. Passenger count dimension
    passenger_count_dim = (
        df[["passenger_count"]].drop_duplicates().reset_index(drop=True)
    )
    passenger_count_dim.insert(0, "passenger_count_id", range(len(passenger_count_dim)))

    # 3. Trip distance dimension
    trip_distance_dim = (
        df[["trip_distance"]].drop_duplicates().reset_index(drop=True)
    )
    trip_distance_dim.insert(0, "trip_distance_id", range(len(trip_distance_dim)))

    # 4. Rate code dimension
    rate_code_type = {
        1: "Standard rate",
        2: "JFK",
        3: "Newark",
        4: "Nassau or Westchester",
        5: "Negotiated fare",
        6: "Group ride",
    }

    rate_code_dim = df[["RatecodeID"]].drop_duplicates().reset_index(drop=True)
    rate_code_dim.insert(0, "rate_code_id", range(len(rate_code_dim)))
    rate_code_dim["rate_code_name"] = (
        rate_code_dim["RatecodeID"].map(rate_code_type).fillna("Unknown")
    )
    rate_code_dim = rate_code_dim[
        ["rate_code_id", "RatecodeID", "rate_code_name"]
    ]

    # 5. Pickup location dimension
    pickup_location_dim = (
        df[["pickup_longitude", "pickup_latitude"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    pickup_location_dim.insert(0, "pickup_location_id", range(len(pickup_location_dim)))
    pickup_location_dim = pickup_location_dim[
        ["pickup_location_id", "pickup_latitude", "pickup_longitude"]
    ]

    # 6. Dropoff location dimension
    dropoff_location_dim = (
        df[["dropoff_longitude", "dropoff_latitude"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dropoff_location_dim.insert(0, "dropoff_location_id", range(len(dropoff_location_dim)))
    dropoff_location_dim = dropoff_location_dim[
        ["dropoff_location_id", "dropoff_latitude", "dropoff_longitude"]
    ]

    # 7. Payment type dimension
    payment_type_name = {
        1: "Credit card",
        2: "Cash",
        3: "No charge",
        4: "Dispute",
        5: "Unknown",
        6: "Voided trip",
    }

    payment_type_dim = (
        df[["payment_type"]].drop_duplicates().reset_index(drop=True)
    )
    payment_type_dim.insert(0, "payment_type_id", range(len(payment_type_dim)))
    payment_type_dim["payment_type_name"] = (
        payment_type_dim["payment_type"].map(payment_type_name).fillna("Unknown")
    )
    payment_type_dim = payment_type_dim[
        ["payment_type_id", "payment_type", "payment_type_name"]
    ]

    # Build the fact table by attaching the dimension IDs to each trip.
    fact_table = (
        df.merge(passenger_count_dim, on="passenger_count", how="left", validate="many_to_one")
        .merge(trip_distance_dim, on="trip_distance", how="left", validate="many_to_one")
        .merge(rate_code_dim, on="RatecodeID", how="left", validate="many_to_one")
        .merge(
            pickup_location_dim,
            on=["pickup_longitude", "pickup_latitude"],
            how="left",
            validate="many_to_one",
        )
        .merge(
            dropoff_location_dim,
            on=["dropoff_longitude", "dropoff_latitude"],
            how="left",
            validate="many_to_one",
        )
        .merge(
            datetime_dim[["datetime_id", "tpep_pickup_datetime", "tpep_dropoff_datetime"]],
            on=["tpep_pickup_datetime", "tpep_dropoff_datetime"],
            how="left",
            validate="many_to_one",
        )
        .merge(payment_type_dim, on="payment_type", how="left", validate="many_to_one")
    )

    fact_table = fact_table[
        [
            "VendorID",
            "datetime_id",
            "passenger_count_id",
            "trip_distance_id",
            "rate_code_id",
            "store_and_fwd_flag",
            "pickup_location_id",
            "dropoff_location_id",
            "payment_type_id",
            "fare_amount",
            "extra",
            "mta_tax",
            "tip_amount",
            "tolls_amount",
            "improvement_surcharge",
            "total_amount",
        ]
    ].copy()

    output = {
        "datetime_dim": datetime_dim,
        "passenger_count_dim": passenger_count_dim,
        "trip_distance_dim": trip_distance_dim,
        "rate_code_dim": rate_code_dim,
        "pickup_location_dim": pickup_location_dim,
        "dropoff_location_dim": dropoff_location_dim,
        "payment_type_dim": payment_type_dim,
        "fact_table": fact_table,
    }

    print(f"Rows in fact_table: {len(fact_table):,}")
    for table_name, table_df in output.items():
        print(f"{table_name}: {len(table_df):,} rows, {len(table_df.columns)} columns")

    return output


@test
def test_output(output, *args) -> None:
    assert isinstance(output, dict), "Transformer output must be a dictionary."
    expected_tables = {
        "datetime_dim",
        "passenger_count_dim",
        "trip_distance_dim",
        "rate_code_dim",
        "pickup_location_dim",
        "dropoff_location_dim",
        "payment_type_dim",
        "fact_table",
    }
    assert expected_tables.issubset(output.keys()), "One or more output tables are missing."
    assert not output["fact_table"].empty, "Fact table is empty."
    assert len(output["fact_table"].columns) == 16, "Fact table should have 16 columns."
