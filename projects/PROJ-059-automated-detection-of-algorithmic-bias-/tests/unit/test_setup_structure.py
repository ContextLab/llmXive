"""
Unit tests for the setup_structure.py script.
Verifies that the directory structure is created correctly.
"""
import os
import shutil
import tempfile
import pytest

# We need to import the function from the script. 
# Since the script is in code/, we might need to adjust sys.path or import it directly.
# For this test, we assume the test runner is configured to find 'code' in the path,
# or we import the specific logic.
# To make this robust, we will import the module logic.
import sys
import importlib.util

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    tmpdir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(tmpdir)
    yield tmpdir
    os.chdir(original_cwd)
    shutil.rmtree(tmpdir)

def load_setup_module():
    """Dynamically load the setup module from the code directory."""
    spec = importlib.util.spec_from_file_location(
        "setup_structure", 
        "code/setup_structure.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["setup_structure"] = module
    spec.loader.exec_module(module)
    return module

def test_directories_created(temp_project_root):
    """Test that all required directories are created."""
    module = load_setup_module()
    
    # Execute the setup
    result = module.create_directories()
    
    assert result is True
    
    required_dirs = [
        "src/bias_pipeline",
        "src/cli",
        "data/raw",
        "data/processed",
        "data/validation",
        "tests/unit",
        "tests/integration",
        "state"
    ]
    
    for dir_name in required_dirs:
        assert os.path.isdir(dir_name), f"Directory {dir_name} was not created."

def test_idempotency(temp_project_root):
    """Test that running the setup twice does not cause errors."""
    module = load_setup_module()
    
    # Run once
    module.create_directories()
    
    # Run again
    result = module.create_directories()
    
    assert result is True
    
    # Verify directories still exist
    assert os.path.isdir("src/bias_pipeline")
    assert os.path.isdir("data/raw")