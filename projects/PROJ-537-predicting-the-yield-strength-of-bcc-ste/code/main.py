"""
Main orchestration script for the BCC steel yield‑strength pipeline.

Adjustments made for T048:
* The validation step now runs **after** the ingestion pipeline (the original
  order caused a premature ERR_INSUFFICIENT_DATA).
* After successful ingestion we invoke the checksum generator so that
  ``data/provenance/checksums.txt`` is refreshed.
* Minor defensive logging added for clarity.
"""

import sys
import argparse
import logging
from pathlib import Path

# Local imports
from config import CONFIG, ERR_INSUFFICIENT_DATA
from utils.logging import get_logger, log_provenance_event

logger = get_logger(__name__)

def validate_dataset_min_rows(min_rows: int = 20) -> bool:
    """
    Validate that the intermediate merged dataset meets the minimum row requirement.
    """
    import pandas as pd

    merged_path = Path(CONFIG.MERGED_DATA_PATH)
    if not merged_path.is_file():
        logger.error(f"Merged dataset not found at {merged_path}")
        log_provenance_event("validation_failed", dataset_not_found=str(merged_path))
        sys.exit(1)

    df = pd.read_csv(merged_path)
    row_count = len(df)
    logger.info(f"Merged dataset contains {row_count} rows")

    if row_count < min_rows:
        msg = f"{ERR_INSUFFICIENT_DATA}: only {row_count} rows (minimum {min_rows})"
        logger.error(msg)
        log_provenance_event("validation_failed", error=msg, rows=row_count)
        sys.exit(1)

    required_cols = ["yield_strength_MPa", "shear_modulus_GPa"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        sys.exit(1)

    if df[required_cols].isnull().any().any():
        logger.warning("Null values found in required columns – proceeding (they should have been cleaned).")

    logger.info("Dataset validation passed")
    return True

def run_ingestion_pipeline():
    """Execute the data ingestion pipeline (US1)."""
    logger.info("Starting ingestion pipeline")
    try:
        from ingestion.fetch_experimental import fetch_experimental_data
        from ingestion.fetch_dft import fetch_dft_data
        from ingestion.merge_and_filter import main as merge_and_filter_main

        # Step 1 – experimental data
        fetch_experimental_data()

        # Step 2 – DFT data (writes RAW DFT CSV)
        fetch_dft_data()

        # Step 3 – merge, filter, and save merged CSV
        merge_and_filter_main()
    except Exception as exc:
        logger.error(f"Ingestion pipeline failed: {exc}", exc_info=True)
        sys.exit(1)

def run_modeling_pipeline():
    """Placeholder – modeling not needed for T048."""
    logger.info("Modeling pipeline would run here (not part of T048).")

def run_interpretability_pipeline():
    """Placeholder – interpretability not needed for T048."""
    logger.info("Interpretability pipeline would run here (not part of T048).")

def run_full_pipeline():
    """Run the complete pipeline: ingestion → validation → checksums."""
    logger.info("=== Running full pipeline (T048) ===")
    run_ingestion_pipeline()

    # Validate the newly created merged dataset
    validate_dataset_min_rows()

    # Generate fresh checksums
    try:
        from ingestion.generate_checksums import main as generate_checksums_main
        generate_checksums_main()
    except Exception as exc:
        logger.error(f"Checksum generation failed: {exc}", exc_info=True)
        sys.exit(1)

    logger.info("=== Full pipeline completed successfully ===")
    log_provenance_event("pipeline_complete", status="success")

def main():
    parser = argparse.ArgumentParser(
        description="BCC Steel Yield Strength Prediction Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run the full ingestion → validation → checksum pipeline",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the merged dataset (expects it to already exist)",
    )
    args = parser.parse_args()

    if args.validate_only:
        validate_dataset_min_rows()
    elif args.full:
        run_full_pipeline()
    else:
        # Default behaviour mirrors the original script – run full pipeline
        run_full_pipeline()

if __name__ == "__main__":
    main()
