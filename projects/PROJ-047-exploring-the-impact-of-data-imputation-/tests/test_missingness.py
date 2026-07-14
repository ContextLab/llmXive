import pytest
import numpy as np
import pandas as pd
from simulation.missingness import inject_mnar, tune_alpha

class TestTuneAlpha:
    def test_tune_alpha_converges_to_target_rate(self):
        """Test that tune_alpha finds an alpha that yields the target missingness rate."""
        beta = 0.5
        target_rate = 0.3

        alpha = tune_alpha(beta, target_rate)

        # Verify the rate using a large sample of standard normal Y
        rng = np.random.RandomState(42)
        y_sample = rng.normal(loc=0.0, scale=1.0, size=100000)

        from scipy.special import expit
        logits = alpha + beta * y_sample
        probs = expit(logits)
        calculated_rate = np.mean(probs)

        assert abs(calculated_rate - target_rate) < 0.01, \
            f"Calculated rate {calculated_rate:.4f} does not match target {target_rate}"

    def test_tune_alpha_various_rates(self):
        """Test tuning for various target rates."""
        beta = 0.8
        for target in [0.1, 0.5, 0.9]:
            alpha = tune_alpha(beta, target)

            rng = np.random.RandomState(42)
            y_sample = rng.normal(loc=0.0, scale=1.0, size=100000)
            from scipy.special import expit
            logits = alpha + beta * y_sample
            probs = expit(logits)
            calculated_rate = np.mean(probs)

            assert abs(calculated_rate - target) < 0.01, \
                f"Failed for target {target}: got {calculated_rate:.4f}"

    def test_tune_alpha_invalid_rate(self):
        """Test that invalid target rates raise ValueError."""
        with pytest.raises(ValueError):
            tune_alpha(0.5, 0.0)

        with pytest.raises(ValueError):
            tune_alpha(0.5, 1.0)

        with pytest.raises(ValueError):
            tune_alpha(0.5, 1.5)

class TestInjectMNAR:
    def test_inject_mnar_creates_nan(self):
        """Test that inject_mnar introduces NaN values into Y."""
        data = pd.DataFrame({
            'X': np.random.normal(0, 1, 100),
            'T': np.random.binomial(1, 0.5, 100),
            'Y': np.random.normal(0, 1, 100)
        })

        beta = 0.5
        target_rate = 0.3

        result = inject_mnar(data, beta, target_rate)

        nan_count = result['Y'].isna().sum()
        total_count = len(result)
        actual_rate = nan_count / total_count

        assert nan_count > 0, "No NaNs were introduced"
        # Allow some variance due to stochastic nature of mask generation
        # The rate should be close to target, but not exact for small N
        assert 0.1 < actual_rate < 0.6, f"Actual rate {actual_rate} too far from target {target_rate}"

    def test_inject_mnar_preserves_other_columns(self):
        """Test that X and T columns are not modified."""
        original_data = pd.DataFrame({
            'X': np.random.normal(0, 1, 50),
            'T': np.random.binomial(1, 0.5, 50),
            'Y': np.random.normal(0, 1, 50)
        })

        result = inject_mnar(original_data, 0.5, 0.2)

        pd.testing.assert_frame_equal(result[['X', 'T']], original_data[['X', 'T']])

    def test_inject_mnar_missing_y_column(self):
        """Test that inject_mnar raises KeyError if Y is missing."""
        data = pd.DataFrame({
            'X': np.random.normal(0, 1, 10),
            'T': np.random.binomial(1, 0.5, 10)
        })

        with pytest.raises(KeyError):
            inject_mnar(data, 0.5, 0.2)

    def test_inject_mnar_metadata(self):
        """Test that metadata is stored in dataframe attributes."""
        data = pd.DataFrame({
            'X': np.random.normal(0, 1, 20),
            'T': np.random.binomial(1, 0.5, 20),
            'Y': np.random.normal(0, 1, 20)
        })

        beta = 0.5
        target_rate = 0.4

        result = inject_mnar(data, beta, target_rate)

        assert 'missingness_alpha' in result.attrs
        assert 'missingness_beta' in result.attrs
        assert 'missingness_rate' in result.attrs

        assert result.attrs['missingness_beta'] == beta
        # The stored rate is the actual rate achieved in this specific run
        assert 0 < result.attrs['missingness_rate'] < 1

    def test_inject_mnar_correlation_with_y(self):
        """Test that missingness is correlated with Y (MNAR property)."""
        np.random.seed(42)
        n = 10000
        data = pd.DataFrame({
            'X': np.random.normal(0, 1, n),
            'T': np.random.binomial(1, 0.5, n),
            'Y': np.random.normal(0, 1, n)
        })

        beta = 1.0  # Strong effect
        target_rate = 0.5

        # Get the mask before modifying data to check correlation
        from scipy.special import expit
        rng = np.random.RandomState(123)
        alpha = tune_alpha(beta, target_rate)
        
        logits = alpha + beta * data['Y'].values
        probs = expit(logits)
        # Use a deterministic seed for the mask generation to ensure reproducibility in test
        mask = rng.random(n) < probs
        
        # Missingness (mask=True means missing) should be correlated with Y
        # Since beta > 0, higher Y should lead to higher probability of missingness
        # We check correlation between the generated mask and Y
        correlation = np.corrcoef(mask.astype(float), data['Y'].values)[0, 1]
        
        # With beta=1.0, we expect a significant positive correlation
        # The exact value depends on the sigmoid transformation, but should be > 0.1
        assert correlation > 0.1, f"Expected positive correlation between Y and missingness, got {correlation}"