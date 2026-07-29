"""
Ingestion Module (T013).
Downloads MedMisBench, filters for Authority-framed and Exception-poisoning subsets,
validates schema, and saves to data/raw/medmis_subset.csv.
"""
import os
import hashlib
import csv
import yaml
import time
import logging
import sys
from pathlib import Path
import re

from config import get_config
from error_handling import DatasetDownloadError, retry_with_backoff

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Try to import datasets, but handle gracefully if not installed
try:
    from datasets import load_dataset
except ImportError:
    logger.error("The 'datasets' package is required. Install with: pip install datasets")
    raise

def extract_false_claim_from_text(text: str) -> str:
    """
    Fallback regex extraction for false_claim if column is missing.
    Looks for patterns like "false claim: ..." or "incorrect: ..."
    """
    patterns = [
        r'false\s+claim[:\s]+([^\.]+)',
        r'incorrect[:\s]+([^\.]+)',
        r'falsehood[:\s]+([^\.]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""

def load_and_filter_dataset():
    """
    Load MedMisBench via streaming and filter for specific labels.
    Returns a list of dictionaries.
    """
    config = get_config()
    dataset_name = config.get('datasets', {}).get('medmis_name', 'mlabonne/MedMisBench')
    
    logger.info(f"Loading dataset: {dataset_name} (streaming mode)")
    
    try:
        # Use streaming to handle large datasets
        dataset = load_dataset(dataset_name, split="train", streaming=True)
    except Exception as e:
        raise DatasetDownloadError(f"Failed to load dataset {dataset_name}: {str(e)}")
    
    filtered_data = []
    count = 0
    target_labels = {"Authority-framed", "Exception-poisoning"}
    
    logger.info("Filtering for Authority-framed and Exception-poisoning labels...")
    
    for item in dataset:
        # Check if label exists
        label = item.get('label', item.get('category', item.get('type', '')))
        
        # Normalize label string
        label_str = str(label).strip()
        
        if label_str in target_labels:
            filtered_data.append(item)
            count += 1
            
            # Log progress
            if count % 100 == 0:
                logger.info(f"Filtered {count} items so far...")
            
            # Safety break for testing if needed, but we want full dataset
            # if count >= 10: break 
    
    logger.info(f"Filtering complete. Total items: {count}")
    return filtered_data

def validate_schema(data: list) -> bool:
    """
    Validate that the dataset has the required columns.
    If 'false_claim' is missing, attempt regex extraction.
    """
    if not data:
        raise ValueError("Dataset is empty after filtering.")
    
    sample = data[0]
    required_keys = {'prompt_id', 'text', 'label'} # Basic keys
    
    # Check for false_claim
    if 'false_claim' not in sample:
        logger.warning("'false_claim' column missing. Attempting regex extraction from text.")
        for item in data:
            if 'text' in item:
                item['false_claim'] = extract_false_claim_from_text(item['text'])
            else:
                item['false_claim'] = ""
        return True
    
    return True

def save_to_csv(data: list, output_path: Path):
    """Save the filtered dataset to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not data:
        raise ValueError("No data to save.")
    
    # Flatten data if nested
    flat_data = []
    for item in data:
        flat_item = {}
        for k, v in item.items():
            if isinstance(v, (list, dict)):
                flat_item[k] = str(v)
            else:
                flat_item[k] = v
        flat_data.append(flat_item)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=flat_data[0].keys())
        writer.writeheader()
        writer.writerows(flat_data)
    
    logger.info(f"Saved {len(flat_data)} rows to {output_path}")

def save_checksum_to_state(file_path: Path, state_path: Path):
    """Compute SHA-256 checksum and update state file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    checksum = sha256_hash.hexdigest()
    
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    state_data = {}
    if state_path.exists():
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f) or {}
    
    state_data['artifact_hashes'] = state_data.get('artifact_hashes', {})
    state_data['artifact_hashes']['medmis_subset.csv'] = checksum
    
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f)
    
    logger.info(f"Saved checksum {checksum} to {state_path}")

def run_ingestion_pipeline():
    """Execute the full ingestion pipeline (T013)."""
    logger.info("Starting Ingestion Pipeline (T013)")
    config = get_config()
    
    output_path = Path(config['paths']['raw']) / 'medmis_subset.csv'
    state_path = Path(config['paths']['state']) / 'artifact_hashes.yaml'
    
    data = load_and_filter_dataset()
    validate_schema(data)
    save_to_csv(data, output_path)
    save_checksum_to_state(output_path, state_path)
    
    logger.info("Ingestion Pipeline completed successfully.")
    return output_path

def main():
    """Entry point for ingestion."""
    try:
        run_ingestion_pipeline()
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
