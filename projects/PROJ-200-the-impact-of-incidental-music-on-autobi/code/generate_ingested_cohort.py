"""
T018: Generate `data/processed/ingested_cohort.parquet` with checksum and update `state.yaml`.

This script orchestrates the final save of the processed cohort data after the
ingestion, filtering, and exposure scoring steps have been completed by the
upstream pipeline functions (T028 -> T013a -> T015 -> T013b -> T014).

It performs the following:
1. Loads the intermediate processed data (assumed to be in memory or a temp location
   after the main pipeline run, or reads from the last intermediate step if needed).
   *Correction*: Since T028 orchestrates the flow, we assume the data is ready to be
   saved. In this modular script approach, we re-run the pipeline logic to ensure
   the data is materialized, or we read the final state if T028 wrote it to a temp file.
   
   Given the task dependency "DEPENDS ON: T028", and T028 is an orchestration function,
   the most robust way to ensure the data exists is to re-run the ingestion pipeline
   up to the point of saving, or have T028 write to a temp file.
   
   However, to strictly follow the "Write/Save" nature of T018 and avoid re-running
   heavy ingestion if T028 already did it, we will assume the pipeline has been run
   and the data is available in `data/processed/` as an intermediate step or we
   re-execute the specific ingestion functions to materialize the final parquet.
   
   Actually, looking at T068 (02_preprocess.py) and T070 (04_exposure.py), they are
   the wrappers that run the logic. T018 is the specific "Save" step.
   
   To make this script runnable independently (as per quickstart), it should:
   1. Check if `data/processed/ingested_cohort.parquet` exists.
   2. If not, or if T028 logic requires a fresh run, execute the ingestion pipeline.
   3. Save the final dataframe to `data/processed/ingested_cohort.parquet`.
   4. Calculate SHA-256 checksum.
   5. Update `state.yaml`.
   
   For this implementation, we will re-run the ingestion pipeline functions to
   ensure the data is generated correctly according to the latest code, then save.
   This ensures the artifact is real and not a stale file.
"""

import os
import sys
import logging
import hashlib
import yaml
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_project_root, get_config_dict
from data_ingestion import (
    download_datasets,
    check_fallback_trigger,
    filter_cohort,
    apply_frequency_threshold,
    fetch_popularity_scores,
    calculate_ratio_score
)
from utils import setup_logging, get_logger

logger = get_logger(__name__)

def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_state_entry(file_path: Path, checksum: str, description: str):
    """Update state.yaml with the file's checksum and metadata."""
    project_root = get_project_root()
    state_file = project_root / "state.yaml"
    
    state = {}
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f) or {}
    
    # Ensure 'files' key exists
    if 'files' not in state:
        state['files'] = {}
    
    relative_path = str(file_path.relative_to(project_root))
    
    state['files'][relative_path] = {
        'checksum': checksum,
        'last_updated': datetime.now().isoformat(),
        'description': description
    }
    
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated state.yaml for {relative_path}")

def run_ingestion_pipeline():
    """
    Execute the full US1 ingestion pipeline to generate the cohort data.
    This mirrors the logic in T028 but ensures the data is materialized.
    """
    logger.info("Starting US1 Ingestion Pipeline for T018...")
    
    # 1. Download Datasets (T013)
    # Note: This will fail loudly if real data is not available and USE_MOCK_DATA is False.
    raw_data = download_datasets()
    
    if raw_data is None:
        raise RuntimeError("Download failed or returned no data. Cannot proceed.")
    
    # 2. Check Fallback Trigger (T023) - MUST run on raw data
    global_exposure_mode = check_fallback_trigger(raw_data)
    
    # 3. Filter Cohort (T013a)
    filtered_cohort = filter_cohort(raw_data, global_exposure_mode)
    
    if filtered_cohort is None or filtered_cohort.empty:
        logger.warning("Filtered cohort is empty. Check data sources and filters.")
        # Even if empty, we might need to save an empty schema-compliant file, 
        # but usually this indicates a failure. We proceed to save what we have.
    
    # 4. Apply Frequency Threshold (T015)
    thresholded_cohort = apply_frequency_threshold(filtered_cohort)
    
    # 5. Fetch Popularity Scores (T013b)
    # This function typically updates the dataframe in place or returns a new one
    # depending on implementation. We assume it returns the updated DF.
    cohort_with_popularity = fetch_popularity_scores(thresholded_cohort)
    
    # 6. Calculate Ratio Score (T014)
    final_cohort = calculate_ratio_score(cohort_with_popularity)
    
    logger.info(f"Pipeline complete. Final dataset shape: {final_cohort.shape if final_cohort is not None else 'None'}")
    return final_cohort

def main():
    """Main entry point for T018."""
    setup_logging()
    project_root = get_project_root()
    config = get_config_dict()
    
    output_file = project_root / "data" / "processed" / "ingested_cohort.parquet"
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if we need to re-run the pipeline
    # For this task, we re-run to ensure the data is fresh and matches the current code logic.
    # If the project uses a cache mechanism, this could be optimized, but T018 is the "Generate" task.
    logger.info("Executing ingestion pipeline to generate ingested_cohort.parquet...")
    
    try:
        df = run_ingestion_pipeline()
        
        if df is None:
            raise RuntimeError("Ingestion pipeline returned None. Check logs.")
        
        # Save to Parquet
        logger.info(f"Saving to {output_file}...")
        df.to_parquet(output_file, index=False)
        
        # Calculate Checksum
        checksum = calculate_file_checksum(output_file)
        logger.info(f"Checksum calculated: {checksum}")
        
        # Update State
        save_state_entry(output_file, checksum, "US1: Ingested Cohort with Exposure Scores")
        
        logger.info("T018 completed successfully.")
        
    except Exception as e:
        logger.error(f"T018 failed: {e}", exc_info=True)
        # Re-raise to fail the script
        raise

if __name__ == "__main__":
    main()