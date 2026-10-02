"""
Tests for visualization generation module.
"""
import os
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Mock the config and utils for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from visualizations import (
    load_null_distribution,
    load_alpha_sweep_data,
    load_cleaned_data,
    plot_null_distribution,
    plot_alpha_sweep,
    plot_correlation_matrix
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_null_data(temp_dir):
    data = {
        "maes": [0.5 + np.random.normal(0, 0.1) for _ in range(200)],
        "n_permutations": 200
    }
    path = temp_dir / "null_distribution.json"
    with open(path, 'w') as f:
        json.dump(data, f)
    return data, path

@pytest.fixture
def mock_alpha_data(temp_dir):
    data = {
        "mae_by_alpha": {
            "0.01": 0.45,
            "0.1": 0.42,
            "1.0": 0.40,
            "10.0": 0.43
        }
    }
    path = temp_dir / "robustness_report.json"
    with open(path, 'w') as f:
        json.dump(data, f)
    return data, path

@pytest.fixture
def mock_cleaned_data(temp_dir):
    df = pd.DataFrame({
        'Global_Signal_SD': np.random.rand(50),
        'MWQ_Score': np.random.rand(50) * 100,
        'Mean_FD': np.random.rand(50) * 0.5,
        'Mean_DVARS': np.random.rand(50) * 10,
        'Age': np.random.randint(18, 65, 50)
    })
    path = temp_dir / "cleaned_data.csv"
    df.to_csv(path, index=False)
    return df, path

def test_plot_null_distribution(temp_dir, mock_null_data):
    data, _ = mock_null_data
    output_path = temp_dir / "null_dist.png"
    
    plot_null_distribution(data, observed_mae=0.40, output_path=output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_plot_alpha_sweep(temp_dir, mock_alpha_data):
    data, _ = mock_alpha_data
    output_path = temp_dir / "alpha_sweep.png"
    
    plot_alpha_sweep(data, output_path=output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_plot_correlation_matrix(temp_dir, mock_cleaned_data):
    df, _ = mock_cleaned_data
    output_path = temp_dir / "corr_matrix.png"
    
    plot_correlation_matrix(df, output_path=output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_load_functions_fail_gracefully(temp_dir):
    # Test loading non-existent files raises appropriate errors
    with pytest.raises(FileNotFoundError):
        load_null_distribution() # Will look in default path which doesn't exist in test context
    
    # Note: The actual load functions expect files in specific relative paths.
    # In a real test suite, we would mock the paths or use temp_dir.
    # For now, we test the plotting functions directly which are the core logic.
