import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import statsmodels.api as sm

from binary_model import fit_binary_model, save_binary_model_results

@pytest.fixture
def sample_data():
    """Create sample data for testing the binary model."""
    np.random.seed(42)
    n = 100
    data = pd.DataFrame({
        'IAT_D_score': np.random.normal(0, 1, n),
        'news_exposure_z': np.random.normal(0, 1, n),
        'ideology_binary': np.random.binomial(1, 0.5, n)
    })
    return data

def test_fit_binary_model_success(sample_data):
    """Test that the binary model fits successfully with valid data."""
    model = fit_binary_model(sample_data)
    assert isinstance(model, sm.OLSResults)
    assert 'interaction' in model.params.index

def test_fit_binary_model_missing_columns(sample_data):
    """Test that fit_binary_model raises ValueError if columns are missing."""
    incomplete_data = sample_data.drop(columns=['ideology_binary'])
    with pytest.raises(ValueError, match="Missing required columns"):
        fit_binary_model(incomplete_data)

def test_fit_binary_model_empty_after_dropna(sample_data):
    """Test that fit_binary_model raises ValueError if no data remains after dropping NaNs."""
    # Create data with all NaNs in required columns
    empty_data = pd.DataFrame({
        'IAT_D_score': [np.nan] * 10,
        'news_exposure_z': [np.nan] * 10,
        'ideology_binary': [np.nan] * 10
    })
    with pytest.raises(ValueError, match="No valid data remaining"):
        fit_binary_model(empty_data)

def test_save_binary_model_results(tmp_path, sample_data):
    """Test that save_binary_model_results creates a valid CSV file."""
    model = fit_binary_model(sample_data)
    output_file = tmp_path / "test_binary_model.csv"
    
    result = save_binary_model_results(model, output_file)
    
    assert output_file.exists()
    assert result is not None
    assert 'coefficient' in result
    assert 'p_value' in result
    
    # Verify CSV content
    df = pd.read_csv(output_file)
    assert 'term' in df.columns
    assert 'coefficient' in df.columns
    assert 'p_value' in df.columns
    assert len(df) > 0
