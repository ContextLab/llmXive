import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Import the function to test
from validate_baseline_results import validate_results_file

@pytest.fixture
def temp_results_dir():
    """Create a temporary directory for test artifacts."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_validate_results_file_success(temp_results_dir):
    """Test that a valid results file passes validation."""
    # Create a valid DataFrame
    data = {
        "material_id": ["id1", "id2", "id3"],
        "true_energy": [-10.0, -12.0, -11.5],
        "predicted_energy": [-10.1, -11.9, -11.0],
        "error": [0.1, 0.1, 0.5], # One error > 0.1
        "mae": [0.23],
        "rmse": [0.30]
    }
    df = pd.DataFrame(data)
    
    file_path = temp_results_dir / "baseline_results.csv"
    df.to_csv(file_path, index=False)

    # Run validation
    assert validate_results_file(file_path) is True

def test_validate_results_file_missing_columns(temp_results_dir):
    """Test that a file with missing columns fails validation."""
    data = {
        "material_id": ["id1"],
        "true_energy": [-10.0],
        # Missing predicted_energy, error, mae, rmse
    }
    df = pd.DataFrame(data)
    
    file_path = temp_results_dir / "baseline_results.csv"
    df.to_csv(file_path, index=False)

    assert validate_results_file(file_path) is False

def test_validate_results_file_empty(temp_results_dir):
    """Test that an empty file fails validation."""
    file_path = temp_results_dir / "baseline_results.csv"
    # Create empty file with headers only
    pd.DataFrame(columns=["material_id", "true_energy", "predicted_energy", "error", "mae", "rmse"]).to_csv(file_path, index=False)

    assert validate_results_file(file_path) is False

def test_validate_results_file_file_not_found():
    """Test that a non-existent file fails validation."""
    assert validate_results_file(Path("/non/existent/path.csv")) is False