import os
import sys
import logging
from pathlib import Path
from config import CONFIG, ERR_INSUFFICIENT_DATA
from utils.logging import get_logger, log_provenance_event
import pandas as pd

logger = get_logger(__name__)

def validate_and_save_merged_dataset(input_path: Path, output_path: Path, min_rows: int = 20) -> None:
    """
    Load the merged dataset, verify it meets the minimum row count requirement,
    and save it to the final intermediate location.
    
    Args:
        input_path: Path to the temporary merged dataset (e.g., from merge_and_filter)
        output_path: Path where the final validated dataset should be saved
        min_rows: Minimum number of rows required (default 20)
        
    Raises:
        SystemExit: If row count is below min_rows, triggering ERR_INSUFFICIENT_DATA
    """
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading merged dataset from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise
    
    current_rows = len(df)
    logger.info(f"Merged dataset contains {current_rows} rows")
    
    # Check for critical columns to ensure data integrity
    required_cols = ['yield_strength_MPa', 'shear_modulus_GPa']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Check for non-null values in critical columns
    null_count = df[required_cols].isnull().sum()
    if null_count.any():
        logger.warning(f"Found null values in critical columns:\n{null_count[null_count > 0]}")
        # Optionally drop rows with null critical values
        initial_count = len(df)
        df = df.dropna(subset=required_cols)
        dropped = initial_count - len(df)
        if dropped > 0:
            logger.info(f"Dropped {dropped} rows due to null critical values")
    
    final_rows = len(df)
    logger.info(f"Dataset after null handling: {final_rows} rows")
    
    if final_rows < min_rows:
        error_msg = f"{ERR_INSUFFICIENT_DATA}: Dataset has {final_rows} rows, minimum required is {min_rows}"
        logger.error(error_msg)
        # Log provenance event for the failure
        log_provenance_event(
            event_type="validation_failed",
            details={"reason": ERR_INSUFFICIENT_DATA, "rows_found": final_rows, "rows_required": min_rows},
            logger=logger
        )
        raise SystemExit(error_msg)
    
    logger.info(f"Validation passed: {final_rows} >= {min_rows} rows")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the validated dataset
    logger.info(f"Saving validated dataset to {output_path}")
    df.to_csv(output_path, index=False)
    
    log_provenance_event(
        event_type="dataset_finalized",
        details={"rows": final_rows, "path": str(output_path)},
        logger=logger
    )
    
    logger.info("Dataset finalization complete")

def main():
    """
    Entry point for finalizing the merged dataset.
    Loads intermediate results, validates row count, and saves final artifact.
    """
    # Define paths based on CONFIG
    input_path = CONFIG.INTERMEDIATE_DIR / "merged_temp.csv"
    output_path = CONFIG.INTERMEDIATE_DIR / "merged.csv"
    
    # Allow override via environment variable for testing flexibility
    if os.getenv("OVERRIDE_INPUT_PATH"):
        input_path = Path(os.getenv("OVERRIDE_INPUT_PATH"))
    
    try:
        validate_and_save_merged_dataset(input_path, output_path, min_rows=20)
        print(f"Success: Final dataset saved to {output_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Validation Error: {e}")
        sys.exit(1)
    except SystemExit as e:
        print(f"Fatal Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during finalization")
        print(f"Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()