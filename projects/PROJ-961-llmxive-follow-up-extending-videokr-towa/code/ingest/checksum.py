import hashlib
import json
import os
import logging
import sys
from pathlib import Path
from typing import Optional

from utils.config import get_project_root, get_path, ensure_dir

logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_raw_data_integrity(file_path: Path, expected_hash: Optional[str] = None) -> bool:
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False
    
    actual_hash = compute_sha256(file_path)
    
    if expected_hash:
        if actual_hash == expected_hash:
            logger.info(f"Checksum verified for {file_path}")
            return True
        else:
            logger.error(f"Checksum mismatch for {file_path}. Expected: {expected_hash}, Actual: {actual_hash}")
            return False
    else:
        # If no expected hash, just log the actual hash
        logger.info(f"Checksum for {file_path}: {actual_hash}")
        return True

def generate_checksum_file(file_paths: list, output_path: Optional[str] = None) -> None:
    if output_path is None:
        output_path = get_path("data/raw/checksums.json")
    
    ensure_dir(output_path)
    
    checksums = {}
    for file_path in file_paths:
        path = Path(file_path)
        if path.exists():
          checksums[str(path)] = compute_sha256(path)
    
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    logger.info(f"Checksums saved to {output_path}")

def verify_all_raw_data() -> bool:
    raw_dir = get_path("data/raw")
    if not raw_dir.exists():
        logger.error("Raw data directory not found.")
        return False
    
    all_valid = True
    checksums_file = get_path("data/raw/checksums.json")
    
    if not checksums_file.exists():
        logger.warning("Checksums file not found. Generating...")
        files = list(raw_dir.glob("*"))
        generate_checksum_file(files)
    
    with open(checksums_file, 'r') as f:
        checksums = json.load(f)
    
    for file_path_str, expected_hash in checksums.items():
        if not verify_raw_data_integrity(Path(file_path_str), expected_hash):
            all_valid = False
    
    return all_valid

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        logger.info("Verifying raw data integrity...")
        if verify_all_raw_data():
            logger.info("All checksums verified.")
        else:
            logger.error("Checksum verification failed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error in checksum main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()