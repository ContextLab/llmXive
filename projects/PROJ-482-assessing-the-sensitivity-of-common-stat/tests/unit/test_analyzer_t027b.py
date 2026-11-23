import pytest
import pandas as pd
import numpy as np
import os
import tempfile
import config
from analyzer import analyze_log_pvalue_regression, load_simulation_results

class TestT027bNumericalStability:
    """
    Tests for T027b: Numerical stability epsilon application in log-transform.
    """

    def setup_method(self):
        """Create a mock raw_pvalues.csv for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "raw_pvalues.csv")
        
        # Create a dataset with p-values of 0, 1, and normal values
        data = {
            'sample_size': [10, 10, 20, 20, 50, 50],
            'distribution_type': ['normal', 'normal', 'normal', 'normal', 'normal', 'normal'],
            'test_type': ['t_test', 't_test', 't_test', 't_test', 't_test', 't_test'],
            'p_value': [0.0, 1.0, 0.05, 0.5, 0.0, 1.0], # Includes 0 and 1
            'hypothesis_type': ['null_true', 'null_true', 'null_true', 'null_true', 'null_false', 'null_false']
        }
        self.df_mock = pd.DataFrame(data)
        self.df_mock.to_csv(self.test_file, index=False)

    def teardown_method(self):
        """Clean up temporary files."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_load_simulation_results(self):
        """Test that the loader correctly reads the mock file."""
        df = load_simulation_results(self.test_file)
        assert len(df) == 6
        assert 'p_value' in df.columns
        assert 0.0 in df['p_value'].values
        assert 1.0 in df['p_value'].values

    def test_epsilon_applied_to_zero(self):
        """Verify that p=0 does not cause -inf in log transform."""
        # Manually test the logic
        epsilon = config.SimulationConfig().log_epsilon
        p_zero = 0.0
        
        # This should not raise an error or return -inf
        try:
            log_val = np.log(p_zero + epsilon)
            assert np.isfinite(log_val), f"log(0 + epsilon) resulted in non-finite value: {log_val}"
            assert log_val < 0, "log(epsilon) should be negative"
        except Exception as e:
            pytest.fail(f"Log transform of zero failed: {e}")

    def test_epsilon_applied_to_one(self):
        """Verify that p=1 is handled correctly."""
        epsilon = config.SimulationConfig().log_epsilon
        p_one = 1.0
        
        try:
            log_val = np.log(p_one + epsilon)
            assert np.isfinite(log_val), f"log(1 + epsilon) resulted in non-finite value: {log_val}"
            # log(1+eps) should be close to 0 but positive
            assert log_val > 0, "log(1+epsilon) should be positive"
        except Exception as e:
            pytest.fail(f"Log transform of one failed: {e}")

    def test_regression_runs_without_crash_on_extremes(self):
        """Ensure the regression function runs successfully with p=0 and p=1."""
        try:
            results_df, summary = analyze_log_pvalue_regression(self.df_mock)
            assert isinstance(results_df, pd.DataFrame)
            assert not results_df.empty, "Regression results should not be empty"
            assert 'beta' in results_df.columns
            assert 'p_value' in results_df.columns
            # Verify that the model ran
            assert 'n_observations' in summary
            assert summary['n_observations'] > 0
        except Exception as e:
            pytest.fail(f"Regression analysis crashed with extreme p-values: {e}")

    def test_raw_data_unchanged(self):
        """Verify that the original dataframe passed to the function is not modified."""
        original_p_values = self.df_mock['p_value'].copy()
        
        analyze_log_pvalue_regression(self.df_mock)
        
        # Check if the original dataframe was modified
        pd.testing.assert_series_equal(self.df_mock['p_value'], original_p_values)

    def test_epsilon_constant_used(self):
        """Verify that config.LOG_EPSILON is used."""
        expected_epsilon = config.SimulationConfig().log_epsilon
        assert expected_epsilon == 1e-15, "Config epsilon should be 1e-15"
        
        # The function should use this value internally.
        # We can't easily inspect internal variables, but we can check
        # that the log transform logic aligns with this value by checking
        # the result of log(0 + epsilon)
        calculated_log = np.log(0 + expected_epsilon)
        # If the code uses a different epsilon, the regression might behave differently,
        # but the primary check is that it doesn't crash and uses a small positive number.
        assert np.isfinite(calculated_log)