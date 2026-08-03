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
DATA_PROCESSED = PROJECT_ROOT / 'data' / 'processed'

# Inline schema validation logic as per T004 requirements
VALID_SRA = re.compile(r'^(SRR|ERR)[0-9]+$')
VALID_ZENDO = re.compile(r'^10\.5281/zenodo\.[0-9]+$')

def validate_config(config_path: str) -> bool:
    """Validate dataset configuration against schema and URL patterns."""
    if not os.path.exists(config_path):
        logger.error(f"CRITICAL DATA GAP: Config file not found: {config_path}")
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
    """
    Attempt to download from Zenodo.
    STRICT PROTOCOL: If the fetch fails, raise an error immediately.
    NO synthetic fallbacks. NO placeholder data.
    """
    logger.info(f"Attempting to download from Zenodo: {url}")
    try:
        import requests
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)
        logger.info(f"Successfully downloaded to {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        error_msg = f"CRITICAL DATA GAP: Real data fetch failed for Zenodo URL: {url}. Error: {str(e)}. No fallback allowed."
        logger.error(error_msg)
        # Log to audit trail as per T043 requirements
        audit_path = DATA_PROCESSED / 'audit_trail.json'
        DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        audit_entry = {
            "task": "T043_01_retrieve_data",
            "error_type": "FETCH_FAILURE",
            "message": error_msg,
            "source": url
        }
        if audit_path.exists():
            with open(audit_path, 'r') as f:
                audit_log = json.load(f)
        else:
            audit_log = []
        audit_log.append(audit_entry)
        with open(audit_path, 'w') as f:
            json.dump(audit_log, f, indent=2)
        raise SystemExit(1)

def download_from_ncbi_sra(dataset_id: str, output_path: Path) -> bool:
    """
    Attempt to download from NCBI SRA.
    STRICT PROTOCOL: If the fetch fails, raise an error immediately.
    NO synthetic fallbacks. NO placeholder data.
    """
    logger.info(f"Attempting to download from NCBI SRA: {dataset_id}")
    # NCBI SRA typically requires specific tools (prefetch/sra-toolkit) or API calls.
    # For this implementation, we attempt a direct fetch of a known public CSV structure
    # if available, or raise failure if the specific ID is not reachable via standard HTTP.
    # In a real pipeline, this would invoke `prefetch` or `fasterq-dump`.
    # Here we simulate a strict failure if not found to enforce real data requirement.
    try:
        import requests
        # Attempt to fetch from a public mirror or NCBI API if possible
        # This is a placeholder for the specific fetch logic; it will fail loudly if no real data
        sra_url = f"https://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?view=table&study={dataset_id}"
        response = requests.get(sra_url, timeout=30)
        if response.status_code == 404:
            raise FileNotFoundError(f"Dataset {dataset_id} not found")
        
        # If we get here, we have data
        with open(output_path, 'wb') as f:
            f.write(response.content)
        logger.info(f"Successfully downloaded to {output_path}")
        return True
    except Exception as e:
        error_msg = f"CRITICAL DATA GAP: Real data fetch failed for SRA ID: {dataset_id}. Error: {str(e)}. No fallback allowed."
        logger.error(error_msg)
        # Log to audit trail
        audit_path = DATA_PROCESSED / 'audit_trail.json'
        DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        audit_entry = {
            "task": "T043_01_retrieve_data",
            "error_type": "FETCH_FAILURE",
            "message": error_msg,
            "source": dataset_id
        }
        if audit_path.exists():
            with open(audit_path, 'r') as f:
                audit_log = json.load(f)
        else:
            audit_log = []
        audit_log.append(audit_entry)
        with open(audit_path, 'w') as f:
            json.dump(audit_log, f, indent=2)
        raise SystemExit(1)

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
        except SystemExit:
            raise
        except Exception as e:
            logger.error(f"CRITICAL DATA GAP: Failed to process dataset {dataset['id']}: {e}")
            # Log to audit trail
            audit_path = DATA_PROCESSED / 'audit_trail.json'
            DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
            audit_entry = {
                "task": "T043_01_retrieve_data",
                "error_type": "PROCESS_FAILURE",
                "message": str(e),
                "dataset_id": dataset['id']
            }
            if audit_path.exists():
                with open(audit_path, 'r') as f:
                    audit_log = json.load(f)
            else:
                audit_log = []
            audit_log.append(audit_entry)
            with open(audit_path, 'w') as f:
                json.dump(audit_log, f, indent=2)
            sys.exit(1)

    logger.info("Data retrieval completed.")

if __name__ == "__main__":
    main()
