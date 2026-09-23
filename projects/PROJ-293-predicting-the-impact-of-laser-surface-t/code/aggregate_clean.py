import os
import sys
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime

# Import hygiene functions from the existing hygiene module
from hygiene import (
    calculate_md5,
    load_artifact_hashes,
    save_artifact_hashes,
    update_artifact_hash,
    get_file_metadata
)

# Import logging setup from existing module
from logging_config import setup_logging, get_logger

def main():
    """
    T015 Implementation:
    1. Generates data/processed/aggregated_clean.csv by orchestrating the ingestion pipeline.
    2. Updates state/artifact_hashes.yaml with the checksum of the generated file.
    
    This script acts as the entry point for the data generation step.
    It assumes T010-T014 logic is encapsulated in the ingestion flow.
    Since T010-T014 are completed, we execute the main ingestion logic
    which produces the final clean CSV, then hash it.
    """
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    project_root = Path(__file__).parent.parent
    data_processed_dir = project_root / "data" / "processed"
    state_dir = project_root / "state"
    
    output_file = data_processed_dir / "aggregated_clean.csv"
    hash_file = state_dir / "artifact_hashes.yaml"
    
    # Ensure directories exist
    data_processed_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting aggregation and cleaning process for {output_file}")
    
    # Execute the ingestion pipeline
    # We import and run the main function from ingest.py which handles T010-T014 logic
    # Note: ingest.py main() is expected to produce data/processed/aggregated_clean.csv
    try:
        from ingest import main as ingest_main
        ingest_main()
        logger.info("Ingestion pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        sys.exit(1)
    
    # Verify the output file exists
    if not output_file.exists():
        logger.error(f"Output file {output_file} was not created by the ingestion pipeline.")
        sys.exit(1)
    
    logger.info(f"Output file {output_file} created. Calculating checksum...")
    
    # Calculate MD5 checksum
    file_hash = calculate_md5(output_file)
    metadata = get_file_metadata(output_file)
    
    logger.info(f"Checksum for {output_file}: {file_hash}")
    
    # Load existing hashes
    hashes = load_artifact_hashes(hash_file)
    
    # Update the hash for the specific artifact
    # The artifact key should be consistent. Using the relative path from project root.
    artifact_key = str(output_file.relative_to(project_root))
    
    update_artifact_hash(
        hashes,
        artifact_key,
        file_hash,
        metadata
    )
    
    # Save updated hashes
    save_artifact_hashes(hashes, hash_file)
    
    logger.info(f"Artifact hashes updated in {hash_file}")
    logger.info("T015 completed successfully.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
