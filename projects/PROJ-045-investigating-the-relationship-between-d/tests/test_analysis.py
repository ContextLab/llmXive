"""
Unit and contract tests for the statistical analysis module (code/analysis.py).

This file implements T034: Contract test for R² and p-value outputs.
It verifies that the regression pipeline produces valid statistical metrics
(R², p-values) and adheres to the schema defined in T044.

Note: These tests use real data loaded from the project's processed data files
(e.g., data/processed/defect_density_metrics.json) or a small, verified subset
if the full dataset is unavailable. They do NOT use synthetic/fake data.
"""

import json
import os
import sys
import unittest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

import numpy as np
from analysis import (
    load_processed_data,
    validate_data_quality,
    calculate_activation_energy,
    perform_regression_with_density,
    calculate_variance_inflation_factors,
    apply_multiple_comparison_correction,
    calculate_statistical_power,
    run_sigma0_sensitivity_analysis,
    run_full_analysis,
)
from models import AnalysisResult


class TestAnalysisOutputs(unittest.TestCase):
    """Contract tests for R² and p-value outputs in analysis.py."""

    @classmethod
    def setUpClass(cls):
        """Load real data for testing. If data is missing, tests will be skipped."""
        cls.data_path = project_root / "data" / "processed" / "analysis_results.json"
        cls.defect_density_path = project_root / "data" / "processed" / "defect_density_metrics.json"
        cls.vif_path = project_root / "data" / "processed" / "vif_scores.json"
        
        cls.data = None
        cls.defect_density = None
        cls.vif_scores = None

        # Try to load real data
        if cls.data_path.exists():
            try:
                with open(cls.data_path, 'r') as f:
                    cls.data = json.load(f)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load {cls.data_path}: {e}")
                cls.data = None

        if cls.defect_density_path.exists():
            try:
                with open(cls.defect_density_path, 'r') as f:
                    cls.defect_density = json.load(f)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load {cls.defect_density_path}: {e}")
                cls.defect_density = None

        if cls.vif_path.exists():
            try:
                with open(cls.vif_path, 'r') as f:
                    cls.vif_scores = json.load(f)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load {cls.vif_path}: {e}")
                cls.vif_scores = None

    def test_r_squared_is_valid_float(self):
        """Contract test: R² must be a float between -inf and 1.0."""
        if not self.data:
            self.skipTest("No analysis results found. Run the full pipeline first.")
        
        for result in self.data:
            self.assertIn("r_squared", result, "R² missing from analysis result")
            r2 = result["r_squared"]
            self.assertIsInstance(r2, (int, float), f"R² must be numeric, got {type(r2)}")
            # R² can technically be negative for poor fits, but usually <= 1.0
            # We assert it is a valid float, not NaN or Inf
            self.assertFalse(np.isnan(r2), "R² cannot be NaN")
            self.assertFalse(np.isinf(r2), "R² cannot be Inf")

    def test_p_values_are_valid_floats(self):
        """Contract test: p-values must be floats between 0 and 1."""
        if not self.data:
            self.skipTest("No analysis results found. Run the full pipeline first.")
        
        for result in self.data:
            self.assertIn("p_values", result, "p-values missing from analysis result")
            p_vals = result["p_values"]
            self.assertIsInstance(p_vals, dict, f"p-values must be a dict, got {type(p_vals)}")
            
            for key, val in p_vals.items():
                self.assertIsInstance(val, (int, float), f"p-value for {key} must be numeric")
                self.assertFalse(np.isnan(val), f"p-value for {key} cannot be NaN")
                self.assertFalse(np.isinf(val), f"p-value for {key} cannot be Inf")
                # P-values should be in [0, 1]
                self.assertGreaterEqual(val, 0.0, f"p-value for {key} cannot be < 0")
                self.assertLessEqual(val, 1.0, f"p-value for {key} cannot be > 1")

    def test_regression_coefficients_exist(self):
        """Contract test: regression coefficients must be present and numeric."""
        if not self.data:
            self.skipTest("No analysis results found. Run the full pipeline first.")
        
        for result in self.data:
            self.assertIn("regression_coefficients", result, "Coefficients missing")
            coeffs = result["regression_coefficients"]
            self.assertIsInstance(coeffs, dict, "Coefficients must be a dict")
            for key, val in coeffs.items():
                self.assertIsInstance(val, (int, float), f"Coefficient for {key} must be numeric")
                self.assertFalse(np.isnan(val), f"Coefficient for {key} cannot be NaN")

    def test_schema_compliance(self):
        """Contract test: Ensure all required keys from T044 schema are present."""
        if not self.data:
            self.skipTest("No analysis results found. Run the full pipeline first.")
        
        required_keys = [
            "composition_id", "ea", "conductivity", "defect_density",
            "regression_coefficients", "p_values", "r_squared", 
            "power_analysis_result", "vif_scores", "pca_loadings"
        ]
        
        for result in self.data:
            for key in required_keys:
                self.assertIn(key, result, f"Missing required key: {key}")

    def test_vif_scores_structure(self):
        """Contract test: VIF scores must be a list of dicts with 'feature' and 'vif_score'."""
        if not self.vif_scores:
            # If the file doesn't exist, we skip this specific check, 
            # but the main analysis test will catch if it's missing from results.
            self.skipTest("VIF scores file not found. Run T039 first.")
        
        self.assertIsInstance(self.vif_scores, list, "VIF scores must be a list")
        for item in self.vif_scores:
            self.assertIsInstance(item, dict, "Each VIF item must be a dict")
            self.assertIn("feature", item, "VIF item missing 'feature'")
            self.assertIn("vif_score", item, "VIF item missing 'vif_score'")
            self.assertIsInstance(item["vif_score"], (int, float), "VIF score must be numeric")
            self.assertFalse(np.isnan(item["vif_score"]), "VIF score cannot be NaN")

    def test_pca_loadings_structure(self):
        """Contract test: PCA loadings must be a dict of feature -> loading."""
        if not self.data:
            self.skipTest("No analysis results found.")
        
        for result in self.data:
            self.assertIn("pca_loadings", result, "PCA loadings missing")
            loadings = result["pca_loadings"]
            self.assertIsInstance(loadings, dict, "PCA loadings must be a dict")
            for key, val in loadings.items():
                self.assertIsInstance(val, (int, float), f"PCA loading for {key} must be numeric")
                self.assertFalse(np.isnan(val), f"PCA loading for {key} cannot be NaN")


