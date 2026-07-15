"""
Unit tests for sensitivity analysis module (Task T028)
"""

import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import numpy as np

# Import the module under test
from sensitivity_analysis import (
    extract_lmm_coefficients,
    compare_against_literature,
    calculate_sensitivity_metrics,
    run_sensitivity_analysis,
    LITERATURE_RANGES
)


class TestExtractLmmCoefficients(unittest.TestCase):
    """Tests for coefficient extraction from LMM results."""
    
    def test_extract_valid_coefficients(self):
        """Test extraction of valid nutrient coefficients."""
        mock_results = {
            "lmm_results": {
                "fixed_effects": {
                    "phosphorus": -0.25,
                    "nitrogen": -0.18,
                    "potassium": -0.12,
                    "intercept": 1.5
                }
            }
        }
        
        coefficients = extract_lmm_coefficients(mock_results)
        
        self.assertIn("phosphorus", coefficients)
        self.assertIn("nitrogen", coefficients)
        self.assertIn("potassium", coefficients)
        self.assertNotIn("intercept", coefficients)
        self.assertAlmostEqual(coefficients["phosphorus"], -0.25)
    
    def test_empty_results(self):
        """Test handling of empty results."""
        coefficients = extract_lmm_coefficients({})
        self.assertEqual(coefficients, {})
    
    def test_missing_fixed_effects(self):
        """Test handling of missing fixed_effects key."""
        mock_results = {"lmm_results": {}}
        coefficients = extract_lmm_coefficients(mock_results)
        self.assertEqual(coefficients, {})

class TestCompareAgainstLiterature(unittest.TestCase):
    """Tests for comparison against literature ranges."""
    
    def test_within_range_coefficient(self):
        """Test coefficient within literature range."""
        coefficients = {"phosphorus": -0.2}
        comparisons = compare_against_literature(coefficients, LITERATURE_RANGES)
        
        self.assertEqual(len(comparisons), 1)
        self.assertEqual(comparisons[0]["status"], "within_range")
        self.assertAlmostEqual(comparisons[0]["fitted_coefficient"], -0.2)
    
    def test_outside_range_coefficient(self):
        """Test coefficient outside literature range."""
        coefficients = {"phosphorus": 2.0}  # Well outside max of 0.5
        comparisons = compare_against_literature(coefficients, LITERATURE_RANGES)
        
        self.assertEqual(len(comparisons), 1)
        self.assertEqual(comparisons[0]["status"], "critical")
    
    def test_warning_threshold(self):
        """Test coefficient triggering warning status."""
        # Typical for phosphorus is -0.2, warning threshold is 30%
        # -0.2 * 1.3 = -0.26, so -0.26 should be warning
        coefficients = {"phosphorus": -0.26}
        comparisons = compare_against_literature(coefficients, LITERATURE_RANGES)
        
        self.assertEqual(len(comparisons), 1)
        self.assertEqual(comparisons[0]["status"], "warning")
    
    def test_multiple_nutrients(self):
        """Test comparison for multiple nutrients."""
        coefficients = {
            "phosphorus": -0.2,
            "nitrogen": -0.15,
            "potassium": -0.1
        }
        comparisons = compare_against_literature(coefficients, LITERATURE_RANGES)
        
        self.assertEqual(len(comparisons), 3)
        for comp in comparisons:
            self.assertEqual(comp["status"], "within_range")

class TestCalculateSensitivityMetrics(unittest.TestCase):
    """Tests for aggregate metric calculation."""
    
    def test_all_within_range(self):
        """Test metrics when all coefficients are within range."""
        comparisons = [
            {"nutrient": "phosphorus", "status": "within_range"},
            {"nutrient": "nitrogen", "status": "within_range"}
        ]
        metrics = calculate_sensitivity_metrics(comparisons)
        
        self.assertEqual(metrics["total_coefficients_tested"], 2)
        self.assertEqual(metrics["within_range_count"], 2)
        self.assertEqual(metrics["critical_count"], 0)
        self.assertEqual(metrics["overall_plausibility"], "plausible")
    
    def test_with_critical(self):
        """Test metrics when some coefficients are critical."""
        comparisons = [
            {"nutrient": "phosphorus", "status": "within_range"},
            {"nutrient": "nitrogen", "status": "critical"}
        ]
        metrics = calculate_sensitivity_metrics(comparisons)
        
        self.assertEqual(metrics["critical_count"], 1)
        self.assertEqual(metrics["overall_plausibility"], "questionable")
    
    def test_empty_comparisons(self):
        """Test metrics with empty comparisons."""
        metrics = calculate_sensitivity_metrics([])
        
        self.assertEqual(metrics["total_coefficients_tested"], 0)
        self.assertEqual(metrics["overall_plausibility"], "unknown")

class TestRunSensitivityAnalysis(unittest.TestCase):
    """Tests for the main analysis function."""
    
    def setUp(self):
        """Set up temporary files for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.model_path = os.path.join(self.temp_dir, "model_results.json")
        self.output_path = os.path.join(self.temp_dir, "sensitivity_results.json")
        
        # Create mock model results
        mock_model_data = {
            "lmm_results": {
                "fixed_effects": {
                    "phosphorus": -0.22,
                    "nitrogen": -0.16,
                    "potassium": -0.09
                }
            }
        }
        
        with open(self.model_path, 'w') as f:
            json.dump(mock_model_data, f)
    
    def test_successful_analysis(self):
        """Test successful sensitivity analysis run."""
        results = run_sensitivity_analysis(self.model_path, self.output_path)
        
        self.assertEqual(results["status"], "success")
        self.assertIn("comparisons", results)
        self.assertIn("metrics", results)
        self.assertEqual(len(results["comparisons"]), 3)
        
        # Verify output file was created
        self.assertTrue(os.path.exists(self.output_path))
        
        # Verify output file content matches results
        with open(self.output_path, 'r') as f:
            saved_results = json.load(f)
        
        self.assertEqual(saved_results["status"], results["status"])
    
    def test_file_not_found(self):
        """Test handling of missing model results file."""
        with self.assertRaises(FileNotFoundError):
            run_sensitivity_analysis("nonexistent.json", self.output_path)
    
    def test_no_coefficients(self):
        """Test handling of model with no coefficients."""
        empty_model_path = os.path.join(self.temp_dir, "empty_model.json")
        with open(empty_model_path, 'w') as f:
            json.dump({}, f)
        
        results = run_sensitivity_analysis(empty_model_path, self.output_path)
        
        self.assertEqual(results["status"], "no_coefficients")
        self.assertEqual(len(results["comparisons"]), 0)

if __name__ == "__main__":
    unittest.main()
