import json
import hashlib
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import get_config, get_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"Checksum verification failed: File not found at {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error reading file {file_path} for checksum: {e}")


def load_checksum_manifest(manifest_path: Path) -> Dict[str, str]:
    """Load the checksum manifest JSON."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Checksum manifest not found at {manifest_path}")
    
    try:
        with open(manifest_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in checksum manifest: {e}")


def verify_checksums(manifest: Dict[str, str], base_path: Path) -> Tuple[List[str], List[str]]:
    """
    Verify checksums for all files in the manifest.
    
    Returns:
        Tuple of (passed_files, failed_files)
    """
    passed = []
    failed = []
    
    for relative_path, expected_checksum in manifest.items():
        full_path = base_path / relative_path
        
        if not full_path.exists():
            logger.error(f"File missing: {relative_path}")
            failed.append(relative_path)
            continue
        
        try:
            actual_checksum = calculate_file_checksum(full_path)
            if actual_checksum == expected_checksum:
                passed.append(relative_path)
                logger.debug(f"Checksum OK: {relative_path}")
            else:
                logger.error(f"Checksum mismatch for {relative_path}: expected {expected_checksum}, got {actual_checksum}")
                failed.append(relative_path)
        except Exception as e:
            logger.error(f"Error verifying {relative_path}: {e}")
            failed.append(relative_path)
    
    return passed, failed


def main():
    """Main entry point for checksum verification."""
    logger.info("Starting checksum verification...")
    
    config = get_config()
    paths = get_paths()
    
    manifest_path = paths["data"] / "checksums.json"
    
    try:
        manifest = load_checksum_manifest(manifest_path)
        logger.info(f"Loaded manifest with {len(manifest)} entries")
    except Exception as e:
        logger.error(f"Failed to load checksum manifest: {e}")
        sys.exit(1)
    
    passed, failed = verify_checksums(manifest, paths["data"])
    
    logger.info(f"Verification complete: {len(passed)} passed, {len(failed)} failed")
    
    if failed:
        logger.error(f"Failed to verify checksums for {len(failed)} files:")
        for f in failed:
            logger.error(f"  - {f}")
        sys.exit(1)
    else:
        logger.info("All checksums verified successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()