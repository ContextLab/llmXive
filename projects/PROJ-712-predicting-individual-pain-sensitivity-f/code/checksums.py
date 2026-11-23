import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any

import yaml

from utils import setup_logging, compute_checksum

logger = logging.getLogger(__name__)

def compute_sha256_file(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def scan_raw_data_directory(raw_dir: Path) -> List[Path]:
    """Recursively scan data/raw for all files."""
    if not raw_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_dir}")
        return []
    
    files = []
    for root, _, filenames in os.walk(raw_dir):
        for filename in filenames:
            # Skip hidden files and common non-data artifacts
            if filename.startswith('.'):
                continue
            files.append(Path(root) / filename)
    return files

def record_checksums_to_state(
    checksums: Dict[str, str],
    state_file: Path,
    project_id: str = "PROJ-712-predicting-individual-pain-sensitivity-f"
) -> None:
    """Record checksums into the project state YAML file."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    existing_data: Dict[str, Any] = {}
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                existing_data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not read existing state file {state_file}: {e}")
            existing_data = {}
    
    # Ensure structure exists
    if "projects" not in existing_data:
        existing_data["projects"] = {}
    
    if project_id not in existing_data["projects"]:
        existing_data["projects"][project_id] = {}
    
    project_data = existing_data["projects"][project_id]
    
    # Update or set checksums
    project_data["data_checksums"] = checksums
    project_data["checksum_algorithm"] = "SHA-256"
    
    # Add metadata
    project_data["last_checksum_update"] = None  # Can be updated with timestamp if needed
    
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(existing_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Checksums recorded to {state_file}")

def main() -> None:
    """Main entry point to compute and record checksums for raw data."""
    setup_logging()
    
    project_root = Path(__file__).resolve().parent.parent
    raw_data_dir = project_root / "data" / "raw"
    state_dir = project_root / "state" / "projects"
    state_file = state_dir / "PROJ-712-predicting-individual-pain-sensitivity-f.yaml"
    
    logger.info(f"Scanning raw data directory: {raw_data_dir}")
    raw_files = scan_raw_data_directory(raw_data_dir)
    
    if not raw_files:
        logger.warning("No files found in raw data directory. Checksums will be empty.")
    
    checksums: Dict[str, str] = {}
    for file_path in raw_files:
        try:
            relative_path = file_path.relative_to(project_root)
            hash_val = compute_sha256_file(file_path)
            checksums[str(relative_path)] = hash_val
            logger.info(f"  Computed checksum for {relative_path}: {hash_val[:16]}...")
        except Exception as e:
            logger.error(f"Failed to compute checksum for {file_path}: {e}")
    
    logger.info(f"Total files processed: {len(checksums)}")
    record_checksums_to_state(checksums, state_file)
    logger.info("Checksum recording complete.")

if __name__ == "__main__":
    main()
