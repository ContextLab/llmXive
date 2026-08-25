"""
Integration test for sensitivity analysis (T038).

Verifies:
1. Threshold sweep across 0.01, 0.05, 0.10 levels.
2. Benjamini-Hochberg FDR correction application.
3. Consistency with regression results from T029.
"""
import os
import sys
import json
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path to allow imports from code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from analysis.sensitivity import (
    load_regression_results,
    apply_benjamini_hochberg,
    run_sensitivity_analysis,
    save_sensitivity_results
)
from utils.logging import AnalysisError


class TestSensitivityAnalysisIntegration:
    """Integration tests for the sensitivity analysis pipeline."""

    @pytest.fixture(scope="class")
    def regression_results_path(self) -> Path:
        """
        Ensure regression results exist before running sensitivity tests.
        In a real CI/CD environment, this would be a prerequisite step.
        For this test, we assume T029 has been run and produced artifacts.
        """
        results_path = PROJECT_ROOT / "data" / "artifacts" / "regression_results.json"
        if not results_path.exists():
            # If results don't exist, we cannot run the integration test.
            # We skip the test rather than failing, as this is an integration
            # test dependent on a prior task's output.
            pytest.skip("Regression results not found. Please run T029 first.")
        return results_path

    @pytest.fixture(scope="class")
    def sensitivity_results_path(self) -> Path:
        """Path where sensitivity results will be saved."""
        return PROJECT_ROOT / "data" / "artifacts" / "sensitivity_results.json"

    def test_threshold_sweep_and_fdr_correction(
        self,
        regression_results_path: Path,
        sensitivity_results_path: Path
    ) -> None:
        """
        Verify that the sensitivity analysis:
        1. Loads regression results correctly.
        2. Sweeps through thresholds [0.01, 0.05, 0.10].
        3. Applies Benjamini-Hochberg FDR correction.
        4. Produces a valid output artifact.
        """
        # Load regression results to verify structure
        regression_data = load_regression_results(regression_results_path)
        
        # Ensure we have the expected structure
        assert "models" in regression_data, "Regression results missing 'models' key"
        assert "coefficients" in regression_data, "Regression results missing 'coefficients' key"
        
        # Run sensitivity analysis
        # We use the standard thresholds defined in T035
        thresholds = [0.01, 0.05, 0.10]
        
        sensitivity_results = run_sensitivity_analysis(
            regression_data,
            thresholds=thresholds
        )
        
        # Verify the results structure
        assert "thresholds" in sensitivity_results, "Results missing 'thresholds' key"
        assert "fdr_corrected" in sensitivity_results, "Results missing 'fdr_corrected' key"
        assert "significant_predictors" in sensitivity_results, "Results missing 'significant_predictors' key"
        
        # Verify thresholds match input
        assert set(sensitivity_results["thresholds"]) == set(thresholds), \
            "Thresholds in results do not match input thresholds"
        
        # Verify FDR correction was applied
        # The FDR corrected results should have adjusted p-values
        fdr_results = sensitivity_results["fdr_corrected"]
        for model_name, model_data in fdr_results.items():
            assert "adjusted_p_values" in model_data, \
                f"Model {model_name} missing 'adjusted_p_values' in FDR results"
            assert "significant_features" in model_data, \
                f"Model {model_name} missing 'significant_features' in FDR results"
        
        # Verify significant predictors are reported
        sig_predictors = sensitivity_results["significant_predictors"]
        assert isinstance(sig_predictors, dict), "significant_predictors should be a dict"
        
        # Save results to verify artifact creation
        save_sensitivity_results(sensitivity_results, sensitivity_results_path)
        
        # Verify the file was actually written
        assert sensitivity_results_path.exists(), \
            "Sensitivity results file was not created"
        
        # Verify the saved file is valid JSON
        with open(sensitivity_results_path, "r") as f:
            saved_data = json.load(f)
        
        assert saved_data == sensitivity_results, \
            "Saved sensitivity results do not match in-memory results"

    def test_fdr_correction_logic(self, regression_results_path: Path) -> None:
        """
        Verify that the Benjamini-Hochberg correction logic is applied correctly.
        This test checks the mathematical validity of the FDR adjustment.
        """
        regression_data = load_regression_results(regression_results_path)
        
        # Extract p-values for testing
        # We assume the regression results contain a list of coefficients with p-values
        all_p_values = []
        feature_names = []
        
        for model_name, model_data in regression_data.get("coefficients", {}).items():
            if isinstance(model_data, list):
                for coef_entry in model_data:
                    if "p_value" in coef_entry:
                        all_p_values.append(coef_entry["p_value"])
                        feature_names.append(coef_entry.get("feature", "unknown"))
        
        if not all_p_values:
            pytest.skip("No p-values found in regression results to test FDR logic.")
        
        # Apply FDR correction
        adjusted_p_values = apply_benjamini_hochberg(all_p_values)
        
        # Verify the output
        assert len(adjusted_p_values) == len(all_p_values), \
            "FDR correction changed the number of p-values"
        
        # Verify monotonicity: adjusted p-values should be non-decreasing
        # when sorted by original p-value
        sorted_indices = sorted(range(len(all_p_values)), key=lambda k: all_p_values[k])
        sorted_adjusted = [adjusted_p_values[i] for i in sorted_indices]
        
        for i in range(1, len(sorted_adjusted)):
            assert sorted_adjusted[i] >= sorted_adjusted[i-1], \
                "Adjusted p-values are not monotonically increasing"
        
        # Verify all adjusted p-values are between 0 and 1
        for p_val in adjusted_p_values:
            assert 0.0 <= p_val <= 1.0, \
                f"Adjusted p-value {p_val} is out of bounds [0, 1]"

    def test_sensitivity_across_thresholds(
        self,
        regression_results_path: Path,
        sensitivity_results_path: Path
    ) -> None:
        """
        Verify that the number of significant predictors changes appropriately
        across different thresholds.
        """
        # Run sensitivity analysis
        thresholds = [0.01, 0.05, 0.10]
        sensitivity_results = run_sensitivity_analysis(
            load_regression_results(regression_results_path),
            thresholds=thresholds
        )
        
        # Count significant predictors at each threshold
        counts = {}
        for threshold in thresholds:
            # Count total significant predictors across all models at this threshold
            total_sig = 0
            for model_name, model_data in sensitivity_results["fdr_corrected"].items():
                # Filter by threshold
                sig_features = model_data["significant_features"]
                for feature in sig_features:
                    if feature.get("adjusted_p_value", 1.0) <= threshold:
                        total_sig += 1
            counts[threshold] = total_sig
        
        # Verify that lower thresholds have fewer or equal significant predictors
        # than higher thresholds (monotonicity)
        sorted_thresholds = sorted(thresholds)
        for i in range(1, len(sorted_thresholds)):
            lower_thresh = sorted_thresholds[i-1]
            higher_thresh = sorted_thresholds[i]
            assert counts[lower_thresh] <= counts[higher_thresh], \
                f"Significant predictors at {lower_thresh} ({counts[lower_thresh]}) " \
                f"should be <= than at {higher_thresh} ({counts[higher_thresh]})"