import os
import shutil
import tempfile
from pathlib import Path
import pytest

# Import the function from the sibling module
from code.data_setup.create_results_dirs import create_results_directories, main

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate project root for testing."""
    original_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_create_results_directories_creates_structure(temp_project_root):
    """Test that the function creates results/ and results/paper/."""
    results = create_results_directories()
    
    assert "results" in results
    assert "results/paper" in results
    assert results["results"] is True  # It was created
    assert results["results/paper"] is True  # It was created
    
    # Verify physical existence
    assert Path("results").exists()
    assert Path("results").is_dir()
    assert Path("results/paper").exists()
    assert Path("results/paper").is_dir()

def test_create_results_directories_idempotent(temp_project_root):
    """Test that running the function twice does not raise errors."""
    # First run
    results1 = create_results_directories()
    assert results1["results"] is True
    
    # Second run
    results2 = create_results_directories()
    # Should report False because they already exist
    assert results2["results"] is False
    assert results2["results/paper"] is False

def test_main_function_returns_zero(temp_project_root, capsys):
    """Test that the main function returns 0 and prints status."""
    exit_code = main()
    assert exit_code == 0
    
    captured = capsys.readouterr()
    assert "Creating results directory structure" in captured.out
    assert "Results directory setup complete" in captured.out
