"""
Unit tests for the statistical testing module.
"""
import pytest
import numpy as np
from pathlib import Path
import tempfile
import csv

from analysis.statistical_tests import (
    perform_two_sample_ttest,
    apply_bonferroni_correction,
    run_noise_sweep_statistics
)


def test_perform_two_sample_ttest_identical_groups():
    """Test that identical groups yield high p-value."""
    group_a = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    group_b = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    
    result = perform_two_sample_ttest(group_a, group_b)
    
    assert result["p_value"] > 0.9
    assert abs(result["t_statistic"]) < 0.001
    assert result["n_a"] == 5
    assert result["n_b"] == 5


def test_perform_two_sample_ttest_different_groups():
    """Test that significantly different groups yield low p-value."""
    group_a = np.array([1.0, 1.1, 1.2, 0.9, 1.0])
    group_b = np.array([5.0, 5.1, 5.2, 4.9, 5.0])
    
    result = perform_two_sample_ttest(group_a, group_b)
    
    assert result["p_value"] < 0.001
    assert result["t_statistic"] < 0  # Group A is smaller
    assert result["mean_a"] < result["mean_b"]


def test_apply_bonferroni_correction():
    """Test Bonferroni correction logic."""
    p_values = [0.01, 0.02, 0.05, 0.20]
    
    adjusted, reject = apply_bonferroni_correction(p_values, alpha=0.05)
    
    # Bonferroni multiplies by number of tests (4)
    # 0.01 * 4 = 0.04 (significant)
    # 0.02 * 4 = 0.08 (not significant)
    # 0.05 * 4 = 0.20 (not significant)
    # 0.20 * 4 = 0.80 (not significant)
    
    assert len(adjusted) == 4
    assert len(reject) == 4
    assert adjusted[0] == pytest.approx(0.04, rel=1e-5)
    assert reject[0] is True
    assert reject[1] is False


def test_run_noise_sweep_statistics_writes_csv():
    """Test that the function writes a valid CSV file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_stats.csv"
        
        # Mock data
        baseline = np.random.normal(0.2, 0.01, 50)
        results = [
            {
                "sigma": 0.01,
                "ellipticity_values": np.random.normal(0.21, 0.01, 50).tolist()
            },
            {
                "sigma": 0.05,
                "ellipticity_values": np.random.normal(0.25, 0.01, 50).tolist()
            }
        ]
        
        run_noise_sweep_statistics(results, baseline, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 2
        assert "p_value_bonferroni" in rows[0]
        assert "is_significant" in rows[0]
        assert "sigma" in rows[0]