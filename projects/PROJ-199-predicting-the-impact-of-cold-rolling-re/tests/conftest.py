"""
Pytest configuration and shared fixtures.

This file configures pytest behavior and provides shared fixtures
for testing across the project.
"""
import os
import sys
import logging
from pathlib import Path
import pytest

# Add project root to path for imports during testing
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    """Ensure the project root is in sys.path for imports."""
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    # Cleanup not strictly necessary as sys.path is process-local

@pytest.fixture(scope="session")
def test_data_dir():
    """Provide a path to a temporary test data directory."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def pytest_configure(config):
    """Configure pytest logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # Silence noisy logs during tests if needed
    # logging.getLogger('orix').setLevel(logging.WARNING)
