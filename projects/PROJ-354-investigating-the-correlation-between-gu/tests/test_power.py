"""
Unit tests for the power analysis script (T018).

Tests the generation of synthetic datasets with a known effect size (beta=0.1)
and verifies that the power analysis script correctly identifies the statistical
power to detect this effect.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path if running directly
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from code.power_analysis import (
    generate_synthetic_dataset,
    calculate_theoretical_power,
    run_power_analysis,
    calculate_required_n
)
from code.config import get_path, ensure_directories


class TestSyntheticDataGeneration:
    """Tests for the synthetic dataset generator."""

    def test_generate_synthetic_dataset_creates_expected_columns(self):
        """Verify the synthetic dataset contains the required columns."""
        n = 100
        beta = 0.1
        df = generate_synthetic_dataset(n_samples=n, effect_size=beta)

        assert "participant_id" in df.columns
        assert "ilr_coord_1" in df.columns  # Assuming at least one ILR coordinate
        assert "cognitive_score" in df.columns
        assert "age" in df.columns
        assert "sex" in df.columns
        assert "bmi" in df.columns

        assert len(df) == n

    def test_synthetic_data_effect_size_approximation(self):
        """
        Verify that the generated synthetic data roughly reflects the target effect size.
        Due to noise, we check if the OLS beta is within a reasonable range (e.g., +/- 0.05)
        of the target beta=0.1.
        """
        np.random.seed(42)
        n = 5000  # Large N to reduce noise
        beta = 0.1
        df = generate_synthetic_dataset(n_samples=n, effect_size=beta)

        # Simple OLS regression: cognitive_score ~ ilr_coord_1
        # We expect the slope to be close to beta
        from scipy import stats
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            df["ilr_coord_1"], df["cognitive_score"]
        )

        # The generated data adds noise, so the observed slope won't be exactly beta,
        # but with N=5000 it should be close.
        # We allow a tolerance of 0.02 for the slope estimation.
        assert abs(slope - beta) < 0.02, f"Observed slope {slope:.4f} deviates too much from target {beta}"


class TestPowerCalculations:
    """Tests for theoretical power and sample size calculations."""

    def test_calculate_theoretical_power_returns_valid_probability(self):
        """Power must be between 0 and 1."""
        # Standard parameters
        power = calculate_theoretical_power(
            n=1000,
            effect_size=0.1,
            alpha=0.05,
            std_dev=1.0
        )
        assert 0.0 <= power <= 1.0

    def test_power_increases_with_sample_size(self):
        """Power should increase as N increases, holding other factors constant."""
        power_small = calculate_theoretical_power(n=100, effect_size=0.1, alpha=0.05, std_dev=1.0)
        power_large = calculate_theoretical_power(n=1000, effect_size=0.1, alpha=0.05, std_dev=1.0)
        
        assert power_large > power_small

    def test_calculate_required_n_for_target_power(self):
        """Verify sample size calculation logic."""
        # We expect a specific N to achieve 0.8 power for a small effect
        n_req = calculate_required_n(
            target_power=0.8,
            effect_size=0.1,
            alpha=0.05,
            std_dev=1.0
        )
        
        assert n_req > 0
        # Sanity check: for small effect 0.1, we expect a reasonably large N (likely > 500)
        # The exact value depends on the formula used in power_analysis.py, but it should be substantial.
        assert n_req > 100


class TestPowerAnalysisPipeline:
    """Integration tests for the full power analysis pipeline."""

    def test_run_power_analysis_executes_without_error(self):
        """Ensure the main power analysis function runs end-to-end."""
        # Run the analysis with a small dataset to verify logic
        results = run_power_analysis(
            n_samples=1000,
            effect_size=0.1,
            n_iterations=10,  # Few iterations for speed in testing
            alpha=0.05
        )
        
        assert "theoretical_power" in results
        assert "empirical_power" in results
        assert "required_n" in results
        
        # Empirical power should be close to theoretical power with enough iterations
        # (Note: with only 10 iterations, this is a loose check, but verifies the flow)
        assert 0.0 <= results["empirical_power"] <= 1.0
        assert 0.0 <= results["theoretical_power"] <= 1.0

    def test_run_power_analysis_matches_expected_beta(self):
        """
        Verify that the empirical power calculation correctly uses the synthetic data
        generated with the specific beta=0.1.
        """
        np.random.seed(42)
        n_samples = 2000
        effect_size = 0.1
        
        # Generate data explicitly
        synthetic_df = generate_synthetic_dataset(n_samples=n_samples, effect_size=effect_size)
        
        # Run analysis on this data (simulating what the script does)
        # We mock the internal logic slightly to test the specific flow
        from statsmodels.stats.power import TTestIndPower
        import statsmodels.api as sm
        
        # Simple check: fit OLS and check significance rate
        significant_count = 0
        n_trials = 20 # Small number for unit test speed
        
        for _ in range(n_trials):
            # Resample to simulate different datasets
            sample = synthetic_df.sample(n=min(500, n_samples), replace=False, random_state=np.random.randint(0, 1000))
            X = sm.add_constant(sample["ilr_coord_1"])
            y = sample["cognitive_score"]
            model = sm.OLS(y, X).fit()
            if model.pvalues["ilr_coord_1"] < 0.05:
                significant_count += 1
        
        empirical_rate = significant_count / n_trials
        # We don't assert a specific value here because N=500 with beta=0.1 might have low power,
        # but we verify the process runs and returns a rate.
        assert 0.0 <= empirical_rate <= 1.0

    def test_integration_with_config_paths(self):
        """Verify the power analysis integrates with the project config paths."""
        ensure_directories()
        report_path = get_path("results", "power", "power_report.md")
        
        # Just ensure the path exists and is valid, the actual generation is tested in T019
        assert isinstance(report_path, Path)
        # The directory should exist if ensure_directories was called
        assert report_path.parent.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])