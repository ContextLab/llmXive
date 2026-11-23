"""
Script to run the data ingestion pipeline for T014.
Downloads 5 distinct public datasets and creates a manifest.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.data.ingestion import (
    ingest_dataset, 
    create_manifest, 
    load_manifest, 
    IngestionError
)
from src.utils.logging import setup_logger, get_logger

logger = get_logger(__name__)

def main():
    # Configuration
    manifest_path = project_root / "data" / "raw" / "manifest.json"
    output_dir = project_root / "data" / "raw"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load dataset configurations
    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        sys.exit(1)
    
    datasets = load_manifest(str(manifest_path))
    logger.info(f"Found {len(datasets)} datasets to ingest")
    
    manifests = []
    failed_datasets = []
    
    for dataset_config in datasets:
        try:
            logger.info(f"Ingesting: {dataset_config['name']}")
            manifest = ingest_dataset(dataset_config, str(output_dir))
            manifests.append(manifest)
            logger.info(f"Successfully ingested: {manifest.name}")
        except IngestionError as e:
            logger.error(f"Failed to ingest {dataset_config['name']}: {e}")
            failed_datasets.append(dataset_config['name'])
        except Exception as e:
            logger.error(f"Unexpected error ingesting {dataset_config['name']}: {e}")
            failed_datasets.append(dataset_config['name'])
    
    if failed_datasets:
        logger.error(f"Failed to ingest the following datasets: {failed_datasets}")
        # Fail loudly as per requirements
        sys.exit(1)
    
    # Create final manifest
    final_manifest_path = output_dir / "manifest_final.json"
    create_manifest(manifests, str(final_manifest_path))
    
    logger.info("Ingestion pipeline completed successfully")
    logger.info(f"Final manifest saved to: {final_manifest_path}")

if __name__ == "__main__":
    setup_logger(level=logging.INFO)
    main()
