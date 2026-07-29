import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import re

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] [%(name)s] %(message)s')
logger = logging.getLogger('01_retrieve_data')

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / 'data' / 'config' / 'dataset_ids.json'
DATA_RAW = PROJECT_ROOT / 'data' / 'raw'

# Inline schema validation logic as per T004 requirements
VALID_SRA = re.compile(r'^(SRR|ERR)[0-9]+$')
VALID_ZENDO = re.compile(r'^10\.5281/zenodo\.[0-9]+$')

def validate_config(config_path: str) -> bool:
    """Validate dataset configuration against schema and URL patterns."""
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        return False

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError:
        logger.error("CRITICAL DATA GAP: Invalid JSON in config file")
        return False

    if 'datasets' not in config or not isinstance(config['datasets'], list):
        logger.error("CRITICAL DATA GAP: 'datasets' key missing or invalid")
        return False

    for item in config['datasets']:
        if 'id' not in item or 'source' not in item or 'url' not in item:
            logger.error(f"CRITICAL DATA GAP: Missing required fields in dataset config: {item}")
            return False

        source = item['source']
        dataset_id = item['id']
        url = item['url']

        if source == "NCBI_SRA":
            if not VALID_SRA.match(dataset_id):
                logger.error(f"CRITICAL DATA GAP: Invalid SRA ID format: {dataset_id}")
                return False
        elif source == "Zenodo":
            if not VALID_ZENDO.match(url):
                logger.error(f"CRITICAL DATA GAP: Invalid Zenodo URL format: {url}")
                return False
        else:
            logger.error(f"CRITICAL DATA GAP: Unknown source: {source}")
            return False

    return True

def download_from_zenodo(url: str, output_path: Path) -> bool:
    """Simulate download from Zenodo."""
    # In a real scenario, this would use requests or wget
    # For now, we create a placeholder to indicate the logic exists
    # The actual data retrieval will fail if no real data is available, which is expected
    logger.info(f"Attempting to download from Zenodo: {url}")
    # Placeholder: In real execution, this would fail if data is not available
    # We do NOT generate synthetic data here as per strict data loader protocol
    raise FileNotFoundError(f"Real data fetch failed for Zenodo URL: {url}. No fallback allowed.")

def download_from_ncbi_sra(dataset_id: str, output_path: Path) -> bool:
    """Simulate download from NCBI SRA."""
    logger.info(f"Attempting to download from NCBI SRA: {dataset_id}")
    # Placeholder: In real execution, this would fail if data is not available
    raise FileNotFoundError(f"Real data fetch failed for SRA ID: {dataset_id}. No fallback allowed.")

def process_dataset(dataset: Dict[str, Any]) -> None:
    """Process a single dataset entry."""
    source = dataset['source']
    dataset_id = dataset['id']
    url = dataset['url']

    output_path = DATA_RAW / f"{dataset_id}.csv"
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    if source == "Zenodo":
        download_from_zenodo(url, output_path)
    elif source == "NCBI_SRA":
        download_from_ncbi_sra(dataset_id, output_path)

def main():
    logger.info("Starting data retrieval process...")
    logger.info(f"Validating configuration file: {CONFIG_PATH}")

    if not validate_config(str(CONFIG_PATH)):
        logger.error("CRITICAL DATA GAP: Validation failed. Halting execution.")
        sys.exit(1)

    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)

    for dataset in config['datasets']:
        try:
            process_dataset(dataset)
        except Exception as e:
            logger.error(f"CRITICAL DATA GAP: Failed to process dataset {dataset['id']}: {e}")
            sys.exit(1)

    logger.info("Data retrieval completed.")

if __name__ == "__main__":
    main()
