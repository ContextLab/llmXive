import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.request import urlopen, urlretrieve
from urllib.error import URLError, HTTPError
import jsonschema
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('code/01_retrieve_data.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def validate_config(config_path: str) -> bool:
    """
    Validates the dataset configuration file against the schema.
    Raises ValueError or SystemExit if validation fails.
    """
    schema_path = Path("data/contracts/dataset-config.schema.yaml")
    
    if not schema_path.exists():
        error_msg = f"CRITICAL DATA GAP: Schema file not found: {schema_path}"
        logger.error(error_msg)
        write_audit_trail("validation_error", error_msg, "T043")
        sys.exit(1)

    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
    except Exception as e:
        error_msg = f"CRITICAL DATA GAP: Failed to load schema: {e}"
        logger.error(error_msg)
        write_audit_trail("validation_error", error_msg, "T043")
        sys.exit(1)

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        error_msg = f"CRITICAL DATA GAP: Config file not found: {config_path}"
        logger.error(error_msg)
        write_audit_trail("validation_error", error_msg, "T043")
        sys.exit(1)
    except json.JSONDecodeError as e:
        error_msg = f"CRITICAL DATA GAP: Invalid JSON in config: {e}"
        logger.error(error_msg)
        write_audit_trail("validation_error", error_msg, "T043")
        sys.exit(1)

    try:
        jsonschema.validate(instance=config, schema=schema)
        logger.info("Configuration validation passed.")
        return True
    except jsonschema.exceptions.ValidationError as e:
        error_msg = f"CRITICAL DATA GAP: Schema validation failed: {e.message}"
        logger.error(error_msg)
        write_audit_trail("validation_error", error_msg, "T043")
        sys.exit(1)

def download_from_zenodo(dataset_id: str, url: str, output_dir: Path) -> Path:
    """
    Downloads a dataset from Zenodo.
    Raises SystemExit if download fails.
    """
    output_path = output_dir / f"zenodo_{dataset_id}.zip"
    logger.info(f"Attempting to download from Zenodo: {url}")
    
    try:
        urlretrieve(url, output_path)
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ValueError("Downloaded file is empty or missing.")
        logger.info(f"Successfully downloaded Zenodo data to {output_path}")
        return output_path
    except HTTPError as e:
        error_msg = f"CRITICAL DATA GAP: Zenodo download failed (HTTP {e.code}): {e.reason}"
        logger.error(error_msg)
        write_audit_trail("download_error", error_msg, "T043")
        sys.exit(1)
    except URLError as e:
        error_msg = f"CRITICAL DATA GAP: Zenodo download failed (URL Error): {e.reason}"
        logger.error(error_msg)
        write_audit_trail("download_error", error_msg, "T043")
        sys.exit(1)
    except Exception as e:
        error_msg = f"CRITICAL DATA GAP: Zenodo download failed: {e}"
        logger.error(error_msg)
        write_audit_trail("download_error", error_msg, "T043")
        sys.exit(1)

def download_from_ncbi_sra(dataset_id: str, output_dir: Path) -> Path:
    """
    Simulates download from NCBI SRA (in real implementation, this would use sra-tools or API).
    For this implementation, we assume the data is provided via a specific URL pattern or mock structure
    if the real API isn't directly callable without credentials, but strictly fail if not found.
    """
    # In a real scenario, we would use `prefetch` or `fasterq-dump`
    # Since we cannot run external binaries reliably here without setup,
    # we check for a pre-defined local path or fail if the task requires real network fetch.
    # Given the strict "Real Data Only" constraint, we assume the URL in config points to a direct file
    # or we raise an error if the specific SRA tooling isn't available.
    
    # For this specific task implementation, we will treat SRA IDs as needing a specific fetch logic.
    # If the config provided a direct URL for SRA, we use that. If just an ID, we fail loudly 
    # unless we have a local cache mechanism which we don't for this strict task.
    
    # Placeholder for logic that would strictly fail if real data isn't fetchable
    logger.warning(f"SRA ID {dataset_id} requires external tooling. Strict mode: checking local cache or failing.")
    
    # In a real pipeline, this would attempt: sra-prefetch dataset_id
    # If that fails, it must exit.
    # Since we are simulating the strict protocol without the binary, we assume the config 
    # MUST provide a direct URL for SRA if available, or we fail.
    # To satisfy the "Real Data" constraint without external binaries:
    # We will assume the 'url' field in config for NCBI_SRA is a direct link to a processed table.
    # If the schema enforces 'url' for NCBI_SRA too, we use that.
    # If not, we fail.
    
    # Re-reading the schema logic in T004: source enum, url required.
    # So we treat NCBI_SRA entries as having a direct URL.
    # This function is a placeholder for the logic that would fail if that URL is bad.
    # We will delegate to a generic downloader if URL is present, or fail.
    raise NotImplementedError("Direct SRA ID download requires sra-tools. Ensure config provides direct URL for processed tables.")

def process_dataset(dataset: Dict[str, Any], raw_dir: Path) -> bool:
    """
    Processes a single dataset entry: validates and downloads.
    """
    dataset_id = dataset['id']
    source = dataset['source']
    url = dataset['url']

    logger.info(f"Processing dataset: {dataset_id} from {source}")

    if source == "Zenodo":
        try:
            download_from_zenodo(dataset_id, url, raw_dir)
        except SystemExit:
            return False
    elif source == "NCBI_SRA":
        # If the schema allows NCBI_SRA with a URL, we treat it like Zenodo for direct downloads
        # otherwise we fail strictly.
        if url and url.startswith('http'):
            try:
                # Reuse zenodo logic for direct URL fetch
                output_path = raw_dir / f"ncbi_{dataset_id}.zip"
                urlretrieve(url, output_path)
                if not output_path.exists() or output_path.stat().st_size == 0:
                    raise ValueError("Downloaded file is empty.")
                logger.info(f"Downloaded NCBI data to {output_path}")
            except Exception as e:
                error_msg = f"CRITICAL DATA GAP: NCBI download failed: {e}"
                logger.error(error_msg)
                write_audit_trail("download_error", error_msg, "T043")
                sys.exit(1)
        else:
            error_msg = f"CRITICAL DATA GAP: NCBI_SRA dataset {dataset_id} missing valid URL for direct fetch."
            logger.error(error_msg)
            write_audit_trail("validation_error", error_msg, "T043")
            sys.exit(1)
    else:
        error_msg = f"CRITICAL DATA GAP: Unknown source type: {source}"
        logger.error(error_msg)
        write_audit_trail("validation_error", error_msg, "T043")
        sys.exit(1)

    return True

def write_audit_trail(event_type: str, message: str, task_id: str):
    """
    Writes an entry to the audit trail JSON file.
    """
    audit_path = Path("data/processed/audit_trail.json")
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": str(Path().resolve().joinpath("time").absolute()), # Simplified for now, use datetime in real
        "event_type": event_type,
        "message": message,
        "task_id": task_id
    }
    
    # In a real run, we'd import datetime
    import datetime
    entry["timestamp"] = datetime.datetime.now().isoformat()

    if audit_path.exists():
        try:
            with open(audit_path, 'r') as f:
                data = json.load(f)
        except:
            data = []
    else:
        data = []
    
    data.append(entry)
    
    with open(audit_path, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    """
    Main entry point for data retrieval.
    """
    logger.info("Starting data retrieval process...")
    config_path = "data/config/dataset_ids.json"
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Validate configuration
    logger.info(f"Validating configuration file: {config_path}")
    validate_config(config_path)

    # Load config to process datasets
    with open(config_path, 'r') as f:
        config = json.load(f)

    datasets = config.get('datasets', [])
    if not datasets:
        error_msg = "CRITICAL DATA GAP: No datasets found in configuration."
        logger.error(error_msg)
        write_audit_trail("validation_error", error_msg, "T043")
        sys.exit(1)

    success_count = 0
    for dataset in datasets:
        if process_dataset(dataset, raw_dir):
            success_count += 1

    if success_count == 0:
        error_msg = "CRITICAL DATA GAP: Failed to retrieve any datasets."
        logger.error(error_msg)
        write_audit_trail("critical_failure", error_msg, "T043")
        sys.exit(1)

    logger.info(f"Successfully retrieved {success_count} datasets.")
    logger.info("Data retrieval process completed.")

if __name__ == "__main__":
    main()
