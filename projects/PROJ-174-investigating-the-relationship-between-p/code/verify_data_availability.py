"""
Verify data availability for the pupil dilation study.

Parses the '# Verified datasets' block in plan.md to identify valid
eye-tracking datasets. Downloads valid datasets to data/raw/ if not present.
Halts execution if no valid eye-tracking datasets are found.
"""
import os
import sys
import re
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import requests
from tqdm import tqdm

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.provenance import hash_file, write_meta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PLAN_MD_PATH = project_root / "plan.md"
DATA_RAW_DIR = project_root / "data" / "raw"
META_SUFFIX = "_meta.json"

# Valid content types for eye-tracking datasets
VALID_CONTENT_TYPES = [
    "eye-tracking",
    "eyetracking",
    "pupil",
    "pupillometry"
]

# Invalid content types (e.g., fMRI, EEG)
INVALID_CONTENT_TYPES = [
    "fMRI",
    "fmri",
    "MRI",
    "mri",
    "EEG",
    "eeg",
    "MEG",
    "meg"
]

def parse_verified_datasets_block(plan_path: Path) -> List[Dict[str, Any]]:
    """
    Parse the '# Verified datasets' block from plan.md.
    
    Returns a list of dictionaries containing dataset information.
    """
    if not plan_path.exists():
        logger.error(f"Plan file not found: {plan_path}")
        return []
    
    with open(plan_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the '# Verified datasets' block
    # Pattern: starts with "# Verified datasets" and ends before next major section or end of file
    pattern = r'# Verified datasets\s*\n(.*?)(?=\n#|\n##|\Z)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    
    if not match:
        logger.warning("No '# Verified datasets' block found in plan.md")
        return []
    
    block_content = match.group(1).strip()
    datasets = []
    
    # Parse dataset entries (assuming format: - ID: description or similar)
    # Common formats:
    # - ds001234: description
    # - ID: ds001234 | type: eye-tracking | ...
    # - OpenNeuro: ds001234
    
    lines = block_content.split('\n')
    current_dataset = {}
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Check for new dataset entry (starts with - or bullet)
        if line.startswith('-') or line.startswith('*'):
            # Save previous dataset if exists
            if current_dataset:
                datasets.append(current_dataset)
            current_dataset = {}
            line = line[1:].strip()
        
        # Parse key-value pairs
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key in ['id', 'dataset', 'openneuro', 'ds']:
                current_dataset['id'] = value
            elif key in ['type', 'content_type', 'modality']:
                current_dataset['content_type'] = value
            elif key in ['description', 'desc']:
                current_dataset['description'] = value
            elif key in ['url', 'download_url']:
                current_dataset['url'] = value
            elif key in ['format', 'data_format']:
                current_dataset['format'] = value
        elif current_dataset and 'id' not in current_dataset:
            # If line looks like an ID without a key
            if re.match(r'^ds\d+$', line) or re.match(r'^[a-z0-9]{6,}$', line, re.IGNORECASE):
                current_dataset['id'] = line
    
    # Add last dataset if exists
    if current_dataset:
        datasets.append(current_dataset)
    
    return datasets

def is_valid_eye_tracking_dataset(dataset: Dict[str, Any]) -> bool:
    """
    Check if a dataset is a valid eye-tracking dataset.
    
    Returns True if the dataset contains eye-tracking data, False otherwise.
    """
    if not dataset.get('id'):
        return False
    
    content_type = dataset.get('content_type', '').lower()
    
    # Check if it's explicitly marked as invalid
    for invalid_type in INVALID_CONTENT_TYPES:
        if invalid_type.lower() in content_type:
            return False
    
    # Check if it's explicitly marked as valid
    for valid_type in VALID_CONTENT_TYPES:
        if valid_type in content_type:
            return True
    
    # If content type is not specified, try to infer from description
    description = dataset.get('description', '').lower()
    for valid_type in VALID_CONTENT_TYPES:
        if valid_type in description:
            return True
    
    # Default to invalid if we can't determine
    return False

def download_dataset(dataset_id: str, output_dir: Path) -> Tuple[bool, str]:
    """
    Download a dataset from OpenNeuro or other sources.
    
    Returns (success, message).
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    dataset_dir = output_dir / dataset_id
    
    # Check if already downloaded
    if dataset_dir.exists() and any(dataset_dir.iterdir()):
        logger.info(f"Dataset {dataset_id} already exists at {dataset_dir}")
        return True, f"Dataset {dataset_id} already exists"
    
    # Try to download from OpenNeuro
    openneuro_url = f"https://datasets.openneuro.org/datasets/{dataset_id}/versions/latest/download"
    
    logger.info(f"Attempting to download {dataset_id} from OpenNeuro...")
    
    try:
        response = requests.get(openneuro_url, stream=True, timeout=300)
        response.raise_for_status()
        
        # Get file size for progress bar
        total_size = int(response.headers.get('content-length', 0))
        
        # Create a zip file path
        zip_path = dataset_dir.parent / f"{dataset_id}.zip"
        
        with open(zip_path, 'wb') as f, tqdm(
            desc=dataset_id,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        # Extract the zip file
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dataset_dir)
        
        # Remove the zip file
        zip_path.unlink()
        
        logger.info(f"Successfully downloaded {dataset_id}")
        
        # Generate metadata
        meta_path = dataset_dir / f"{dataset_id}{META_SUFFIX}"
        meta = {
            'hash': hash_file(str(dataset_dir)),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': 'openneuro',
            'dataset_id': dataset_id
        }
        write_meta(str(meta_path), meta)
        
        return True, f"Successfully downloaded {dataset_id}"
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {dataset_id} from OpenNeuro: {e}")
        return False, f"Failed to download {dataset_id}: {e}"
    except Exception as e:
        logger.error(f"Unexpected error downloading {dataset_id}: {e}")
        return False, f"Unexpected error downloading {dataset_id}: {e}"

def verify_data_availability() -> int:
    """
    Main function to verify data availability.
    
    Returns:
        0: Success (valid datasets found and downloaded)
        1: Failure (no valid datasets found)
    """
    logger.info("Starting data availability verification...")
    
    # Parse verified datasets from plan.md
    datasets = parse_verified_datasets_block(PLAN_MD_PATH)
    
    if not datasets:
        logger.error("No datasets found in '# Verified datasets' block")
        print("ERROR: No verified datasets found in plan.md. Pipeline cannot proceed.")
        return 1
    
    logger.info(f"Found {len(datasets)} dataset(s) in plan.md")
    
    # Filter for valid eye-tracking datasets
    valid_datasets = [d for d in datasets if is_valid_eye_tracking_dataset(d)]
    
    if not valid_datasets:
        logger.error("No valid eye-tracking datasets found")
        print("ERROR: No verified eye-tracking dataset found. Pipeline cannot proceed.")
        return 1
    
    logger.info(f"Found {len(valid_datasets)} valid eye-tracking dataset(s)")
    
    # Download valid datasets
    success_count = 0
    for dataset in valid_datasets:
        dataset_id = dataset['id']
        success, message = download_dataset(dataset_id, DATA_RAW_DIR)
        if success:
            success_count += 1
        else:
            logger.error(message)
    
    if success_count == 0:
        logger.error("Failed to download any valid datasets")
        print("ERROR: Failed to download any valid eye-tracking datasets. Pipeline cannot proceed.")
        return 1
    
    logger.info(f"Successfully downloaded {success_count}/{len(valid_datasets)} valid datasets")
    print(f"SUCCESS: Found and downloaded {success_count} valid eye-tracking dataset(s)")
    return 0

if __name__ == "__main__":
    exit_code = verify_data_availability()
    sys.exit(exit_code)