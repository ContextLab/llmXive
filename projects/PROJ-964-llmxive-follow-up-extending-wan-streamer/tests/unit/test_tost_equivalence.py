"""
Unit tests for TOST equivalence testing (T049).
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'code'))

from metrics.tost_equivalence import (
    perform_tost_test,
    run_tost_equivalence_tests,
    load_hybrid_output,
    load_baseline_metrics
)


class TestTOSTEquivalence:
    """Test suite for TOST equivalence testing functions."""

    def test_perform_tost_test_equivalent(self):
        """Test TOST when data is truly equivalent."""
        # Generate data centered around 0 with small variance
        np.random.seed(42)
        sample_data = pd.Series(np.random.normal(0, 0.01, 100))
        
        p_lower, p_upper, is_equivalent = perform_tost_test(
            sample_data,
            reference_value=0.0,
            equivalence_margin=0.05,
            alpha=0.05
        )
        
        assert is_equivalent, "Data centered at 0 should be equivalent within Δ=0.05"
        assert p_lower < 0.05
        assert p_upper < 0.05

    def test_perform_tost_test_not_equivalent_high(self):
        """Test TOST when data mean is too high."""
        # Generate data with mean outside equivalence margin
        np.random.seed(42)
        sample_data = pd.Series(np.random.normal(0.1, 0.01, 100))
        
        p_lower, p_upper, is_equivalent = perform_tost_test(
            sample_data,
            reference_value=0.0,
            equivalence_margin=0.05,
            alpha=0.05
        )
        
        assert not is_equivalent, "Data with mean=0.1 should not be equivalent within Δ=0.05"

    def test_perform_tost_test_not_equivalent_low(self):
        """Test TOST when data mean is too low."""
        # Generate data with mean outside equivalence margin (negative)
        np.random.seed(42)
        sample_data = pd.Series(np.random.normal(-0.1, 0.01, 100))
        
        p_lower, p_upper, is_equivalent = perform_tost_test(
            sample_data,
            reference_value=0.0,
            equivalence_margin=0.05,
            alpha=0.05
        )
        
        assert not is_equivalent, "Data with mean=-0.1 should not be equivalent within Δ=0.05"

    def test_perform_tost_test_insufficient_samples(self):
        """Test TOST with insufficient samples."""
        sample_data = pd.Series([0.01, 0.02])
        
        with pytest.raises(ValueError, match="Need at least 2 samples"):
            perform_tost_test(
                sample_data,
                reference_value=0.0,
                equivalence_margin=0.05,
                alpha=0.05
            )

    def test_run_tost_equivalence_tests(self):
        """Test the full TOST pipeline."""
        # Create mock hybrid output
        np.random.seed(42)
        hybrid_output = pd.DataFrame({
            'fid_degradation': np.random.normal(0.01, 0.02, 500),
            'proxy_mos': np.random.normal(4.5, 0.3, 500)
        })
        
        baseline_metrics = {
            'proxy_mos': 4.5
        }
        
        results = run_tost_equivalence_tests(
            hybrid_output,
            baseline_metrics,
            equivalence_margin=0.05,
            alpha=0.05
        )
        
        assert 'fid_degradation' in results
        assert 'proxy_mos' in results
        assert 'mean' in results['fid_degradation']
        assert 'p_value_lower' in results['fid_degradation']
        assert 'p_value_upper' in results['fid_degradation']
        assert 'is_equivalent' in results['fid_degradation']

    def test_run_tost_equivalence_tests_missing_metric(self):
        """Test TOST when a metric is missing."""
        hybrid_output = pd.DataFrame({
            'fid_degradation': np.random.normal(0.01, 0.02, 100)
        })
        
        baseline_metrics = {}
        
        results = run_tost_equivalence_tests(
            hybrid_output,
            baseline_metrics,
            equivalence_margin=0.05,
            alpha=0.05
        )
        
        # Only fid_degradation should be in results
        assert 'fid_degradation' in results
        assert 'proxy_mos' not in results

    def test_load_hybrid_output_file_not_found(self):
        """Test loading non-existent hybrid output."""
        with pytest.raises(FileNotFoundError):
            load_hybrid_output(Path('/nonexistent/path/output.parquet'))

    def test_load_baseline_metrics_file_not_found(self):
        """Test loading non-existent baseline metrics."""
        with pytest.raises(FileNotFoundError):
            load_baseline_metrics(Path('/nonexistent/path/metrics.json'))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])