"""
T022: Save cleaned dataset to data/processed/clean_mg_data.parquet with checksum manifest.

This script assumes that the data ingestion (T013-T015) and feature extraction (T016-T017)
have already run and populated the in-memory DataFrame or a temporary intermediate file.
However, to make this a standalone executable artifact as per the "whole-file" constraint
and to ensure it runs end-to-end, it re-orchestrates the fetch and feature extraction
pipeline defined in the previous tasks, then saves the result.

Prerequisites:
- code/ingestion/fetch_data.py (T013, T014, T015)
- code/features/descriptors.py (T016, T017)
- code/utils/io.py (T005a: compute_sha256)
- code/utils/config.py (T004)
"""
import os
import sys
import logging
import json
from pathlib import Path

# Add project root to path to allow relative imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.io import setup_logging, compute_sha256
from utils.config import get_env_var
from ingestion.fetch_data import fetch_data, filter_amorphous_entries
from features.descriptors import extract_descriptors

logger = setup_logging()

def main():
    logger.info("Starting T022: Saving cleaned dataset to parquet with checksum.")
    
    # 1. Fetch Data
    # We assume the fetch_data function returns a raw DataFrame from APIs/Zenodo
    # The fetch_data module handles the "fail loud" logic if no data is found.
    try:
        raw_df = fetch_data()
    except Exception as e:
        logger.error(f"Data fetching failed: {e}")
        raise

    if raw_df is None or raw_df.empty:
        logger.error("No data returned from fetch. Aborting save.")
        raise ValueError("No data available to save.")

    # 2. Filter Amorphous Entries
    # T015 logic: filter for amorphous state flag and non-null CTE
    df_filtered = filter_amorphous_entries(raw_df)

    if df_filtered.empty:
        logger.error("No amorphous entries found after filtering. Aborting save.")
        raise ValueError("No amorphous entries found.")

    # 3. Extract Descriptors
    # T016/T017 logic: calculate features
    df_final = extract_descriptors(df_filtered)

    # 4. Define Output Paths
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "clean_mg_data.parquet"
    checksum_file = output_dir / "clean_mg_data.sha256"
    manifest_file = output_dir / "clean_mg_data_manifest.json"

    # 5. Save Parquet
    logger.info(f"Saving dataset to {output_file}")
    # Ensure pyarrow or fastparquet is available (handled by requirements.txt in T002)
    df_final.to_parquet(output_file, index=False)
    
    if not output_file.exists():
        raise RuntimeError(f"Failed to write parquet file to {output_file}")

    # 6. Compute Checksum
    checksum = compute_sha256(str(output_file))
    logger.info(f"Computed SHA256: {checksum}")

    # 7. Write Checksum Manifest
    manifest_data = {
        "file": "clean_mg_data.parquet",
        "sha256": checksum,
        "row_count": len(df_final),
        "columns": list(df_final.columns),
        "status": "completed"
    }

    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2)

    logger.info(f"Manifest written to {manifest_file}")
    logger.info("T022 completed successfully.")

if __name__ == "__main__":
    main()
