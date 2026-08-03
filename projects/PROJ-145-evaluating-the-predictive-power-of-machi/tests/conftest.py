"""
Pytest configuration and shared fixtures for the llmXive research pipeline.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the project root is in the path for imports
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    """Automatically add the project root to sys.path for all tests."""
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Ensure the code directory is accessible
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    yield
    
    # Cleanup if necessary (usually not needed for path insertion)
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))

@pytest.fixture
def project_root():
    """Provide the project root path."""
    return Path(__file__).parent.parent

@pytest.fixture
def data_dir(project_root):
    """Provide the path to the data directory."""
    return project_root / "data"

@pytest.fixture
def processed_data_dir(project_root):
    """Provide the path to the processed data directory."""
    return project_root / "data" / "processed"

@pytest.fixture
def models_dir(project_root):
    """Provide the path to the models directory."""
    return project_root / "data" / "models"

@pytest.fixture
def code_dir(project_root):
    """Provide the path to the code directory."""
    return project_root / "code"
