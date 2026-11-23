import os
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from uq.uncertainty_decomposition import (
    load_predictions,
    write_uncertainty_types,
    generate_decomposition_report,
    save_decomposition
)

@pytest.fixture
def sample_predictions(tmp_path):
    """Create a sample predictions DataFrame for testing."""
    data = {
        'sample_id': range(100),
        'method': ['baseline'] * 25 + ['deep_ensemble'] * 25 + 
                 ['mc_dropout'] * 25 + ['sparse_gp'] * 25,
        'prediction': np.random.randn(100),
        'variance': np.abs(np.random.randn(100)) + 0.1,
        'lower_50': np.random.randn(100),
        'upper_50': np.random.randn(100),
        'lower_90': np.random.randn(100),
        'upper_90': np.random.randn(100)
    }
    df = pd.DataFrame(data)
    output_path = tmp_path / "uq_predictions.csv"
    df.to_csv(output_path, index=False)
    return str(output_path), df

@pytest.fixture
def sample_calibration_report(tmp_path):
    """Create a sample calibration report DataFrame for testing."""
    data = {
        'method': ['baseline', 'deep_ensemble', 'mc_dropout', 'sparse_gp'],
        'ece': [0.05, 0.03, 0.04, 0.06],
        'interval_score': [0.12, 0.10, 0.11, 0.13],
        'sharpness': [0.15, 0.14, 0.14, 0.16]
    }
    df = pd.DataFrame(data)
    output_path = tmp_path / "calibration_report.csv"
    df.to_csv(output_path, index=False)
    return str(output_path), df

def test_load_predictions_valid(sample_predictions):
    """Test loading a valid predictions file."""
    path, expected_df = sample_predictions
    loaded_df = load_predictions(path)
    
    assert len(loaded_df) == 100
    assert 'sample_id' in loaded_df.columns
    assert 'method' in loaded_df.columns
    assert 'prediction' in loaded_df.columns
    assert 'variance' in loaded_df.columns

def test_load_predictions_missing_file(tmp_path):
    """Test loading a non-existent predictions file."""
    path = tmp_path / "nonexistent.csv"
    with pytest.raises(FileNotFoundError):
        load_predictions(str(path))

def test_load_predictions_missing_columns(tmp_path):
    """Test loading a predictions file with missing required columns."""
    data = {
        'sample_id': range(10),
        'prediction': np.random.randn(10)
        # Missing 'method' and 'variance'
    }
    df = pd.DataFrame(data)
    output_path = tmp_path / "bad_predictions.csv"
    df.to_csv(output_path, index=False)
    
    with pytest.raises(ValueError):
        load_predictions(str(output_path))

def test_write_uncertainty_types(sample_predictions, tmp_path):
    """Test writing uncertainty types to predictions file."""
    path, original_df = sample_predictions
    output_path = tmp_path / "output_predictions.csv"
    
    write_uncertainty_types(original_df, str(output_path))
    
    # Verify the file was created
    assert os.path.exists(output_path)
    
    # Load and check the uncertainty_type column
    result_df = pd.read_csv(output_path)
    assert 'uncertainty_type' in result_df.columns
    
    # Check that uncertainty types are correctly assigned
    expected_types = {
        'baseline': 'aleatoric',
        'deep_ensemble': 'epistemic',
        'mc_dropout': 'epistemic',
        'sparse_gp': 'mixed'
    }
    
    for method in original_df['method'].unique():
        mask = result_df['method'] == method
        assert all(result_df.loc[mask, 'uncertainty_type'] == expected_types[method])

def test_generate_decomposition_report(sample_predictions, tmp_path):
    """Test generating the uncertainty decomposition report."""
    path, predictions_df = sample_predictions
    output_path = tmp_path / "uncertainty_decomposition.csv"
    
    result_df = generate_decomposition_report(predictions_df, str(output_path))
    
    # Verify the file was created
    assert os.path.exists(output_path)
    
    # Check required columns
    assert 'method' in result_df.columns
    assert 'aleatoric' in result_df.columns
    assert 'epistemic' in result_df.columns
    assert 'total' in result_df.columns
    
    # Check that we have entries for all methods
    assert set(result_df['method']) == set(predictions_df['method'].unique())
    
    # Verify that aleatoric, epistemic, and total are positive
    assert all(result_df['aleatoric'] > 0)
    assert all(result_df['epistemic'] >= 0)
    assert all(result_df['total'] > 0)
    
    # Verify that total = aleatoric + epistemic (approximately)
    expected_total = result_df['aleatoric'] + result_df['epistemic']
    assert np.allclose(result_df['total'], expected_total)

def test_save_decomposition(sample_predictions, tmp_path):
    """Test saving the decomposition DataFrame to CSV."""
    path, predictions_df = sample_predictions
    decomposition_df = generate_decomposition_report(predictions_df, str(tmp_path / "decomp.csv"))
    output_path = tmp_path / "saved_decomposition.csv"
    
    save_decomposition(decomposition_df, str(output_path))
    
    assert os.path.exists(output_path)
    loaded_df = pd.read_csv(output_path)
    assert len(loaded_df) == len(decomposition_df)
    assert list(loaded_df.columns) == list(decomposition_df.columns)

def test_uncertainty_type_mapping(tmp_path):
    """Test that uncertainty types are correctly mapped for various methods."""
    data = {
        'sample_id': range(10),
        'method': ['baseline', 'deep_ensemble', 'mc_dropout', 'sparse_gp', 'unknown_method'] * 2,
        'prediction': np.random.randn(10),
        'variance': np.abs(np.random.randn(10)) + 0.1
    }
    df = pd.DataFrame(data)
    output_path = tmp_path / "test_mapping.csv"
    
    write_uncertainty_types(df, str(output_path))
    
    result_df = pd.read_csv(output_path)
    
    # Check specific mappings
    assert result_df.loc[result_df['method'] == 'baseline', 'uncertainty_type'].iloc[0] == 'aleatoric'
    assert result_df.loc[result_df['method'] == 'deep_ensemble', 'uncertainty_type'].iloc[0] == 'epistemic'
    assert result_df.loc[result_df['method'] == 'mc_dropout', 'uncertainty_type'].iloc[0] == 'epistemic'
    assert result_df.loc[result_df['method'] == 'sparse_gp', 'uncertainty_type'].iloc[0] == 'mixed'
    # Unknown method should map to 'unknown'
    assert result_df.loc[result_df['method'] == 'unknown_method', 'uncertainty_type'].iloc[0] == 'unknown'