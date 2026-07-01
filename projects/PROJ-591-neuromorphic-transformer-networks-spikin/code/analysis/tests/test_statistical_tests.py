"""
Unit tests for statistical analysis module.
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
import pytest
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.statistical_tests import (
    load_metrics_data,
    prepare_paired_data,
    run_paired_ttest,
    apply_bonferroni_correction,
    generate_statistical_report
)

@pytest.fixture
def temp_csv_files():
    """Create temporary CSV files with mock data for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        baseline_path = os.path.join(tmpdir, "baseline_metrics.csv")
        spiking_path = os.path.join(tmpdir, "spiking_metrics.csv")
        
        # Create mock data with matching seeds
        # Using deterministic values to ensure reproducible test results
        seeds = [1, 2, 3, 4, 5]
        baseline_data = {
            "seed": seeds * 3,  # 3 epochs per seed
            "epoch": [1, 2, 3] * 5,
            "perplexity": [10.0, 9.0, 8.0, 11.0, 10.0, 9.0, 12.0, 11.0, 10.0, 13.0, 12.0, 11.0, 14.0, 13.0, 12.0],
            "energy_per_token_kWh": [0.1, 0.09, 0.08, 0.11, 0.1, 0.09, 0.12, 0.11, 0.1, 0.13, 0.12, 0.11, 0.14, 0.13, 0.12]
        }
        spiking_data = {
            "seed": seeds * 3,
            "epoch": [1, 2, 3] * 5,
            "perplexity": [10.5, 9.5, 8.5, 11.5, 10.5, 9.5, 12.5, 11.5, 10.5, 13.5, 12.5, 11.5, 14.5, 13.5, 12.5],
            "energy_per_token_kWh": [0.08, 0.07, 0.06, 0.09, 0.08, 0.07, 0.10, 0.09, 0.08, 0.11, 0.10, 0.09, 0.12, 0.11, 0.10]
        }
        
        pd.DataFrame(baseline_data).to_csv(baseline_path, index=False)
        pd.DataFrame(spiking_data).to_csv(spiking_path, index=False)
        
        yield baseline_path, spiking_path

def test_load_metrics_data(temp_csv_files):
    baseline_path, spiking_path = temp_csv_files
    baseline_df, spiking_df = load_metrics_data(baseline_path, spiking_path)
    
    assert len(baseline_df) == 15
    assert len(spiking_df) == 15
    assert list(baseline_df.columns) == ["seed", "epoch", "perplexity", "energy_per_token_kWh"]
    assert list(spiking_df.columns) == ["seed", "epoch", "perplexity", "energy_per_token_kWh"]

def test_prepare_paired_data(temp_csv_files):
    baseline_path, spiking_path = temp_csv_files
    baseline_df, spiking_df = load_metrics_data(baseline_path, spiking_path)
    
    b_vals, s_vals = prepare_paired_data(baseline_df, spiking_df, "perplexity")
    
    assert len(b_vals) == 5  # 5 seeds
    assert len(s_vals) == 5
    assert isinstance(b_vals, np.ndarray)
    assert isinstance(s_vals, np.ndarray)

def test_run_paired_ttest(temp_csv_files):
    baseline_path, spiking_path = temp_csv_files
    baseline_df, spiking_df = load_metrics_data(baseline_path, spiking_path)
    
    result = run_paired_ttest(baseline_df, spiking_df, "perplexity")
    
    assert "p_value" in result
    assert "t_statistic" in result
    assert "is_significant_at_0.05" in result
    assert "mean_difference" in result
    assert result["n_pairs"] == 5

def test_apply_bonferroni_correction():
    p_values = [0.01, 0.03, 0.04, 0.06]
    result = apply_bonferroni_correction(p_values, alpha=0.05)
    
    assert len(result["corrected_p_values"]) == 4
    assert result["n_tests"] == 4
    assert result["alpha_corrected"] == 0.05 / 4
    
    # Check that corrected p-values are <= 1.0
    assert all(p <= 1.0 for p in result["corrected_p_values"])

def test_generate_statistical_report(temp_csv_files):
    baseline_path, spiking_path = temp_csv_files
    output_path = os.path.join(os.path.dirname(baseline_path), "test_report.json")
    
    try:
        report = generate_statistical_report(baseline_path, spiking_path, output_path)
        
        assert os.path.exists(output_path)
        assert "tests" in report
        assert "perplexity" in report["tests"]
        assert "energy_per_token_kWh" in report["tests"]
        assert "multiple_comparison_correction" in report
        
        # Verify JSON content
        with open(output_path, 'r') as f:
            loaded = json.load(f)
            assert loaded == report
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

def test_insufficient_seeds():
    """Test error handling when seeds do not match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        baseline_path = os.path.join(tmpdir, "baseline.csv")
        spiking_path = os.path.join(tmpdir, "spiking.csv")
        
        # Create data with non-overlapping seeds
        pd.DataFrame({
            "seed": [1, 2, 3],
            "epoch": [1, 1, 1],
            "perplexity": [10, 10, 10],
            "energy_per_token_kWh": [0.1, 0.1, 0.1]
        }).to_csv(baseline_path, index=False)
        
        pd.DataFrame({
            "seed": [4, 5, 6],
            "epoch": [1, 1, 1],
            "perplexity": [10, 10, 10],
            "energy_per_token_kWh": [0.1, 0.1, 0.1]
        }).to_csv(spiking_path, index=False)
        
        baseline_df = pd.read_csv(baseline_path)
        spiking_df = pd.read_csv(spiking_path)
        
        with pytest.raises(ValueError, match="Insufficient matching seeds"):
            prepare_paired_data(baseline_df, spiking_df, "perplexity")