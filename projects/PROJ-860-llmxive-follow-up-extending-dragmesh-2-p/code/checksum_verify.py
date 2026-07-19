"""
Checksum verification utility for data hygiene (Constitution Principle III).

Implements SHA256 hashing for all files in data/raw and data/generated,
writing results to the state YAML file.
"""
import os
import sys
import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Optional
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_GENERATED_DIR = PROJECT_ROOT / "data" / "generated"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml"

def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def scan_directory(directory: Path) -> List[Path]:
    """
    Recursively scan a directory for all files.
    
    Args:
        directory: Path to the directory to scan.
        
    Returns:
        List of Path objects for all files found.
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []
    
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            files.append(Path(root) / filename)
    
    return sorted(files)

def load_existing_checksums(state_file: Path) -> Dict:
    """
    Load existing checksums from the state YAML file.
    
    Args:
        state_file: Path to the state YAML file.
        
    Returns:
        Dictionary containing state data.
    """
    if not state_file.exists():
        logger.info(f"State file does not exist, creating new: {state_file}")
        return {
            "artifact_hashes": {},
            "updated_at": None
        }
    
    try:
        with open(state_file, "r") as f:
            return yaml.safe_load(f) or {"artifact_hashes": {}, "updated_at": None}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing state file {state_file}: {e}")
        return {"artifact_hashes": {}, "updated_at": None}

def save_checksums(state_file: Path, state_data: Dict) -> None:
    """
    Save checksums to the state YAML file.
    
    Args:
        state_file: Path to the state YAML file.
        state_data: Dictionary containing state data to save.
    """
    # Ensure directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(state_file, "w") as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Checksums saved to {state_file}")
    except IOError as e:
        logger.error(f"Error saving state file {state_file}: {e}")
        raise

def verify_data_integrity(state_file: Path, data_dirs: List[Path]) -> bool:
    """
    Verify data integrity by comparing current hashes with stored hashes.
    
    Args:
        state_file: Path to the state YAML file.
        data_dirs: List of directories to verify.
        
    Returns:
        True if all files match, False otherwise.
    """
    state_data = load_existing_checksums(state_file)
    stored_hashes = state_data.get("artifact_hashes", {})
    
    all_valid = True
    for data_dir in data_dirs:
        if not data_dir.exists():
            logger.warning(f"Directory not found, skipping: {data_dir}")
            continue
        
        files = scan_directory(data_dir)
        for file_path in files:
            rel_path = str(file_path.relative_to(PROJECT_ROOT))
            current_hash = compute_sha256(file_path)
            
            if rel_path not in stored_hashes:
                logger.warning(f"No stored hash for: {rel_path}")
                all_valid = False
                continue
            
            if stored_hashes[rel_path] != current_hash:
                logger.error(f"Hash mismatch for {rel_path}: "
                             f"stored={stored_hashes[rel_path]}, current={current_hash}")
                all_valid = False
            else:
                logger.debug(f"Hash verified for {rel_path}")
    
    return all_valid

def update_checksums(state_file: Path, data_dirs: List[Path]) -> Dict:
    """
    Compute and update checksums for all files in specified directories.
    
    Args:
        state_file: Path to the state YAML file.
        data_dirs: List of directories to scan and hash.
        
    Returns:
        Updated state dictionary with new checksums.
    """
    import datetime
    
    state_data = load_existing_checksums(state_file)
    new_hashes = {}
    
    for data_dir in data_dirs:
        if not data_dir.exists():
            logger.warning(f"Directory not found, skipping: {data_dir}")
            continue
        
        files = scan_directory(data_dir)
        logger.info(f"Scanning {data_dir}: found {len(files)} files")
        
        for file_path in files:
            try:
                rel_path = str(file_path.relative_to(PROJECT_ROOT))
                file_hash = compute_sha256(file_path)
                new_hashes[rel_path] = file_hash
                logger.debug(f"Computed hash for {rel_path}")
            except (FileNotFoundError, IOError) as e:
                logger.error(f"Error processing {file_path}: {e}")
    
    state_data["artifact_hashes"] = new_hashes
    state_data["updated_at"] = datetime.datetime.now().isoformat()
    
    return state_data

def main():
    """Main entry point for checksum verification."""
    parser = argparse.ArgumentParser(
        description="Compute and verify SHA256 checksums for data files."
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing checksums against current files."
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update checksums for all files in data directories."
    )
    parser.add_argument(
        "--state-file",
        type=str,
        default=str(STATE_FILE),
        help=f"Path to state YAML file (default: {STATE_FILE})"
    )
    parser.add_argument(
        "--data-dirs",
        type=str,
        nargs="+",
        default=[str(DATA_RAW_DIR), str(DATA_GENERATED_DIR)],
        help=f"Directories to scan (default: {DATA_RAW_DIR}, {DATA_GENERATED_DIR})"
    )
    
    args = parser.parse_args()
    state_file = Path(args.state_file)
    data_dirs = [Path(d) for d in args.data_dirs]
    
    if not args.verify and not args.update:
        # Default behavior: update checksums
        logger.info("No action specified, defaulting to --update")
        args.update = True
    
    if args.verify:
        logger.info("Verifying data integrity...")
        is_valid = verify_data_integrity(state_file, data_dirs)
        if is_valid:
            logger.info("All checksums verified successfully.")
            sys.exit(0)
        else:
            logger.error("Data integrity check failed. Some files do not match.")
            sys.exit(1)
    
    if args.update:
        logger.info("Updating checksums...")
        state_data = update_checksums(state_file, data_dirs)
        save_checksums(state_file, state_data)
        logger.info("Checksum update complete.")
        sys.exit(0)

if __name__ == "__main__":
    main()
