import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Adjust import based on project structure if needed, assuming code/ is in path
import sys
sys.path.insert(0, 'code')
from analyze import compute_correlations, get_network_metrics, get_thermal_conductivity_col

def test_compute_correlations_basic():
    """Test correlation computation with synthetic but realistic data."""
    # Create a mock DataFrame with network metrics and thermal conductivity
    np.random.seed(42)
    n = 50
    data = {
        'average_degree': np.random.normal(4.0, 1.0, n),
        'average_shortest_path_length': np.random.normal(3.5, 0.5, n),
        'clustering_coefficient': np.random.normal(0.4, 0.1, n),
        'thermal_conductivity_scalar': np.random.normal(10.0, 2.0, n),
        'unit_cell_volume': np.random.normal(100.0, 10.0, n), # Physical descriptor, should be ignored
        'total_atom_count': np.random.randint(10, 50, n)
    }
    df = pd.DataFrame(data)
    
    # Mock logger
    logger = MagicMock()
    
    # Run analysis
    results = compute_correlations(df, logger)
    
    # Verify structure
    assert "correlations" in results
    assert len(results["correlations"]) == 3 # degree, path, clustering
    
    # Verify content for one metric
    first_corr = results["correlations"][0]
    assert "metric" in first_corr
    assert "target" in first_corr
    assert "pearson" in first_corr
    assert "spearman" in first_corr
    
    # Verify Bonferroni correction is present
    assert "p_value_bonferroni_corrected" in first_corr["pearson"]
    assert "p_value_bonferroni_corrected" in first_corr["spearman"]
    
    # Verify physical descriptors were NOT included
    metrics_in_results = [c["metric"] for c in results["correlations"]]
    assert "unit_cell_volume" not in metrics_in_results
    assert "total_atom_count" not in metrics_in_results

def test_compute_correlations_missing_thermal():
    """Test handling of missing thermal conductivity column."""
    df = pd.DataFrame({
        'average_degree': [1, 2, 3],
        'clustering_coefficient': [0.1, 0.2, 0.3]
    })
    logger = MagicMock()
    results = compute_correlations(df, logger)
    
    assert results == {}
    logger.error.assert_called()

def test_compute_correlations_insufficient_data():
    """Test handling of insufficient data points."""
    df = pd.DataFrame({
        'average_degree': [1.0, 2.0], # Only 2 points
        'thermal_conductivity_scalar': [10.0, 20.0]
    })
    logger = MagicMock()
    results = compute_correlations(df, logger)
    
    # Should return empty or warn, but not crash
    # The function skips if n < 3
    assert results == {} 
    logger.warning.assert_called()

def test_get_network_metrics():
    """Test identification of network metric columns."""
    df = pd.DataFrame({
        'average_degree': [1],
        'average_shortest_path_length': [1],
        'clustering_coefficient': [1],
        'unit_cell_volume': [1]
    })
    metrics = get_network_metrics(df)
    assert set(metrics) == {'average_degree', 'average_shortest_path_length', 'clustering_coefficient'}

def test_get_thermal_conductivity_col():
    """Test identification of thermal conductivity column."""
    df = pd.DataFrame({
        'thermal_conductivity_scalar': [1],
        'other_col': [1]
    })
    col = get_thermal_conductivity_col(df)
    assert col == 'thermal_conductivity_scalar'

    # Fallback test
    df2 = pd.DataFrame({
        'mean_thermal_conductivity': [1],
        'other': [1]
    })
    col2 = get_thermal_conductivity_col(df2)
    assert col2 == 'mean_thermal_conductivity'
