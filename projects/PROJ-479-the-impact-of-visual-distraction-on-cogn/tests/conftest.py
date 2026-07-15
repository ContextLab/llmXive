"""
Pytest configuration and shared fixtures.

This file ensures that the test environment is properly configured
to import project modules and access necessary resources.
"""
import os
import sys
import pytest

# Add the project root to the Python path to allow imports from 'code'
# This assumes the tests are run from the project root or via pytest discovery
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    """Automatically add the project root to sys.path for imports."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Also ensure 'code' directory is accessible if relative imports are used
    code_dir = os.path.join(project_root, "code")
    if os.path.isdir(code_dir) and code_dir not in sys.path:
        sys.path.insert(0, code_dir)
    
    yield
    
    # Cleanup (optional, but good practice)
    if project_root in sys.path:
        sys.path.remove(project_root)
    if code_dir in sys.path:
        sys.path.remove(code_dir)

@pytest.fixture
def sample_data_dir(tmp_path):
    """Create a temporary directory structure mimicking the data folder."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "raw").mkdir()
    (data_dir / "processed").mkdir()
    return data_dir

@pytest.fixture
def sample_results_dir(tmp_path):
    """Create a temporary directory structure mimicking the results folder."""
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    (results_dir / "statistics").mkdir()
    (results_dir / "plots").mkdir()
    (results_dir / "sensitivity").mkdir()
    (results_dir / "methodology").mkdir()
    return results_dir
