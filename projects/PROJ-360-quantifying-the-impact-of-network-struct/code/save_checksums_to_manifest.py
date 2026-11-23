"""
Helper script to ensure checksums are propagated to the main manifest if needed.
T008 primarily focuses on saving CIFs and computing checksums, but T011 requires
a specific checksums.json. This script ensures the checksums computed in T008
are available for the next step if they weren't already written to a separate file.

Note: The primary T008 logic is in save_cifs_and_checksums.py which updates metadata.yaml.
This script is a bridge to ensure data/processed/checksums.json is populated if T011
expects it specifically from T008's output.
"""
import os
import json
import logging
import yaml
from pathlib import Path
from datetime import datetime
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import setup_logging

logger = setup_logging("checksum_manifest_logger", level=logging.INFO)

def main():
    metadata_path = "data/metadata.yaml"
    output_path = "data/processed/checksums.json"
    
    if not os.path.exists(metadata_path):
        logger.error(f"Metadata file {metadata_path} not found. Run T008 first.")
        sys.exit(1)

    with open(metadata_path, 'r') as f:
        metadata = yaml.safe_load(f)

    # Extract the latest download record
    downloads = metadata.get('downloads', [])
    if not downloads:
        logger.error("No download records found in metadata.yaml")
        sys.exit(1)

    latest_record = downloads[-1]
    source_checksums = latest_record.get('checksums', {})
    material_ids = latest_record.get('material_ids', [])

    # Prepare the structure required for T011
    # { "source_cifs": {...}, "derived_graphs": {}, "derivation": "..." }
    # Since derived graphs don't exist yet, we leave that empty or null
    manifest_structure = {
        "source_cifs": source_checksums,
        "derived_graphs": {}, 
        "derivation": "CIF -> Network via covalent radii + fallback (Pending T009/T010)"
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(manifest_structure, f, indent=2)

    logger.info(f"Checksum manifest written to {output_path}")
    logger.info(f"Source CIFs recorded: {len(source_checksums)}")

if __name__ == "__main__":
    main()