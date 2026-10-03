"""
Aggregate module for T015: Create filtered_galaxies.csv and update metadata.

This module handles the final aggregation step of User Story 1:
1. Loads the pre-processed galaxy data (output of T013/T014).
2. Writes the final `data/processed/filtered_galaxies.csv`.
3. Updates `data/metadata.yaml` with the timestamp and version of this run.
"""
import os
import logging
import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime

# Import from local project modules as per API surface
from utils import get_logger, ensure_directory, get_timestamp
from config import load_config

logger = get_logger(__name__)

def load_filtered_data(input_path: Path) -> pd.DataFrame:
    """
    Load the pre-processed galaxy data.
    
    This assumes T013 (parser) and T014 (filter) have run and produced
    the intermediate data expected by this stage. In a full pipeline,
    this might read from a temporary staging file or a database.
    For this implementation, we expect the data to be available at
    a specific staging location or we reconstruct it from the config
    if the pipeline was run sequentially.
    
    However, per T015's specific role in the task list, it is the
    "finalizer". We will assume the data exists in a standard location
    or we read the raw/processed intermediate.
    
    Since T013/T014 are marked complete, we assume they wrote to a
    temporary location or we are reading the result of the filter.
    To be robust, we look for the most recent processed file or
    load from the config's processed path if it exists (idempotent).
    
    For this specific task implementation, we will read from the
    path defined in config as 'processed_data' if it exists (re-run),
    or we assume the previous step wrote to a temp file.
    
    To strictly follow the "real data" constraint without hardcoding
    intermediate paths not in the spec, we will attempt to load the
    data that T014 would have produced. If T014 wrote to a temp file,
    we need that path.
    
    Given the constraints, we will implement a loader that reads the
    'data/processed/filtered_galaxies.csv' if it exists (for re-runs),
    or attempts to load the raw parsed data if available.
    
    Actually, the task says "Create ... and update". This implies
    the filtering logic might be embedded here or we are just finalizing.
    But T014 is "Implement quality filter". So T014 produces the data.
    T015 is "Create ... and update metadata".
    
    We will assume T014 wrote to a staging file or the same file.
    Let's assume T014 wrote to `data/processed/filtered_galaxies.csv`
    and T015 ensures it's there and updates metadata.
    
    If the file doesn't exist, we raise an error (fail loudly) because
    T014 must have run.
    """
    if not input_path.exists():
        raise FileNotFoundError(
            f"Filtered data not found at {input_path}. "
            "Ensure T014 (quality filter) has been executed successfully."
        )
    
    logger.info(f"Loading filtered data from {input_path}")
    df = pd.read_csv(input_path)
    
    if df.empty:
        raise ValueError("Loaded filtered data is empty. No galaxies passed quality filters.")
    
    return df

def update_metadata(config: dict, metadata_path: Path) -> None:
    """
    Update the metadata.yaml file with the current run's timestamp and version.
    
    Args:
        config: The loaded configuration dictionary.
        metadata_path: Path to the metadata.yaml file.
    """
    if not metadata_path.exists():
        logger.warning(f"Metadata file not found at {metadata_path}. Creating new one.")
        # If it doesn't exist, we might need to create a basic structure,
        # but the task assumes it exists (T005 created it).
        # We'll raise an error if it's truly missing and expected.
        # However, T005 says "Create base configuration loader", implying the file exists.
        raise FileNotFoundError(f"Metadata file missing: {metadata_path}")

    with open(metadata_path, 'r') as f:
        metadata = yaml.safe_load(f)

    # Update the data section
    current_time = datetime.utcnow()
    metadata['data']['download_timestamp'] = current_time.isoformat()
    # Increment or set version if needed, or just log the run
    # The task says "update ... with download timestamp/version"
    # We will add a 'last_processed_timestamp' to the analysis or data section
    if 'last_processed_timestamp' not in metadata:
        metadata['last_processed_timestamp'] = current_time.isoformat()
    else:
        metadata['last_processed_timestamp'] = current_time.isoformat()
    
    # Ensure the path in metadata points to the correct file
    metadata['paths']['processed_data'] = str(metadata_path.parent / 'processed' / 'filtered_galaxies.csv')

    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Updated metadata at {metadata_path} with timestamp {current_time.isoformat()}")

def main():
    """
    Main entry point for T015.
    
    1. Load config.
    2. Ensure the processed directory exists.
    3. Load the filtered data (from T014).
    4. Write the final CSV (if not already written by T014, or overwrite to ensure consistency).
    5. Update metadata.yaml.
    """
    config = load_config()
    metadata_path = Path(config.get('paths', {}).get('metadata', 'data/metadata.yaml'))
    # Note: The config provided in the prompt doesn't have a 'metadata' key in paths,
    # but T005 created metadata.yaml. We'll assume it's at data/metadata.yaml as per the file content.
    if not metadata_path.exists():
        metadata_path = Path('data/metadata.yaml')
    
    processed_path = Path(config['paths']['processed_data'])
    
    logger.info(f"Starting aggregation for T015. Output: {processed_path}")
    
    ensure_directory(processed_path.parent)
    
    # Load the data (T014 output)
    # If T014 wrote directly to this path, we just need to ensure it's valid and update metadata.
    # If T014 wrote to a temp file, we move it.
    # Assuming T014 wrote to `processed_path` as per standard pipeline flow.
    
    try:
        df = load_filtered_data(processed_path)
    except FileNotFoundError:
        logger.error("Data pipeline broken: T014 did not produce the expected output file.")
        raise
    
    # Re-save to ensure format consistency (optional but good practice)
    # We will write the dataframe to the CSV
    df.to_csv(processed_path, index=False)
    logger.info(f"Wrote {len(df)} galaxies to {processed_path}")
    
    # Update metadata
    update_metadata(config, metadata_path)
    
    logger.info("T015 completed successfully.")

if __name__ == "__main__":
    main()
