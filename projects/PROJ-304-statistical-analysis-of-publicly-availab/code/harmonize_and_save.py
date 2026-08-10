import logging
import sys
from pathlib import Path
from typing import Optional

# Import from project API surface
from logger import get_logger, get_project_root
from hygiene import compute_and_record_checksums
from ingestion import load_synthetic_data_chunked, harmonize_spatial_data

def main():
    """
    Orchestrates the final step of User Story 1:
    1. Loads synthetic data (chunked).
    2. Harmonizes spatial data.
    3. Writes the harmonized dataset to data/processed/harmonized.parquet.
    4. Updates checksums in the project state file.
    """
    logger = get_logger(__name__)
    project_root = get_project_root()
    
    logger.info("Starting harmonization and save process (T016).")

    # 1. Load data
    # T011 implemented load_synthetic_data_chunked
    logger.info("Loading synthetic data chunked...")
    raw_data = load_synthetic_data_chunked()
    
    if raw_data is None or raw_data.empty:
        logger.error("Loaded data is empty. Cannot proceed with harmonization.")
        sys.exit(1)

    # 2. Harmonize
    # T014 implemented harmonize_spatial_data (merges covariates, handles missing)
    logger.info("Harmonizing spatial data...")
    harmonized_df = harmonize_spatial_data(raw_data)
    
    if harmonized_df is None or harmonized_df.empty:
        logger.error("Harmonized data is empty. Cannot proceed with saving.")
        sys.exit(1)

    # 3. Save to Parquet
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "harmonized.parquet"
    
    logger.info(f"Writing harmonized dataset to {output_path}...")
    try:
        # Use pyarrow engine for robust parquet writing
        harmonized_df.to_parquet(output_path, index=False, engine='pyarrow')
        logger.info(f"Successfully wrote {len(harmonized_df)} rows to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write parquet file: {e}")
        sys.exit(1)

    # 4. Update Checksums
    # T004b implemented compute_and_record_checksums
    logger.info("Updating project checksums...")
    try:
        compute_and_record_checksums(project_root)
        logger.info("Checksums updated successfully.")
    except Exception as e:
        logger.error(f"Failed to update checksums: {e}")
        # We proceed but log the error, as the data is saved
        sys.exit(1)

    logger.info("T016 completed successfully.")

if __name__ == "__main__":
    main()