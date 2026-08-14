"""
Pytest configuration and shared fixtures.
Sets up paths to access code/ modules and configures logging for tests.
"""
import sys
import os
import logging
import pytest
from pathlib import Path

# Add project root to path to resolve imports like `from utils import ...`
# assuming tests are run as `pytest` from the project root.
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging to capture output during tests without cluttering
@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for test runs."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    yield
    # Optional: cleanup handlers if needed

@pytest.fixture
def project_root():
    """Return the project root path."""
    return PROJECT_ROOT

@pytest.fixture
def data_dir(project_root):
    """Return the data directory path."""
    return project_root / "data"

@pytest.fixture
def code_dir(project_root):
    """Return the code directory path."""
    return project_root / "code"
