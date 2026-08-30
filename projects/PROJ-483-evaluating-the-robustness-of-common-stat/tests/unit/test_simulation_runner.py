import pytest
import numpy as np
from scipy import stats
from simulation_runner import run_single_replication, SimulationError

@pytest.fixture
def clean_seed():
    np.random.seed(42)
    yield

class TestNullHypothesisConstruction:
    def test_null_hypothesis_uniform_pvalues(self, clean_seed):
        """Verify that p-values are uniform under r=0 (true null)."""
        n_replications = 1000
        p_values = []

        for _ in range(n_replications):
            # Run a single replication with r=0 (no dependency)
            p_val = run_single_replication(
                test_type="t-test",
                dependency_type="ar1",
                dependency_strength=0.0,
                n_samples=50,
                seed=42
            )
            p_values.append(p_val)

        # Kolmogorov-Smirnov test for uniformity
        ks_stat, p_val_ks = stats.kstest(p_values, 'uniform')
        
        # We expect p-values to be uniform, so the KS test p-value should be high (> 0.05)
        assert p_val_ks > 0.05, f"P-values are not uniform under null: KS p-value = {p_val_ks}"

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

class TestEdgeCases:
    def test_small_sample_size_handling(self, clean_seed):
        """Test handling of small sample sizes (N < 50)."""
        # This test assumes the runner raises an error or handles small N gracefully
        # Depending on implementation, this might raise SimulationError or return a specific value
        with pytest.raises(SimulationError):
            run_single_replication(
                test_type="t-test",
                dependency_type="ar1",
                dependency_strength=0.0,
                n_samples=10,  # Too small
                seed=42
            )
