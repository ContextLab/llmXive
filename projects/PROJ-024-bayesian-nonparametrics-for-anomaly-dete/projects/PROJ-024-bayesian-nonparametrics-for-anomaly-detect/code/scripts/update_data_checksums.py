#!/usr/bin/env python3
"""
Update state file with SHA256 checksums for all raw data files.

This script scans data/raw/ for all data files, computes their SHA256
checksums, and updates the project state file at
state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detect.yaml

Consistent with T012 and T008 checksum recording logic.
"""
import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_file_checksum_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_file_info(file_path: Path) -> Dict[str, Any]:
    """Get file metadata including size and modification time."""
    stat = file_path.stat()
    return {
        "size_bytes": stat.st_size,
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat()
    }

def find_raw_data_files(raw_data_dir: Path) -> List[Path]:
    """Find all data files in the raw data directory."""
    if not raw_data_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_data_dir}")
        return []
    
    data_files = []
    # Common data file extensions
    extensions = {'.csv', '.json', '.txt', '.parquet', '.feather', '.pkl', '.npy'}
    
    for file_path in raw_data_dir.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            data_files.append(file_path)
    
    return sorted(data_files)

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """Load the existing state file or create a new structure."""
    if state_path.exists():
        with open(state_path, 'r') as f:
            return yaml.safe_load(f) or {}
    else:
        # Create initial state structure
        return {
            "project_id": "PROJ-024-bayesian-nonparametrics-for-anomaly-detect",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "artifacts": {},
            "data_checksums": {}
        }

def save_state_file(state_path: Path, state: Dict[str, Any]) -> None:
    """Save the updated state file."""
    # Ensure directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    state["updated_at"] = datetime.now().isoformat()
    
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"State file saved: {state_path}")

def update_data_checksums(state: Dict[str, Any], raw_data_dir: Path) -> Dict[str, Any]:
    """Update data checksums section of the state."""
    data_files = find_raw_data_files(raw_data_dir)
    
    if not data_files:
        logger.warning("No data files found in raw directory")
        return state
    
    if "data_checksums" not in state:
        state["data_checksums"] = {}
    
    checksums_updated = 0
    for file_path in data_files:
        # Use relative path from project root
        relative_path = str(file_path.relative_to(raw_data_dir.parent.parent))
        
        checksum = compute_file_checksum_sha256(file_path)
        file_info = get_file_info(file_path)
        
        state["data_checksums"][relative_path] = {
            "checksum_sha256": checksum,
            "size_bytes": file_info["size_bytes"],
            "modified_time": file_info["modified_time"],
            "updated_at": datetime.now().isoformat()
        }
        
        checksums_updated += 1
        logger.info(f"  Checksum: {relative_path} -> {checksum[:16]}...")
    
    logger.info(f"Updated checksums for {checksums_updated} files")
    return state

def main() -> int:
    """Main entry point."""
    # Determine project root (assume script is at code/scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    # Define paths
    raw_data_dir = project_root / "data" / "raw"
    state_file = project_root / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-detect.yaml"
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Raw data directory: {raw_data_dir}")
    logger.info(f"State file: {state_file}")
    
    # Load existing state
    state = load_state_file(state_file)
    
    # Update data checksums
    state = update_data_checksums(state, raw_data_dir)
    
    # Save updated state
    save_state_file(state_file, state)
    
    # Verify the state file was updated
    if state_file.exists():
        with open(state_file, 'r') as f:
            content = f.read()
            if "data_checksums" in content:
                logger.info("✓ State file successfully updated with data checksums")
                return 0
    
    logger.error("✗ Failed to update state file")
    return 1

if __name__ == "__main__":
    sys.exit(main())
