"""
Versioning script for llmXive project.
Computes checksums for all data files and updates the project state YAML.
Implements Constitution Principle V: Data Integrity and Reproducibility.
"""
import os
import sys
import hashlib
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from utils.logging import get_logger

logger = get_logger(__name__)

def compute_file_checksum(filepath: Path, algorithm: str = "sha256") -> str:
    """
    Compute a cryptographic checksum for a single file.
    
    Args:
        filepath: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
    
    Returns:
        Hex digest string of the file checksum
    
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be read
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    hasher = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()

def get_all_data_files(data_dir: Path) -> List[Path]:
    """
    Recursively find all data files in the data directory.
    
    Args:
        data_dir: Path to the data directory
    
    Returns:
        List of Path objects for all files found
    """
    if not data_dir.exists():
        logger.warning(f"Data directory does not exist: {data_dir}")
        return []
    
    data_files = []
    for root, _, files in os.walk(data_dir):
        for file in files:
            # Skip hidden files and common non-data files
            if file.startswith('.') or file.endswith(('.pyc', '.pyo', '__pycache__')):
                continue
            data_files.append(Path(root) / file)
    
    return sorted(data_files)

def checksum_data_directory(data_dir: Path) -> Dict[str, str]:
    """
    Compute checksums for all files in the data directory.
    
    Args:
        data_dir: Path to the data directory
    
    Returns:
        Dictionary mapping relative file paths to their checksums
    """
    checksums = {}
    data_files = get_all_data_files(data_dir)
    
    logger.info(f"Found {len(data_files)} files in {data_dir}")
    
    for filepath in data_files:
        try:
            rel_path = filepath.relative_to(data_dir)
            checksum = compute_file_checksum(filepath)
            checksums[str(rel_path)] = checksum
            logger.debug(f"Checksummed: {rel_path} -> {checksum[:16]}...")
        except Exception as e:
            logger.error(f"Failed to checksum {filepath}: {e}")
            raise
    
    return checksums

def load_project_state(state_file: Path) -> Dict[str, Any]:
    """
    Load the project state YAML file.
    
    Args:
        state_file: Path to the state YAML file
    
    Returns:
        Dictionary containing the project state
    """
    if not state_file.exists():
        logger.info(f"State file does not exist, creating new one: {state_file}")
        return {
            "project_id": "PROJ-923-llmxive-follow-up-extending-zone-of-prox",
            "version": "1.0.0",
            "last_updated": None,
            "data_checksums": {},
            "metadata": {
                "created_by": "versioning.py",
                "created_at": None
            }
        }
    
    with open(state_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_project_state(state_file: Path, state: Dict[str, Any]) -> None:
    """
    Save the project state to a YAML file.
    
    Args:
        state_file: Path to the state YAML file
        state: Dictionary containing the project state
    """
    # Ensure directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    logger.info(f"Project state saved to: {state_file}")

def update_project_state(
    state_file: Path,
    data_dir: Path,
    project_id: str = "PROJ-923-llmxive-follow-up-extending-zone-of-prox"
) -> Dict[str, Any]:
    """
    Update the project state with new data checksums.
    
    Args:
        state_file: Path to the state YAML file
        data_dir: Path to the data directory
        project_id: Project identifier
    
    Returns:
        Updated project state dictionary
    """
    # Load existing state or create new
    state = load_project_state(state_file)
    
    # Update project ID if not set
    if "project_id" not in state:
        state["project_id"] = project_id
    
    # Compute new checksums
    logger.info(f"Computing checksums for data directory: {data_dir}")
    new_checksums = checksum_data_directory(data_dir)
    
    # Update state
    state["data_checksums"] = new_checksums
    state["last_updated"] = datetime.utcnow().isoformat()
    
    if "metadata" not in state:
        state["metadata"] = {}
    state["metadata"]["last_versioned_at"] = datetime.utcnow().isoformat()
    state["metadata"]["last_versioned_by"] = "versioning.py"
    
    # Save updated state
    save_project_state(state_file, state)
    
    logger.info(f"Updated {len(new_checksums)} file checksums in project state")
    return state

def main():
    """
    Main entry point for the versioning script.
    
    Usage:
        python code/versioning.py [--data-dir <path>] [--state-file <path>]
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Versioning script: checksum data and update project state"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Path to the data directory (default: data)"
    )
    parser.add_argument(
        "--state-file",
        type=str,
        default="state/projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox.yaml",
        help="Path to the project state YAML file"
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default="PROJ-923-llmxive-follow-up-extending-zone-of-prox",
        help="Project identifier (default: PROJ-923-llmxive-follow-up-extending-zone-of-prox)"
    )
    
    args = parser.parse_args()
    
    # Resolve paths relative to project root
    project_root = Path(__file__).parent.parent
    data_dir = project_root / args.data_dir
    state_file = project_root / args.state_file
    
    logger.info(f"Starting versioning process")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"State file: {state_file}")
    logger.info(f"Project ID: {args.project_id}")
    
    try:
        # Update project state with new checksums
        state = update_project_state(
            state_file=state_file,
            data_dir=data_dir,
            project_id=args.project_id
        )
        
        # Print summary
        logger.info("Versioning completed successfully!")
        logger.info(f"Files checksummed: {len(state.get('data_checksums', {}))}")
        logger.info(f"Last updated: {state.get('last_updated', 'N/A')}")
        
        # Return success
        return 0
        
    except Exception as e:
        logger.error(f"Versioning failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
