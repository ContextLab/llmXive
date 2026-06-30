"""
Setup script for dataset metadata structure.
Initializes data/metadata.yaml with the schema for versioning and checksums.

This task defines the schema only; population occurs after data download.

Schema Structure:
- dataset_name: str
- version: str (semantic versioning)
- created_at: ISO 8601 timestamp
- datasets: list of dataset entries
  - name: str (e.g., "filtered_open_x_embodiment")
  - path: str (relative path to data file)
  - format: str (e.g., "parquet")
  - version: str
  - checksum: str (SHA256, populated after download)
  - row_count: int (populated after download)
  - description: str
  - source_url: str
  - filters_applied: list of str
- metadata_version: str (schema version)
"""

import os
import yaml
from datetime import datetime
from pathlib import Path

# Ensure we are in the project root context
# The script should be run from the project root or code/ directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
METADATA_FILE = DATA_DIR / "metadata.yaml"

SCHEMA_VERSION = "1.0.0"

def ensure_data_directory():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def create_initial_metadata():
    """Create the initial metadata.yaml file with the schema structure."""
    metadata = {
        "metadata_version": SCHEMA_VERSION,
        "dataset_name": "qwen-vla-cross-embodiment-transfer",
        "version": "0.0.1",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "description": "Metadata for Open X-Embodiment dataset subsets used in cross-embodiment transfer study.",
        "datasets": [
            {
                "name": "filtered_open_x_embodiment",
                "path": "data/filtered_open_x_embodiment.parquet",
                "format": "parquet",
                "version": "pending",
                "checksum": "pending",
                "row_count": 0,
                "description": "Multi-platform filtered Open X-Embodiment dataset (franka, ur5, kuka)",
                "source_url": "https://huggingface.co/datasets/open-x-embodiment",
                "filters_applied": [
                    "platform_id in [franka, ur5, kuka]",
                    "sampled to ~50k demonstrations"
                ],
                "status": "pending_download"
            },
            {
                "name": "filtered_open_x_embodiment_single_platform",
                "path": "data/filtered_open_x_embodiment_single_platform.parquet",
                "format": "parquet",
                "version": "pending",
                "checksum": "pending",
                "row_count": 0,
                "description": "Single-platform (franka) filtered Open X-Embodiment dataset for baseline",
                "source_url": "https://huggingface.co/datasets/open-x-embodiment",
                "filters_applied": [
                    "platform_id == franka",
                    "sampled to ~50k demonstrations"
                ],
                "status": "pending_download"
            }
        ],
        "schema_documentation": {
            "fields": {
                "metadata_version": "Version of the metadata schema itself",
                "dataset_name": "Name of the overall project dataset",
                "version": "Semantic version of the dataset collection",
                "created_at": "ISO 8601 timestamp of creation",
                "datasets": "List of individual dataset entries",
                "datasets[].name": "Unique identifier for the dataset",
                "datasets[].path": "Relative path from project root to the data file",
                "datasets[].format": "File format (e.g., parquet, csv)",
                "datasets[].version": "Version of this specific dataset file",
                "datasets[].checksum": "SHA256 checksum of the file (populated after download)",
                "datasets[].row_count": "Number of rows in the dataset (populated after download)",
                "datasets[].description": "Human-readable description",
                "datasets[].source_url": "URL to the original data source",
                "datasets[].filters_applied": "List of filtering criteria applied",
                "datasets[].status": "Current status: pending_download, downloaded, verified"
            }
        }
    }
    
    return metadata

def write_metadata(metadata):
    """Write metadata to YAML file."""
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(
            metadata, 
            f, 
            default_flow_style=False, 
            allow_unicode=True,
            sort_keys=False,
            indent=2
        )

def main():
    """Main entry point."""
    print(f"Setting up metadata schema at: {METADATA_FILE}")
    
    # Ensure data directory exists
    ensure_data_directory()
    
    # Create initial metadata structure
    metadata = create_initial_metadata()
    
    # Write to file
    write_metadata(metadata)
    
    print(f"Successfully created metadata schema at {METADATA_FILE}")
    print(f"Schema version: {SCHEMA_VERSION}")
    print("Note: Dataset entries are initialized with 'pending' status.")
    print("Checksums and row counts will be populated after data download (T012/T012b).")
    print("Verification and updates will occur in T012c.")

if __name__ == "__main__":
    main()
