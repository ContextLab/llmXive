"""
Pytest configuration for llmXive project.
Implements random seed pinning and checksum verification constraints.
"""
import os
import random
import time
import hashlib
import logging
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any

import pytest

# Configure logging for the test session
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global seed pinning
RANDOM_SEED = 42

def set_random_seed(seed: int = RANDOM_SEED) -> None:
    """Pin random seeds for reproducibility."""
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def pytest_configure(config: Any) -> None:
    """Configure pytest with seed pinning."""
    set_random_seed(RANDOM_SEED)
    logger.info(f"Random seeds pinned to {RANDOM_SEED}")

def pytest_addoption(parser: Any) -> None:
    """Add command-line options for checksum verification."""
    parser.addoption(
        "--verify-checksums",
        action="store_true",
        default=False,
        help="Verify checksums of downloaded files against results/checksums.txt"
    )

def pytest_sessionstart(session: Any) -> None:
    """Start session: ensure deterministic environment."""
    set_random_seed(RANDOM_SEED)
    logger.info("Test session started with deterministic seed")

def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    """End session: cleanup and log summary."""
    logger.info(f"Test session finished with exit status: {exitstatus}")

@pytest.fixture(scope="function")
def temp_data_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for data artifacts during tests."""
    temp_dir = Path(tempfile.mkdtemp(prefix="llmxive_test_data_"))
    try:
        yield temp_dir
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

@pytest.fixture(scope="function")
def temp_results_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for results artifacts during tests."""
    temp_dir = Path(tempfile.mkdtemp(prefix="llmxive_test_results_"))
    try:
        yield temp_dir
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

@pytest.fixture(autouse=True)
def deterministic_environment(temp_data_dir: Path, temp_results_dir: Path) -> Generator[None, None, None]:
    """
    Autouse fixture to enforce deterministic environment for all tests.
    - Sets random seeds
    - Creates necessary temp directories
    - Ensures checksums file exists if required
    """
    set_random_seed(RANDOM_SEED)
    
    # Ensure directories exist
    temp_data_dir.mkdir(parents=True, exist_ok=True)
    temp_results_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a placeholder checksums file if it doesn't exist
    # This allows tests to run without failing on missing files
    checksums_file = temp_results_dir / "checksums.txt"
    if not checksums_file.exists():
        checksums_file.write_text("# Checksums file created for testing\n")
    
    yield

def verify_checksum_against_log(
    file_path: Path, 
    checksums_log: Path, 
    algorithm: str = "sha256"
) -> bool:
    """
    Verify a file's checksum against the logged checksums.
    
    Args:
        file_path: Path to the file to verify
        checksums_log: Path to the checksums log file (results/checksums.txt)
        algorithm: Hash algorithm to use (default: sha256)
    
    Returns:
        True if checksum matches, False otherwise
    
    Raises:
        FileNotFoundError: If file or checksums log doesn't exist
        ValueError: If checksum not found in log
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not checksums_log.exists():
        raise FileNotFoundError(f"Checksums log not found: {checksums_log}")
    
    # Calculate current checksum
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    current_checksum = hasher.hexdigest()
    
    # Parse checksums log
    with open(checksums_log, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split()
                if len(parts) >= 2:
                    stored_checksum = parts[0]
                    stored_file = parts[1]
                    if Path(stored_file).name == file_path.name:
                        if stored_checksum != current_checksum:
                            logger.error(
                                f"Checksum mismatch for {file_path.name}. "
                                f"Expected: {stored_checksum}, Got: {current_checksum}"
                            )
                            return False
                        else:
                            logger.info(f"Checksum verified for {file_path.name}")
                            return True
    
    raise ValueError(f"No checksum entry found for {file_path.name} in {checksums_log}")

@pytest.fixture
def checksum_verifier(temp_results_dir: Path) -> Generator[callable, None, None]:
    """
    Fixture providing a checksum verifier function.
    Uses temp_results_dir as the default location for checksums.txt
    """
    def verifier(file_path: Path) -> bool:
        return verify_checksum_against_log(file_path, temp_results_dir / "checksums.txt")
    
    return verifier