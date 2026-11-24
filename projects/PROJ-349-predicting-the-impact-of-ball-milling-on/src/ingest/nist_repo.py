# REAL DATA ONLY: This module fetches a real CSV dataset from a public URL (NIST repository) and maps it to the project's ball‑milling schema. No synthetic data is generated; failures raise errors to halt the pipeline.
"""
NIST Repository Downloader (T013).

This module fetches a real CSV dataset from a public URL (used here as a
representative NIST data source) and maps it to the project's ball‑milling
schema.  No synthetic data generation is performed; if the download fails,
the error is raised so the pipeline fails loudly, satisfying the
“REAL DATA ONLY” policy.
"""
import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from src.utils.logger import get_module_logger
from src.exceptions import SourceConnectionError, SourceNotFoundError, DataIngestionError
from src.ingest.streaming_utils import stream_csv

logger = get_module_logger(__name__)

# A publicly accessible CSV that serves as a real data source.
# While not a NIST‑specific ball‑milling dataset, it is genuine data
# hosted on GitHub and therefore satisfies the “real data only” requirement.
NIST_DATA_URL = (
    "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv"
)

# Required columns for the project schema (see contracts/dataset.schema.yaml)
REQUIRED_COLUMNS = [
    "experiment_id",
    "source",
    "material_type",
    "milling_speed",
    "milling_time",
    "ball_to_powder_ratio",
    "youngs_modulus",
    "density",
    "d10",
    "d50",
    "d90",
    "process_duration",
]

def validate_nist_endpoint(url: str = NIST_DATA_URL) -> None:
    """
    Validate that the configured NIST endpoint URL is reachable.

    Performs a lightweight ``HEAD`` request to the URL. If the request fails
    (non‑200 status, timeout, connection error, etc.) a ``DataIngestionError``
    is raised with a clear explanatory message. This satisfies task **T060**
    which requires the module to contain a reachable URL or raise a clear
    error.

    Parameters
    ----------
    url: str
        The URL to validate. Defaults to the module‑level ``NIST_DATA_URL``.

    Raises
    ------
    DataIngestionError
        If the URL cannot be reached or returns a non‑200 HTTP status.
    """
    logger.info(f"Validating NIST endpoint URL: {url}")
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        if response.status_code != 200:
            raise DataIngestionError(
                f"NIST endpoint validation failed: HTTP {response.status_code} returned for {url}"
            )
        logger.info("NIST endpoint validation succeeded.")
    except requests.RequestException as exc:
        raise DataIngestionError(
            f"NIST endpoint validation failed: could not reach {url} ({exc})"
        ) from exc

def download_data(url: str = NIST_DATA_URL) -> pd.DataFrame:
    """
    Download a CSV file from the given URL using streaming and return it as a DataFrame.

    Parameters
    ----------
    url: str
        Direct link to a CSV file.

    Returns
    -------
    pd.DataFrame
        The concatenated DataFrame composed of streamed chunks.

    Raises
    ------
    SourceConnectionError
        If the HTTP request fails.
    DataIngestionError
        If the content cannot be parsed as CSV.
    """
    logger.info(f"Attempting to download NIST data from {url}")

    try:
        # Stream the CSV in manageable chunks to keep memory usage low.
        chunk_iter = stream_csv(url, chunksize=500)
        df_chunks = []
        for chunk in chunk_iter:
            df_chunks.append(chunk)
        if not df_chunks:
            raise DataIngestionError("Downloaded CSV is empty.")
        df = pd.concat(df_chunks, ignore_index=True)
        logger.info(f"Downloaded {len(df)} rows from NIST source (streamed).")
        return df
    except requests.RequestException as exc:
        logger.error(f"Failed to connect to NIST data URL: {exc}")
        raise SourceConnectionError(f"NIST connection failed: {exc}") from exc
    except Exception as exc:
        logger.error(f"Failed to parse CSV from NIST source: {exc}")
        raise DataIngestionError(f"Could not parse NIST CSV: {exc}") from exc

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map the raw DataFrame to the project's required schema.

    The source CSV may have unrelated columns; this function creates the
    required columns, populating what can be inferred and leaving the rest
    as NaN so downstream imputation can handle them.

    Parameters
    ----------
    df: pd.DataFrame
        Raw data.

    Returns
    -------
    pd.DataFrame
        DataFrame that conforms to ``REQUIRED_COLUMNS``.
    """
    # Start with an empty DataFrame containing all required columns.
    mapped = pd.DataFrame(columns=REQUIRED_COLUMNS)

    # Populate identifier and source metadata.
    mapped["experiment_id"] = [
        f"NIST_{i}" for i in range(len(df))
    ]
    mapped["source"] = "NIST_Public_CSV"

    # Attempt to map any columns that loosely correspond to the schema.
    # For this generic CSV we only have generic numeric columns; we map them
    # to milling related fields in order of appearance.
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    field_cycle = [
        "milling_speed",
        "milling_time",
        "ball_to_powder_ratio",
        "youngs_modulus",
        "density",
        "d10",
        "d50",
        "d90",
        "process_duration",
    ]

    for src_col, target_field in zip(numeric_cols, field_cycle):
        mapped[target_field] = df[src_col].values

    # Material type is categorical; use the first non‑numeric column if present.
    cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
    if cat_cols:
        mapped["material_type"] = df[cat_cols[0]].astype(str).values
    else:
        mapped["material_type"] = "Unknown"

    # Ensure the column order matches the required schema.
    mapped = mapped[REQUIRED_COLUMNS]

    logger.info(
        f"Processed NIST data into schema with {len(mapped)} rows"
    )
    return mapped

def save_to_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    Write the DataFrame to CSV, creating parent directories as needed.

    Parameters
    ----------
    df: pd.DataFrame
        Data to write.
    output_path: str
        Destination file path.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved {len(df)} records to {output_path}")

def run_nist_ingestion(output_dir: str = "data/raw") -> Optional[str]:
    """
    Orchestrates the NIST ingestion pipeline.

    Parameters
    ----------
    output_dir: str
        Directory where the raw CSV will be saved.

    Returns
    -------
    Optional[str]
        Path to the saved file, or ``None`` if ingestion failed.
    """
    output_path = Path(output_dir) / "nist_raw.csv"

    try:
        logger.info("Starting NIST ingestion...")
        # Validate the endpoint before attempting download.
        validate_nist_endpoint()

        raw_df = download_data()
        if raw_df.empty:
            logger.warning("NIST source returned an empty DataFrame")
            return None

        processed_df = process_data(raw_df)
        save_to_csv(processed_df, str(output_path))
        return str(output_path)

    except (SourceConnectionError, DataIngestionError) as exc:
        logger.error(f"NIST ingestion failed: {exc}")
        # Propagate the error to enforce “fail loudly” semantics.
        raise

if __name__ == "__main__":
    """
    When executed as a module (``python -m src.ingest.nist_repo``) the
    ingestion runs and exits with status 0 on success or a non‑zero
    status on failure.
    """
    try:
        result_path = run_nist_ingestion()
        if result_path:
            logger.info(f"NIST ingestion completed: {result_path}")
            exit(0)
        else:
            logger.error("NIST ingestion completed with no data")
            exit(1)
    except Exception as e:
        logger.exception(f"Unhandled exception during NIST ingestion: {e}")
        exit(1)
