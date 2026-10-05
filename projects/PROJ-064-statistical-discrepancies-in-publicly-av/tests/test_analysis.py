import pytest
import numpy as np
import pandas as pd
import json
import os
import tempfile
from pathlib import Path
from analysis import (
    run_sensitivity_analysis,
    load_sensitivity_thresholds,
    generate_sensitivity_report,
    generate_stability_plot,
    calculate_jurisdiction_p_values
)

@pytest.fixture
def mock_discrepancies():
    """Create a mock DataFrame with discrepancy data."""
    np.random.seed(42)
    n = 100
    data = {
        'jurisdiction_id': [f"J{i}" for i in range(n)],
        'discrepancy_pct': np.random.normal(0, 0.01, n),
        'precinct_sum': np.random.randint(100, 1000, n),
        'county_reported': np.random.randint(100, 1000, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_null_dist():
    """Create a mock null distribution."""
    np.random.seed(42)
    return np.random.normal(0, 0.005, 10000)

@pytest.fixture
def temp_config_file():
    """Create a temporary config file for thresholds."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
primary_threshold: 0.005
sweep_thresholds:
  - 0.0001
  - 0.0005
  - 0.0010
""")
        return f.name

@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_load_sensitivity_thresholds(temp_config_file):
    """Test loading sensitivity thresholds from YAML."""
    config = load_sensitivity_thresholds(temp_config_file)
    assert 'primary_threshold' in config
    assert 'sweep_thresholds' in config
    assert config['primary_threshold'] == 0.005
    assert len(config['sweep_thresholds']) == 3

def test_run_sensitivity_analysis(mock_discrepancies, mock_null_dist, temp_config_file):
    """Test running the sensitivity analysis."""
    # Prepare null distributions
    null_dist_nb = mock_null_dist
    null_dist_perm = mock_null_dist * 1.1 # Slightly different for permutation
    
    thresholds = load_sensitivity_thresholds(temp_config_file)
    
    results = run_sensitivity_analysis(
        mock_discrepancies, 
        null_dist_nb, 
        null_dist_perm, 
        thresholds
    )
    
    # Verify structure
    assert 'primary_results' in results
    assert 'sweep_results' in results
    assert 'stability_metrics' in results
    
    # Verify counts are integers
    assert isinstance(results['primary_results']['nb_flagged_count'], int)
    assert isinstance(results['primary_results']['perm_flagged_count'], int)
    
    # Verify sweep data exists
    assert len(results['sweep_results']['nb_model']) == len(thresholds['sweep_thresholds'])
    assert len(results['sweep_results']['perm_model']) == len(thresholds['sweep_thresholds'])

def test_generate_sensitivity_report(mock_discrepancies, mock_null_dist, temp_config_file, temp_output_dir):
    """Test generating the sensitivity report markdown."""
    thresholds = load_sensitivity_thresholds(temp_config_file)
    results = run_sensitivity_analysis(
        mock_discrepancies, 
        mock_null_dist, 
        mock_null_dist, 
        thresholds
    )
    
    report_path = os.path.join(temp_output_dir, "report.md")
    generate_sensitivity_report(results, report_path)
    
    assert os.path.exists(report_path)
    with open(report_path, 'r') as f:
        content = f.read()
    
    assert "Sensitivity Analysis Report" in content
    assert "Primary Threshold" in content
    assert "Stability Metrics" in content

def test_generate_stability_plot(mock_discrepancies, mock_null_dist, temp_config_file, temp_output_dir):
    """Test generating the stability plot."""
    thresholds = load_sensitivity_thresholds(temp_config_file)
    results = run_sensitivity_analysis(
        mock_discrepancies, 
        mock_null_dist, 
        mock_null_dist, 
        thresholds
    )
    
    plot_path = os.path.join(temp_output_dir, "plot.png")
    generate_stability_plot(results, plot_path)
    
    assert os.path.exists(plot_path)
    assert os.path.getsize(plot_path) > 0

def test_calculate_jurisdiction_p_values(mock_discrepancies, mock_null_dist):
    """Test p-value calculation for jurisdictions."""
    df = mock_discrepancies.copy()
    result_df = calculate_jurisdiction_p_values(df, mock_null_dist)
    
    assert 'p_value' in result_df.columns
    assert len(result_df) == len(mock_discrepancies)
    # P-values should be between 0 and 1
    assert all(0 <= p <= 1 for p in result_df['p_value'])
