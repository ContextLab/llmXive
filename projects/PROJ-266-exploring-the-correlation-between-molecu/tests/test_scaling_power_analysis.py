"""
Unit tests for T028: Statistical power analysis and hypothesis testing
for scaling exponents.
"""
import json
import tempfile
import os
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.scaling_power_analysis import (
    calculate_effect_size_for_exponent,
    run_power_analysis,
    load_analysis_data_fallback,
    get_project_root_fallback
)

class TestScalingPowerAnalysis:
    """Test suite for scaling power analysis functions."""

    def test_calculate_effect_size_for_exponent(self):
        """Test effect size calculation for different sample sizes."""
        # Small sample
        min_eff_small, power_small = calculate_effect_size_for_exponent(
            n=30, alpha=0.05, power_target=0.80, null_exponent=0.5
        )
        assert min_eff_small > 0
        assert power_small == 0.80
        
        # Large sample - should detect smaller effects
        min_eff_large, power_large = calculate_effect_size_for_exponent(
            n=500, alpha=0.05, power_target=0.80, null_exponent=0.5
        )
        assert min_eff_large > 0
        assert min_eff_large < min_eff_small  # Larger sample detects smaller effects
        assert power_large == 0.80

    def test_run_power_analysis_basic(self):
        """Test basic power analysis execution."""
        sample_size = 100
        estimated_exp = 0.6
        nulls = [0.25, 0.5, 1.0]
        
        results = run_power_analysis(
            sample_size=sample_size,
            estimated_exponent=estimated_exp,
            null_hypotheses=nulls,
            alpha=0.05,
            power_target=0.80
        )
        
        # Verify structure
        assert "sample_size" in results
        assert "estimated_exponent" in results
        assert "null_hypotheses" in results
        assert "hypothesis_tests" in results
        assert "summary" in results
        
        # Verify hypothesis tests
        assert len(results["hypothesis_tests"]) == len(nulls)
        
        for test in results["hypothesis_tests"]:
            assert "null_exponent" in test
            assert "effect_size" in test
            assert "statistical_power" in test
            assert "min_detectable_effect_size" in test
            assert "can_reject_null" in test
            assert "sufficient_power" in test
            
            # Values should be reasonable
            assert 0 <= test["statistical_power"] <= 1
            assert test["effect_size"] >= 0

    def test_run_power_analysis_with_large_sample(self):
        """Test that larger samples yield higher power."""
        small_results = run_power_analysis(
            sample_size=50,
            estimated_exponent=0.6,
            null_hypotheses=[0.5],
            alpha=0.05,
            power_target=0.80
        )
        
        large_results = run_power_analysis(
            sample_size=500,
            estimated_exponent=0.6,
            null_hypotheses=[0.5],
            alpha=0.05,
            power_target=0.80
        )
        
        small_power = small_results["hypothesis_tests"][0]["statistical_power"]
        large_power = large_results["hypothesis_tests"][0]["statistical_power"]
        
        assert large_power >= small_power

    def test_run_power_analysis_edge_cases(self):
        """Test edge cases in power analysis."""
        # Very small sample size
        with pytest.raises(Exception):  # Should handle gracefully or raise
            # We expect this to either work or raise a clear error
            pass  # Actual behavior depends on statsmodels

    def test_summary_statistics(self):
        """Test that summary statistics are computed correctly."""
        results = run_power_analysis(
            sample_size=200,
            estimated_exponent=0.7,
            null_hypotheses=[0.25, 0.5, 1.0],
            alpha=0.05,
            power_target=0.80
        )
        
        summary = results["summary"]
        assert summary["total_nulls_tested"] == 3
        assert summary["significant_rejections"] >= 0
        assert summary["significant_rejections"] <= 3
        assert 0 <= summary["rejection_rate"] <= 1

def test_integration_with_mock_data(tmp_path):
    """
    Integration test with mock correlation data to ensure full pipeline works.
    """
    # Create temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create mock data directory
        data_dir = tmpdir / "data" / "processed"
        data_dir.mkdir(parents=True)
        
        # Create mock correlation_results.csv
        mock_data = pd.DataFrame({
            "smiles": ["CCO", "CCC", "CCCC"],
            "logPapp": [1.0, 1.5, 2.0],
            "dihedral_variance": [0.1, 0.2, 0.3],
            "scaling_exponent": [0.6, 0.6, 0.6]  # Simulated T027 output
        })
        
        mock_file = data_dir / "correlation_results.csv"
        mock_data.to_csv(mock_file, index=False)
        
        # Temporarily override get_project_root_fallback
        import data.scaling_power_analysis as spm
        original_func = spm.get_project_root_fallback
        
        def mock_get_root():
            return tmpdir
        
        spm.get_project_root_fallback = mock_get_root
        
        try:
            # Run the main function
            result = spm.main()
            
            # Verify output file was created
            output_file = data_dir / "scaling_analysis_results.json"
            assert output_file.exists(), "Output JSON file was not created"
            
            # Verify content
            with open(output_file, 'r') as f:
                content = json.load(f)
            
            assert "sample_size" in content
            assert content["sample_size"] == 3
            assert "hypothesis_tests" in content
            assert len(content["hypothesis_tests"]) == 3
            
        finally:
            # Restore original function
            spm.get_project_root_fallback = original_func