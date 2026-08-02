"""
Utilities for configuring pytest environment:
- Random seed pinning for reproducibility
- GitHub job duration logging
- Checksum determinism enforcement
"""
import os
import random
import time
from pathlib import Path
from datetime import datetime
import hashlib
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)

def pin_random_seeds(seed: int = 42) -> None:
    """
    Pin random seeds for Python, NumPy, and other libraries to ensure reproducibility.
    
    Args:
        seed: The random seed to use (default: 42)
    """
    # Set Python's random seed
    random.seed(seed)
    
    # Set NumPy's random seed if available
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        logger.warning("NumPy not available, skipping NumPy seed pinning")
    
    # Set PyTorch's random seed if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        logger.debug("PyTorch not available, skipping PyTorch seed pinning")
    
    # Set environment variable for downstream processes
    os.environ["PYTHONHASHSEED"] = str(seed)
    os.environ["RANDOM_SEED"] = str(seed)
    
    logger.info(f"Random seeds pinned to {seed}")


def log_github_job_duration(start: bool = True) -> None:
    """
    Log the GitHub job duration to the environment and console.
    
    Args:
        start: If True, record the start time. If False, calculate and log duration.
    """
    timestamp = datetime.now().isoformat()
    
    if start:
        # Record start time
        os.environ["GITHUB_JOB_START_TIME"] = timestamp
        logger.info(f"Test run started at {timestamp}")
    else:
        # Calculate duration
        start_time_str = os.environ.get("GITHUB_JOB_START_TIME")
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str)
                duration = (datetime.now() - start_time).total_seconds()
                duration_minutes = duration / 60
                
                os.environ["GITHUB_JOB_DURATION"] = f"{duration:.2f}s"
                
                logger.info(f"Test run completed. Duration: {duration:.2f}s ({duration_minutes:.2f} minutes)")
                
                # Print to stdout for GitHub Actions to capture
                print(f"::notice::GITHUB_JOB_DURATION={duration:.2f}s")
            except ValueError as e:
                logger.error(f"Failed to parse start time: {e}")
        else:
            logger.warning("GITHUB_JOB_START_TIME not found, cannot calculate duration")


def enforce_checksum_determinism(check_mode: str = "pre") -> None:
    """
    Enforce checksum determinism for data loading operations.
    
    This function validates that data files have not been modified since they were
    downloaded, ensuring reproducibility. It is intended to be called by data
    download scripts (e.g., T004, T011) to verify checksums immediately after download.
    
    Args:
        check_mode: "pre" for pre-download validation, "post" for post-download validation
    """
    data_dir = Path(__file__).parent.parent.parent / "data"
    
    if not data_dir.exists():
        logger.warning(f"Data directory {data_dir} does not exist. Skipping checksum validation.")
        return
    
    # Walk through all files in the data directory
    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            # Calculate checksum
            sha256_hash = hashlib.sha256()
            try:
                with open(file_path, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
                
                checksum = sha256_hash.hexdigest()
                
                # Check if a .checksum file exists for this file
                checksum_file = file_path.with_suffix(file_path.suffix + ".checksum")
                if checksum_file.exists():
                    with open(checksum_file, "r") as cf:
                        expected_checksum = cf.read().strip()
                    
                    if checksum != expected_checksum:
                        error_msg = (
                            f"CHECKSUM MISMATCH DETECTED:\n"
                            f"File: {file_path}\n"
                            f"Expected: {expected_checksum}\n"
                            f"Actual: {checksum}\n"
                            f"Mode: {check_mode}"
                        )
                        logger.error(error_msg)
                        raise ValueError(error_msg)
                    else:
                        logger.debug(f"Checksum verified for {file_path}")
                else:
                    logger.warning(f"No checksum file found for {file_path}. Creating one.")
                    with open(checksum_file, "w") as cf:
                        cf.write(checksum)
                        
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                raise
