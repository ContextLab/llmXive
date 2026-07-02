import json
import os
import hashlib
import pathlib
import sys
import tempfile
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

@dataclass
class DatasetManifest:
    dataset_id: str
    status: str
    eeg_available: bool
    questionnaire_available: bool
    file_paths: Dict[str, str] = field(default_factory=dict)
    verification_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_and_verify_dataset(dataset_id: str, target_dir: str) -> Dict[str, Any]:
    """
    Download dataset from OpenNeuro and verify basic structure.
    Returns a dict with status and file paths.
    """
    # Placeholder for actual download logic using OpenNeuro CLI or API
    # For now, we simulate the structure check
    base_url = f"https://openneuro.org/datasets/{dataset_id}/"
    # In a real implementation, we would use `datalad` or `openneuro-py`
    # Here we return a status indicating the dataset is "verified" if it exists in our mock data
    # or raise an error if not.
    
    # Mock path for demonstration (in real code, this would be the actual download path)
    mock_path = os.path.join(target_dir, dataset_id)
    
    # Check if we have the required files (mock check)
    # Real implementation: check for .nii, .bids.json, participant.tsv
    eeg_found = os.path.exists(os.path.join(mock_path, "sourcedata")) # Simplified check
    qs_found = os.path.exists(os.path.join(mock_path, "phenotype"))   # Simplified check

    return {
        "status": "verified" if eeg_found and qs_found else "missing_components",
        "eeg_available": eeg_found,
        "questionnaire_available": qs_found,
        "file_paths": {"mock_path": mock_path}
    }

def write_manifest(manifests: List[DatasetManifest], output_path: str) -> None:
    """Write list of manifests to a JSON file."""
    data = [asdict(m) for m in manifests]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def verify_checksums(manifest_path: str, checksum_path: str) -> None:
    """Read manifest, compute checksums, and write to state/checksums.json."""
    with open(manifest_path, 'r') as f:
        manifests = json.load(f)
    
    checksums = {}
    for item in manifests:
        for key, path in item.get('file_paths', {}).items():
            if os.path.exists(path):
                checksums[path] = compute_sha256(path)
    
    os.makedirs(os.path.dirname(checksum_path), exist_ok=True)
    with open(checksum_path, 'w') as f:
        json.dump(checksums, f, indent=2)

# --- Logging Infrastructure for T007 ---

def setup_exclusion_logging(log_path: str) -> logging.Logger:
    """
    Initialize and return a logger specifically for tracking exclusion logs.
    Creates the logger, file handler, and formatter.
    Writes an initial header to the log file.
    """
    logger = logging.getLogger("exclusion_logger")
    logger.setLevel(logging.INFO)

    # Prevent adding multiple handlers if called multiple times
    if not logger.handlers:
        # Ensure directory exists
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        # File handler
        fh = logging.FileHandler(log_path, mode='a')
        fh.setLevel(logging.INFO)

        # Formatter with timestamp
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)

        logger.addHandler(fh)

    # Write header if file is new (check by file size or existence of last line)
    # Simple check: if file is empty, write header
    if os.path.getsize(log_path) == 0:
        logger.info("--- Exclusion Log Started ---")
        logger.info(f"Project: PROJ-456-decoding-affective-state-from-resting-st")
        logger.info(f"Task: T007 - Logging Infrastructure")

    return logger

def log_exclusion(logger: logging.Logger, subject_id: str, reason: str, details: Optional[str] = None) -> None:
    """
    Log an exclusion event for a subject.
    """
    msg = f"EXCLUSION: Subject={subject_id}, Reason={reason}"
    if details:
        msg += f" | Details={details}"
    logger.info(msg)

def main():
    """Main entry point for utils.py execution."""
    print("Running utils.py utilities...")
    
    # Initialize logging for T007
    log_path = "data/logs/exclusion.log"
    logger = setup_exclusion_logging(log_path)
    
    # Log a test exclusion to verify functionality
    log_exclusion(logger, "sub-001", "low_signal_quality", "SNR < 5dB")
    log_exclusion(logger, "sub-002", "missing_questionnaire", "PANAS not found")
    
    print(f"Exclusion logging initialized. Log written to: {log_path}")

if __name__ == "__main__":
    main()
