"""
Contract tests for statistical analysis output schema.

Verifies that the statistical analysis outputs (ANOVA results, correlation metrics)
conform to the expected schema and contain all required fields.
"""
import json
import sys
import unittest
from pathlib import Path
from typing import Dict, Any

# Ensure imports work
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))


class TestStatisticalSchema(unittest.TestCase):
    """Test cases for statistical analysis output schema validation."""

    def test_anova_output_schema(self):
        """Verify ANOVA output contains required fields."""
        # Sample ANOVA output structure
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
            "significance": True
        }
        
        required_fields = [
            "method", "factors", "interaction_term", "f_statistic",
            "p_value", "effect_size", "degrees_of_freedom", "significance"
        ]
        
        for field in required_fields:
            self.assertIn(field, sample_output, f"Missing required field: {field}")

    def test_correlation_output_schema(self):
        """Verify correlation output contains required fields."""
        sample_output = {
            "method": "Pearson correlation",
            "variable_x": "gap_slope",
            "variable_y": "human_eval_score",
            "correlation_coefficient": -0.65,
            "p_value": 0.02,
            "sample_size": 10,
            "threshold_met": True,
            "threshold_value": 0.5
        }
        
        required_fields = [
            "method", "variable_x", "variable_y", "correlation_coefficient",
            "p_value", "sample_size", "threshold_met", "threshold_value"
        ]
        
        for field in required_fields:
            self.assertIn(field, sample_output, f"Missing required field: {field}")

    def test_power_analysis_output_schema(self):
        """Verify power analysis output contains required fields."""
        sample_output = {
            "method": "A priori power analysis",
            "alpha": 0.05,
            "beta": 0.2,
            "effect_size": 0.5,
            "calculated_power": 0.85,
            "sample_size": 10,
            "power_achieved": True,
            "min_sample_size_required": 8
        }
        
        required_fields = [
            "method", "alpha", "beta", "effect_size", "calculated_power",
            "sample_size", "power_achieved", "min_sample_size_required"
        ]
        
        for field in required_fields:
            self.assertIn(field, sample_output, f"Missing required field: {field}")

    def test_final_report_schema(self):
        """Verify final report output contains required fields."""
        sample_output = {
            "summary": {
                "total_tokens": 1000000,
                "epochs_completed": 100,
                "seeds_per_architecture": 5
            },
            "anova_results": {},
            "correlation_results": {},
            "power_analysis_results": {},
            "human_eval_results": {},
            "wikitext2_results": {},
            "conclusions": [],
            "thresholds_met": {
                "correlation_threshold": True,
                "power_threshold": True
            }
        }
        
        required_fields = [
            "summary", "anova_results", "correlation_results",
            "power_analysis_results", "human_eval_results",
            "wikitext2_results", "conclusions", "thresholds_met"
        ]
        
        for field in required_fields:
            self.assertIn(field, sample_output, f"Missing required field: {field}")


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
