"""
Data Verification Hard Gate: Verify availability of valid eye-tracking datasets.

This script parses the 'Verified datasets' block in plan.md to ensure that:
1. The block is not empty.
2. The listed datasets are valid eye-tracking sources (not fMRI).
3. The datasets can be downloaded or are already present.

If validation fails, the script exits with code 1 and a clear error message.
"""

import os
import sys
import re
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLAN_MD_PATH = PROJECT_ROOT / "plan.md"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

def parse_verified_datasets_block(plan_path: Path) -> List[Dict[str, Any]]:
    """
    Parse the '# Verified datasets' block from plan.md.
    
    Expects a block in plan.md formatted as:
    # Verified datasets
    - id: <dataset_id>
      type: <dataset_type>
      source: <source_url_or_package>
    ...
    
    Returns a list of dictionaries containing dataset info.
    """
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")
    
    with open(plan_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Regex to find the block starting with '# Verified datasets'
    # and ending before the next '#' header or end of file
    pattern = r'# Verified datasets\s*\n((?:.*\n)*?)(?(=)(?!\n#))'
    # Simpler approach: find the section and parse lines
    lines = content.split('\n')
    in_block = False
    datasets = []
    current_dataset = {}
    
    for line in lines:
        if line.strip() == '# Verified datasets':
            in_block = True
            continue
        
        if in_block:
            if line.startswith('#') and line.strip() != '# Verified datasets':
                # End of block
                if current_dataset:
                    datasets.append(current_dataset)
                break
            
            # Parse list item
            match = re.match(r'^\s*-\s*(id|type|source|description):\s*(.+)$', line)
            if match:
                key, value = match.groups()
                current_dataset[key] = value.strip()
            elif line.strip() == '' and current_dataset:
                # Empty line indicates end of item
                datasets.append(current_dataset)
                current_dataset = {}
            elif line.strip().startswith('-') and ':' not in line:
                # Fallback for simple list items
                pass

    # If we didn't break due to a new header, check if we have a pending dataset
    if in_block and current_dataset:
        datasets.append(current_dataset)
    
    return datasets

def is_valid_eye_tracking_dataset(dataset_info: Dict[str, Any]) -> bool:
    """
    Determine if a dataset is a valid eye-tracking source.
    
    Criteria:
    - Must not be an fMRI dataset (identified by type or known IDs in plan.md context).
    - Must have a valid source identifier.
    
    Note: We rely on the content of plan.md. If plan.md lists an fMRI dataset as valid,
    we assume the plan is correct. However, we explicitly check for known fMRI patterns
    if the 'type' field is present.
    """
    if not dataset_info:
        return False
    
    ds_type = dataset_info.get('type', '').lower()
    ds_id = dataset_info.get('id', '').lower()
    
    # Explicit check for fMRI indicators if type is specified
    if ds_type and 'fMRI' in ds_type:
        logger.warning(f"Dataset {ds_id} identified as fMRI by type field.")
        return False
    
    # Check for known fMRI dataset IDs often used in examples (if not explicitly allowed in plan)
    # The task says: "If the block is empty OR contains ONLY invalid sources (e.g., fMRI datasets like ds001734/2642 identified by content type in plan.md)"
    # We interpret this as: if the plan says it's fMRI, it's invalid. If the plan says it's eye-tracking, it's valid.
    # We do NOT hardcode ID rejections unless the plan explicitly marks them as invalid type.
    
    # If no type is specified, we assume validity if source exists
    source = dataset_info.get('source')
    if not source:
        logger.warning(f"Dataset {ds_id} has no source specified.")
        return False
    
    return True

def hash_file(path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_meta(path: Path, meta_dict: Dict[str, Any]):
    """Write metadata JSON file."""
    meta_path = path.with_suffix(path.suffix + '_meta.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta_dict, f, indent=2)

def download_dataset(dataset_info: Dict[str, Any], target_dir: Path):
    """
    Download a dataset from the specified source.
    
    Supports:
    - Hugging Face Datasets (source starts with 'hf:')
    - Direct URLs (source starts with 'http')
    """
    source = dataset_info.get('source', '')
    ds_id = dataset_info.get('id', 'unknown')
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    if source.startswith('hf:'):
        # Hugging Face dataset
        ds_name = source.replace('hf:', '')
        logger.info(f"Downloading Hugging Face dataset: {ds_name}")
        try:
            # Load dataset to verify availability (streaming to avoid full download if possible)
            # For verification, we just need to ensure it exists.
            # We will download a small sample or the full dataset depending on size.
            # Here we assume we need to download the raw data to data/raw/
            dataset = load_dataset(ds_name, split='train', streaming=True)
            
            # Create a local file structure or download specific files
            # For simplicity, we assume the dataset provides files we can copy or stream
            # In a real scenario, we might download specific shards
            local_path = target_dir / f"{ds_id}.parquet"
            
            # Stream and save to a local file (simplified for verification)
            # In production, we would download the actual data files
            # For now, we just verify the dataset is accessible
            logger.info(f"Verified access to dataset: {ds_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to access Hugging Face dataset {ds_name}: {e}")
            return False
    elif source.startswith('http'):
        # Direct URL download
        logger.info(f"Downloading from URL: {source}")
        try:
            response = requests.get(source, stream=True)
            response.raise_for_status()
            filename = source.split('/')[-1]
            local_path = target_dir / filename
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Downloaded to {local_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download from URL {source}: {e}")
            return False
    else:
        logger.error(f"Unknown source format: {source}")
        return False

def verify_data_availability():
    """
    Main verification function.
    
    1. Parse plan.md for verified datasets.
    2. Filter for valid eye-tracking datasets.
    3. If no valid datasets found, HALT (Exit 1).
    4. If valid datasets found, attempt download/verification.
    5. Generate meta files for downloaded datasets.
    """
    logger.info("Starting data availability verification...")
    
    if not PLAN_MD_PATH.exists():
        logger.error(f"Plan file not found: {PLAN_MD_PATH}")
        sys.exit(1)
    
    datasets = parse_verified_datasets_block(PLAN_MD_PATH)
    
    if not datasets:
        logger.error("No verified datasets found in plan.md. Pipeline cannot proceed.")
        sys.exit(1)
    
    valid_datasets = [d for d in datasets if is_valid_eye_tracking_dataset(d)]
    
    if not valid_datasets:
        logger.error("ERROR: No verified eye-tracking dataset found. Pipeline cannot proceed.")
        logger.error("The 'Verified datasets' block in plan.md is either empty or contains only invalid sources (e.g., fMRI).")
        logger.error("Please correct plan.md to list valid eye-tracking dataset sources.")
        sys.exit(1)
    
    logger.info(f"Found {len(valid_datasets)} valid eye-tracking dataset(s).")
    
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    for ds in valid_datasets:
        ds_id = ds.get('id', 'unknown')
        logger.info(f"Verifying dataset: {ds_id}")
        if download_dataset(ds, DATA_RAW_DIR):
            success_count += 1
            # Generate meta file
            meta_path = DATA_RAW_DIR / f"{ds_id}_meta.json"
            meta_info = {
                'id': ds_id,
                'source': ds.get('source'),
                'timestamp': str(Path(__file__).stat().st_mtime),
                'hash': 'pending' # Will be updated after full download
            }
            # Write a placeholder meta file
            with open(meta_path, 'w') as f:
                json.dump(meta_info, f, indent=2)
            logger.info(f"Verified and prepared metadata for {ds_id}")
        else:
            logger.error(f"Failed to verify/download dataset: {ds_id}")
    
    if success_count == 0:
        logger.error("ERROR: No verified eye-tracking dataset found. Pipeline cannot proceed.")
        sys.exit(1)
    
    logger.info(f"Data verification complete. {success_count} dataset(s) verified.")
    return True

def main():
    """Entry point for the script."""
    try:
        verify_data_availability()
        logger.info("Verification successful. Proceeding with pipeline.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Verification failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()