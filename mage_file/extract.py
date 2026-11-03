import io
import pandas as pd
import requests

if "data_loader" not in globals():
    from mage_ai.data_preparation.decorators import data_loader

if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data_from_api(*args, **kwargs):
    """
    Extract Uber trip data from the project's Google Cloud Storage CSV.
    Mage calls this block a Data Loader, although it performs extraction
    from the source and loads the response into a pandas DataFrame.
    """
    url = "https://storage.googleapis.com/uber-data-engineer-sonu/uber_data.csv"

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    df = pd.read_csv(io.BytesIO(response.content))

    if df.empty:
        raise ValueError("The source CSV was downloaded, but it contains no rows.")

    print(f"Extracted {len(df):,} rows and {len(df.columns)} columns.")
    print("Columns:", df.columns.tolist())

    return df


@test
def test_output(output, *args) -> None:
    assert output is not None, "The output is undefined."
    assert isinstance(output, pd.DataFrame), "Expected a pandas DataFrame."
    assert not output.empty, "The extracted DataFrame is empty."
    assert "tpep_pickup_datetime" in output.columns
    assert "tpep_dropoff_datetime" in output.columns
