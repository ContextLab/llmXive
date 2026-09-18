import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Optional, Union
from datasets import load_dataset

# ---------------------------------------------------------------------------
# Exception Definitions
# ---------------------------------------------------------------------------

class DataSchemaError(Exception):
    """
    Exception raised when the input dataset does not conform to the required
    schema for the experimental design.

    This typically occurs when mandatory columns (e.g., 'recommended_categories',
    'enrolled_categories') are missing from the provided DataFrame or file.
    """
    pass

# ---------------------------------------------------------------------------
# Validation Logic
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = ['recommended_categories', 'enrolled_categories']

def validate_schema(df: pd.DataFrame) -> None:
    """
    Validates that the input DataFrame contains the required columns for the
    experimental design.

    Parameters
    ----------
    df : pd.DataFrame
        The dataset to validate.

    Raises
    ------
    DataSchemaError
        If 'recommended_categories' or 'enrolled_categories' are missing.
        The error message will be exactly:
        "Required columns [recommended_categories, enrolled_categories] missing. Dataset does not support the specified experimental design."
    """
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing_cols:
        # Format the missing columns exactly as requested in the task spec
        missing_str = str(missing_cols)
        msg = f"Required columns {missing_str} missing. Dataset does not support the specified experimental design."
        raise DataSchemaError(msg)

    # If we reach here, validation passed
    logging.debug("Schema validation passed: all required columns present.")

# ---------------------------------------------------------------------------
# Data Loading Helpers
# ---------------------------------------------------------------------------

def load_data_from_hf(dataset_name: str, split: str = "train") -> pd.DataFrame:
    """
    Loads a dataset from the Hugging Face Hub.

    Parameters
    ----------
    dataset_name : str
        The name of the dataset on Hugging Face.
    split : str
        The split to load (default: "train").

    Returns
    -------
    pd.DataFrame
        The loaded dataset as a Pandas DataFrame.
    """
    try:
        ds = load_dataset(dataset_name, split=split)
        return ds.to_pandas()
    except Exception as e:
        logging.error(f"Failed to load dataset '{dataset_name}' from Hugging Face: {e}")
        raise

def ingest_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs basic cleaning on the ingested DataFrame.

    - Validates schema (raises DataSchemaError if invalid).
    - Logs warnings for rows with empty enrolled_categories.
    - Excludes rows where 'enrolled_categories' is empty (or represents an empty list).

    Parameters
    ----------
    df : pd.DataFrame
        The raw DataFrame.

    Returns
    -------
    pd.DataFrame
        The cleaned DataFrame.
    """
    # 1. Validate Schema
    validate_schema(df)

    initial_count = len(df)
    logging.info(f"Starting ingestion with {initial_count} rows.")

    # 2. Handle Empty Enrollments
    # We assume 'enrolled_categories' is stored as a string representation of a list
    # or an actual list. We need to filter out empty ones.
    def is_empty(val):
        if isinstance(val, list):
            return len(val) == 0
        if isinstance(val, str):
            return val.strip() == "" or val == "[]"
        return False

    # Filter out rows with empty enrollments
    # Note: Using apply for robustness against mixed types (str vs list)
    mask = df['enrolled_categories'].apply(lambda x: not is_empty(x))
    cleaned_df = df[mask].copy()
    excluded_count = initial_count - len(cleaned_df)

    if excluded_count > 0:
        logging.warning(f"Excluded {excluded_count} rows with empty 'enrolled_categories'.")
    else:
        logging.debug("No rows excluded due to empty enrollments.")

    logging.info(f"Ingestion complete. Final row count: {len(cleaned_df)}")
    return cleaned_df

def load_project_data(data_path: Union[str, Path]) -> pd.DataFrame:
    """
    Loads data from a local file (CSV or Parquet) and ingests it.

    Parameters
    ----------
    data_path : Union[str, Path]
        Path to the data file.

    Returns
    -------
    pd.DataFrame
        The cleaned DataFrame.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    DataSchemaError
        If the file content does not match the required schema.
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    logging.info(f"Loading data from {path}")

    if path.suffix == '.csv':
        df = pd.read_csv(path)
    elif path.suffix == '.parquet':
        df = pd.read_parquet(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .csv or .parquet.")

    return ingest_and_clean(df)
