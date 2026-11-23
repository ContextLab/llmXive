"""
record_nlcd_provenance.py

Records the exact version, date, and source URL of the downloaded NLCD 2019 raster
in data/metadata.yaml to satisfy Constitution Principle VI (Habitat Data Provenance).

This script verifies the existence of the NLCD 2019 file, computes its hash, and
updates the project's metadata.yaml with the specific provenance details.
"""

import os
import sys
import logging
import yaml
import hashlib
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_data_dir, get_raw_data_dir, get_project_root
from utils.provenance import compute_file_hash

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for NLCD 2019
NLCD_VERSION = "NLCD_2019_Land_Cover_Land_Use"
NLCD_YEAR = 2019
# USGS EarthExplorer / NLCD specific source URL pattern
NLCD_SOURCE_URL = "https://www.mrlc.gov/data/nlcd-2019-land-cover-land-use"
NLCD_FILENAME = "nlcd_2019.zip"
METADATA_FILENAME = "metadata.yaml"

def load_metadata(metadata_path: Path) -> dict:
    """Load existing metadata.yaml or return an empty structure."""
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def save_metadata(metadata_path: Path, data: dict) -> None:
    """Save metadata dictionary to YAML file."""
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, 'w') as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Saved metadata to {metadata_path}")

def verify_nlcd_file_exists(raw_data_dir: Path) -> Path:
    """
    Verify that the NLCD 2019 file exists in the raw data directory.
    Raises FileNotFoundError if not found.
    """
    expected_path = raw_data_dir / NLCD_FILENAME
    if not expected_path.exists():
        raise FileNotFoundError(
            f"NLCD 2019 file not found at {expected_path}. "
            f"Please run data/download_nlcd.py first."
        )
    return expected_path

def compute_and_record_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of the file and return it."""
    logger.info(f"Computing SHA-256 hash for {file_path}...")
    file_hash = compute_file_hash(str(file_path))
    logger.info(f"File hash: {file_hash}")
    return file_hash

def record_nlcd_provenance(metadata: dict, file_path: Path, file_hash: str) -> dict:
    """
    Update the metadata dictionary with NLCD provenance information.
    Ensures the 'nlcd' key exists and updates the specific version details.
    """
    if 'nlcd' not in metadata:
        metadata['nlcd'] = {}

    nlcd_data = metadata['nlcd']
    nlcd_data['version'] = NLCD_VERSION
    nlcd_data['year'] = NLCD_YEAR
    nlcd_data['source_url'] = NLCD_SOURCE_URL
    nlcd_data['filename'] = NLCD_FILENAME
    nlcd_data['file_hash_sha256'] = file_hash
    nlcd_data['downloaded_at'] = datetime.utcnow().isoformat() + "Z"
    nlcd_data['recorded_at'] = datetime.utcnow().isoformat() + "Z"
    
    # Explicitly record the dataset identifier as per USGS/MRLC standards
    nlcd_data['dataset_id'] = "NLCD_2019_Land_Cover_Land_Use"
    
    logger.info("NLCD provenance recorded in metadata.")
    return metadata

def main():
    """
    Main entry point for recording NLCD provenance.
    """
    data_dir = get_data_dir()
    raw_data_dir = get_raw_data_dir()
    metadata_path = data_dir / METADATA_FILENAME

    try:
        # 1. Verify file exists
        nlcd_file_path = verify_nlcd_file_exists(raw_data_dir)
        logger.info(f"Verified NLCD file exists: {nlcd_file_path}")

        # 2. Load existing metadata
        metadata = load_metadata(metadata_path)

        # 3. Compute hash
        file_hash = compute_and_record_hash(nlcd_file_path)

        # 4. Record provenance
        updated_metadata = record_nlcd_provenance(metadata, nlcd_file_path, file_hash)

        # 5. Save updated metadata
        save_metadata(metadata_path, updated_metadata)

        logger.info("Task T008c completed successfully: NLCD provenance recorded.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
