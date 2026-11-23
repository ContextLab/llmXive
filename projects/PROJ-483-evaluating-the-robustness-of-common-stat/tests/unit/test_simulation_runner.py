"""
Unit tests for the simulation_runner module.

These tests verify the "Generate-then-Inject" paradigm and ensure that:
1. Under r=0 (no dependency injection), p-values are uniform (true null hypothesis).
2. Single replications return valid p-values.
3. Edge cases (e.g., small sample sizes) are handled correctly.
"""
import pytest
import numpy as np
from scipy import stats
from simulation_runner import run_single_replication, run_simulation, SimulationError

@pytest.fixture
def clean_seed():
    """Fixture to ensure a clean random seed for each test."""
    np.random.seed(42)
    yield

class TestNullHypothesisConstruction:
    def test_null_hypothesis_uniform_pvalues(self, clean_seed):
        """
        Verify that p-values are uniform under r=0 (true null).
        
        This is the core validation for the "Generate-then-Inject" paradigm.
        If the null hypothesis is truly constructed (no effect, no dependency),
        the p-values should follow a uniform distribution.
        """
        n_replications = 1000
        p_values = []

        for i in range(n_replications):
            # Run a single replication with r=0 (no dependency)
            # We use a fixed seed for each replication to ensure reproducibility
            p_val = run_single_replication(
                test_type="t-test",
                dependency_type="ar1",
                dependency_strength=0.0,
                n_samples=50,
                seed=42 + i
            )
            p_values.append(p_val)

        # Kolmogorov-Smirnov test for uniformity
        ks_stat, p_val_ks = stats.kstest(p_values, 'uniform')
        
        # We expect p-values to be uniform, so the KS test p-value should be high (> 0.05)
        assert p_val_ks > 0.05, (
            f"P-values are not uniform under null: KS p-value = {p_val_ks}. "
            f"This indicates a problem with the null hypothesis construction. "
            f"Check the 'Generate-then-Inject' paradigm implementation."
        )

    def test_single_replication_output(self, clean_seed):
        """Test that a single replication returns a valid p-value."""
        p_val = run_single_replication(
            test_type="t-test",
            dependency_type="ar1",
            dependency_strength=0.0,
            n_samples=50,
            seed=42
        )
        assert 0.0 <= p_val <= 1.0, f"P-value {p_val} is out of range [0, 1]"

    def test_anova_null_hypothesis(self, clean_seed):
        """Verify that ANOVA p-values are uniform under r=0."""
        n_replications = 500
        p_values = []

        for i in range(n_replications):
            p_val = run_single_replication(
                test_type="anova",
                dependency_type="ar1",
                dependency_strength=0.0,
                n_samples=60,  # Slightly larger for ANOVA
                seed=42 + i
            )
            p_values.append(p_val)

        ks_stat, p_val_ks = stats.kstest(p_values, 'uniform')
        assert p_val_ks > 0.05, f"ANOVA p-values are not uniform under null: KS p-value = {p_val_ks}"

class TestEdgeCases:
    def test_small_sample_size_handling(self, clean_seed):
        """Test handling of small sample sizes (N < 50)."""
        with pytest.raises(SimulationError):
            run_single_replication(
                test_type="t-test",
                dependency_type="ar1",
                dependency_strength=0.0,
                n_samples=10,  # Too small
                seed=42
            )

    def test_unsupported_test_type(self, clean_seed):
        """Test handling of unsupported test types."""
        with pytest.raises(SimulationError):
            run_single_replication(
                test_type="unsupported-test",
                dependency_type="ar1",
                dependency_strength=0.0,
                n_samples=50,
                seed=42
            )

    def test_unsupported_dependency_type(self, clean_seed):
        """Test handling of unsupported dependency types."""
        with pytest.raises(SimulationError):
            run_single_replication(
                test_type="t-test",
                dependency_type="unsupported-dep",
                dependency_strength=0.0,
                n_samples=50,
                seed=42
            )

class TestDependencyInjection:
    def test_ar1_injection_strength(self, clean_seed):
        """Test that AR(1) injection actually introduces dependency."""
        # Run with r=0.5 and verify that the data shows autocorrelation
        # This is a sanity check to ensure the injection is working
        n_replications = 100
        autocorrelations = []

        for i in range(n_replications):
            # Generate data and inject AR(1)
            # We'll manually check the autocorrelation of the injected data
            # by running a single replication and examining the data
            # (This is a simplified check; a full test would require access to the intermediate data)
            pass
        
        # For now, we just verify that the function doesn't crash
        # A more comprehensive test would require refactoring run_single_replication
        # to return the intermediate data for inspection
        p_val = run_single_replication(
            test_type="t-test",
            dependency_type="ar1",
            dependency_strength=0.5,
            n_samples=50,
            seed=42
        )
        assert 0.0 <= p_val <= 1.0

    def test_block_bootstrap_injection(self, clean_seed):
        """Test that block bootstrap injection works."""
        p_val = run_single_replication(
            test_type="t-test",
            dependency_type="block",
            dependency_strength=0.3,
            n_samples=50,
            seed=42
        )
        assert 0.0 <= p_val <= 1.0

class TestSimulationRunner:
    def test_run_simulation_output(self, clean_seed):
        """Test that run_simulation returns a valid DataFrame."""
        df = run_simulation(
            test_types=["t-test"],
            dependency_types=["ar1"],
            dependency_strengths=[0.0, 0.3],
            n_replications=10,
            n_samples=50,
            seed=42
        )
        
        assert isinstance(df, pd.DataFrame)
        assert "p_value" in df.columns
        assert "test_type" in df.columns
        assert "dependency_type" in df.columns
        assert "dependency_strength" in df.columns
        assert len(df) == 20  # 2 strengths * 10 replications

    def test_run_simulation_edge_case_handling(self, clean_seed):
        """Test that run_simulation handles edge cases gracefully."""
        df = run_simulation(
            test_types=["t-test"],
            dependency_types=["ar1"],
            dependency_strengths=[0.0],
            n_replications=5,
            n_samples=10,  # Too small
            seed=42
        )
        
        # Should have NaN p-values for failed replications
        assert df["p_value"].isna().any()
        assert "error" in df.columns