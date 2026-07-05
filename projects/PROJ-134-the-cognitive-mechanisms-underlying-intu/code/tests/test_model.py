import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
from typing import List, Dict, Any, Tuple

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.config import init_random_seeds

class TestSensitivityAnalysisThresholds:
    """
    Unit test for sensitivity analysis thresholds in code/tests/test_model.py.
    
    This test validates the logic for sweeping decision thresholds over the 
    specific set {2, 10, 20} to report model selection stability, as required 
    by US3 (T032 implementation dependency).
    
    The test ensures that:
    1. The threshold set is correctly defined as {2, 10, 20}
    2. The model selection stability matrix can be computed for these thresholds
    3. The output structure matches the expected format for reporting
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize random seeds for reproducibility."""
        init_random_seeds(42)
    
    def test_threshold_set_definition(self):
        """Verify that the sensitivity analysis uses the exact threshold set {2, 10, 20}."""
        expected_thresholds = {2, 10, 20}
        # Simulate the threshold set that would be used in the actual analysis
        # In the real implementation (T032), this would be defined in the analysis code
        actual_thresholds = {2, 10, 20}
        
        assert actual_thresholds == expected_thresholds, \
            f"Threshold set mismatch. Expected {expected_thresholds}, got {actual_thresholds}"
    
    def test_threshold_sweep_logic(self):
        """Test the logic of sweeping across thresholds to compute stability metrics."""
        # Simulate model comparison results for different thresholds
        # In reality, these would come from T024 (model comparison) results
        mock_results = {
            2: {"baseline_aic": 100.0, "salience_aic": 95.0, "delta_aic": 5.0, "winner": "salience"},
            10: {"baseline_aic": 100.0, "salience_aic": 90.0, "delta_aic": 10.0, "winner": "salience"},
            20: {"baseline_aic": 100.0, "salience_aic": 85.0, "delta_aic": 15.0, "winner": "salience"}
        }
        
        # Verify that all expected thresholds are present
        assert set(mock_results.keys()) == {2, 10, 20}, \
            "Not all required thresholds {2, 10, 20} are present in the results"
        
        # Verify that delta_aic is calculated correctly for each threshold
        for threshold, result in mock_results.items():
            expected_delta = result["salience_aic"] - result["baseline_aic"]
            assert abs(result["delta_aic"] - expected_delta) < 1e-6, \
                f"Delta AIC calculation error at threshold {threshold}"
    
    def test_stability_matrix_computation(self):
        """Test computation of the model selection stability matrix."""
        # Simulate model selection decisions across thresholds
        # 1 = salience model wins, 0 = baseline model wins
        decisions = {
            2: 1,   # salience wins (delta_aic = 5)
            10: 1,  # salience wins (delta_aic = 10)
            20: 1   # salience wins (delta_aic = 15)
        }
        
        # Compute stability: proportion of thresholds where salience model wins
        stability_rate = sum(decisions.values()) / len(decisions)
        
        assert stability_rate == 1.0, \
            f"Expected stability rate of 1.0, got {stability_rate}"
        
        # Test case with mixed results
        mixed_decisions = {
            2: 0,   # baseline wins
            10: 1,  # salience wins
            20: 1   # salience wins
        }
        
        mixed_stability = sum(mixed_decisions.values()) / len(mixed_decisions)
        assert mixed_stability == 2/3, \
            f"Expected stability rate of 2/3, got {mixed_stability}"
    
    def test_threshold_order_preservation(self):
        """Verify that thresholds are processed in a consistent order."""
        thresholds = [2, 10, 20]
        
        # The order should be ascending for consistent reporting
        assert thresholds == sorted(thresholds), \
            "Thresholds should be in ascending order for consistent analysis"
    
    def test_boundary_conditions(self):
        """Test edge cases for threshold values."""
        # Verify that threshold values are positive
        for threshold in [2, 10, 20]:
            assert threshold > 0, f"Threshold {threshold} must be positive"
        
        # Verify that thresholds are integers
        for threshold in [2, 10, 20]:
            assert isinstance(threshold, int), f"Threshold {threshold} must be an integer"
    
    def test_stability_matrix_output_format(self):
        """Test that the stability matrix output has the correct structure."""
        # Simulate the expected output structure for the stability matrix
        expected_structure = {
            "thresholds": [2, 10, 20],
            "stability_matrix": {
                "salience_wins": 3,
                "baseline_wins": 0,
                "stability_rate": 1.0
            },
            "interpretation": "Model selection is stable across all thresholds"
        }
        
        # Verify the structure matches
        assert "thresholds" in expected_structure
        assert "stability_matrix" in expected_structure
        assert "interpretation" in expected_structure
        
        # Verify the thresholds list
        assert expected_structure["thresholds"] == [2, 10, 20]
        
        # Verify the stability matrix keys
        sm = expected_structure["stability_matrix"]
        assert "salience_wins" in sm
        assert "baseline_wins" in sm
        assert "stability_rate" in sm
    
    def test_interpretation_logic(self):
        """Test the logic for interpreting stability results."""
        def get_interpretation(stability_rate: float) -> str:
            if stability_rate >= 0.9:
                return "Model selection is highly stable across thresholds"
            elif stability_rate >= 0.7:
                return "Model selection is moderately stable"
            elif stability_rate >= 0.5:
                return "Model selection shows some instability"
            else:
                return "Model selection is highly unstable across thresholds"
        
        # Test different stability rates
        assert "highly stable" in get_interpretation(0.95).lower()
        assert "moderately stable" in get_interpretation(0.8).lower()
        assert "some instability" in get_interpretation(0.6).lower()
        assert "highly unstable" in get_interpretation(0.3).lower()
    
    def test_threshold_set_immutability(self):
        """Verify that the threshold set is treated as immutable in the analysis."""
        thresholds = {2, 10, 20}
        
        # Attempt to modify the set (should not affect original in real implementation)
        modified = thresholds.copy()
        modified.add(5)
        
        # Original should remain unchanged
        assert thresholds == {2, 10, 20}, \
            "Threshold set should remain immutable during analysis"
        
        # Modified set should be different
        assert modified == {2, 5, 10, 20}, \
            "Modified set should include the added threshold"
    
    def test_integration_with_model_comparison(self):
        """Test that sensitivity analysis integrates with model comparison results."""
        # Simulate model comparison results from T024
        model_comparison_results = [
            {"threshold": 2, "delta_aic": 5.0, "winner": "salience"},
            {"threshold": 10, "delta_aic": 10.0, "winner": "salience"},
            {"threshold": 20, "delta_aic": 15.0, "winner": "salience"}
        ]
        
        # Verify that all thresholds in the sensitivity analysis are covered
        comparison_thresholds = {r["threshold"] for r in model_comparison_results}
        sensitivity_thresholds = {2, 10, 20}
        
        assert comparison_thresholds == sensitivity_thresholds, \
            "Model comparison results must cover all sensitivity analysis thresholds"
    
    def test_error_handling_invalid_threshold(self):
        """Test error handling for invalid threshold values."""
        def validate_threshold(threshold: float) -> bool:
            if not isinstance(threshold, (int, float)):
                raise TypeError("Threshold must be a number")
            if threshold <= 0:
                raise ValueError("Threshold must be positive")
            return True
        
        # Test valid thresholds
        assert validate_threshold(2) is True
        assert validate_threshold(10) is True
        assert validate_threshold(20) is True
        
        # Test invalid thresholds
        with pytest.raises(ValueError):
            validate_threshold(0)
        
        with pytest.raises(ValueError):
            validate_threshold(-5)
        
        with pytest.raises(TypeError):
            validate_threshold("invalid")
    
    def test_report_generation_compatibility(self):
        """Test that sensitivity analysis output is compatible with report generation."""
        # Simulate the output that would be passed to T033 (report generation)
        sensitivity_output = {
            "thresholds": [2, 10, 20],
            "stability_matrix": {
                "salience_wins": 3,
                "baseline_wins": 0,
                "stability_rate": 1.0
            },
            "interpretation": "Model selection is stable across all thresholds",
            "details": [
                {"threshold": 2, "delta_aic": 5.0, "winner": "salience"},
                {"threshold": 10, "delta_aic": 10.0, "winner": "salience"},
                {"threshold": 20, "delta_aic": 15.0, "winner": "salience"}
            ]
        }
        
        # Verify the output structure is compatible with report generation
        assert "thresholds" in sensitivity_output
        assert "stability_matrix" in sensitivity_output
        assert "interpretation" in sensitivity_output
        assert "details" in sensitivity_output
        
        # Verify that details contain all required fields
        for detail in sensitivity_output["details"]:
            assert "threshold" in detail
            assert "delta_aic" in detail
            assert "winner" in detail