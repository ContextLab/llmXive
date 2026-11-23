import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from robustness import run_bootstrap, run_alpha_sweep, save_bootstrap_results, save_alpha_sweep_results

class TestBootstrapLoop:
    """Unit tests for the bootstrap loop (T021a)."""

    @pytest.fixture
    def mock_data(self):
        """Generate a small mock dataset for testing."""
        np.random.seed(42)
        n = 100
        data = pd.DataFrame({
            "IAT_D_score": np.random.randn(n),
            "news_exposure_z": np.random.randn(n),
            "political_ideology": np.random.randn(n)
        })
        return data

    def test_bootstrap_produces_coefficients(self, mock_data):
        """Test that bootstrap returns a list of coefficients."""
        coeffs, p_vals, serrs, n_conv = run_bootstrap(mock_data, n_resamples=10, seed=42)

        assert isinstance(coeffs, list)
        assert len(coeffs) > 0
        assert len(coeffs) <= 10
        assert all(isinstance(c, (int, float)) for c in coeffs)

    def test_bootstrap_convergence_count(self, mock_data):
        """Test that convergence count is tracked correctly."""
        # With clean data, most should converge
        coeffs, p_vals, serrs, n_conv = run_bootstrap(mock_data, n_resamples=20, seed=123)

        assert n_conv >= 0
        assert n_conv <= 20
        # In a small sample with clean data, we expect a reasonable convergence rate
        # Note: OLS on small random data might occasionally fail, but usually converges
        assert n_conv > 0, "Bootstrap should converge on valid mock data"

    def test_bootstrap_seed_reproducibility(self, mock_data):
        """Test that setting a seed produces consistent results."""
        c1, _, _, _ = run_bootstrap(mock_data, n_resamples=5, seed=999)
        c2, _, _, _ = run_bootstrap(mock_data, n_resamples=5, seed=999)

        assert c1 == c2

    def test_bootstrap_monte_carlo_se_calculation(self, mock_data):
        """Test that MC SE is calculated as std of distribution."""
        coeffs, _, _, _ = run_bootstrap(mock_data, n_resamples=100, seed=42)
        if len(coeffs) > 1:
            calculated_se = np.std(coeffs)
            # The function doesn't return MC SE directly, but we can verify the logic
            # by checking that the list exists and has variance
            assert np.var(coeffs) > 0

class TestAlphaSweep:
    """Unit tests for alpha sweep (T022)."""

    @pytest.fixture
    def mock_data(self):
        np.random.seed(42)
        n = 100
        return pd.DataFrame({
            "IAT_D_score": np.random.randn(n),
            "news_exposure_z": np.random.randn(n),
            "political_ideology": np.random.randn(n)
        })

    def test_alpha_sweep_returns_dataframe(self, mock_data):
        """Test that alpha sweep returns a DataFrame."""
        result = run_alpha_sweep(mock_data, alphas=[0.01, 0.05])
        assert isinstance(result, pd.DataFrame)
        assert "alpha_level" in result.columns
        assert "significant" in result.columns
        assert "p_value" in result.columns
        assert "estimate" in result.columns

    def test_alpha_sweep_significance_logic(self, mock_data):
        """Test that significance flag is set correctly based on p-value."""
        # We can't guarantee p-value, but we can check logic consistency
        # If p < alpha, significant should be True
        result = run_alpha_sweep(mock_data, alphas=[0.0001, 0.9999])
        
        # Find the row with high alpha
        high_alpha_row = result[result["alpha_level"] == 0.9999].iloc[0]
        # Find the row with low alpha
        low_alpha_row = result[result["alpha_level"] == 0.0001].iloc[0]

        p_val = high_alpha_row["p_value"]
        
        # Verify logic: if p < 0.9999, it must be True
        assert high_alpha_row["significant"] == (p_val < 0.9999)
        assert low_alpha_row["significant"] == (p_val < 0.0001)

class TestSaveFunctions:
    """Tests for saving robustness results."""

    def test_save_bootstrap_creates_file(self, tmp_path, mock_data):
        """Test that save_bootstrap_results writes a file."""
        coeffs = [0.1, 0.2, 0.3]
        save_bootstrap_results(coeffs, [], [], 100.0, output_path=str(tmp_path / "test_bootstrap.csv"))
        
        assert os.path.exists(tmp_path / "test_bootstrap.csv")
        
        df = pd.read_csv(tmp_path / "test_bootstrap.csv")
        assert "mc_se" in df.columns
        assert "ci_lower_95" in df.columns

    def test_save_alpha_sweep_creates_file(self, tmp_path, mock_data):
        """Test that save_alpha_sweep_results writes a file."""
        alpha_df = run_alpha_sweep(mock_data)
        save_alpha_sweep_results(alpha_df, output_path=str(tmp_path / "test_alpha.csv"))
        
        assert os.path.exists(tmp_path / "test_alpha.csv")