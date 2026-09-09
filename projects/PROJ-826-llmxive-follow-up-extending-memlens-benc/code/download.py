import hashlib
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional

import config
from utils.logger import get_logger

logger = get_logger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_memlens_dataset(output_dir: str) -> Dict[str, str]:
    """
    Fetch MemLens dataset from HuggingFace.
    Returns a dict mapping file paths to their local locations.
    """
    from datasets import load_dataset

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("Loading MemLens dataset from HuggingFace...")
    try:
        # Load the dataset
        dataset = load_dataset("memlens/memlens", split="train")
        
        # Save to parquet for stability and checksumming
        data_file = output_path / "memlens_train.parquet"
        dataset.to_parquet(str(data_file))
        
        logger.info(f"Dataset saved to {data_file}")
        return {"dataset": str(data_file)}
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise

def compute_checksums(file_paths: List[str]) -> Dict[str, str]:
    """Compute SHA-256 checksums for a list of files."""
    checksums = {}
    for path in file_paths:
        if os.path.exists(path):
            checksums[path] = calculate_sha256(path)
            logger.info(f"Checksum for {path}: {checksums[path]}")
        else:
            logger.warning(f"File not found for checksum: {path}")
    return checksums

def update_state_file(artifact_paths: List[str], state_file_path: str) -> Dict[str, Any]:
    """
    Update the project state YAML file with artifact hashes.
    Creates the file if it doesn't exist.
    
    Args:
        artifact_paths: List of file paths to hash and record
        state_file_path: Path to the state YAML file to update
        
    Returns:
        The updated state dictionary
    """
    state_path = Path(state_file_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state or initialize new
    state_data = {}
    if state_path.exists():
        try:
            with open(state_path, 'r') as f:
                state_data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not read existing state file: {e}. Starting fresh.")
            state_data = {}
    
    # Ensure project key exists
    project_id = config.PROJECT_ID
    if project_id not in state_data:
        state_data[project_id] = {
            "artifacts": {},
            "last_updated": None
        }
    
    # Compute hashes and update
    current_time = os.popen("date -u +%Y-%m-%dT%H:%M:%SZ").read().strip()
    state_data[project_id]["last_updated"] = current_time
    
    for path in artifact_paths:
        if os.path.exists(path):
            file_hash = calculate_sha256(path)
            state_data[project_id]["artifacts"][path] = {
                "sha256": file_hash,
                "size_bytes": os.path.getsize(path)
            }
            logger.info(f"Recorded hash for {path}: {file_hash}")
        else:
            logger.warning(f"Artifact not found, skipping: {path}")
    
    # Write updated state
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"State file updated: {state_path}")
    return state_data

def main():
    """Main entry point for downloading and state management."""
    project_root = Path(config.PROJECT_ROOT)
    data_dir = project_root / "data" / "raw"
    state_file = project_root / "state" / "projects" / f"{config.PROJECT_ID}.yaml"
    
    # Ensure directories exist
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Download dataset
    downloaded_files = download_memlens_dataset(str(data_dir))
    
    # Compute checksums
    checksums = compute_checksums(list(downloaded_files.values()))
    
    # Update state file
    update_state_file(list(downloaded_files.values()), str(state_file))
    
    logger.info("Download and state update complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
