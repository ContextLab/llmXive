"""
Pytest configuration utilities for the llmXive science pipeline.

Provides:
- Random seed pinning for reproducibility
- GitHub job duration logging
- Checksum determinism enforcement for data downloads
"""
import os
import random
import time
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def pin_random_seeds(seed: int = 42) -> None:
    """
    Pin all random number generators to a fixed seed for reproducibility.
    
    Args:
        seed: The random seed to use (default: 42)
    """
    random.seed(seed)
    # Also set numpy seed if available
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        logger.warning("numpy not available, skipping numpy seed pinning")
    
    logger.info(f"Random seeds pinned to {seed}")


def log_github_job_duration(start_time: Optional[float] = None) -> Dict[str, Any]:
    """
    Log the duration of the GitHub job for performance monitoring.
    
    Args:
        start_time: Unix timestamp of job start (if None, uses current time)
        
    Returns:
        Dictionary with timing information
    """
    if start_time is None:
        start_time = time.time()
    
    end_time = time.time()
    duration_seconds = end_time - start_time
    duration_minutes = duration_seconds / 60.0
    
    # Log to stdout for GitHub Actions parsing
    github_job_duration = f"GITHUB_JOB_DURATION={duration_seconds:.2f}s"
    print(github_job_duration)
    print(f"GITHUB_JOB_DURATION_MINUTES={duration_minutes:.2f}m")
    
    logger.info(f"Job duration: {duration_seconds:.2f}s ({duration_minutes:.2f}m)")
    
    return {
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": duration_seconds,
        "duration_minutes": duration_minutes,
        "github_annotation": github_job_duration
    }


def compute_sha256_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum
        
    Returns:
        Hexadecimal SHA-256 hash string
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def enforce_checksum_determinism(
    download_script_path: Path,
    checksum_output_path: Path,
    expected_checksums: Optional[Dict[str, str]] = None
) -> bool:
    """
    Enforce deterministic behavior for data downloads via checksum verification.
    
    This function:
    1. Runs the download script
    2. Computes checksums of all downloaded files
    3. Writes checksums to the output file
    4. Optionally validates against expected checksums
    
    Args:
        download_script_path: Path to the download script to execute
        checksum_output_path: Path where checksums.txt should be written
        expected_checksums: Optional dict of {filename: expected_hash} for validation
        
    Returns:
        True if checksums match expected (or no expected provided), False otherwise
        
    Raises:
        RuntimeError: If the download script fails
    """
    logger.info(f"Enforcing checksum determinism for {download_script_path}")
    
    # Execute the download script
    import subprocess
    import sys
    
    result = subprocess.run(
        [sys.executable, str(download_script_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        error_msg = f"Download script failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Compute checksums of all downloaded files
    checksums = {}
    checksum_output_path = Path(checksum_output_path)
    checksum_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Look for downloaded files in data/ directory
    data_dir = download_script_path.parent.parent / "data"
    if data_dir.exists():
        for file_path in data_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(data_dir.parent)
                checksum = compute_sha256_checksum(file_path)
                checksums[str(rel_path)] = checksum
    
    # Write checksums to output file
    with open(checksum_output_path, "w") as f:
        f.write("# SHA-256 checksums for downloaded data files\n")
        f.write(f"# Generated at: {datetime.now().isoformat()}\n")
        f.write("# Format: filepath  checksum\n")
        for filepath, checksum in sorted(checksums.items()):
            f.write(f"{filepath}  {checksum}\n")
    
    logger.info(f"Wrote {len(checksums)} checksums to {checksum_output_path}")
    
    # Validate against expected checksums if provided
    if expected_checksums:
        for filename, expected_hash in expected_checksums.items():
            if filename in checksums:
                if checksums[filename] != expected_hash:
                    logger.error(f"Checksum mismatch for {filename}: expected {expected_hash}, got {checksums[filename]}")
                    return False
            else:
                logger.error(f"Expected file {filename} not found in downloads")
                return False
    
    logger.info("Checksum determinism check passed")
    return True


# Pytest hooks for seed pinning
def pytest_configure(config):
    """Pytest hook to configure random seeds at test start."""
    seed = config.getoption("--seed", 42)
    pin_random_seeds(seed)
    logger.info(f"Pytest configured with seed: {seed}")


def pytest_addoption(parser):
    """Pytest hook to add custom command-line options."""
    parser.addoption(
        "--seed",
        action="store",
        default=42,
        type=int,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.addoption(
        "--log-duration",
        action="store_true",
        default=False,
        help="Log GitHub job duration at test end"
    )


def pytest_sessionstart(session):
    """Pytest hook to start timing the test session."""
    session.config._test_start_time = time.time()
    logger.info("Test session started")


def pytest_sessionfinish(session, exitstatus):
    """Pytest hook to log job duration at test end."""
    if session.config.getoption("--log-duration"):
        log_github_job_duration(session.config._test_start_time)
    logger.info(f"Test session finished with exit status: {exitstatus}")