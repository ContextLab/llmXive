"""
Task T016: Write harmonized dataset to data/processed/harmonized.parquet and update checksums.

This script loads the output from the ingestion/preprocessing pipeline (harmonized data),
ensures it exists, writes it to a Parquet file, and updates the project state checksums.
"""
import logging
import sys
from pathlib import Path

# Add project root to path to ensure imports work in various execution contexts
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from logger import get_logger, get_project_root
from hygiene import compute_and_record_checksums
from ingestion import load_synthetic_data_chunked, harmonize_spatial_data

logger = get_logger(__name__)

def main():
    """
    Main entry point for T016.
    1. Loads and harmonizes data (re-running the pipeline steps to ensure data freshness).
    2. Writes the result to data/processed/harmonized.parquet.
    3. Updates checksums in state/projects/PROJ-304-statistical-analysis-of-publicly-availab.yaml.
    """
    project_root = get_project_root()
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    output_file = processed_dir / "harmonized.parquet"

    logger.info(f"Starting T016: Harmonizing data and saving to {output_file}")

    # 1. Load and Harmonize Data
    # We re-run the ingestion logic to ensure we have the latest harmonized state.
    # T011, T012, T013, T014 are assumed to be implemented and functional.
    try:
        # Load synthetic data (chunked for memory safety)
        raw_data = load_synthetic_data_chunked()
        logger.info(f"Loaded raw synthetic data with {len(raw_data)} rows.")

        # Apply harmonization (spatial merge, filtering, aggregation)
        # This calls the logic implemented in T011-T014
        harmonized_df = harmonize_spatial_data(raw_data)
        logger.info(f"Harmonized data created with {len(harmonized_df)} rows.")

        if harmonized_df.empty:
            logger.warning("Harmonized dataset is empty. Proceeding with save anyway.")

    except Exception as e:
        logger.error(f"Failed to load or harmonize data: {e}", exc_info=True)
        raise

    # 2. Write to Parquet
    try:
        # Use pyarrow engine as specified in requirements
        harmonized_df.to_parquet(
            output_file,
            engine='pyarrow',
            index=False
        )
        logger.info(f"Successfully wrote harmonized dataset to {output_file}")
    except Exception as e:
        logger.error(f"Failed to write parquet file: {e}", exc_info=True)
        raise

    # 3. Update Checksums
    try:
        logger.info("Updating project checksums...")
        compute_and_record_checksums()
        logger.info("Checksums updated successfully.")
    except Exception as e:
        logger.error(f"Failed to update checksums: {e}", exc_info=True)
        raise

    logger.info("T016 completed successfully.")

if __name__ == "__main__":
    main()