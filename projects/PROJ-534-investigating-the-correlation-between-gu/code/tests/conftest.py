import os
import sys
import logging
from pathlib import Path
import pytest

# Configure logging for tests to avoid silent failures
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    # Assuming the project structure is code/ at the root of the repo
    # and tests are inside code/tests/
    current_file = Path(__file__).resolve()
    code_root = current_file.parent.parent
    return code_root

@pytest.fixture
def sample_data_dir(project_root):
    """Return a path to a sample data directory for testing."""
    data_dir = project_root / "data" / "raw"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

@pytest.fixture
def sample_output_dir(project_root):
    """Return a temporary output directory for test artifacts."""
    output_dir = project_root / "data" / "processed"
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

@pytest.fixture(autouse=True)
def add_project_root_to_path(project_root):
    """Add project root to sys.path to ensure imports work."""
    sys.path.insert(0, str(project_root))
    yield
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))
