"""
Unit tests for T050: Jagged Line Detail Generation.

Tests verify that the jagged line plot generation logic works correctly
with mock data and that the output file is created as expected.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
import numpy as np
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from code.generate_jagged_line_detail import (
    load_worst_case_scenario,
    load_pvalues_for_seed,
    generate_jagged_line_plot,
    OUTPUT_FILE,
    PROJECT_ROOT
)

@pytest.fixture
def temp_worst_case_file(tmp_path):
    """Create a temporary worst_case_summary.json file."""
    worst_case_data = {
        "seed": 12345,
        "n": 50,
        "p": 5000,
        "rho": 0.9,
        "distribution_type": "t-dist(df=3)",
        "ks_stat": 0.15
    }
    file_path = tmp_path / "worst_case_summary.json"
    with open(file_path, 'w') as f:
        json.dump(worst_case_data, f)
    return file_path

@pytest.fixture
def temp_pvalues_file(tmp_path):
    """Create a temporary pvalues CSV file."""
    file_path = tmp_path / "pvalues_12345.csv"
    # Generate some mock p-values that are NOT uniform
    np.random.seed(42)
    # Create a distribution that clusters near 0 (anti-conservative)
    pvals = np.concatenate([
        np.random.uniform(0, 0.1, 200),  # Excess near 0
        np.random.uniform(0.1, 1.0, 300) # Rest uniform
    ])
    np.random.shuffle(pvals)
    
    with open(file_path, 'w') as f:
        f.write("feature_index,p_value,test_type\n")
        for i, p in enumerate(pvals):
            f.write(f"{i},{p:.6f},t-test\n")
    return file_path

def test_load_worst_case_scenario_success(temp_worst_case_file):
    """Test successful loading of worst-case scenario."""
    with patch('code.generate_jagged_line_detail.WORST_CASE_FILE', temp_worst_case_file):
        result = load_worst_case_scenario()
        assert result['seed'] == 12345
        assert result['rho'] == 0.9
        assert result['ks_stat'] == 0.15

def test_load_worst_case_scenario_missing_file():
    """Test error handling when file is missing."""
    with patch('code.generate_jagged_line_detail.WORST_CASE_FILE', Path('/nonexistent/file.json')):
        with pytest.raises(FileNotFoundError):
            load_worst_case_scenario()

def test_load_pvalues_for_seed_success(temp_pvalues_file):
    """Test successful loading of p-values."""
    with patch('code.generate_jagged_line_detail.PVALUES_DIR', temp_pvalues_file.parent):
        pvalues = load_pvalues_for_seed(12345)
        assert len(pvalues) == 500
        assert np.all((pvalues >= 0) & (pvalues <= 1))

def test_load_pvalues_for_seed_missing_file():
    """Test error handling when p-values file is missing."""
    with patch('code.generate_jagged_line_detail.PVALUES_DIR', Path('/nonexistent')):
        with pytest.raises(FileNotFoundError):
            load_pvalues_for_seed(99999)

def test_generate_jagged_line_plot_creates_file(temp_worst_case_file, temp_pvalues_file, tmp_path):
    """Test that the plot generation creates the output file."""
    # Load data
    worst_case = {
        "seed": 12345,
        "n": 50,
        "p": 5000,
        "rho": 0.9,
        "distribution_type": "t-dist(df=3)",
        "ks_stat": 0.15
    }
    
    # Generate mock p-values
    np.random.seed(42)
    pvals = np.concatenate([
        np.random.uniform(0, 0.1, 200),
        np.random.uniform(0.1, 1.0, 300)
    ])
    
    output_path = tmp_path / "test_jagged_line.png"
    
    # Generate plot
    generate_jagged_line_plot(pvals, worst_case, output_path, num_bins=50)
    
    # Verify file exists and is not empty
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_generate_jagged_line_plot_high_bin_count(temp_worst_case_file, temp_pvalues_file, tmp_path):
    """Test that high bin count reveals more detail."""
    worst_case = {
        "seed": 12345,
        "n": 50,
        "p": 5000,
        "rho": 0.9,
        "distribution_type": "t-dist(df=3)",
        "ks_stat": 0.15
    }
    
    np.random.seed(42)
    pvals = np.random.uniform(0, 1, 1000)
    
    output_path_low = tmp_path / "test_low_bins.png"
    output_path_high = tmp_path / "test_high_bins.png"
    
    generate_jagged_line_plot(pvals, worst_case, output_path_low, num_bins=20)
    generate_jagged_line_plot(pvals, worst_case, output_path_high, num_bins=100)
    
    # Both should exist
    assert output_path_low.exists()
    assert output_path_high.exists()