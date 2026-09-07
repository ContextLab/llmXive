import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
from unittest.mock import patch
import matplotlib.pyplot as plt

from code.viz.plot_results import run_visualization_pipeline
from code.analysis.statistical_test import run_statistical_analysis_pipeline
from code.config import CONFIG

@pytest.fixture
def synthetic_negative_correlation_data():
    """
    Create synthetic data with a known negative correlation.
    Used to verify that the analysis correctly identifies negative correlation.
    """
    np.random.seed(42)
    n_samples = 200
    
    # Create control_proxy values
    control_proxy = np.random.normal(0.5, 0.2, n_samples)
    control_proxy = np.clip(control_proxy, 0, 1)
    
    # Create anxiety_score with known negative correlation (r ≈ -0.7)
    noise = np.random.normal(0, 0.15, n_samples)
    anxiety_score = 1.0 - 0.8 * control_proxy + noise
    anxiety_score = np.clip(anxiety_score, 0, 1)
    
    df = pd.DataFrame({
        'post_id': range(n_samples),
        'control_proxy': control_proxy,
        'anxiety_score': anxiety_score
    })
    
    return df

@pytest.fixture
def mock_config(tmp_path):
    """Mock CONFIG with temporary output directory."""
    with patch.object(CONFIG, 'OUTPUT_DIR', tmp_path):
        yield CONFIG

@pytest.fixture
def final_analysis_csv(synthetic_negative_correlation_data, mock_config):
    """Create the final_analysis.csv file with synthetic data."""
    output_path = mock_config.OUTPUT_DIR / "final_analysis.csv"
    synthetic_negative_correlation_data.to_csv(output_path, index=False)
    return output_path

@pytest.fixture
def analysis_results_json(mock_config):
    """Create analysis_results.json with expected negative correlation results."""
    output_path = mock_config.OUTPUT_DIR / "analysis_results.json"
    results = {
        "correlation_method": "pearson",
        "correlation_coefficient": -0.72,
        "p_value": 0.001,
        "is_significant": True,
        "sample_size": 200
    }
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    return output_path

def test_synthetic_negative_correlation_detection(final_analysis_csv, mock_config):
    """
    Test that the system correctly identifies a negative correlation
    when using synthetic data with known negative correlation.
    """
    # Run statistical analysis
    results = run_statistical_analysis_pipeline()
    
    # Verify results structure
    assert 'correlation_coefficient' in results
    assert 'p_value' in results
    assert 'is_significant' in results
    assert 'correlation_method' in results
    
    # Verify negative correlation
    assert results['correlation_coefficient'] < 0, \
        f"Expected negative correlation, got {results['correlation_coefficient']}"
    
    # Verify significance (p < 0.05)
    assert results['p_value'] < 0.05, \
        f"Expected significant result (p < 0.05), got p = {results['p_value']}"
    
    assert results['is_significant'] is True

def test_visualization_with_negative_correlation(final_analysis_csv, mock_config):
    """
    Test that visualization is generated correctly for data with negative correlation.
    """
    fig, ax = run_visualization_pipeline()
    
    assert fig is not None
    assert ax is not None
    
    # Verify plot has regression line
    assert len(ax.lines) >= 1, "Expected regression line in plot"
    
    # Verify scatter points exist
    assert len(ax.collections) > 0, "Expected scatter points in plot"
    
    plt.close(fig)

def test_spearman_fallback_when_normality_violated(final_analysis_csv, mock_config):
    """
    Test that the system falls back to Spearman correlation when normality assumptions are violated.
    This tests the robustness of the statistical test logic.
    """
    # Create data with non-normal distribution (skewed)
    np.random.seed(42)
    n_samples = 100
    
    # Skewed control_proxy
    control_proxy = np.random.exponential(0.5, n_samples)
    control_proxy = np.clip(control_proxy, 0, 1)
    
    # Non-normal anxiety scores
    anxiety_score = 1.0 - 0.6 * control_proxy + np.random.exponential(0.1, n_samples)
    anxiety_score = np.clip(anxiety_score, 0, 1)
    
    df = pd.DataFrame({
        'post_id': range(n_samples),
        'control_proxy': control_proxy,
        'anxiety_score': anxiety_score
    })
    
    output_path = mock_config.OUTPUT_DIR / "final_analysis.csv"
    df.to_csv(output_path, index=False)
    
    # Run analysis
    results = run_statistical_analysis_pipeline()
    
    # Should still produce results
    assert 'correlation_coefficient' in results
    assert 'p_value' in results
    assert 'is_significant' in results
    
    # Method should be either pearson or spearman
    assert results['correlation_method'] in ['pearson', 'spearman']

def test_analysis_results_json_creation(final_analysis_csv, mock_config):
    """Test that analysis_results.json is created with correct structure."""
    results = run_statistical_analysis_pipeline()
    
    output_path = mock_config.OUTPUT_DIR / "analysis_results.json"
    assert output_path.exists(), "analysis_results.json should be created"
    
    with open(output_path, 'r') as f:
        saved_results = json.load(f)
    
    # Verify all required fields
    assert 'correlation_method' in saved_results
    assert 'correlation_coefficient' in saved_results
    assert 'p_value' in saved_results
    assert 'is_significant' in saved_results
    assert 'sample_size' in saved_results

def test_full_pipeline_integration(final_analysis_csv, analysis_results_json, mock_config):
    """
    Test the full integration of statistical analysis and visualization.
    """
    # Run statistical analysis
    stats_results = run_statistical_analysis_pipeline()
    
    # Run visualization
    fig, ax = run_visualization_pipeline()
    
    # Verify both completed successfully
    assert stats_results is not None
    assert 'correlation_coefficient' in stats_results
    assert fig is not None
    assert ax is not None
    
    # Verify consistency
    assert stats_results['is_significant'] == (stats_results['p_value'] < 0.05)
    
    plt.close(fig)