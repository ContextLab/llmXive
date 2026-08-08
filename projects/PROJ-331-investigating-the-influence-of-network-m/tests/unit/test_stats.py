"""
Unit tests for stats.py aggregation logic.
"""
import os
import json
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import tempfile
import shutil

# Mock the imports from code/
import sys
sys.path.insert(0, 'code')

from stats import aggregate_subject_metrics
from utils import safe_write_json, save_npy

@pytest.fixture
def temp_processed_dir():
    """Create a temporary data/processed directory with mock files."""
    temp_dir = tempfile.mkdtemp()
    processed_dir = Path(temp_dir) / "processed"
    processed_dir.mkdir()
    
    # Mock global_efficiency.json
    eff_data = {
        "sub_01": 0.45,
        "sub_02": 0.52,
        "sub_03": 0.48
    }
    with open(processed_dir / "global_efficiency.json", "w") as f:
        json.dump(eff_data, f)
    
    # Mock motif_profiles.json
    motif_data = {
        "metadata": {},
        "motifs": {
            "0,0,0,0,0,0,0,0,0": {"median_z": 1.5, "z_10p": 1.5, "z_20p": 1.5, "z_30p": 1.5},
            "0,0,0,0,0,0,0,1,0": {"median_z": 2.0, "z_10p": 2.0, "z_20p": 2.0, "z_20p": 2.0},
            "1,0,0,0,0,0,0,0,0": {"median_z": -1.0, "z_10p": -1.0, "z_20p": -1.0, "z_20p": -1.0}
        }
    }
    with open(processed_dir / "motif_profiles.json", "w") as f:
        json.dump(motif_data, f)
    
    # Mock rsfc.npy as a dict of matrices
    rsfc_dict = {}
    for i, sub in enumerate(["sub_01", "sub_02", "sub_03"]):
        # Create a random 10x10 matrix
        mat = np.random.rand(10, 10)
        rsfc_dict[sub] = mat
    
    save_npy(processed_dir / "rsfc.npy", rsfc_dict)
    
    return processed_dir

def test_aggregate_metrics_structure(temp_processed_dir):
    """Test that the aggregation function produces the correct CSV structure."""
    # Temporarily change the base_dir in the function or mock it.
    # Since the function uses hardcoded "data/processed", we must mock the environment
    # or modify the function to accept a path. For this test, we will create a symlink
    # or run in a specific directory. 
    # Better: Patch the function or the imports.
    # Given the constraint to not modify the function signature in this task (T039),
    # we will run the test by changing the current working directory.
    
    original_cwd = os.getcwd()
    temp_root = temp_processed_dir.parent
    os.chdir(temp_root)
    
    try:
        # Ensure data/processed exists relative to cwd
        # The fixture created temp_root/processed, but the code expects data/processed
        # So we create a 'data' folder and symlink or move.
        data_dir = Path(temp_root) / "data"
        data_dir.mkdir(exist_ok=True)
        # The fixture created temp_root/processed. We need temp_root/data/processed.
        # Let's move the content.
        shutil.move(str(temp_processed_dir), str(data_dir / "processed"))
        
        df = aggregate_subject_metrics()
        
        # Assertions
        assert isinstance(df, pd.DataFrame)
        assert "subject_id" in df.columns
        assert "global_efficiency" in df.columns
        assert "rsfc_mean_strength" in df.columns
        assert "motif_0,0,0,0,0,0,0,0,0_z" in df.columns
        
        # Check row count
        assert len(df) == 3
        
        # Check data types
        assert df["global_efficiency"].dtype in [np.float64, np.float32]
        
    finally:
        os.chdir(original_cwd)

def test_aggregate_metrics_missing_file():
    """Test that FileNotFoundError is raised when input is missing."""
    original_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    Path("data").mkdir()
    Path("data/processed").mkdir()
    
    try:
        with pytest.raises(FileNotFoundError):
            aggregate_subject_metrics()
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)