"""
Pytest configuration and fixtures for the llmXive research pipeline.

This module:
1. Pins all random seeds (Python, NumPy, PyTorch if available) to ensure reproducibility.
2. Logs the GitHub Job Duration (GITHUB_JOB_DURATION) at the start and end of the test run.
3. Provides fixtures to enforce checksum determinism for data loaders.
"""
import os
import sys
import random
import time
from pathlib import Path
from datetime import datetime
import pytest

# Import the utility functions from the project's utils module
# Note: The path 'code/utils/pytest_config.py' is relative to the project root.
# We adjust sys.path to ensure we can import from 'code' as a package.
project_root = Path(__file__).resolve().parent.parent
if str(project_root / "code") not in sys.path:
    sys.path.insert(0, str(project_root / "code"))

from utils.pytest_config import pin_random_seeds, log_github_job_duration, enforce_checksum_determinism


def pytest_configure(config):
    """
    Hook called at the start of the test session.
    Pins random seeds and logs the start time for duration tracking.
    """
    # Pin random seeds for reproducibility
    pin_random_seeds(seed=42)
    
    # Log GitHub job duration start time
    log_github_job_duration(start=True)


def pytest_sessionfinish(session, exitstatus):
    """
    Hook called at the end of the test session.
    Logs the total duration of the test run.
    """
    log_github_job_duration(start=False)


@pytest.fixture(autouse=True)
def enforce_determinism_fixture():
    """
    Autouse fixture that ensures checksum determinism for any data loading
    operations performed during the test.
    """
    # Setup: Verify checksums before test if needed
    # This is a placeholder for more complex setup if specific data files
    # need to be validated before each test.
    enforce_checksum_determinism(check_mode="pre")
    
    yield
    
    # Teardown: Verify checksums after test
    enforce_checksum_determinism(check_mode="post")
