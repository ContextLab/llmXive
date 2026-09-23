import os
import sys
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from ingest import load_aggregated_data, main as ingest_main
from hygiene import register_multiple_artifacts, load_artifact_hashes, save_artifact_hashes
from logging_config import setup_logging, get_logger, raise_on_missing_data
from seed import set_seed

logger = get_logger(__name__)

def main():
    """
    T015: Generate data/processed/aggregated_clean.csv and update state/artifact_hashes.yaml.
    
    This task assumes T010-T014 have run successfully and produced the intermediate files.
    It verifies the existence of the aggregated clean file, computes its checksum,
    and registers it in the state/artifact_hashes.yaml file.
    """
    setup_logging()
    set_seed(42)
    
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data" / "processed"
    state_dir = project_root / "state"
    
    # Ensure directories exist
    data_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    
    input_file = data_dir / "aggregated_clean.csv"
    hash_file = state_dir / "artifact_hashes.yaml"
    
    # Check if the input file exists (produced by T014)
    if not input_file.exists():
        msg = f"Required input file missing: {input_file}. Ensure T014 has run successfully."
        logger.error(msg)
        raise FileNotFoundError(msg)
    
    logger.info(f"Found input file: {input_file}")
    
    # Load and verify the data is not empty
    try:
        df = pd.read_csv(input_file)
        if df.empty:
            msg = f"Input file {input_file} is empty. Cannot proceed with artifact generation."
            logger.error(msg)
            raise ValueError(msg)
        logger.info(f"Loaded {len(df)} records from {input_file}")
    except Exception as e:
        msg = f"Failed to read {input_file}: {e}"
        logger.error(msg)
        raise e
    
    # Register the artifact and update hashes
    # This function handles MD5 calculation and YAML update
    try:
        register_multiple_artifacts([str(input_file)], str(hash_file))
        logger.info(f"Successfully updated artifact hashes in {hash_file}")
    except Exception as e:
        msg = f"Failed to register artifact hashes: {e}"
        logger.error(msg)
        raise e
    
    logger.info("T015 completed successfully.")

if __name__ == "__main__":
    main()
