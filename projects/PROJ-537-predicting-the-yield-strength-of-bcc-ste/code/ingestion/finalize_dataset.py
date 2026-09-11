import os
import sys
import logging
from pathlib import Path
from config import CONFIG, ERR_INSUFFICIENT_DATA
from utils.logging import get_logger, log_provenance_event

logger = get_logger(__name__)

def validate_and_save_merged_dataset(input_path: str, output_path: str, min_rows: int = 20) -> bool:
    """
    Validates the merged dataset has at least min_rows rows with non-null critical fields
    and saves it to the output path. Raises ERR_INSUFFICIENT_DATA if validation fails.
    """
    import pandas as pd

    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise

    logger.info(f"Loaded {len(df)} rows from {input_path}")

    # Critical columns required for the downstream pipeline
    required_cols = ['yield_strength_MPa', 'shear_modulus_GPa']
    for col in required_cols:
        if col not in df.columns:
            msg = f"Missing required column: {col}"
            logger.error(msg)
            raise KeyError(msg)

    # Filter out rows with nulls in critical columns
    valid_df = df.dropna(subset=required_cols)
    valid_count = len(valid_df)

    logger.info(f"Rows with non-null {required_cols}: {valid_count}")

    if valid_count < min_rows:
        msg = f"{ERR_INSUFFICIENT_DATA}: Valid rows ({valid_count}) < required minimum ({min_rows})"
        logger.error(msg)
        # Raise the specific error defined in config to halt the pipeline
        raise RuntimeError(msg)

    # Save the validated dataframe
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    valid_df.to_csv(output_path, index=False)
    logger.info(f"Saved {valid_count} validated rows to {output_path}")

    # Log provenance
    log_provenance_event(
        event_type="dataset_validated",
        details={
            "input_file": input_path,
            "output_file": output_path,
            "total_rows_loaded": len(df),
            "valid_rows": valid_count,
            "min_rows_required": min_rows
        }
    )

    return True

def main():
    """
    Entry point for T017: Validate and save the merged dataset.
    Reads from data/intermediate/merged_raw.csv (produced by merge_and_filter)
    and writes to data/intermediate/merged.csv.
    """
    # Determine paths based on CONFIG
    # Assuming merge_and_filter.py writes a raw intermediate file first
    input_file = CONFIG.INTERMEDIATE_DIR / "merged_raw.csv"
    output_file = CONFIG.INTERMEDIATE_DIR / "merged.csv"

    # If the raw file doesn't exist, check if the final one was already created
    # or if we need to trigger the merge step. For this specific task, we assume
    # the previous task (T015/T016) produced the raw intermediate.
    if not input_file.exists():
        # Fallback: maybe merge_and_filter writes directly? Check common names.
        # If strictly following T015/T016, they might write to a temp or raw file.
        # Let's check if the output already exists (idempotency) or fail.
        if output_file.exists():
            logger.warning("Output file already exists. Skipping validation.")
            return True
        else:
            logger.error(f"Input file {input_file} not found. Ensure T015/T016 ran successfully.")
            raise FileNotFoundError(f"Input file {input_file} not found")

    try:
        validate_and_save_merged_dataset(
            input_path=str(input_file),
            output_path=str(output_file),
            min_rows=20
        )
        logger.info("T017 completed successfully.")
    except RuntimeError as e:
        if ERR_INSUFFICIENT_DATA in str(e):
            logger.critical(f"Pipeline halted: {e}")
            sys.exit(1)
        raise

if __name__ == "__main__":
    main()