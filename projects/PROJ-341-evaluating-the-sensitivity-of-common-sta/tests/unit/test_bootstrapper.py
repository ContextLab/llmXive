import pytest
import numpy as np
import pandas as pd
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

# Import the module under test
from code.analysis.bootstrapper import (
    bootstrap_power_estimate,
    calculate_ks_distance,
    run_bootstrapped_validation,
    save_power_results
)

class TestBootstrapPowerEstimate:
    def test_empty_pvalues_raises(self):
        with pytest.raises(ValueError):
            bootstrap_power_estimate(pd.Series([]), alpha=0.05)

    def test_bootstrap_returns_expected_structure(self):
        # Create a deterministic set of p-values
        np.random.seed(42)
        pvals = pd.Series(np.random.uniform(0, 1, 1000))
        
        result = bootstrap_power_estimate(pvals, alpha=0.05, n_bootstrap=100)
        
        assert "mean_power" in result
        assert "std_error" in result
        assert "ci_95_lower" in result
        assert "ci_95_upper" in result
        assert "n_bootstrap" in result
        assert result["n_bootstrap"] == 100
        assert 0 <= result["mean_power"] <= 1

    def test_power_calculation_logic(self):
        # Create p-values where exactly 50% are < 0.05
        pvals = pd.Series([0.01] * 50 + [0.5] * 50)
        result = bootstrap_power_estimate(pvals, alpha=0.05, n_bootstrap=1000)
        
        # With 1000 bootstraps, mean should be very close to 0.5
        assert abs(result["mean_power"] - 0.5) < 0.05

class TestCalculateKsDistance:
    def test_empty_arrays_raises(self):
        with pytest.raises(ValueError):
            calculate_ks_distance(np.array([]), np.array([1, 2, 3]))
        
        with pytest.raises(ValueError):
            calculate_ks_distance(np.array([1, 2, 3]), np.array([]))

    def test_identical_distributions(self):
        data = np.array([1, 2, 3, 4, 5])
        dist = calculate_ks_distance(data, data)
        assert dist == 0.0

    def test_different_distributions(self):
        dist1 = np.random.normal(0, 1, 1000)
        dist2 = np.random.normal(2, 1, 1000)
        
        ks = calculate_ks_distance(dist1, dist2)
        assert 0 < ks <= 1.0

class TestRunBootstrappedValidation:
    @patch('code.analysis.bootstrapper.load_real_data_pvalues')
    @patch('code.analysis.bootstrapper.load_p_values_raw')
    def test_validation_flow(self, mock_sim_load, mock_real_load):
        # Mock real data
        real_df = pd.DataFrame({
            "test_type": ["t-test", "t-test", "t-test", "t-test"],
            "sample_size": [50, 50, 50, 50],
            "p_value": [0.01, 0.04, 0.06, 0.8]
        })
        mock_real_load.return_value = real_df

        # Mock simulated data
        sim_df = pd.DataFrame({
            "test_type": ["t-test", "t-test", "t-test", "t-test"],
            "sample_size": [50, 50, 50, 50],
            "p_value": [0.02, 0.03, 0.05, 0.9]
        })
        mock_sim_load.return_value = sim_df

        results = run_bootstrapped_validation(
            real_data_file="dummy.csv",
            simulated_data_file="dummy_sim.csv",
            n_bootstrap=50,
            ks_threshold=0.10
        )

        assert "validation_status" in results
        assert "details" in results
        assert len(results["details"]) > 0

class TestSavePowerResults:
    def test_save_to_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_output.json")
            results = {"test": "data", "value": 123}
            
            save_power_results(results, output_path)
            
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert loaded == results
