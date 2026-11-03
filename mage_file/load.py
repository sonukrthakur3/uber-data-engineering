from os import path

from pandas import DataFrame

from mage_ai.data_preparation.repo_manager import get_repo_path
from mage_ai.io.bigquery import BigQuery
from mage_ai.io.config import ConfigFileLoader

if "data_exporter" not in globals():
    from mage_ai.data_preparation.decorators import data_exporter


@data_exporter
def export_data_to_big_query(data, **kwargs) -> None:
    """
    Export each DataFrame returned by the Transformer to BigQuery.

    Before running this block:
    1. Configure the Google Cloud credentials in io_config.yaml.
    2. Ensure the VM/service account has permission to create or replace
       tables in the target BigQuery dataset.
    """

    config_path = path.join(get_repo_path(), "io_config.yaml")
    config_profile = "default"

    project_id = "uber-513106"
    dataset_id = "uber_data_engineering"

    for table_name, table_data in data.items():
        table_id = f"{project_id}.{dataset_id}.{table_name}"

        # Transformer returns pandas DataFrames. This also accepts
        # dictionary-like table data if the block output is changed later.
        dataframe = (
            table_data.copy()
            if isinstance(table_data, DataFrame)
            else DataFrame(table_data)
        )

        print(f"Exporting {table_name}: {len(dataframe):,} rows")

        BigQuery.with_config(
            ConfigFileLoader(config_path, config_profile)
        ).export(
            dataframe,
            table_id,
            if_exists="replace",
        )

        print(f"Successfully exported: {table_id}")
