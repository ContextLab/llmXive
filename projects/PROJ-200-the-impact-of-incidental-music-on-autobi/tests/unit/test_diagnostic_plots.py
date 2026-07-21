import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_diagnostic_plots import (
    calculate_residuals,
    create_residuals_plot,
    create_qq_plot,
    create_scale_location_plot,
    generate_all_plots
)
from config import get_project_root

@pytest.fixture
def sample_user_track_df():
    """Create a synthetic dataset mimicking user_track_pairs.parquet structure."""
    np.random.seed(42)
    n = 100
    data = {
        'user_id': np.random.choice(['u1', 'u2', 'u3', 'u4', 'u5'], n),
        'track_id': np.random.choice(['t1', 't2', 't3'], n),
        'mean_vividness': np.random.normal(5.0, 1.5, n),
        'mean_valence': np.random.normal(0.0, 1.0, n),
        'residualized_exposure_score': np.random.normal(0.0, 1.0, n),
        'overall_popularity_score': np.random.normal(50.0, 20.0, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_residuals_df():
    """Create a synthetic residuals dataframe."""
    n = 100
    return pd.DataFrame({
        'fitted_values': np.random.normal(5.0, 1.0, n),
        'residuals': np.random.normal(0.0, 0.5, n),
        'observed': np.random.normal(5.0, 1.0, n),
        'user_id': ['u1'] * n
    })

def test_calculate_residuals_success(sample_user_track_df):
    """Test that residuals are calculated correctly from user-track data."""
    # This function refits the model to get residuals
    residuals_df = calculate_residuals(None, sample_user_track_df)
    
    assert isinstance(residuals_df, pd.DataFrame)
    assert 'residuals' in residuals_df.columns
    assert 'fitted_values' in residuals_df.columns
    assert len(residuals_df) == len(sample_user_track_df.dropna())

def test_create_residuals_plot(sample_residuals_df, tmp_path):
    """Test that residuals plot is generated."""
    save_path = tmp_path / "residuals_test.png"
    create_residuals_plot(sample_residuals_df, save_path)
    
    assert save_path.exists()
    assert save_path.stat().st_size > 0

def test_create_qq_plot(sample_residuals_df, tmp_path):
    """Test that QQ plot is generated."""
    save_path = tmp_path / "qq_test.png"
    create_qq_plot(sample_residuals_df, save_path)
    
    assert save_path.exists()
    assert save_path.stat().st_size > 0

def test_create_scale_location_plot(sample_residuals_df, tmp_path):
    """Test that Scale-Location plot is generated."""
    save_path = tmp_path / "scale_test.png"
    create_scale_location_plot(sample_residuals_df, save_path)
    
    assert save_path.exists()
    assert save_path.stat().st_size > 0

def test_missing_data_raises_error():
    """Test that missing required columns raises an error."""
    empty_df = pd.DataFrame({'user_id': ['u1']})
    with pytest.raises(ValueError):
        calculate_residuals(None, empty_df)
