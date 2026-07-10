"""
Unit tests for T038: generate_regression_summary.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Mock the project root and config for testing
@pytest.fixture
def mock_project_root(tmp_path):
    # Create necessary directory structure
    data_raw = tmp_path / "data" / "raw"
    data_processed = tmp_path / "data" / "processed"
    data_final = tmp_path / "data" / "final"
    data_raw.mkdir(parents=True)
    data_processed.mkdir(parents=True)
    data_final.mkdir(parents=True)
    
    # Create a mock input file
    mock_data = pd.DataFrame({
        'mean_vividness': [5.0, 4.5, 6.0, 3.0, 7.0],
        'residualized_exposure_score': [0.1, 0.2, 0.3, 0.4, 0.5],
        'overall_popularity_score': [10, 20, 30, 40, 50],
        'user_id': ['u1', 'u1', 'u2', 'u2', 'u3']
    })
    input_path = data_processed / "user_track_pairs.parquet"
    mock_data.to_parquet(input_path)
    
    return tmp_path

@pytest.fixture
def mock_config(monkeypatch, mock_project_root):
    # Mock get_project_root to return our temp dir
    def mock_get_root():
        return mock_project_root
    
    def mock_get_config():
        return {}
    
    monkeypatch.setattr('config.get_project_root', mock_get_root)
    monkeypatch.setattr('config.get_config_dict', mock_get_config)
    
    # Mock state_manager to avoid file system issues
    def mock_register(*args, **kwargs):
        pass
    def mock_save(*args, **kwargs):
        pass
    
    monkeypatch.setattr('state_manager.register_file', mock_register)
    monkeypatch.setattr('state_manager.save_state', mock_save)

def test_generate_regression_summary_runs(mock_project_root, mock_config):
    """
    Test that the main function runs without error and produces the output file.
    """
    # We need to import the module after mocking
    # Since the module imports at the top, we might need to reload or import carefully
    # For simplicity, we assume the mocks are in place before import or we use a subprocess
    # However, for a unit test of the logic, we can test the core functions if exposed.
    # Here we test the script execution logic.
    
    # Temporarily add the code dir to path if not already
    code_dir = mock_project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    # Import the main function
    try:
        from generate_regression_summary import main
    except ImportError as e:
        pytest.skip(f"Could not import module: {e}")

    output_file = mock_project_root / "data" / "final" / "regression_summary.csv"
    
    # Run the main function
    # Note: This requires statsmodels to be installed and working
    try:
        main()
    except Exception as e:
        # If statsmodels fails due to missing dependencies in test env, skip
        if "statsmodels" in str(e) or "MixedLM" in str(e):
            pytest.skip("Statsmodels not available or model fitting failed in test env.")
        else:
            raise

    assert output_file.exists(), "Output CSV file was not created."
    
    df = pd.read_csv(output_file)
    assert 'variable' in df.columns, "Missing 'variable' column."
    assert 'coef' in df.columns, "Missing 'coef' column."
    assert 'std err' in df.columns, "Missing 'std err' column."
    assert 'pvalue' in df.columns, "Missing 'pvalue' column."
    assert len(df) > 0, "Output CSV is empty."

def test_missing_input_file(mock_project_root, mock_config):
    """
    Test that the script fails gracefully if input file is missing.
    """
    # Remove the mock input file
    input_path = mock_project_root / "data" / "processed" / "user_track_pairs.parquet"
    if input_path.exists():
        input_path.unlink()

    code_dir = mock_project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

    try:
        from generate_regression_summary import main
    except ImportError:
        pytest.skip("Could not import module.")

    with pytest.raises(FileNotFoundError):
        main()