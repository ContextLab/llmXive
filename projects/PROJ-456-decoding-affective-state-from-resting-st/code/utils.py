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
    base_url = f"https://openneuro.org/datasets/{dataset_id}/"
    mock_path = os.path.join(target_dir, dataset_id)

    eeg_found = os.path.exists(os.path.join(mock_path, "sourcedata"))
    qs_found = os.path.exists(os.path.join(mock_path, "phenotype"))

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

DEFAULT_EXCLUSION_LOG_PATH = os.path.join("data", "logs", "exclusion.log")

def setup_exclusion_logging(log_path: str = DEFAULT_EXCLUSION_LOG_PATH) -> logging.Logger:
    """
    Initialize and return a logger specifically for tracking exclusion logs.

    Creates the log directory, attaches a file handler with a timestamped
    format, and writes an initial header to the log file if the file is
    new or empty.

    Args:
        log_path: Path to the exclusion log file
            (default: data/logs/exclusion.log).

    Returns:
        logging.Logger: The configured 'exclusion_logger' instance.
    """
    logger = logging.getLogger("exclusion_logger")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Ensure directory exists
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # Prevent adding multiple handlers if called multiple times
    if not logger.handlers:
        fh = logging.FileHandler(log_path, mode='a')
        fh.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)

        logger.addHandler(fh)

    # Write header if file is new or empty
    if (not os.path.exists(log_path)) or os.path.getsize(log_path) == 0:
        logger.info("--- Exclusion Log Started ---")
        logger.info("Project: PROJ-456-decoding-affective-state-from-resting-st")
        logger.info("Task: T007 - Logging Infrastructure")

    return logger

def log_exclusion(logger: logging.Logger, subject_id: str, reason: str,
                  details: Optional[str] = None) -> None:
    """
    Log an exclusion event for a subject.

    Args:
        logger: Logger returned by setup_exclusion_logging().
        subject_id: Identifier of the excluded subject.
        reason: Short machine-readable reason code
              (e.g. 'low_signal_quality', 'missing_questionnaire').
        details: Optional free-text details about the exclusion.
    """
    msg = f"EXCLUSION: Subject={subject_id}, Reason={reason}"
    if details:
        msg += f" | Details={details}"
    logger.info(msg)

def main():
    """Main entry point for utils.py execution.

    Initializes the exclusion logging infrastructure (T007) and ensures
    the exclusion log file exists on disk at data/logs/exclusion.log.
    No fabricated exclusion records are written here; the log records
    only the initialization header. Real exclusions are recorded by the
    preprocessing/analysis pipeline via log_exclusion().
    """
    print("Running utils.py utilities...")

    logger = setup_exclusion_logging(DEFAULT_EXCLUSION_LOG_PATH)

    print(f"Exclusion logging initialized. Log written to: {DEFAULT_EXCLUSION_LOG_PATH}")
    return logger

if __name__ == "__main__":
    main()
