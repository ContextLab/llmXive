"""
Tests for User Story 2: Distribution Fitting and Goodness-of-Fit Testing.
Includes contract tests and integration tests for fit_distributions.py.
"""
import csv
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.fit_distributions import fit_distribution, process_game, load_config
from scripts.utils.checkpoint import save_checkpoint, load_checkpoint
from scripts.validate_distribution_fits import load_schema, validate_row, validate_distribution_fits

class TestDistributionFitting(unittest.TestCase):

    def setUp(self):
        self.test_data_dir = tempfile.mkdtemp()
        self.mock_game_id = "test-game"
        # Generate synthetic data for testing the logic (not for production)
        # Using a log-normal distribution for the mock
        self.mock_run_times = [float(x) for x in [100, 105, 110, 120, 130, 150, 200, 250, 300, 400]]
        
    def tearDown(self):
        # Cleanup temp files if any
        pass

    def test_fit_distribution_lognormal_success(self):
        """Test that log-normal fitting returns valid parameters and stats."""
        # Generate a larger dataset that definitely fits log-normal
        data = [float(x) for x in [100, 102, 105, 110, 120, 130, 150, 180, 200, 250, 300, 400, 500, 600, 700]]
        
        params, ks_stat, p_val, aic = fit_distribution(data, "lognormal")
        
        self.assertIsNotNone(params)
        self.assertIn("s", params)
        self.assertIn("scale", params)
        self.assertGreater(ks_stat, 0)
        self.assertLessEqual(p_val, 1.0)
        self.assertGreater(aic, -float('inf'))

    def test_fit_distribution_invalid_data(self):
        """Test fitting with insufficient data returns None."""
        data = [100.0]
        params, ks_stat, p_val, aic = fit_distribution(data, "lognormal")
        self.assertIsNone(params)

    def test_process_game_low_sample(self):
        """Test that games with < min_sample are flagged as excluded."""
        min_sample = 100
        small_data = [100.0] * 50  # 50 runs
        
        results = process_game("small-game", small_data, min_sample)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "excluded_low_sample")
        self.assertEqual(results[0]["game_id"], "small-game")

    def test_process_game_valid_sample(self):
        """Test that games with >= min_sample produce fit results."""
        min_sample = 10
        # Create a dataset of 100 log-normal-like values
        data = [float(100 + i*10 + (i%5)*5) for i in range(100)]
        
        results = process_game("valid-game", data, min_sample)
        
        # Should have 3 results (lognormal, weibull, gamma)
        self.assertEqual(len(results), 3)
        
        # Check structure
        for res in results:
            self.assertIn("distribution_family", res)
            self.assertIn("KS_D", res)
            self.assertIn("KS_pvalue", res)
            self.assertIn("AIC", res)
            self.assertIn("best_fit", res)

    def test_contract_validation_structure(self):
        """
        Contract test: Verify output structure matches distribution_fit.schema.yaml
        """
        min_sample = 5
        data = [float(100 + i*10) for i in range(10)]
        
        results = process_game("contract-test", data, min_sample)
        
        required_fields = [
            "game_id", "sample_size", "status", "distribution_family",
            "parameters", "KS_D", "KS_pvalue", "AIC", "best_fit"
        ]
        
        for res in results:
            for field in required_fields:
                self.assertIn(field, res, f"Missing field {field} in result: {res}")

    def test_schema_contract_validation_integration(self):
        """
        Contract test: Validate that the actual output CSV from fit_distributions
        strictly adheres to the fields defined in contracts/distribution_fit.schema.yaml.
        This ensures data integrity before downstream consumption (e.g., T027).
        """
        # 1. Prepare a small valid dataset
        min_sample = 5
        data = [float(100 + i*10) for i in range(10)]
        
        # 2. Generate results using the actual process_game function
        results = process_game("schema-test-game", data, min_sample)
        
        # 3. Write results to a temporary CSV file
        temp_csv_path = os.path.join(self.test_data_dir, "temp_fits.csv")
        with open(temp_csv_path, 'w', newline='') as f:
            if results:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
        
        # 4. Load the schema
        schema_path = "contracts/distribution_fit.schema.yaml"
        # If schema doesn't exist in test env, we skip or create a mock check
        # However, the task requires validating against the REAL schema file.
        # We assume T005 created it.
        try:
            schema = load_schema(schema_path)
        except FileNotFoundError:
            self.skipTest(f"Schema file not found at {schema_path}. Ensure T005 is complete.")
            return

        # 5. Validate the generated CSV against the schema
        # validate_distribution_fits returns a report dict
        report = validate_distribution_fits(temp_csv_path, schema)
        
        # 6. Assert that validation passed
        self.assertTrue(report["valid"], f"Schema validation failed: {report.get('errors', [])}")
        self.assertEqual(report["total_rows"], len(results))
        self.assertEqual(report["valid_rows"], len(results))
        self.assertEqual(report["invalid_rows"], 0)

    def test_integration_single_game_ks_goodness_of_fit(self):
        """
        Integration test for distribution fitting on a single game (KS p >= 0.05 check).
        This verifies that the fitting pipeline correctly identifies a good fit
        when the data actually follows the assumed distribution.
        
        This test uses synthetic data that is mathematically guaranteed to fit
        a log-normal distribution well, ensuring the KS test logic is correct.
        """
        # 1. Create a dataset that is explicitly log-normal distributed
        # We generate log-normal data using scipy.stats.lognorm
        # This ensures the KS test should pass (p >= 0.05) for log-normal fit
        import math
        from scipy.stats import lognorm
        
        # Generate 200 samples from a log-normal distribution
        # s=0.5, scale=100 (median ~100)
        rng = 42
        n_samples = 200
        data = list(lognorm.rvs(s=0.5, scale=100, size=n_samples, random_state=rng))
        data = [float(x) for x in data]
        
        # 2. Run the distribution fitting process for this "game"
        min_sample = 50
        game_id = "integration-test-game"
        
        results = process_game(game_id, data, min_sample)
        
        # 3. Verify we got results for all three distributions
        self.assertEqual(len(results), 3, "Should have results for lognormal, weibull, and gamma")
        
        # 4. Find the log-normal result
        lognormal_result = next((r for r in results if r["distribution_family"] == "lognormal"), None)
        self.assertIsNotNone(lognormal_result, "Log-normal result should exist")
        
        # 5. Verify the KS test passed (p-value >= 0.05)
        # This is the core assertion: if data is truly log-normal, the fit should be good
        ks_pvalue = float(lognormal_result["KS_pvalue"])
        self.assertGreaterEqual(ks_pvalue, 0.05, 
            f"KS test p-value ({ks_pvalue}) should be >= 0.05 for a good fit. "
            f"Data was generated from a log-normal distribution.")
        
        # 6. Verify the KS statistic is reasonable (should be small for good fit)
        ks_stat = float(lognormal_result["KS_D"])
        self.assertLess(ks_stat, 0.15, 
            f"KS statistic ({ks_stat}) should be small for a good fit. "
            f"Expected < 0.15 for n=200 and p>=0.05")
        
        # 7. Verify the log-normal is selected as the best fit (lowest AIC)
        best_fit = lognormal_result["best_fit"]
        self.assertTrue(best_fit, "Log-normal should be the best fit for log-normal data")
        
        # 8. Verify the result structure matches the contract
        self.assertIn("game_id", lognormal_result)
        self.assertIn("sample_size", lognormal_result)
        self.assertIn("parameters", lognormal_result)
        self.assertIn("AIC", lognormal_result)
        self.assertEqual(lognormal_result["game_id"], game_id)
        self.assertEqual(lognormal_result["sample_size"], n_samples)

    def test_integration_single_game_ks_rejection(self):
        """
        Integration test verifying that distributions are correctly rejected
        when the data does NOT follow the assumed distribution (KS p < 0.05).
        
        We use uniform data which should NOT fit a log-normal distribution well.
        """
        # 1. Create a dataset that is uniformly distributed (not log-normal)
        n_samples = 200
        data = [float(50 + i * 0.5) for i in range(n_samples)]
        
        # 2. Run the distribution fitting process
        min_sample = 50
        game_id = "integration-test-reject"
        
        results = process_game(game_id, data, min_sample)
        
        # 3. Find the log-normal result
        lognormal_result = next((r for r in results if r["distribution_family"] == "lognormal"), None)
        self.assertIsNotNone(lognormal_result, "Log-normal result should exist even if fit is bad")
        
        # 4. Verify the KS test failed (p-value < 0.05)
        # Uniform data should NOT fit log-normal well
        ks_pvalue = float(lognormal_result["KS_pvalue"])
        self.assertLess(ks_pvalue, 0.05, 
            f"KS test p-value ({ks_pvalue}) should be < 0.05 for a poor fit. "
            f"Data was uniformly distributed, not log-normal.")
        
        # 5. Verify the log-normal is NOT the best fit
        best_fit = lognormal_result["best_fit"]
        self.assertFalse(best_fit, "Log-normal should NOT be the best fit for uniform data")

if __name__ == '__main__':
    unittest.main()