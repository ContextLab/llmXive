"""
Checksum Generation Module (Task T018)

Implements checksum generation for data integrity verification.
Specifically targets data/ground_truth/manual_labels.csv and records
the result in state/checksums.json.
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Ensure code directory is in path for imports if running as script
if __name__ == "__main__":
    code_dir = Path(__file__).parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

from utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)

# Constants based on project structure
PROJECT_ROOT = Path(__file__).parent.parent
DATA_GROUND_TRUTH_DIR = PROJECT_ROOT / "data" / "ground_truth"
STATE_DIR = PROJECT_ROOT / "state"
MANUAL_LABELS_PATH = DATA_GROUND_TRUTH_DIR / "manual_labels.csv"
CHECKSUMS_PATH = STATE_DIR / "checksums.json"

def setup_output_directories() -> None:
    """Ensure required output directories exist."""
    DATA_GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Verified directories: {DATA_GROUND_TRUTH_DIR}, {STATE_DIR}")

def calculate_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hex digest string of the file checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or unreadable.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
    except PermissionError:
        logger.error(f"Permission denied reading file: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

    return hasher.hexdigest()

def load_existing_checksums() -> Dict[str, Any]:
    """
    Load existing checksums from state/checksums.json.
    Returns an empty dict if the file does not exist.
    """
    if CHECKSUMS_PATH.exists():
        try:
            with open(CHECKSUMS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Corrupt checksum file at {CHECKSUMS_PATH}, starting fresh.")
            return {}
    return {}

def save_checksums(checksums: Dict[str, Any]) -> None:
    """
    Save checksums to state/checksums.json.
    """
    with open(CHECKSUMS_PATH, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {CHECKSUMS_PATH}")

def generate_checksum_for_manual_labels() -> str:
    """
    Main logic for T018: Generate checksum for manual_labels.csv and record it.
    
    This function:
    1. Verifies the existence of data/ground_truth/manual_labels.csv.
    2. Calculates its SHA-256 checksum.
    3. Updates state/checksums.json with the new entry.
    
    Returns:
        The calculated checksum string.
    
    Raises:
        FileNotFoundError: If manual_labels.csv does not exist (T017a output missing).
    """
    setup_output_directories()

    if not MANUAL_LABELS_PATH.exists():
        raise FileNotFoundError(
            f"Required input file missing: {MANUAL_LABELS_PATH}. "
            "Ensure T017a (Ground Truth Selection) has been completed successfully."
        )

    logger.info(f"Calculating checksum for: {MANUAL_LABELS_PATH}")
    checksum_value = calculate_file_checksum(MANUAL_LABELS_PATH)
    
    logger.info(f"Calculated checksum: {checksum_value}")

    # Load existing state
    existing_checksums = load_existing_checksums()

    # Update state with new entry
    # Key by filename for simplicity, or use relative path
    entry_key = "manual_labels.csv"
    
    existing_checksums[entry_key] = {
        "file": str(MANUAL_LABELS_PATH.relative_to(PROJECT_ROOT)),
        "checksum": checksum_value,
        "algorithm": "sha256",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "task_id": "T018"
    }

    # Save updated state
    save_checksums(existing_checksums)

    logger.info(f"Successfully recorded checksum for {entry_key} in {CHECKSUMS_PATH}")
    return checksum_value

def main():
    """Entry point for the checksum generation script."""
    setup_logging()
    try:
        checksum = generate_checksum_for_manual_labels()
        print(f"SUCCESS: Checksum generated for manual_labels.csv: {checksum}")
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"FAILURE: Input file missing - {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception("An unexpected error occurred during checksum generation.")
        print(f"FAILURE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
