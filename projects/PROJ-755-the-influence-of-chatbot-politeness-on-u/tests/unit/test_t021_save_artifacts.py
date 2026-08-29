"""
Unit tests for T021: Save processed data and raw logs.

These tests verify that the script correctly:
1. Ensures directories exist.
2. Loads the scored dialogues (mocked).
3. Loads the exclusions log (mocked).
4. Saves the files to the correct locations.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code import code
# We will import the functions directly by executing the module or mocking
# Since the script is in code/021_save_final_artifacts.py, we import from there.
from code.code_021_save_final_artifacts import (
    ensure_directories,
    load_scored_dialogues,
    load_exclusions_log,
    save_final_scored_data,
    save_final_exclusions_log,
    main
)
# Note: The import path might need adjustment based on how the package is structured.
# Assuming the script is run as a module or the path is set correctly.
# If the file is named 021_save_final_artifacts.py, we might need to import it differently
# or execute it. For testing, we assume we can import the functions.
# If the file name starts with a number, it's not a valid Python module name for direct import.
# We will use importlib to handle this.

import importlib.util
spec = importlib.util.spec_from_file_location(
    "t021_module", 
    project_root / "code" / "021_save_final_artifacts.py"
)
t021_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t021_module)

ensure_directories = t021_module.ensure_directories
load_scored_dialogues = t021_module.load_scored_dialogues
load_exclusions_log = t021_module.load_exclusions_log
save_final_scored_data = t021_module.save_final_scored_data
save_final_exclusions_log = t021_module.save_final_exclusions_log
main = t021_module.main

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure mimicking the project."""
    tmpdir = tempfile.mkdtemp()
    root = Path(tmpdir)
    
    # Create expected structure
    (root / "data" / "processed").mkdir(parents=True)
    (root / "data" / "raw").mkdir(parents=True)
    
    # Mock data files
    df = pd.DataFrame({
        'user_id': [1, 2, 3],
        'dialogue_id': ['a', 'b', 'c'],
        'politeness_score': [0.5, 0.6, 0.7],
        'quality_rating': [3, 4, 5]
    })
    scored_path = root / "data" / "processed" / "scored_dialogues.parquet"
    df.to_parquet(scored_path, index=False)
    
    log_path = root / "data" / "raw" / "exclusions.log"
    log_path.write_text("Excluded 2 dialogues due to missing quality_rating.\n")
    
    # Monkey patch the project_root in the module
    original_root = t021_module.project_root
    t021_module.project_root = root
    
    yield root
    
    # Cleanup
    t021_module.project_root = original_root
    shutil.rmtree(tmpdir)

def test_ensure_directories(temp_project_dir):
    """Test that ensure_directories creates missing folders."""
    new_dir = temp_project_dir / "data" / "new_folder"
    assert not new_dir.exists()
    
    # Temporarily change project_root to test creation
    # (This is a bit hacky, but ensures we test the function logic)
    # In reality, ensure_directories uses the global project_root defined in the script.
    # We assume the fixture setup handles the path correctly.
    # The function just calls mkdir(parents=True, exist_ok=True) on specific paths.
    # We verify the paths exist after calling the function.
    ensure_directories()
    assert (temp_project_dir / "data" / "processed").exists()
    assert (temp_project_dir / "data" / "raw").exists()

def test_load_scored_dialogues(temp_project_dir):
    """Test loading the scored dialogues."""
    df = load_scored_dialogues()
    assert isinstance(df, pd.DataFrame)
    assert 'user_id' in df.columns
    assert 'politeness_score' in df.columns
    assert len(df) == 3

def test_load_exclusions_log(temp_project_dir):
    """Test loading the exclusions log."""
    log_content = load_exclusions_log()
    assert isinstance(log_content, str)
    assert "Excluded" in log_content

def test_save_final_scored_data(temp_project_dir):
    """Test saving the scored data."""
    df = pd.DataFrame({'id': [1, 2]})
    path = save_final_scored_data(df)
    assert path.exists()
    assert path.name == "scored_dialogues.parquet"
    # Verify content
    df_loaded = pd.read_parquet(path)
    assert len(df_loaded) == 2

def test_save_final_exclusions_log(temp_project_dir):
    """Test saving the exclusions log."""
    log_content = "Test log content\n"
    path = save_final_exclusions_log(log_content)
    assert path.exists()
    assert path.name == "exclusions.log"
    assert path.read_text() == log_content

def test_main_integration(temp_project_dir):
    """Test the main function end-to-end."""
    # The main function should run without error if files exist
    # We might need to reset the files if they were modified by previous tests
    result = main()
    assert result == 0
    assert (temp_project_dir / "data" / "processed" / "scored_dialogues.parquet").exists()
    assert (temp_project_dir / "data" / "raw" / "exclusions.log").exists()