import os
import sys
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingest import parse_research_md, fetch_openml_data, fetch_huggingface_data, fetch_literature_data, standardize_schema, handle_missing_values, apply_archard_normalization, ingest_all_data
from hygiene import calculate_md5, save_artifact_hashes, load_artifact_hashes
from seed import set_seed
from verify_dirs import ensure_directory
from config.loader import load_schema_map

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    T015 Implementation:
    1. Orchestrates the full ingestion and cleaning pipeline.
    2. Writes the final clean dataset to data/processed/aggregated_clean.csv.
    3. Updates state/artifact_hashes.yaml with the checksum of the new file.
    """
    logger.info("Starting T015: Aggregation and Cleaning Pipeline")
    
    # 1. Setup Environment
    set_seed(42)
    ensure_directory("data/processed")
    ensure_directory("state")
    
    output_path = Path("data/processed/aggregated_clean.csv")
    hash_path = Path("state/artifact_hashes.yaml")
    
    # 2. Ingest Data
    # This calls the functions defined in T010-T013 to fetch, standardize,
    # handle missing values, and apply Archard normalization.
    logger.info("Fetching and processing data from sources...")
    try:
        # ingest_all_data is the main entry point defined in T010
        df_clean = ingest_all_data()
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        raise

    if df_clean is None or df_clean.empty:
        logger.error("Ingestion produced no data. Cannot proceed.")
        raise ValueError("Ingestion produced empty dataset.")

    # 3. Write Output
    logger.info(f"Writing {len(df_clean)} records to {output_path}")
    df_clean.to_csv(output_path, index=False)
    
    # 4. Update Checksums (T005 requirement)
    logger.info("Calculating MD5 and updating artifact hashes...")
    file_hash = calculate_md5(output_path)
    
    # Load existing hashes or create new dict
    current_hashes = load_artifact_hashes(hash_path)
    
    # Update with the new artifact
    # Format: { "path": { "hash": "...", "timestamp": "..." } }
    current_hashes[str(output_path)] = {
        "hash": file_hash,
        "timestamp": datetime.now().isoformat(),
        "type": "processed_dataset"
    }
    
    save_artifact_hashes(current_hashes, hash_path)
    
    logger.info(f"T015 Complete. Output: {output_path}, Hash: {file_hash}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
