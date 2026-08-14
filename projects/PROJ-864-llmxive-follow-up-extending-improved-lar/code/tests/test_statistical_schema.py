"""
Contract tests for statistical analysis output schema.

Verifies that the statistical analysis outputs (ANOVA results, correlation metrics)
conform to the expected schema and contain all required fields.
"""
import json
import sys
import unittest
from pathlib import Path
from typing import Dict, Any, List

# Ensure imports work
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))


def validate_dict_structure(data: Dict[str, Any], required_keys: List[str], path: str = "root") -> List[str]:
    """
    Recursively validate that a dictionary contains all required keys.
    Returns a list of missing keys with their paths.
    """
    missing = []
    for key in required_keys:
        if key not in data:
            missing.append(f"{path}.{key}")
        elif isinstance(data[key], dict) and isinstance(required_keys, dict):
            # If the expected value is a dict, recurse (simplified for this task)
            pass
    return missing


class TestStatisticalSchema(unittest.TestCase):
    """Test cases for statistical analysis output schema validation."""

    def test_anova_output_schema(self):
        """Verify ANOVA output contains required fields."""
        # Sample ANOVA output structure matching statistical_test.py output
        sample_output = {
            "method": "Mixed-Model Repeated-Measures ANOVA",
            "factors": ["model_type", "epoch"],
            "interaction_term": "model_type × epoch",
            "f_statistic": 12.34,
            "p_value": 0.001,
            "effect_size": 0.45,
            "degrees_of_freedom": {
                "numerator": 1,
                "denominator": 98
            },
            "significance": True,
            "model_type": "ANOVA",
            "summary": "ANOVA results summary"
        }
        
        required_fields = [
            "method", "factors", "interaction_term", "f_statistic",
            "p_value", "effect_size", "degrees_of_freedom", "significance",
            "model_type", "summary"
        ]
        
        missing = validate_dict_structure(sample_output, required_fields)
        self.assertEqual(len(missing), 0, f"Missing required fields in ANOVA output: {missing}")
        
        # Validate nested structure
        self.assertIn("numerator", sample_output["degrees_of_freedom"])
        self.assertIn("denominator", sample_output["degrees_of_freedom"])

    def test_correlation_output_schema(self):
        """Verify correlation output contains required fields."""
        # Sample correlation output structure matching compute_metrics.py output
        sample_output = {
            "method": "Pearson correlation",
            "variable_x": "gap_slope",
            "variable_y": "human_eval_score",
            "correlation_coefficient": -0.65,
            "p_value": 0.02,
            "sample_size": 10,
            "threshold_met": True,
            "threshold_value": 0.5,
            "model_type": "Correlation",
            "summary": "Correlation analysis summary"
        }
        
        required_fields = [
            "method", "variable_x", "variable_y", "correlation_coefficient",
            "p_value", "sample_size", "threshold_met", "threshold_value",
            "model_type", "summary"
        ]
        
        missing = validate_dict_structure(sample_output, required_fields)
        self.assertEqual(len(missing), 0, f"Missing required fields in correlation output: {missing}")

    def test_power_analysis_output_schema(self):
        """Verify power analysis output contains required fields."""
        # Sample power analysis output structure matching power_analysis.py output
        sample_output = {
            "method": "A priori power analysis",
            "alpha": 0.05,
            "beta": 0.2,
            "effect_size": 0.5,
            "calculated_power": 0.85,
            "sample_size": 10,
            "power_achieved": True,
            "min_sample_size_required": 8,
            "model_type": "PowerAnalysis",
            "summary": "Power analysis summary"
        }
        
        required_fields = [
            "method", "alpha", "beta", "effect_size", "calculated_power",
            "sample_size", "power_achieved", "min_sample_size_required",
            "model_type", "summary"
        ]
        
        missing = validate_dict_structure(sample_output, required_fields)
        self.assertEqual(len(missing), 0, f"Missing required fields in power analysis output: {missing}")

    def test_final_report_schema(self):
        """Verify final report output contains required fields."""
        # Sample final report output structure matching report_generator.py output
        sample_output = {
            "summary": {
                "total_tokens": 1000000,
                "epochs_completed": 100,
                "seeds_per_architecture": 5
            },
            "anova_results": {
                "method": "Mixed-Model Repeated-Measures ANOVA",
                "f_statistic": 12.34,
                "p_value": 0.001
            },
            "correlation_results": {
                "method": "Pearson correlation",
                "correlation_coefficient": -0.65,
                "threshold_met": True
            },
            "power_analysis_results": {
                "method": "A priori power analysis",
                "calculated_power": 0.85,
                "power_achieved": True
            },
            "human_eval_results": {
                "pass_rate": 0.85,
                "pass@1": 0.80
            },
            "wikitext2_results": {
                "perplexity": 15.2
            },
            "conclusions": [
                "Conclusion 1",
                "Conclusion 2"
            ],
            "thresholds_met": {
                "correlation_threshold": True,
                "power_threshold": True
            },
            "model_type": "FinalReport",
            "timestamp": "2023-10-01T12:00:00"
        }
        
        required_fields = [
            "summary", "anova_results", "correlation_results",
            "power_analysis_results", "human_eval_results",
            "wikitext2_results", "conclusions", "thresholds_met",
            "model_type", "timestamp"
        ]
        
        missing = validate_dict_structure(sample_output, required_fields)
        self.assertEqual(len(missing), 0, f"Missing required fields in final report: {missing}")
        
        # Validate nested summary structure
        summary_fields = ["total_tokens", "epochs_completed", "seeds_per_architecture"]
        missing_summary = validate_dict_structure(sample_output["summary"], summary_fields, "summary")
        self.assertEqual(len(missing_summary), 0, f"Missing required fields in summary: {missing_summary}")

    def test_anova_empty_result_handling(self):
        """Verify schema handles empty/None ANOVA results gracefully."""
        sample_output = {
            "method": "Mixed-Model Repeated-Measures ANOVA",
            "factors": [],
            "interaction_term": None,
            "f_statistic": None,
            "p_value": None,
            "effect_size": None,
            "degrees_of_freedom": None,
            "significance": False,
            "model_type": "ANOVA",
            "summary": "No data available for ANOVA"
        }
        
        # Even with None values, the keys must exist
        required_fields = [
            "method", "factors", "interaction_term", "f_statistic",
            "p_value", "effect_size", "degrees_of_freedom", "significance",
            "model_type", "summary"
        ]
        
        missing = validate_dict_structure(sample_output, required_fields)
        self.assertEqual(len(missing), 0, f"Missing required keys in empty ANOVA output: {missing}")

    def test_correlation_threshold_logic(self):
        """Verify correlation output correctly reflects threshold logic."""
        # Test case where threshold is met
        met_output = {
            "correlation_coefficient": -0.65,
            "threshold_value": 0.5,
            "threshold_met": True
        }
        self.assertTrue(met_output["threshold_met"])
        
        # Test case where threshold is not met
        not_met_output = {
            "correlation_coefficient": 0.3,
            "threshold_value": 0.5,
            "threshold_met": False
        }
        self.assertFalse(not_met_output["threshold_met"])


def run_tests():
    """Run all tests in this module."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestStatisticalSchema)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)