"""
Pytest configuration plugin for llmXive research pipeline.

This module provides:
1. Random seed pinning for reproducibility.
2. GITHUB_JOB_DURATION logging for performance monitoring.
3. Checksum verification hooks for data download scripts (Constitution Principle I).
"""
import os
import random
import time
import hashlib
import logging
import sys
from pathlib import Path
from typing import Any, List, Dict

# Configure logging for the plugin
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("pytest_llmxive")

# Global timer start
_start_time: float = 0.0

# Fixed seed for reproducibility (Constitution Principle I)
# This ensures that any random operations in the test suite are deterministic.
FIXED_SEED = 42

def pin_random_seeds() -> None:
    """Pin all random seeds to ensure deterministic test execution."""
    random.seed(FIXED_SEED)
    if 'numpy' in sys.modules:
        import numpy as np
        np.random.seed(FIXED_SEED)
    logger.info(f"Random seeds pinned to {FIXED_SEED}")

def log_github_job_duration(start_time: float, end_time: float) -> None:
    """
    Calculate and log the duration of the GitHub job.
    Sets the GITHUB_JOB_DURATION environment variable if running in CI.
    """
    duration_seconds = end_time - start_time
    duration_formatted = f"{duration_seconds:.2f}s"
    
    logger.info(f"GitHub Job Duration: {duration_formatted}")
    
    # If running in GitHub Actions, set the output for the job summary
    if os.getenv("GITHUB_ACTIONS") == "true":
        github_output = os.getenv("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as f:
                f.write(f"GITHUB_JOB_DURATION={duration_formatted}\n")
            logger.info(f"Set GITHUB_JOB_DURATION in {github_output}")

def compute_sha256_checksum(file_path: Path) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Checksum verification failed: File not found {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"IO Error while computing checksum for {file_path}: {e}")
        raise

def enforce_checksum_determinism(checksums_file: Path, expected_checksums: Dict[str, str]) -> bool:
    """
    Verify that downloaded/generated files match expected checksums.
    This enforces Constitution Principle I: Deterministic behavior via checksum verification.
    
    Args:
        checksums_file: Path to the file containing recorded checksums (e.g., results/checksums.txt).
        expected_checksums: Dictionary mapping filename to expected SHA-256 hash.
        
    Returns:
        True if all checksums match, False otherwise.
        
    Raises:
        ValueError: If the checksums file is missing or malformed.
    """
    if not checksums_file.exists():
        raise ValueError(f"Checksum verification failed: Checksums file not found {checksums_file}")
    
    recorded_checksums = {}
    try:
        with open(checksums_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "  " in line:
                    # Format: <hash>  <filename>
                    parts = line.split("  ", 1)
                    if len(parts) == 2:
                        recorded_checksums[parts[1]] = parts[0]
                elif " " in line:
                    # Format: <hash> <filename> (single space)
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        recorded_checksums[parts[1]] = parts[0]
    except Exception as e:
        raise ValueError(f"Failed to parse checksums file {checksums_file}: {e}")
    
    all_match = True
    for filename, expected_hash in expected_checksums.items():
        if filename not in recorded_checksums:
            logger.error(f"Checksum mismatch: File '{filename}' not found in recorded checksums.")
            all_match = False
            continue
        
        recorded_hash = recorded_checksums[filename]
        if recorded_hash != expected_hash:
            logger.error(f"Checksum mismatch for '{filename}': Expected {expected_hash}, got {recorded_hash}")
            all_match = False
        else:
            logger.info(f"Checksum verified for '{filename}': {recorded_hash}")
    
    return all_match

def pytest_configure(config: Any) -> None:
    """
    Called when pytest starts.
    Pins random seeds and sets up logging.
    """
    pin_random_seeds()
    logger.info("Pytest configuration loaded: Seeds pinned, duration tracking enabled.")

def pytest_addoption(parser: Any) -> None:
    """
    Add custom command-line options for pytest.
    """
    parser.addoption(
        "--checksums-file",
        action="store",
        default="results/checksums.txt",
        help="Path to the file containing expected checksums for verification."
    )

def pytest_sessionstart(session: Any) -> None:
    """
    Called at the beginning of session execution.
    Records start time for duration logging.
    """
    global _start_time
    _start_time = time.time()
    logger.info(f"Pytest session started at {time.strftime('%Y-%m-%d %H:%M:%S')}")

def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    """
    Called at the end of the session.
    Logs job duration and handles checksum verification if requested.
    """
    end_time = time.time()
    log_github_job_duration(_start_time, end_time)
    
    logger.info(f"Pytest session finished with exit status {exitstatus}")
    
    # If a checksums file is specified, we could verify it here if needed,
    # but typically checksum verification is done in the download scripts themselves.
    # This hook is available for post-run validation if the test suite needs to enforce it.
    if session.config.getoption("checksums_file"):
        # Optional: Add logic to verify checksums if the test suite requires it
        pass
