"""
Dataset Integrity Verification Script

This script fetches expected checksums from the project's state manifest
and validates the integrity of raw GSM8K and MATH datasets before processing.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Configuration
MANIFEST_PATH = project_root / "state" / "dataset_manifest.json"
DATASET_INFO = {
    "gsm8k": {
        "name": "openai/gsm8k",
        "expected_files": ["train.jsonl", "test.jsonl"],
        "data_dir": project_root / "data" / "raw" / "gsm8k"
    },
    "math": {
        "name": "hendrycks/math",
        "expected_files": ["train.jsonl", "test.jsonl"],
        "data_dir": project_root / "data" / "raw" / "math"
    }
}

def compute_file_hash(file_path: Path) -> Optional[str]:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        return None
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return None

def load_manifest() -> Dict:
    """Load the dataset manifest from the state directory."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Manifest file not found at {MANIFEST_PATH}. "
            "Please ensure the state/dataset_manifest.json file exists."
        )
    
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def verify_dataset(dataset_key: str, manifest: Dict) -> bool:
    """
    Verify a specific dataset's integrity against the manifest.
    
    Args:
        dataset_key: Key in DATASET_INFO (e.g., 'gsm8k', 'math')
        manifest: Loaded manifest dictionary
        
    Returns:
        True if all files match checksums, False otherwise
    """
    dataset_config = DATASET_INFO.get(dataset_key)
    if not dataset_config:
        logger.error(f"Unknown dataset key: {dataset_key}")
        return False

    dataset_name = dataset_config["name"]
    expected_files = dataset_config["expected_files"]
    data_dir = dataset_config["data_dir"]

    logger.info(f"Verifying {dataset_name}...")
    
    all_valid = True
    for filename in expected_files:
        file_path = data_dir / filename
        
        if not file_path.exists():
            logger.error(f"Missing file: {file_path}")
            all_valid = False
            continue

        # Get expected checksum from manifest
        manifest_entry = manifest.get(dataset_name, {})
        expected_checksum = manifest_entry.get(filename)
        
        if not expected_checksum:
            logger.warning(f"No checksum found in manifest for {filename}")
            # Continue checking other files even if manifest is incomplete
            continue

        # Compute actual checksum
        actual_checksum = compute_file_hash(file_path)
        
        if actual_checksum is None:
            logger.error(f"Failed to compute checksum for {file_path}")
            all_valid = False
            continue

        if actual_checksum != expected_checksum:
            logger.error(
                f"Checksum mismatch for {file_path}:\n"
                f"  Expected: {expected_checksum}\n"
                f"  Actual:   {actual_checksum}"
            )
            all_valid = False
        else:
            logger.info(f"✓ {filename} checksum verified")

    return all_valid

def main():
    """Main entry point for dataset verification."""
    logger.info("Starting dataset integrity verification...")
    
    try:
        manifest = load_manifest()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest: {e}")
        sys.exit(1)

    all_datasets_valid = True

    for dataset_key in DATASET_INFO.keys():
        if not verify_dataset(dataset_key, manifest):
            all_datasets_valid = False
            logger.error(f"Verification FAILED for {dataset_key}")
        else:
            logger.info(f"Verification PASSED for {dataset_key}")

    if all_datasets_valid:
        logger.info("All datasets verified successfully.")
        sys.exit(0)
    else:
        logger.error("Dataset verification FAILED. One or more datasets have integrity issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()