"""
Artifact hashing and versioning for Constitution Principle V.
Computes SHA256 hashes for all files in specified directories and updates
the project state YAML file.
"""
import hashlib
import json
from pathlib import Path
import logging
import sys
import os
import yaml
from datetime import datetime

# Ensure code directory is in path for imports if running as script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from config import get_project_config

def hash_file(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logging.error(f"Error hashing file {file_path}: {e}")
        return None

def hash_directory(dir_path: Path) -> dict:
    """
    Recursively hash all files in a directory.
    Returns a dict mapping relative file paths to their SHA256 hashes.
    """
    hashes = {}
    if not dir_path.exists():
        logging.warning(f"Directory {dir_path} does not exist, skipping.")
        return hashes
    
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file():
            # Skip hidden files and common temp files
            if file_path.name.startswith('.') or file_path.name.endswith('~'):
                continue
            rel_path = file_path.relative_to(dir_path)
            # Normalize path separators for consistency
            rel_path_str = str(rel_path).replace(os.sep, '/')
            file_hash = hash_file(file_path)
            if file_hash:
                hashes[rel_path_str] = file_hash
    return hashes

def update_state_file(state_path: Path, data_hashes: dict, code_hashes: dict):
    """
    Update the project state YAML file with new hashes.
    Creates the file if it doesn't exist.
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    current_state = {}
    if state_path.exists():
        try:
            with open(state_path, 'r') as f:
                current_state = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logging.error(f"Error parsing existing state file: {e}")
            current_state = {}
    
    # Update with new hashes
    current_state['data_hashes'] = data_hashes
    current_state['code_hashes'] = code_hashes
    current_state['last_updated'] = datetime.now().isoformat()
    
    with open(state_path, 'w') as f:
        yaml.dump(current_state, f, default_flow_style=False, sort_keys=False)
    
    logging.info(f"State file updated at {state_path}")

def main():
    """Main entry point for hashing artifacts (T044)."""
    logger = logging.getLogger("hash_artifacts")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    
    logger.info("Starting artifact hashing for T044...")
    
    # Determine project root
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    code_dir = project_root / "code"
    
    # State file path as per T044 spec
    state_dir = project_root / "state" / "projects"
    state_file = state_dir / "PROJ-314-predicting-the-impact-of-composition-on-.yaml"
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Code directory: {code_dir}")
    logger.info(f"State file: {state_file}")
    
    # Hash directories
    data_hashes = hash_directory(data_dir)
    code_hashes = hash_directory(code_dir)
    
    logger.info(f"Hashed {len(data_hashes)} files in data/")
    logger.info(f"Hashed {len(code_hashes)} files in code/")
    
    # Update state file
    update_state_file(state_file, data_hashes, code_hashes)
    
    logger.info("Artifact hashing completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())