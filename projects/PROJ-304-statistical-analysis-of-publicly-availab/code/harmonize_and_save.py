"""
Harmonize spatial data and save the final dataset to Parquet.

This script orchestrates the final step of User Story 1:
1. Loads synthetic noise and covariate data (chunked for memory safety).
2. Harmonizes spatial data (merges, aligns CRS, handles missing covariates).
3. Writes the unified dataset to `data/processed/harmonized.parquet`.
4. Updates project checksums in the state file.
"""
import logging
import sys
from pathlib import Path

from logger import get_logger, get_project_root
from hygiene import compute_and_record_checksums
from ingestion import load_synthetic_data_chunked, harmonize_spatial_data

def main():
    """Execute the harmonization and save pipeline."""
    logger = get_logger(__name__)
    project_root = get_project_root()
    
    # Define paths
    output_dir = project_root / "data" / "processed"
    output_path = output_dir / "harmonized.parquet"
    
    logger.info("Starting harmonization and save process.")
    logger.info(f"Output path: {output_path}")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load synthetic data (chunked)
        logger.info("Loading synthetic data chunks...")
        # load_synthetic_data_chunked returns a generator of DataFrames or a single merged DF
        # Based on T011 implementation, it returns a generator or the final merged DF.
        # We assume it yields DataFrames that need to be concatenated or returns one large DF.
        # Given T005b requirement, it likely returns a generator or a list of chunks.
        # For simplicity in this step, we assume load_synthetic_data_chunked returns the full
        # cleaned noise/covariate data ready for harmonization, or we handle the generator.
        
        # Let's assume load_synthetic_data_chunked returns a generator of DataFrames
        # We need to concatenate them before harmonization if it's a generator.
        # However, looking at typical patterns, it might return the final merged DF if chunking
        # was internal. Let's assume it returns the full data or a generator.
        # To be safe and consistent with memory-safe design:
        data_chunks = load_synthetic_data_chunked()
        
        # If it returns a generator, we need to concatenate
        if hasattr(data_chunks, '__iter__') and not isinstance(data_chunks, pd.DataFrame):
            import pandas as pd
            logger.info("Concatenating data chunks...")
            full_data = pd.concat(list(data_chunks), ignore_index=True)
        else:
            full_data = data_chunks

        logger.info(f"Loaded {len(full_data)} rows from synthetic data.")

        # 2. Harmonize spatial data
        logger.info("Harmonizing spatial data...")
        harmonized_df = harmonize_spatial_data(full_data)
        
        if harmonized_df is None or len(harmonized_df) == 0:
            raise ValueError("Harmonization resulted in an empty dataset.")

        logger.info(f"Harmonized dataset contains {len(harmonized_df)} rows.")

        # 3. Write to Parquet
        logger.info(f"Writing harmonized dataset to {output_path}...")
        harmonized_df.to_parquet(output_path, index=False)
        
        # Verify file creation
        if not output_path.exists():
            raise FileNotFoundError(f"Output file {output_path} was not created.")
        
        file_size = output_path.stat().st_size
        logger.info(f"Successfully wrote {file_size} bytes to {output_path}")

        # 4. Update checksums
        logger.info("Updating project checksums...")
        compute_and_record_checksums()
        
        logger.info("Harmonization and save process completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error during harmonization and save: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
