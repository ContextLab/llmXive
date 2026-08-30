import pytest
import numpy as np
from scipy import stats
from dependency_injector import ar1_inject, validate_ar1_injection, block_bootstrap, validate_block_bootstrap

@pytest.fixture
def clean_seed():
    np.random.seed(42)
    yield
    np.random.seed(42)

class TestAR1Injection:
    def test_ar1_injection_matches_target(self, clean_seed):
        """Test that injected AR(1) autocorrelation matches target r within 5% tolerance."""
        n = 1000
        r_target = 0.5
        data = np.random.randn(n)

        injected_data = ar1_inject(data, r=r_target, seed=42)

        # Calculate actual autocorrelation at lag 1
        actual_r = np.corrcoef(injected_data[:-1], injected_data[1:])[0, 1]

        # Validate within 5% tolerance
        assert validate_ar1_injection(injected_data, r_target, tolerance=0.05), \
            f"Actual r ({actual_r:.3f}) deviates more than 5% from target ({r_target})"

    def test_ar1_injection_zero_r(self, clean_seed):
        """Test that r=0 returns data with near-zero autocorrelation."""
        n = 1000
        data = np.random.randn(n)
        injected_data = ar1_inject(data, r=0.0, seed=42)

        actual_r = np.corrcoef(injected_data[:-1], injected_data[1:])[0, 1]
        assert abs(actual_r) < 0.05, f"Expected near-zero autocorrelation, got {actual_r}"

class TestBlockBootstrap:
    def test_block_bootstrap_structure(self, clean_seed):
        """Test that block bootstrap preserves block structure."""
        n = 100
        block_size = 10
        data = np.arange(n)  # Use sequential data to verify block preservation

        # Run block bootstrap
        resampled_indices = block_bootstrap(n, block_size=block_size, seed=42)
        resampled_data = data[resampled_indices]

        # Verify that the resampled data contains blocks of the original size
        # (This is a simplified check; a full validation would check distribution of block sizes)
        assert len(resampled_data) == n, "Resampled data length must match original"

    def test_block_bootstrap_validation(self, clean_seed):
        """Test validation logic for block bootstrap."""
        n = 100
        block_size = 10
        data = np.random.randn(n)

        resampled_indices = block_bootstrap(n, block_size=block_size, seed=42)
        resampled_data = data[resampled_indices]

        # Validation should pass for a correctly implemented bootstrap
        assert validate_block_bootstrap(resampled_data, block_size, tolerance=0.1), \
            "Block bootstrap validation failed unexpectedly"
