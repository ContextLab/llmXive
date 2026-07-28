"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path

import pytest

# Ensure the code directory is in the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add the project code directory to sys.path."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure mimicking the project layout."""
    temp_dir = tempfile.mkdtemp()
    project_root = Path(temp_dir)
    
    # Create standard directories
    dirs = [
        "code", "data/raw", "data/processed", "data/processed/augmented",
        "data/reports", "tests", "state", "figures"
    ]
    for d in dirs:
        (project_root / d).mkdir(parents=True, exist_ok=True)
    
    yield project_root
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_smiles():
    """Provide a list of valid SMILES strings for testing."""
    return [
        "CC(=O)Oc1ccccc1C(=O)O",  # Aspirin-like ester
        "CC(=O)O",                # Acetic acid
        "C1=CC=C(C=C1)C(=O)OC",   # Methyl benzoate
        "CCO",                    # Ethanol (not an ester)
    ]

@pytest.fixture
def logger_config():
    """Configure logging for tests to capture output."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    yield logging.getLogger("pytest")

@pytest.fixture
def mock_config_env(temp_project_dir):
    """Create a mock configuration environment."""
    env_file = temp_project_dir / ".env"
    env_file.write_text(
        "PROJECT_ROOT=" + str(temp_project_dir) + "\n"
        "DATA_RAW_DIR=" + str(temp_project_dir / "data" / "raw") + "\n"
        "DATA_PROCESSED_DIR=" + str(temp_project_dir / "data" / "processed") + "\n"
        "DATA_REPORTS_DIR=" + str(temp_project_dir / "data" / "reports") + "\n"
    )
    os.environ["PROJECT_ROOT"] = str(temp_project_dir)
    os.environ["DATA_RAW_DIR"] = str(temp_project_dir / "data" / "raw")
    os.environ["DATA_PROCESSED_DIR"] = str(temp_project_dir / "data" / "processed")
    os.environ["DATA_REPORTS_DIR"] = str(temp_project_dir / "data" / "reports")
    yield
    # Cleanup env vars if they existed before
    for key in ["PROJECT_ROOT", "DATA_RAW_DIR", "DATA_PROCESSED_DIR", "DATA_REPORTS_DIR"]:
        if key in os.environ:
            del os.environ[key]
