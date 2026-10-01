"""
Unit tests for visualization module sensitivity analysis threshold sweeping logic.

This module tests the threshold sweeping logic in `code/visualization.py`,
specifically the `perform_sensitivity_analysis` function which sweeps thresholds
at absolute deviations {0.01, 0.05, 0.1} from a baseline.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import sys
import os

# Add the project root to the path to allow imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from visualization import perform_sensitivity_analysis
from config import get_path


class TestSensitivityAnalysisThresholdSweep:
    """Tests for the threshold sweeping logic in sensitivity analysis."""

    @pytest.fixture
    def mock_results_data(self):
        """Create mock results data for sensitivity analysis."""
        return {
            "hypothesis_test": {
                "baseline_r2": 0.45,
                "augmented_r2": 0.52,
                "p_value": 0.03,
                "r2_improvement": 0.07
            },
            "model_metrics": {
                "baseline": {"r2": 0.45, "mae": 0.15},
                "augmented": {"r2": 0.52, "mae": 0.12}
            }
        }

    @pytest.fixture
    def mock_sensitivity_input(self):
        """Create mock input data for sensitivity analysis."""
        # Simulate a small dataset of predicted residuals and actual residuals
        np.random.seed(42)
        n_samples = 100
        return pd.DataFrame({
            "predicted_residual": np.random.normal(0, 0.1, n_samples),
            "actual_residual": np.random.normal(0, 0.1, n_samples)
        })

    def test_threshold_sweep_values(self, mock_sensitivity_input):
        """Verify that the sweep uses the correct threshold deviations: {0.01, 0.05, 0.1}."""
        # We mock the calculation logic to capture the thresholds used
        captured_thresholds = []

        def mock_calculate_metrics(df, threshold):
            captured_thresholds.append(threshold)
            return {"f1": 0.5, "fpr": 0.1}

        with patch("visualization.calculate_metrics", side_effect=mock_calculate_metrics):
            # Run the analysis
            result = perform_sensitivity_analysis(mock_sensitivity_input, mock_sensitivity_input)

        # Verify the expected thresholds were used
        expected_deviations = {0.01, 0.05, 0.1}
        actual_deviations = set(captured_thresholds)
        
        assert expected_deviations == actual_deviations, (
            f"Expected thresholds {expected_deviations} but got {actual_deviations}. "
            "The sweep logic must use exactly {0.01, 0.05, 0.1} deviations."
        )

    def test_baseline_calculation_logic(self, mock_sensitivity_input):
        """Verify that the baseline is calculated as the 90th percentile of absolute residuals."""
        expected_baseline = np.percentile(mock_sensitivity_input["actual_residual"].abs(), 90)
        
        # We verify the logic by checking the internal behavior or mocking the baseline calculation
        # Since the function is internal, we test the output structure which depends on the baseline
        def mock_calculate_metrics(df, threshold):
            # Just return a dummy metric
            return {"f1": 0.5, "fpr": 0.1}

        with patch("visualization.calculate_metrics", side_effect=mock_calculate_metrics):
            result = perform_sensitivity_analysis(mock_sensitivity_input, mock_sensitivity_input)

        # The result should contain the baseline used
        assert "baseline" in result, "Result must contain the baseline threshold."
        assert np.isclose(result["baseline"], expected_baseline, rtol=1e-5), (
            f"Baseline {result['baseline']} does not match expected 90th percentile {expected_baseline}"
        )

    def test_metric_calculation_for_each_threshold(self, mock_sensitivity_input):
        """Verify that metrics are calculated and returned for each swept threshold."""
        def mock_calculate_metrics(df, threshold):
            # Return a deterministic metric based on threshold to ensure it's called
            return {
                "f1": 0.5 + threshold,
                "fpr": 0.1 + threshold,
                "threshold": threshold
            }

        with patch("visualization.calculate_metrics", side_effect=mock_calculate_metrics):
            result = perform_sensitivity_analysis(mock_sensitivity_input, mock_sensitivity_input)

        # Check that sensitivity data exists and has entries for each threshold
        assert "sensitivity_analysis" in result, "Result must contain 'sensitivity_analysis' key."
        sensitivity_data = result["sensitivity_analysis"]
        
        assert "thresholds" in sensitivity_data, "Sensitivity data must contain 'thresholds' list."
        assert len(sensitivity_data["thresholds"]) == 3, (
            f"Expected 3 threshold entries, got {len(sensitivity_data['thresholds'])}"
        )

        # Verify each threshold entry has the required metrics
        for entry in sensitivity_data["thresholds"]:
            assert "threshold" in entry, "Each entry must have 'threshold'."
            assert "f1_score" in entry, "Each entry must have 'f1_score'."
            assert "false_positive_rate" in entry, "Each entry must have 'false_positive_rate'."

    def test_robustness_report_generation(self, mock_sensitivity_input):
        """Verify that the robustness report is generated correctly."""
        def mock_calculate_metrics(df, threshold):
            return {"f1": 0.5, "fpr": 0.1}

        with patch("visualization.calculate_metrics", side_effect=mock_calculate_metrics):
            result = perform_sensitivity_analysis(mock_sensitivity_input, mock_sensitivity_input)

        # Verify the robustness flag logic
        assert "robustness_assessment" in result, "Result must contain 'robustness_assessment'."
        robustness = result["robustness_assessment"]
        
        assert "headline_holds" in robustness, "Robustness assessment must indicate if headline holds."
        assert isinstance(robustness["headline_holds"], bool), "headline_holds must be a boolean."

    def test_integration_with_mocked_data(self, mock_sensitivity_input):
        """Integration test to ensure the full flow works without errors."""
        # Ensure no exceptions are raised during the full flow
        def mock_calculate_metrics(df, threshold):
            return {"f1": 0.5, "fpr": 0.1}

        try:
            with patch("visualization.calculate_metrics", side_effect=mock_calculate_metrics):
                result = perform_sensitivity_analysis(mock_sensitivity_input, mock_sensitivity_input)
            
            # Verify the result structure is complete
            assert "baseline" in result
            assert "sensitivity_analysis" in result
            assert "robustness_assessment" in result
            assert "thresholds" in result["sensitivity_analysis"]
            
        except Exception as e:
            pytest.fail(f"Sensitivity analysis flow failed: {str(e)}")

    def test_handles_empty_dataframe(self):
        """Verify that the function handles empty input gracefully."""
        empty_df = pd.DataFrame(columns=["predicted_residual", "actual_residual"])
        
        # The function should either raise a clear error or handle it
        # We expect it to raise an error if the data is insufficient for percentile calculation
        with pytest.raises((ValueError, IndexError)):
            perform_sensitivity_analysis(empty_df, empty_df)

    def test_handles_non_numeric_columns(self):
        """Verify that the function handles non-numeric data gracefully."""
        df = pd.DataFrame({
            "predicted_residual": ["a", "b", "c"],
            "actual_residual": ["x", "y", "z"]
        })
        
        # Should raise TypeError or similar when trying to compute percentiles on strings
        with pytest.raises((TypeError, ValueError)):
            perform_sensitivity_analysis(df, df)

    def test_output_format_matches_spec(self, mock_sensitivity_input):
        """Verify that the output format matches the specification for results.json."""
        def mock_calculate_metrics(df, threshold):
            return {"f1": 0.5, "fpr": 0.1}

        with patch("visualization.calculate_metrics", side_effect=mock_calculate_metrics):
            result = perform_sensitivity_analysis(mock_sensitivity_input, mock_sensitivity_input)

        # Check top-level keys required by spec
        required_keys = ["baseline", "sensitivity_analysis", "robustness_assessment"]
        for key in required_keys:
            assert key in result, f"Missing required key '{key}' in output."

        # Check sensitivity analysis structure
        sens = result["sensitivity_analysis"]
        assert "thresholds" in sens
        assert isinstance(sens["thresholds"], list)
        
        # Check each threshold entry
        for entry in sens["thresholds"]:
            assert "threshold" in entry
            assert "f1_score" in entry
            assert "false_positive_rate" in entry

        # Check robustness assessment
        robust = result["robustness_assessment"]
        assert "headline_holds" in robust
        assert "variance" in robust