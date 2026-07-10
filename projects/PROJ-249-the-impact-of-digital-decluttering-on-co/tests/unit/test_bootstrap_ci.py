"""
Unit tests for bootstrapped CI calculation.
"""
import pytest
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.bootstrap_ci import (
    calculate_bootstrap_ci,
    run_bootstrap_analysis,
    BootstrapResult
)
from utils.random_seed import set_global_seed


class TestCalculateBootstrapCI:
    """Tests for the core bootstrap CI calculation function."""

    def test_basic_bootstrap_ci(self):
        """Test basic bootstrap CI calculation with known data."""
        set_global_seed(42)
        values = [1.0, 2.0, 3.0, 4.0, 5.0]

        mean, ci_lower, ci_upper, failed = calculate_bootstrap_ci(
            values=values,
            n_resamples=1000,
            confidence_level=0.95,
            seed=42
        )

        assert not failed, "Bootstrap should not fail on valid data"
        assert abs(mean - 3.0) < 0.01, f"Mean should be close to 3.0, got {mean}"
        assert ci_lower < mean < ci_upper, "Mean should be within CI bounds"
        assert ci_lower < ci_upper, "CI lower should be less than upper"

    def test_empty_data(self):
        """Test handling of empty data."""
        mean, ci_lower, ci_upper, failed = calculate_bootstrap_ci(
            values=[],
            n_resamples=1000
        )

        assert failed, "Should fail on empty data"
        assert mean == 0.0
        assert ci_lower == 0.0
        assert ci_upper == 0.0

    def test_single_value(self):
        """Test handling of single value."""
        set_global_seed(42)
        values = [5.0]

        mean, ci_lower, ci_upper, failed = calculate_bootstrap_ci(
            values=values,
            n_resamples=1000,
            seed=42
        )

        assert not failed, "Should handle single value"
        assert abs(mean - 5.0) < 0.01

    def test_constant_values(self):
        """Test handling of constant values (zero variance)."""
        values = [5.0, 5.0, 5.0, 5.0, 5.0]

        mean, ci_lower, ci_upper, failed = calculate_bootstrap_ci(
            values=values,
            n_resamples=1000
        )

        assert not failed, "Should handle constant values"
        assert abs(mean - 5.0) < 0.01
        assert abs(ci_lower - 5.0) < 0.01
        assert abs(ci_upper - 5.0) < 0.01

    def test_confidence_level(self):
        """Test different confidence levels."""
        set_global_seed(42)
        values = np.random.normal(10, 2, 100)

        # 95% CI
        _, ci_95_lower, ci_95_upper, _ = calculate_bootstrap_ci(
            values=values,
            n_resamples=1000,
            confidence_level=0.95,
            seed=42
        )

        # 99% CI (should be wider)
        _, ci_99_lower, ci_99_upper, _ = calculate_bootstrap_ci(
            values=values,
            n_resamples=1000,
            confidence_level=0.99,
            seed=42
        )

        assert (ci_99_lower <= ci_95_lower), "99% CI lower should be <= 95% CI lower"
        assert (ci_95_upper <= ci_99_upper), "99% CI upper should be >= 95% CI upper"

    def test_reproducibility(self):
        """Test that results are reproducible with same seed."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]

        mean1, ci1_lower, ci1_upper, _ = calculate_bootstrap_ci(
            values=values,
            n_resamples=1000,
            seed=123
        )

        mean2, ci2_lower, ci2_upper, _ = calculate_bootstrap_ci(
            values=values,
            n_resamples=1000,
            seed=123
        )

        assert mean1 == mean2, "Means should be identical with same seed"
        assert ci1_lower == ci2_lower, "CI lower should be identical with same seed"
        assert ci1_upper == ci2_upper, "CI upper should be identical with same seed"


class TestRunBootstrapAnalysis:
    """Tests for the full analysis pipeline."""

    def test_run_analysis_creates_output(self, tmp_path):
        """Test that analysis creates output file."""
        # Create a minimal merged data file
        merged_data = [
            ['participant_id', 'metric', 'timepoint', 'value'],
            ['P001', 'SART', 'baseline', 12.0],
            ['P001', 'SART', 'post', 8.0],
            ['P002', 'SART', 'baseline', 15.0],
            ['P002', 'SART', 'post', 10.0],
        ]

        input_file = tmp_path / 'merged_data.csv'
        output_file = tmp_path / 'bootstrap_results.json'

        with open(input_file, 'w') as f:
            for row in merged_data:
                f.write(','.join(map(str, row)) + '\n')

        # Run analysis
        results = run_bootstrap_analysis(
            input_path=str(input_file),
            output_path=str(output_file),
            n_resamples=100,  # Small for test speed
            seed=42
        )

        # Check output file exists
        assert output_file.exists(), "Output file should be created"

        # Check results
        assert len(results) > 0, "Should have at least one result"
        assert results[0]['metric'] == 'SART'
        assert not results[0]['convergence_failed']

    def test_convergence_detection(self, tmp_path):
        """Test that convergence failures are detected."""
        # Create data that might cause issues
        merged_data = [
            ['participant_id', 'metric', 'timepoint', 'value'],
            ['P001', 'SART', 'baseline', 12.0],
            ['P001', 'SART', 'post', 12.0],  # No change
        ]

        input_file = tmp_path / 'merged_data.csv'
        output_file = tmp_path / 'bootstrap_results.json'

        with open(input_file, 'w') as f:
            for row in merged_data:
                f.write(','.join(map(str, row)) + '\n')

        results = run_bootstrap_analysis(
            input_path=str(input_file),
            output_path=str(output_file),
            n_resamples=100,
            seed=42
        )

        # Should still work (constant difference is fine)
        assert len(results) == 1
        assert results[0]['metric'] == 'SART'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])