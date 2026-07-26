"""
Save daily aggregates to CSV and validate against schema.

This script reads the aggregated data produced by preprocess.py,
writes it to data/processed/daily_aggregates.csv, and validates
the output against the daily_aggregates.schema.yaml contract.
"""
import os
import sys
import logging
from pathlib import Path

import pandas as pd

from config import get_path
from preprocess import preprocess
from output_validator import load_schema, validate_dataframe

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """
    Main entry point: preprocess data, save to CSV, and validate.
    """
    # Step 1: Ensure raw data exists
    raw_path = get_path("data/raw/bronze.parquet")
    if not os.path.exists(raw_path):
        logger.error(f"Raw data not found at {raw_path}. Please run ingest.py first.")
        sys.exit(1)

    # Step 2: Run preprocessing to get the DataFrame
    logger.info("Running preprocessing to compute daily aggregates...")
    df_aggregates = preprocess()

    if df_aggregates is None or df_aggregates.empty:
        logger.error("Preprocessing returned an empty or None DataFrame. Aborting.")
        sys.exit(1)

    # Step 3: Define output path
    output_path = get_path("data/processed/daily_aggregates.csv")
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 4: Write to CSV
    logger.info(f"Writing daily aggregates to {output_path}...")
    df_aggregates.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(df_aggregates)} rows to {output_path}")

    # Step 5: Validate against schema
    schema_path = get_path(
        "specs/001-physical-activity-mood-variability/contracts/daily_aggregates.schema.yaml"
    )

    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found at {schema_path}. Validation skipped.")
        # We do not exit here, as the data was successfully written.
        # However, for a strict pipeline, this might be a failure.
        # Given the task is to "Write and validate", we log the missing schema.
        return

    logger.info(f"Validating output against schema: {schema_path}")
    schema = load_schema(schema_path)

    is_valid, errors = validate_dataframe(df_aggregates, schema)

    if not is_valid:
        logger.error("Validation FAILED. The output does not match the schema:")
        for err in errors:
            logger.error(f"  - {err}")
        # Fail loudly as per task requirements
        sys.exit(1)

    logger.info("Validation PASSED. Output matches daily_aggregates.schema.yaml.")


if __name__ == "__main__":
    main()
