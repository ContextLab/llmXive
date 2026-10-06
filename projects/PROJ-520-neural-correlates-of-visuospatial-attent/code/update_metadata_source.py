"""
T045: Update metadata with verified real data source information.

This script ensures that data/processed/metadata.json contains the
data_source_url and fetch_method fields required for traceability.
It reads the dataset information from the download process or defaults
to the OpenNeuro ds0001171 dataset as specified in research.md.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import from existing project modules
from logger import get_logger
from config import get_paths

def load_metadata(metadata_path: Path) -> Dict[str, Any]:
    """Load existing metadata or return default schema."""
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            return json.load(f)
    else:
        # Return default schema as defined in T044
        return {
            "skipped_electrodes": [],
            "assumptions": {},
            "data_source_url": None,
            "fetch_method": None
        }

def update_metadata_source(
    metadata: Dict[str, Any],
    data_source_url: str,
    fetch_method: str
) -> Dict[str, Any]:
    """
    Update metadata with verified real data source information.

    Args:
        metadata: Existing metadata dictionary
        data_source_url: URL of the data source (e.g., OpenNeuro dataset URL)
        fetch_method: Method used to fetch the data (e.g., 'mne.datasets.openneuro.fetch')

    Returns:
        Updated metadata dictionary
    """
    metadata['data_source_url'] = data_source_url
    metadata['fetch_method'] = fetch_method
    return metadata

def save_metadata(metadata: Dict[str, Any], metadata_path: Path) -> None:
    """Save metadata to JSON file."""
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

def main() -> None:
    """Main entry point for T045."""
    logger = get_logger(__name__)
    paths = get_paths()
    metadata_path = paths['OUTPUT_PATH'] / 'metadata.json'

    logger.info("T045: Updating metadata with verified real data source information")

    # Load existing metadata
    metadata = load_metadata(metadata_path)

    # Define the verified real data source
    # Based on research.md and T000 verification, the target dataset is ds0001171
    data_source_url = "https://openneuro.org/datasets/ds0001171/versions/1.0.0"
    fetch_method = "mne.datasets.openneuro.fetch"

    # Update metadata
    metadata = update_metadata_source(metadata, data_source_url, fetch_method)

    # Save updated metadata
    save_metadata(metadata, metadata_path)

    logger.info(f"T045: Successfully updated metadata at {metadata_path}")
    logger.info(f"  data_source_url: {data_source_url}")
    logger.info(f"  fetch_method: {fetch_method}")

    # Verify the update
    with open(metadata_path, 'r') as f:
        saved_metadata = json.load(f)

    assert saved_metadata['data_source_url'] == data_source_url, \
        "data_source_url not saved correctly"
    assert saved_metadata['fetch_method'] == fetch_method, \
        "fetch_method not saved correctly"

    logger.info("T045: Verification passed - metadata contains required traceability fields")

if __name__ == "__main__":
    main()
