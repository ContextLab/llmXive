"""
Unit tests for save_regression_results module (T027).

These tests verify that the regression results are correctly saved to CSV
with the expected schema: coefficient, std_err, p_value, predictor.
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from save_regression_results import save_regression_results, REGRESSION_RESULTS_PATH

@pytest.fixture
def sample_regression_results():
    """Create sample regression results DataFrame."""
    return pd.DataFrame({
        'predictor': ['shannon_index', 'age', 'sex', 'bmi', 'dqs'],
        'coefficient': [0.15, -0.02, 0.08, -0.01, 0.03],
        'std_err': [0.05, 0.01, 0.03, 0.005, 0.02],
        'p_value': [0.002, 0.04, 0.01, 0.06, 0.15]
    })

@pytest.fixture
def temp_output_path():
    """Create a temporary file path for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        path = Path(f.name)
    yield path
    # Cleanup
    if path.exists():
        os.unlink(path)

def test_save_regression_results_creates_file(sample_regression_results, temp_output_path):
    """Test that save_regression_results creates the output file."""
    result_path = save_regression_results(sample_regression_results, temp_output_path)
    
    assert result_path.exists(), "Output file was not created"
    assert result_path == temp_output_path

def test_save_regression_results_correct_columns(sample_regression_results, temp_output_path):
    """Test that the saved CSV has the correct columns."""
    save_regression_results(sample_regression_results, temp_output_path)
    
    saved_df = pd.read_csv(temp_output_path)
    expected_cols = ['predictor', 'coefficient', 'std_err', 'p_value']
    
    for col in expected_cols:
        assert col in saved_df.columns, f"Missing column: {col}"

def test_save_regression_results_data_integrity(sample_regression_results, temp_output_path):
    """Test that the saved data matches the input data."""
    save_regression_results(sample_regression_results, temp_output_path)
    
    saved_df = pd.read_csv(temp_output_path)
    
    # Check row count
    assert len(saved_df) == len(sample_regression_results), "Row count mismatch"
    
    # Check specific values
    assert np.isclose(saved_df['coefficient'].iloc[0], 0.15), "Coefficient value mismatch"
    assert np.isclose(saved_df['std_err'].iloc[0], 0.05), "Std err value mismatch"
    assert np.isclose(saved_df['p_value'].iloc[0], 0.002), "P-value mismatch"

def test_save_regression_results_empty_dataframe_raises_error(temp_output_path):
    """Test that saving an empty DataFrame raises an error."""
    empty_df = pd.DataFrame(columns=['predictor', 'coefficient', 'std_err', 'p_value'])
    
    with pytest.raises(ValueError, match="Regression results missing required columns"):
        save_regression_results(empty_df, temp_output_path)

def test_save_regression_results_missing_columns_raises_error(temp_output_path):
    """Test that missing required columns raises an error."""
    incomplete_df = pd.DataFrame({
        'predictor': ['shannon_index'],
        'coefficient': [0.15]
        # Missing std_err and p_value
    })
    
    with pytest.raises(ValueError, match="Regression results missing required columns"):
        save_regression_results(incomplete_df, temp_output_path)

def test_save_regression_results_default_path_structure(sample_regression_results):
    """Test that the default path follows the expected structure."""
    # We don't actually write to the default path in tests to avoid clutter
    # but we verify the constant is set correctly
    assert str(REGRESSION_RESULTS_PATH) == "data/processed/regression_results.csv"
    assert REGRESSION_RESULTS_PATH.parent == Path("data/processed")