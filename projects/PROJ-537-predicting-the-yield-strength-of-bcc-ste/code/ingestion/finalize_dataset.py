import os
import sys
import logging
from pathlib import Path

# Add project root to path to ensure imports work when run from root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import CONFIG, ERR_INSUFFICIENT_DATA
from utils.logging import get_logger, log_provenance_event
from ingestion.merge_and_filter import validate_merged_dataset, save_merged_dataset

logger = get_logger(__name__)

def main():
    """
    Finalize the merged dataset for T017.
    
    Loads the intermediate merged data, validates it meets the minimum row count (>=20),
    and writes the final artifact to data/intermediate/merged.csv.
    Raises ERR_INSUFFICIENT_DATA if validation fails.
    """
    logger.info("Starting dataset finalization (T017)...")
    
    input_path = CONFIG.INTERMEDIATE_DIR / "merged.csv"
    output_path = CONFIG.INTERMEDIATE_DIR / "merged.csv"
    min_rows = 20

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Intermediate merged dataset not found at {input_path}. "
                                "Run ingestion pipeline first.")

    # Load and validate
    df, validation_result = validate_merged_dataset(input_path)

    if df is None:
        logger.error("Validation failed: could not load or parse dataset.")
        raise ValueError("Failed to load merged dataset.")

    row_count = len(df)
    logger.info(f"Loaded {row_count} rows from {input_path}")

    # Check minimum row constraint (FR-001 / US1 requirement)
    if row_count < min_rows:
        error_msg = f"{ERR_INSUFFICIENT_DATA}: Dataset has {row_count} rows, minimum required is {min_rows}."
        logger.error(error_msg)
        # Log provenance event for the failure
        log_provenance_event(
            event_type="dataset_validation_failed",
            details={"reason": ERR_INSUFFICIENT_DATA, "row_count": row_count, "min_required": min_rows}
        )
        raise SystemExit(error_msg)

    # Validate specific columns exist and are non-null (as per task description)
    # The validate_merged_dataset function should have already checked this,
    # but we double-check the specific constraints mentioned in T017.
    required_cols = ["yield_strength_MPa", "shear_modulus_GPa"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' missing from dataset.")
        null_count = df[col].isnull().sum()
        if null_count > 0:
            logger.warning(f"Column '{col}' has {null_count} null values. "
                           "These will be dropped or handled by downstream logic.")

    # Save the final dataset
    # Since input and output are the same in this context (overwriting/confirming),
    # we ensure it is saved cleanly.
    save_merged_dataset(df, output_path)
    
    logger.info(f"Successfully validated and saved merged dataset to {output_path} ({row_count} rows).")
    log_provenance_event(
        event_type="dataset_finalized",
        details={"path": str(output_path), "row_count": row_count, "min_rows": min_rows}
    )

    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            sys.exit(0)
    except Exception as e:
        logger.exception("Fatal error during T017 execution")
        sys.exit(1)