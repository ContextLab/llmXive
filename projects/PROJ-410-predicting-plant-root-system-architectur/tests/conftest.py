import os
import sys
import logging
import pytest
from pathlib import Path

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.fixture(scope="session")
def project_root_path():
    """Returns the root path of the project."""
    # Assuming tests/ is at project root or code/tests/
    # Adjust based on actual structure. Here we assume tests/ is in code/ based on API surface
    # But the task asks for root structure. Let's assume standard layout:
    # project_root/
    #   code/
    #     tests/
    #   data/
    #   contracts/
    
    # If this file is in code/tests/, go up two levels
    current_file = Path(__file__).resolve()
    root = current_file.parent.parent
    return root

@pytest.fixture(scope="session")
def data_dir(project_root_path):
    """Returns the path to the data directory."""
    return project_root_path / "data"

@pytest.fixture(scope="session")
def processed_data_dir(project_root_path):
    """Returns the path to the processed data directory."""
    return project_root_path / "data" / "processed"

@pytest.fixture(scope="session")
def raw_data_dir(project_root_path):
    """Returns the path to the raw data directory."""
    return project_root_path / "data" / "raw"

@pytest.fixture(scope="session")
def code_dir(project_root_path):
    """Returns the path to the code directory."""
    return project_root_path / "code"
