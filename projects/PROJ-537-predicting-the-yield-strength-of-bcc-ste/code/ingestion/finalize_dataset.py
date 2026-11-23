"""
finalize_dataset.py

Implements Task T017: Write the final merged dataset to data/intermediate/merged.csv
and verify row count >= 20. Raises ERR_INSUFFICIENT_DATA if not.

This module is responsible for the final validation and persistence step of the
ingestion pipeline (User Story 1). It ensures that the merged dataset meets the
minimum row threshold required for subsequent modeling tasks.
"""
import os
import sys
import logging
from pathlib import Path

# Import from local project structure
from config import CONFIG, ERR_INSUFFICIENT_DATA
from utils.logging import get_logger, log_provenance_event

logger = get_logger(__name__)


def validate_and_save_merged_dataset(
    input_df,
    output_path: Path,
    min_rows: int = 20
) -> bool:
    """
    Validates the merged dataset and saves it to the specified output path.

    Args:
        input_df (pd.DataFrame): The merged dataframe from previous ingestion steps.
        output_path (Path): Path where the CSV should be saved.
        min_rows (int): Minimum required number of rows (default 20).

    Returns:
        bool: True if validation and save successful.

    Raises:
        ValueError: If the dataset has fewer than min_rows.
        RuntimeError: If file I/O fails.
    """
    if input_df is None or input_df.empty:
        logger.error("Input dataframe is empty or None.")
        raise ValueError("Input dataframe is empty or None.")

    row_count = len(input_df)
    logger.info(f"Validating merged dataset: {row_count} rows found.")

    # Check for critical columns being non-null
    required_cols = ['yield_strength_MPa', 'shear_modulus_GPa']
    for col in required_cols:
        if col not in input_df.columns:
            logger.error(f"Required column '{col}' missing from merged dataset.")
            raise ValueError(f"Required column '{col}' missing.")

    null_counts = input_df[required_cols].isnull().sum()
    if null_counts.any():
        logger.warning(f"Null values found in required columns: {null_counts[null_counts > 0].to_dict()}")
        # Note: We do not drop rows here as merge_and_filter.py should have handled nulls.
        # If rows are dropped here, we must re-check the count.
        valid_mask = input_df[required_cols].notnull().all(axis=1)
        valid_count = valid_mask.sum()
        logger.info(f"Rows with valid required columns: {valid_count}")
        
        if valid_count < min_rows:
            logger.error(f"Insufficient valid rows ({valid_count}) after null check. Minimum required: {min_rows}")
            raise ValueError(ERR_INSUFFICIENT_DATA)
        
        # Filter to valid rows for saving
        output_df = input_df[valid_mask].reset_index(drop=True)
    else:
        output_df = input_df
        valid_count = row_count

    if valid_count < min_rows:
        logger.error(f"Insufficient rows ({valid_count}) in merged dataset. Minimum required: {min_rows}")
        raise ValueError(ERR_INSUFFICIENT_DATA)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        output_df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved merged dataset to {output_path} ({valid_count} rows).")
        
        # Log provenance
        log_provenance_event(
            event_type="dataset_saved",
            details={
                "path": str(output_path),
                "row_count": valid_count,
                "min_required": min_rows,
                "status": "success"
            }
        )
        return True
    except Exception as e:
        logger.error(f"Failed to save merged dataset: {e}")
        raise RuntimeError(f"Failed to save dataset: {e}")


def main():
    """
    Main entry point for the finalize dataset task.
    Reads the intermediate merged data, validates it, and saves the final version.
    """
    logger.info("Starting finalize_dataset task (T017)...")

    # Define paths based on config
    input_path = CONFIG.MERGED_DATA_PATH
    output_path = CONFIG.MERGED_DATA_PATH  # Overwrite the intermediate with the validated one, or save to a new name?
    # According to tasks.md: "Write the final merged dataset to data/intermediate/merged.csv"
    # We assume the input from merge_and_filter.py is already at CONFIG.MERGED_DATA_PATH
    # We will validate and save it back to the same path (or a slightly different one if needed).
    # Let's assume the previous step wrote to a temp or the same path, and we finalize it here.
    # To be safe, we read from CONFIG.MERGED_DATA_PATH and write to CONFIG.MERGED_DATA_PATH.
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("The merge_and_filter.py step must run successfully before this task.")
        sys.exit(1)

    try:
        import pandas as pd
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read input CSV: {e}")
        sys.exit(1)

    try:
        validate_and_save_merged_dataset(df, input_path, min_rows=20)
        logger.info("Task T017 completed successfully.")
    except ValueError as e:
        if str(e) == ERR_INSUFFICIENT_DATA:
            logger.critical(f"CRITICAL: {ERR_INSUFFICIENT_DATA}")
            # This is a hard stop for the pipeline
            sys.exit(1)
        else:
            logger.critical(f"Validation failed: {e}")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during finalization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
