"""
Variable Engineering Pipeline (T017, T018, T019).

This module handles the transformation of raw ingested data into the final
cleaned dataset required for modeling. It computes derived variables,
handles missing outcomes, and validates the output against the schema contract.

Workflow:
1. Load raw CSVs from `data/raw/`.
2. Engineer `switching_index` = `num_platforms` * `self_reported_switching_frequency`.
3. Exclude rows with missing `cognitive_flexibility_score`.
4. Save result to `data/processed/participants_cleaned.csv`.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd
import yaml

# Import local utilities
from utils import log_setup
from config import ensure_directories


def load_schema_contract(schema_path: str) -> dict:
    """
    Load the dataset schema contract from a YAML file.

    Args:
        schema_path: Relative path to the schema YAML file.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema contract not found at {schema_path}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_schema_structure(df: pd.DataFrame, schema: dict) -> bool:
    """
    Validate that the dataframe contains the columns defined in the schema.

    Args:
        df: The DataFrame to validate.
        schema: The schema dictionary containing 'required_columns'.

    Returns:
        True if validation passes.

    Raises:
        ValueError: If required columns are missing.
    """
    required_cols = schema.get('required_columns', [])
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns from schema: {missing}")
    return True


def parse_raw_file(file_path: str) -> pd.DataFrame:
    """
    Parse a raw CSV file from data/raw/ into a DataFrame.

    Attempts to decode the file using common encodings (utf-8, latin-1, cp1252).

    Args:
        file_path: Path to the CSV file.

    Returns:
        Parsed DataFrame.

    Raises:
        ValueError: If decoding fails for all attempted encodings.
        Exception: If other parsing errors occur.
    """
    encodings = ['utf-8', 'latin-1', 'cp1252']
    last_error = None

    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            logging.debug(f"Successfully decoded {file_path} with {encoding}")
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            last_error = e
            continue

    if last_error:
        raise last_error
    raise ValueError(f"Could not decode file {file_path} with common encodings.")


def engineer_switching_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the derived variable: switching_index = num_platforms * self_reported_switching_frequency.

    Ensures numeric types for source variables, coercing errors to NaN.

    Args:
        df: Input DataFrame containing source variables.

    Returns:
        DataFrame with the new 'switching_index' column added.

    Raises:
        ValueError: If source variables are missing.
    """
    required_sources = ['num_platforms', 'self_reported_switching_frequency']
    missing = [col for col in required_sources if col not in df.columns]
    if missing:
        raise ValueError(f"Missing source variables for switching_index engineering: {missing}")

    # Ensure numeric types, coercing errors to NaN
    df['num_platforms'] = pd.to_numeric(df['num_platforms'], errors='coerce')
    df['self_reported_switching_frequency'] = pd.to_numeric(
        df['self_reported_switching_frequency'], errors='coerce'
    )

    # Compute derived variable
    df['switching_index'] = df['num_platforms'] * df['self_reported_switching_frequency']

    stats = {
        'mean': df['switching_index'].mean(),
        'count': len(df),
        'non_null': df['switching_index'].notna().sum()
    }
    logging.info(
        f"Engineered switching_index. Mean: {stats['mean']:.2f}, "
        f"Total Count: {stats['count']}, Non-Null: {stats['non_null']}"
    )
    return df


def handle_missing_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing outcomes by excluding rows with missing `cognitive_flexibility_score`.

    Logs the number of excluded rows.

    Args:
        df: Input DataFrame.

    Returns:
        Cleaned DataFrame with missing outcomes removed.
    """
    outcome_col = 'cognitive_flexibility_score'
    if outcome_col not in df.columns:
        logging.warning(
            f"Column '{outcome_col}' not found. Skipping missing outcome handling."
        )
        return df

    initial_count = len(df)
    df_clean = df.dropna(subset=[outcome_col])
    excluded_count = initial_count - len(df_clean)

    if excluded_count > 0:
        logging.info(f"Excluded {excluded_count} rows due to missing {outcome_col}.")
    else:
        logging.info(f"No rows excluded due to missing {outcome_col}.")

    return df_clean


def validate_and_save(df: pd.DataFrame, output_path: str, schema: dict) -> None:
    """
    Perform final validation against schema and save the DataFrame to CSV.

    Args:
        df: The DataFrame to save.
        output_path: Destination path for the CSV file.
        schema: Schema dictionary for validation.

    Raises:
        ValueError: If validation fails.
        IOError: If file writing fails.
    """
    # Validate structure again after engineering
    validate_schema_structure(df, schema)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)
    logging.info(
        f"Saved cleaned data to {output_path} "
        f"({len(df)} rows, {len(df.columns)} columns)."
    )


def load_all_raw_data(raw_dir: Path) -> List[pd.DataFrame]:
    """
    Load all CSV files from the raw directory.

    Args:
        raw_dir: Path to the raw data directory.

    Returns:
        List of DataFrames.
    """
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV files found in {raw_dir}")

    dfs = []
    for file in csv_files:
        logging.info(f"Loading raw file: {file}")
        try:
            df = parse_raw_file(str(file))
            dfs.append(df)
        except Exception as e:
            logging.error(f"Failed to load {file}: {e}")
            raise

    return dfs


def main():
    """
    Main entry point for the variable engineering pipeline (T019).

    Orchestrates the loading, engineering, cleaning, and saving of data.
    """
    # Setup logging
    logger = log_setup()
    ensure_directories()

    # Configuration
    schema_path = "contracts/dataset.schema.yaml"
    raw_dir = Path("data/raw")
    output_path = "data/processed/participants_cleaned.csv"

    # Load schema contract
    try:
        schema = load_schema_contract(schema_path)
    except FileNotFoundError as e:
        logging.error(f"Schema error: {e}")
        sys.exit(1)

    # Step 1: Load raw data
    try:
        dfs = load_all_raw_data(raw_dir)
    except (FileNotFoundError, ValueError) as e:
        logging.error(f"Data loading failed: {e}")
        sys.exit(1)

    if not dfs:
        logging.error("No data loaded from raw directory.")
        sys.exit(1)

    # Combine datasets
    combined_df = pd.concat(dfs, ignore_index=True)
    logging.info(f"Combined dataset shape: {combined_df.shape}")

    # Step 2: Engineer switching_index (T017)
    try:
        combined_df = engineer_switching_index(combined_df)
    except ValueError as e:
        logging.error(f"Engineering failed: {e}")
        sys.exit(1)

    # Step 3: Handle missing outcomes (T018)
    combined_df = handle_missing_outcomes(combined_df)

    # Step 4: Output final cleaned CSV (T019)
    try:
        validate_and_save(combined_df, output_path, schema)
    except Exception as e:
        logging.error(f"Failed to save output: {e}")
        sys.exit(1)

    logging.info("Variable engineering pipeline completed successfully.")


if __name__ == "__main__":
    main()