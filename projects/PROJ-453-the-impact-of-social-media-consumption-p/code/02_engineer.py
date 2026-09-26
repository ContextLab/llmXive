"""
Variable Engineering Module for Social Media Cognitive Flexibility Study.

This module handles the transformation of raw dataset variables into derived
features (e.g., switching_index), handles missing data, and validates the
output against the project schema.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd

# Import project utilities
from config import DATA_ROOT
from logging_config import get_logger
from utils import checksum_file

logger = get_logger(__name__)

# Constants
SCHEMA_PATH = Path("contracts/dataset.schema.yaml")
RAW_DATA_DIR = Path(DATA_ROOT) / "raw"
PROCESSED_DATA_DIR = Path(DATA_ROOT) / "processed"
OUTPUT_FILE = PROCESSED_DATA_DIR / "participants_cleaned.csv"


def load_schema_contract() -> Dict[str, Any]:
    """
    Load the dataset schema contract from the YAML file.

    Returns:
        Dict[str, Any]: The schema definition dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is malformed.
    """
    try:
        import yaml
        with open(SCHEMA_PATH, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Schema contract not found at {SCHEMA_PATH}")
        raise
    except Exception as e:
        logger.error(f"Failed to load schema contract: {e}")
        raise


def validate_schema_structure(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Validate that the DataFrame columns match the schema keys.

    Args:
        df: The DataFrame to validate.
        schema: The schema dictionary containing expected column names.

    Returns:
        bool: True if validation passes.

    Raises:
        ValueError: If columns are missing or types do not match.
    """
    expected_columns = schema.get('columns', [])
    missing_columns = [col for col in expected_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Data Gap: Schema mismatch. Missing columns: {missing_columns}")

    logger.info("Schema validation passed.")
    return True


def load_all_raw_data() -> List[pd.DataFrame]:
    """
    Load all available raw CSV files from the data/raw directory.

    Returns:
        List[pd.DataFrame]: A list of DataFrames, one for each raw CSV file found.

    Raises:
        FileNotFoundError: If no raw CSV files are found in the directory.
    """
    if not RAW_DATA_DIR.exists():
        raise FileNotFoundError(f"Raw data directory not found: {RAW_DATA_DIR}")

    raw_files = list(RAW_DATA_DIR.glob("*.csv"))

    if not raw_files:
        logger.error("No raw CSV files found in data/raw/")
        raise FileNotFoundError("No raw CSV files found in data/raw/")

    dataframes = []
    for file_path in raw_files:
        logger.info(f"Loading raw data from {file_path}")
        try:
            df = pd.read_csv(file_path)
            dataframes.append(df)
            logger.info(f"Loaded {len(df)} rows from {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            raise

    return dataframes


def engineer_switching_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the derived variable `switching_index`.

    Formula: switching_index = num_platforms * self_reported_switching_frequency

    Args:
        df: The input DataFrame containing raw variables.

    Returns:
        pd.DataFrame: The DataFrame with the new `switching_index` column added.

    Raises:
        ValueError: If required source columns are missing.
    """
    required_cols = ['num_platforms', 'self_reported_switching_frequency']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Data Gap: Missing source columns for switching_index: {missing}")

    df['switching_index'] = df['num_platforms'] * df['self_reported_switching_frequency']
    logger.info("Engineered switching_index column.")
    return df


def handle_missing_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Exclude rows where the outcome variable (cognitive_flexibility_score) is missing.

    Args:
        df: The input DataFrame.

    Returns:
        pd.DataFrame: The DataFrame with missing outcome rows removed.
    """
    outcome_col = 'cognitive_flexibility_score'
    if outcome_col not in df.columns:
        # If the column doesn't exist, we can't check for missing outcomes
        # but we should have caught this in schema validation earlier.
        logger.warning(f"Outcome column '{outcome_col}' not found in data.")
        return df

    original_count = len(df)
    df_clean = df.dropna(subset=[outcome_col])
    excluded_count = original_count - len(df_clean)

    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} rows due to missing {outcome_col}.")
    else:
        logger.info("No rows excluded due to missing outcomes.")

    return df_clean


def validate_and_save(df: pd.DataFrame, output_path: Path) -> None:
    """
    Validate the final DataFrame against the output schema and save to CSV.

    Args:
        df: The final processed DataFrame.
        output_path: The path where the CSV should be saved.

    Raises:
        ValueError: If the DataFrame does not contain all required output columns.
    """
    # Define required output columns based on T017 spec
    required_output_cols = [
        'participant_id', 'age', 'total_screen_time', 'num_platforms',
        'switching_frequency', 'switching_index', 'cognitive_flexibility_score'
    ]

    missing_cols = [c for c in required_output_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Data Gap: Output missing required columns: {missing_cols}")

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")

    # Log checksum
    checksum = checksum_file(output_path)
    logger.info(f"Output file checksum (MD5): {checksum}")


def main() -> None:
    """
    Main entry point for the variable engineering pipeline.
    """
    logger.info("Starting variable engineering pipeline.")

    try:
        # 1. Load Schema
        schema = load_schema_contract()

        # 2. Load Raw Data
        raw_dfs = load_all_raw_data()

        # 3. Process each dataset (assuming one per file or merged)
        # For this pipeline, we assume raw files are already filtered/merged or processed individually.
        # We will concatenate them if multiple exist, or process the single one.
        if len(raw_dfs) == 1:
            df = raw_dfs[0]
        else:
            logger.info(f"Concatenating {len(raw_dfs)} raw datasets.")
            df = pd.concat(raw_dfs, ignore_index=True)

        # 4. Validate Input Schema
        validate_schema_structure(df, schema)

        # 5. Engineer Variables
        df = engineer_switching_index(df)

        # 6. Handle Missing Outcomes
        df = handle_missing_outcomes(df)

        # 7. Validate and Save
        validate_and_save(df, OUTPUT_FILE)

        logger.info("Variable engineering pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
