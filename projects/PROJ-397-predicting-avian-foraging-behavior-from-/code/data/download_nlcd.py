"""
Download NLCD 2021 land cover data from HuggingFace.

This script implements Task T060, fetching the NLCD 2021 dataset from the
verified HuggingFace repository 'usgs/nlcd_2021' instead of the unavailable
USGS API. It adheres to the deviation from Constitution Principle VI and FR-002
as documented in docs/decisions/003-nlcd-2021-amendment.md.

The script downloads the landcover split, computes a SHA-256 hash for provenance,
and records metadata. It raises FileNotFoundError if the fetch fails, with no fallback.
"""

import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from datasets import load_dataset
except ImportError:
    logging.error("The 'datasets' library is required. Install it via: pip install datasets")
    sys.exit(1)

from utils.config import get_project_root, get_raw_data_dir, get_metadata_file, get_logger

# Constants
DATASET_NAME = "usgs/nlcd_2021"
DATASET_SPLIT = "landcover"
DATASET_REVISION = "main"
OUTPUT_FILENAME = "nlcd_2021_landcover.parquet"
OUTPUT_DIR_RELATIVE = "data/raw"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_metadata(metadata: dict, metadata_path: Path) -> None:
    """Append NLCD provenance to the global metadata.yaml file."""
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            try:
                current_metadata = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                logging.warning(f"Could not parse existing metadata.yaml: {e}. Overwriting.")
                current_metadata = {}
    else:
        current_metadata = {}

    current_metadata['nlcd_2021'] = metadata

    with open(metadata_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(current_metadata, f, default_flow_style=False, sort_keys=False)

    logging.info(f"Updated metadata file: {metadata_path}")

def main():
    logger = get_logger("download_nlcd")
    project_root = get_project_root()
    raw_data_dir = project_root / "data" / "raw"
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    metadata_path = project_root / "data" / "metadata.yaml"
    output_path = raw_data_dir / OUTPUT_FILENAME

    logger.info(f"Starting NLCD 2021 download from HuggingFace: {DATASET_NAME}")
    logger.info(f"Dataset Split: {DATASET_SPLIT}, Revision: {DATASET_REVISION}")

    try:
        # Load the dataset from HuggingFace
        # The task requires this exact fetch command structure
        ds = load_dataset(DATASET_NAME, split=DATASET_SPLIT, revision=DATASET_REVISION)
        
        logger.info(f"Successfully loaded dataset. Size: {len(ds)} rows.")
        
        # The dataset object might be a Dataset or DatasetDict. 
        # For usgs/nlcd_2021, it typically returns a Dataset directly if split is specified.
        # We need to save it to parquet.
        
        logger.info(f"Saving dataset to: {output_path}")
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to parquet format
        ds.to_parquet(str(output_path))
        
        logger.info(f"Dataset saved successfully to {output_path}")

    except Exception as e:
        logger.error(f"Failed to fetch or save NLCD 2021 data: {e}")
        # Fail loudly as per requirements - no fallback
        raise FileNotFoundError(f"Could not retrieve NLCD 2021 data from {DATASET_NAME}. Error: {e}")

    # Compute hash
    file_hash = compute_sha256(output_path)
    file_size = output_path.stat().st_size

    # Record provenance
    metadata_record = {
        "source": f"HuggingFace: {DATASET_NAME}",
        "split": DATASET_SPLIT,
        "revision": DATASET_REVISION,
        "extraction_date": datetime.utcnow().isoformat(),
        "file_name": OUTPUT_FILENAME,
        "file_path": str(output_path),
        "file_size_bytes": file_size,
        "sha256_hash": file_hash,
        "deviation_note": "Using NLCD 2021 (HuggingFace) instead of NLCD 2019 (USGS API) per T066 amendment."
    }

    save_metadata(metadata_record, metadata_path)
    logger.info(f"Provenance recorded. Hash: {file_hash}")

if __name__ == "__main__":
    main()
