import os
import yaml
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import csv

from utils.config import get_project_root, get_data_processed_path

logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        raise

def count_rows_csv(file_path: str) -> int:
    """Count rows in a CSV file (excluding header)."""
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip header
            next(reader, None)
            return sum(1 for _ in reader)
    except FileNotFoundError:
        logger.error(f"File not found for row count: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error counting rows in {file_path}: {e}")
        raise

def count_rows_json(file_path: str) -> int:
    """Count items in a JSON list file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return len(data)
            return 0
    except FileNotFoundError:
        logger.error(f"File not found for row count: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error counting rows in {file_path}: {e}")
        raise

def load_metadata() -> Dict[str, Any]:
    """Load the metadata.yaml file."""
    project_root = get_project_root()
    metadata_path = project_root / "data" / "metadata.yaml"
    
    if not metadata_path.exists():
        logger.warning(f"Metadata file not found at {metadata_path}, creating default.")
        return {
            "version": "1.0",
            "last_updated": "",
            "project": "PROJ-107-quantifying-the-effects-of-dark-matter-h",
            "pipeline_version": "1.0.0",
            "datasets": {},
            "flags": {},
            "gaps": {},
            "checksums": {"algorithm": "sha256", "files": []},
            "sampling_protocol": {}
        }
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_metadata(metadata: Dict[str, Any]) -> None:
    """Save the metadata.yaml file."""
    project_root = get_project_root()
    metadata_path = project_root / "data" / "metadata.yaml"
    
    from datetime import datetime
    metadata["last_updated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    with open(metadata_path, 'w', encoding='utf-8') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Metadata saved to {metadata_path}")

def update_dataset_metadata(
    dataset_key: str,
    path: str,
    status: str,
    description: Optional[str] = None,
    row_count: Optional[int] = None,
    checksum: Optional[str] = None,
    associational_only: bool = True
) -> None:
    """Update a specific dataset entry in metadata.yaml."""
    metadata = load_metadata()
    
    if "datasets" not in metadata:
        metadata["datasets"] = {}
    
    if dataset_key not in metadata["datasets"]:
        metadata["datasets"][dataset_key] = {
            "associational_only": True,
            "path": "",
            "checksum": None,
            "row_count": None,
            "status": "pending",
            "description": ""
        }
    
    dataset_entry = metadata["datasets"][dataset_key]
    dataset_entry["path"] = path
    dataset_entry["status"] = status
    dataset_entry["associational_only"] = associational_only
    
    if description:
        dataset_entry["description"] = description
    
    # If row_count or checksum not provided, try to calculate from file
    full_path = get_project_root() / path
    if full_path.exists():
        if row_count is None:
            if path.endswith('.csv'):
                dataset_entry["row_count"] = count_rows_csv(str(full_path))
            elif path.endswith('.json'):
                dataset_entry["row_count"] = count_rows_json(str(full_path))
            else:
                dataset_entry["row_count"] = 0
        else:
            dataset_entry["row_count"] = row_count
        
        if checksum is None:
            dataset_entry["checksum"] = calculate_sha256(str(full_path))
        else:
            dataset_entry["checksum"] = checksum
    else:
        if row_count is not None:
            dataset_entry["row_count"] = row_count
        if checksum is not None:
            dataset_entry["checksum"] = checksum

def update_gap_status(gap_key: str, status: str, reason: str, sc_status: str = "PENDING") -> None:
    """Update a gap entry in metadata.yaml."""
    metadata = load_metadata()
    
    if "gaps" not in metadata:
        metadata["gaps"] = {}
    
    if gap_key not in metadata["gaps"]:
        metadata["gaps"][gap_key] = {
            "status": "pending",
            "reason": "",
            "sc_004_status": "PENDING"
        }
    
    metadata["gaps"][gap_key]["status"] = status
    metadata["gaps"][gap_key]["reason"] = reason
    metadata["gaps"][gap_key]["sc_004_status"] = sc_status
    
    save_metadata(metadata)

def flag_all_output_datasets() -> None:
    """Ensure all output datasets have associational_only=true flag."""
    metadata = load_metadata()
    
    if "datasets" not in metadata:
        return
    
    for key, entry in metadata["datasets"].items():
        if "associational_only" not in entry:
            entry["associational_only"] = True
    
    save_metadata(metadata)

def main() -> None:
    """Main entry point for metadata management demonstration."""
    logger.info("Initializing metadata management system.")
    
    # Example: Update a dataset entry
    # update_dataset_metadata(
    #     dataset_key="halo_shapes",
    #     path="data/processed/halo_shapes.csv",
    #     status="completed",
    #     description="Computed axial ratios for TNG-100 haloes"
    # )
    
    # Example: Update a gap status
    # update_gap_status("millennium_fetch", "failed", "Data source unavailable", "Not Measurable")
    
    # Example: Flag all datasets
    flag_all_output_datasets()
    
    logger.info("Metadata management system initialized.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