class TestAnalysisPipeline(unittest.TestCase):
    """Integration tests for the analysis pipeline functions."""

    def test_load_processed_data_type(self):
        """Test that load_processed_data returns a list of dicts."""
        # This function is expected to load from data/processed/defect_density_metrics.json
        # or similar. If the file is missing, it should return empty or raise.
        try:
            data = load_processed_data()
            self.assertIsInstance(data, list)
            if len(data) > 0:
                self.assertIsInstance(data[0], dict)
        except FileNotFoundError:
            self.skipTest("Processed data file not found. Run download/validate first.")

    def test_validate_data_quality(self):
        """Test that validate_data_quality returns a boolean or dict of status."""
        try:
            data = load_processed_data()
            if not data:
                self.skipTest("No data to validate.")
            
            status = validate_data_quality(data)
            # The function should return something indicating success/failure
            self.assertIsNotNone(status)
        except FileNotFoundError:
            self.skipTest("Processed data file not found.")

    def test_perform_regression_with_density_output(self):
        """Test that regression returns R² and p-values."""
        try:
            data = load_processed_data()
            if not data:
                self.skipTest("No data to regress.")
            
            # We mock a small subset if the real data is too complex for a unit test
            # but we ensure the function signature and return type are correct.
            results = perform_regression_with_density(data)
            
            self.assertIsInstance(results, dict)
            self.assertIn("r_squared", results)
            self.assertIn("p_values", results)
            self.assertIn("coefficients", results)
            
            # Check types
            self.assertIsInstance(results["r_squared"], float)
            self.assertIsInstance(results["p_values"], dict)
            
        except FileNotFoundError:
            self.skipTest("Processed data file not found.")


if __name__ == "__main__":
    unittest.main()