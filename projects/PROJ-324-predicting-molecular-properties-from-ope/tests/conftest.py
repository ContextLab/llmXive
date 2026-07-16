"""
Pytest configuration and shared fixtures for the project.

This file ensures the test environment is set up correctly,
particularly handling the project root path and logging.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging to appear in test output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Ensure the project root is in the path
# This allows imports like `from data.download import ...`
# when running tests from the project root or tests/ directory
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Optional: Setup fixture for common test data paths
@pytest.fixture(scope="session")
def data_paths():
    """Return a dictionary of important data paths."""
    return {
        "raw": project_root / "data" / "raw",
        "processed": project_root / "data" / "processed",
        "derived": project_root / "data" / "derived",
    }

import pytest