"""
Unit tests for top feature plot generation.
"""
import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import matplotlib.pyplot as plt

# Import the module under test
from code.plot_top_features import (
    get_top_features,
    create_scatter_plot_with_regression,
    generate_top_feature_plots,
    create_combined_plot
)

@pytest.fixture
def sample_importance_df():
    """Sample feature importance DataFrame."""
    return pd.DataFrame({
        'feature': ['degree_mean', 'path_length_mean', 'aromaticity_index', 
                   'bond_polarity', 'resonance_energy', 'ring_count'],
        'importance': [0.25, 0.20, 0.18, 0.15, 0.12, 0.10]
    })

@pytest.fixture
def sample_correlation_df():
    """Sample correlation results DataFrame."""
    return pd.DataFrame({
        'feature': ['degree_mean', 'path_length_mean', 'aromaticity_index',
                   'bond_polarity', 'resonance_energy'],
        'correlation': [0.75, -0.65, 0.82, 0.55, 0.48],
        'p_value': [1e-10, 1e-8, 1e-15, 1e-5, 1e-4]
    })

@pytest.fixture
def sample_data():
    """Sample processed data DataFrame."""
    np.random.seed(42)
    n_samples = 100
    return pd.DataFrame({
        'degree_mean': np.random.normal(3.5, 0.5, n_samples),
        'path_length_mean': np.random.normal(5.0, 1.0, n_samples),
        'aromaticity_index': np.random.normal(0.8, 0.1, n_samples),
        'bond_polarity': np.random.normal(0.3, 0.1, n_samples),
        'resonance_energy': np.random.normal(15.0, 2.0, n_samples),
        'ring_count': np.random.randint(1, 5, n_samples),
        'log_conductivity': np.random.normal(2.0, 0.5, n_samples)
    })

def test_get_top_features(sample_importance_df):
    """Test getting top N features by importance."""
    top_3 = get_top_features(sample_importance_df, 3)
    assert len(top_3) == 3
    assert top_3[0] == 'degree_mean'
    assert top_3[1] == 'path_length_mean'
    assert top_3[2] == 'aromaticity_index'

def test_get_top_features_invalid_columns(sample_importance_df):
    """Test error handling for invalid columns."""
    df = sample_importance_df.rename(columns={'feature': 'wrong_feature'})
    with pytest.raises(ValueError):
        get_top_features(df, 3)

def test_create_scatter_plot_with_regression(sample_data, tmp_path):
    """Test scatter plot creation with regression line."""
    output_path = tmp_path / "test_plot.png"
    
    create_scatter_plot_with_regression(
        data=sample_data,
        x_feature='degree_mean',
        y_target='log_conductivity',
        output_path=str(output_path),
        title='Test Plot'
    )
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_generate_top_feature_plots(sample_data, sample_importance_df, sample_correlation_df, tmp_path):
    """Test generation of top feature plots."""
    output_dir = tmp_path / "plots"
    output_dir.mkdir()
    
    plot_paths = generate_top_feature_plots(
        data=sample_data,
        importance_df=sample_importance_df,
        correlation_df=sample_correlation_df,
        target_var='log_conductivity',
        output_dir=str(output_dir),
        top_n=3
    )
    
    assert len(plot_paths) >= 3  # 3 individual + 1 combined
    assert any('corr_plot_top5.png' in p for p in plot_paths)
    
    # Check that all files exist
    for path in plot_paths:
        assert os.path.exists(path), f"Plot file not found: {path}"

def test_create_combined_plot(sample_data, tmp_path):
    """Test combined plot creation."""
    features = ['degree_mean', 'path_length_mean', 'aromaticity_index']
    output_path = tmp_path / "combined.png"
    
    create_combined_plot(
        data=sample_data,
        features=features,
        target_var='log_conductivity',
        output_path=str(output_path)
    )
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_generate_top_feature_plots_missing_feature(sample_data, sample_importance_df, sample_correlation_df, tmp_path):
    """Test handling of missing features in data."""
    # Add a feature that doesn't exist in data
    sample_importance_df.loc[len(sample_importance_df)] = ['nonexistent_feature', 0.05]
    
    output_dir = tmp_path / "plots"
    output_dir.mkdir()
    
    # Should not raise an error, just skip the missing feature
    plot_paths = generate_top_feature_plots(
        data=sample_data,
        importance_df=sample_importance_df,
        correlation_df=sample_correlation_df,
        target_var='log_conductivity',
        output_dir=str(output_dir),
        top_n=5
    )
    
    assert len(plot_paths) > 0  # Should still generate plots for existing features

def test_generate_top_feature_plots_missing_target(sample_data, sample_importance_df, sample_correlation_df, tmp_path):
    """Test handling of missing target variable."""
    output_dir = tmp_path / "plots"
    output_dir.mkdir()
    
    # Should raise an error if no suitable target is found
    with pytest.raises(ValueError):
        generate_top_feature_plots(
            data=sample_data.drop(columns=['log_conductivity']),
            importance_df=sample_importance_df,
            correlation_df=sample_correlation_df,
            target_var='log_conductivity',
            output_dir=str(output_dir),
            top_n=3
        )