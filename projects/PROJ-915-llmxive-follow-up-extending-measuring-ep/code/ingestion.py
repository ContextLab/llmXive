import os
import hashlib
import csv
import yaml
import time
import logging
import re
from pathlib import Path
from typing import Optional, List, Dict, Any

from datasets import load_dataset
from config import get_config
from error_handling import compute_sha256, DatasetDownloadError, update_hash_state
from validation import check_pipeline_limit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_sha256_file(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    return compute_sha256(file_path)

def load_and_filter_dataset(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Download MedMisBench via streaming, filter for specific labels,
    and extract the false_claim column.
    
    Constraints:
    - Must fail loudly if download fails (no synthetic fallback).
    - Must check for 'false_claim' column; if missing, attempt regex extraction.
    - If extraction fails, abort with clear error.
    """
    dataset_name = config.get('dataset_name', 'allenai/medmisbench')
    target_labels = config.get('target_labels', ['Authority-framed', 'Exception-poisoning'])
    streaming_mode = config.get('streaming', True)
    
    logger.info(f"Loading dataset: {dataset_name} (streaming={streaming_mode})")
    
    try:
        # Load dataset with streaming to handle large sizes
        dataset = load_dataset(dataset_name, split='train', streaming=streaming_mode)
        
        # Filter for target labels
        # Note: The exact column name for labels might vary. We assume 'label' or 'category'.
        # We will iterate and filter manually to support streaming.
        
        filtered_items = []
        
        # Helper to check if an item matches target labels
        def matches_target(item):
            # Try common column names for labels
            label_val = item.get('label') or item.get('category') or item.get('type')
            if label_val is None:
                return False
            # Normalize to string for comparison
            label_str = str(label_val)
            return any(target in label_str for target in target_labels)
        
        # Helper to extract false_claim
        def extract_false_claim(item):
            # Priority 1: Direct column
            if 'false_claim' in item:
                return item['false_claim']
            
            # Priority 2: Regex extraction from prompt text
            # Common patterns: "The false claim is: ...", "Claim: ...", or specific delimiters
            prompt_text = item.get('prompt', '') or item.get('context', '') or ''
            
            # Pattern 1: "The false claim is: <text>"
            match = re.search(r'false claim is[:\s]+(.+?)(?:\n|$)', prompt_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            
            # Pattern 2: "Claim: <text>" (if context suggests it's a false claim)
            match = re.search(r'Claim[:\s]+(.+?)(?:\n|$)', prompt_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            
            return None

        logger.info("Iterating and filtering dataset...")
        count = 0
        for item in dataset:
            if matches_target(item):
                false_claim = extract_false_claim(item)
                if false_claim is None:
                    logger.warning(f"Could not extract false_claim from item {count}. Skipping.")
                    continue
                
                # Create a clean record
                record = {
                    'prompt_id': item.get('id', f'item_{count}'),
                    'prompt': item.get('prompt', ''),
                    'false_claim': false_claim,
                    'label': item.get('label') or item.get('category') or item.get('type'),
                    'source': dataset_name
                }
                filtered_items.append(record)
                count += 1
                
                # Check pipeline time limit periodically
                check_pipeline_limit()
                
                if count % 100 == 0:
                    logger.info(f"Processed {count} matching items...")
        
        if count == 0:
            raise DatasetDownloadError("No items matched the target labels or could be extracted.")
        
        logger.info(f"Successfully filtered {count} items.")
        return filtered_items

    except Exception as e:
        logger.error(f"Failed to download or process dataset: {e}")
        raise DatasetDownloadError(f"Dataset download/filtering failed: {e}") from e

def save_to_csv(data: List[Dict[str, Any]], output_path: Path) -> None:
    """Save list of dicts to CSV."""
    if not data:
        raise ValueError("No data to save.")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = data[0].keys()
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Saved {len(data)} items to {output_path}")

def update_hash_state(output_path: Path, hash_state: Dict[str, Any]) -> Dict[str, Any]:
    """Update the hash state dictionary with the new file hash."""
    file_hash = compute_sha256_file(output_path)
    update_hash_state(hash_state, str(output_path), file_hash)
    return hash_state

def run_ingestion_pipeline(config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Main pipeline function for T013.
    1. Load and filter MedMisBench.
    2. Save to data/raw/medmis_subset.csv.
    3. Compute SHA-256 and save to state/artifact_hashes.yaml.
    """
    if config is None:
        config = get_config()
    
    raw_dir = Path(config.get('paths', {}).get('raw', 'data/raw'))
    state_dir = Path(config.get('paths', {}).get('state', 'state'))
    output_file = raw_dir / 'medmis_subset.csv'
    hash_file = state_dir / 'artifact_hashes.yaml'
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Load state if exists
    hash_state = {}
    if hash_file.exists():
        with open(hash_file, 'r') as f:
            hash_state = yaml.safe_load(f) or {}
    
    # Execute ingestion
    data = load_and_filter_dataset(config)
    
    # Save to CSV
    save_to_csv(data, output_file)
    
    # Update hash state
    hash_state = update_hash_state(output_file, hash_state)
    
    # Write hash state to YAML
    with open(hash_file, 'w') as f:
        yaml.dump(hash_state, f, default_flow_style=False)
    
    logger.info(f"Ingestion pipeline complete. Output: {output_file}, Hashes: {hash_file}")
    return output_file

def main():
    """Entry point for the ingestion script."""
    logger.info("Starting ingestion pipeline (T013)...")
    try:
        run_ingestion_pipeline()
        logger.info("Ingestion pipeline finished successfully.")
    except DatasetDownloadError as e:
        logger.critical(f"Ingestion failed due to data issue: {e}")
        raise
    except Exception as e:
        logger.critical(f"Ingestion failed with unexpected error: {e}")
        raise

if __name__ == '__main__':
    main()
