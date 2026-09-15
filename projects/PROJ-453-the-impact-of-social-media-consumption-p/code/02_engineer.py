import os
import sys
import logging
import yaml
import pandas as pd
from pathlib import Path

from config import DATA_ROOT
from utils import log_setup

# Initialize logger for this module
logger = log_setup()

def load_schema_contract():
    """Load the dataset schema contract from YAML."""
    schema_path = Path(DATA_ROOT).parent / "contracts" / "dataset.schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema contract not found at {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_schema_structure(df, schema):
    """Validate DataFrame columns against schema."""
    required_cols = schema.get("required_columns", [])
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def parse_raw_file(raw_path):
    """Parse raw file into DataFrame."""
    logger.info(f"Parsing raw file: {raw_path}")
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw file not found: {raw_path}")
    df = pd.read_csv(raw_path)
    logger.info(f"Parsed {len(df)} rows from {raw_path}")
    return df

def engineer_switching_index(df):
    """Compute switching_index = num_platforms * self_reported_switching_frequency."""
    logger.info("Engineering switching_index variable.")
    if "num_platforms" not in df.columns or "self_reported_switching_frequency" not in df.columns:
        logger.error("Required columns for switching_index missing.")
        raise ValueError("Missing columns for switching_index calculation")
    df["switching_index"] = df["num_platforms"] * df["self_reported_switching_frequency"]
    logger.info("switching_index calculated successfully.")
    return df

def handle_missing_outcomes(df):
    """Exclude rows with missing cognitive_flexibility_score and log count."""
    logger.info("Handling missing outcome values.")
    initial_count = len(df)
    df = df.dropna(subset=["cognitive_flexibility_score"])
    excluded_count = initial_count - len(df)
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} rows due to missing cognitive_flexibility_score.")
    else:
        logger.info("No rows excluded due to missing outcomes.")
    return df

def validate_and_save(df, output_path):
    """Validate and save processed data."""
    logger.info(f"Validating and saving data to {output_path}")
    schema = load_schema_contract()
    if not validate_schema_structure(df, schema):
        raise ValueError("Schema validation failed")
    df.to_csv(output_path, index=False)
    logger.info(f"Data saved to {output_path}")

def main():
    """Main entry point for engineering."""
    logger.info("Starting variable engineering pipeline.")
    # Example flow (would be parameterized in real usage)
    # df = parse_raw_file("data/processed/ingested.csv")
    # df = engineer_switching_index(df)
    # df = handle_missing_outcomes(df)
    # validate_and_save(df, "data/processed/participants_cleaned.csv")
    logger.info("Engineering pipeline completed.")

if __name__ == "__main__":
    main()
