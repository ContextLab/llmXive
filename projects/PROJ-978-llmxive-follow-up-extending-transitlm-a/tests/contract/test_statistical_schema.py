"""
Contract test for statistical output schema (T018).

Validates that statistical analysis outputs from US2 (survival analysis,
log-rank tests, Bonferroni corrections) adhere to the defined JSON schema.

This test ensures that:
1. survival_data.json contains required fields for Kaplan-Meier curves
2. final_inflection_report.json contains corrected p-values and inflection point
3. statistical_report.json contains all required metrics and confidence intervals

Run: pytest tests/contract/test_statistical_schema.py -v
"""

import json
import os
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent.parent
ANALYSIS_DIR = PROJECT_ROOT / "data" / "analysis"


class TestSurvivalDataSchema:
    """Contract tests for data/analysis/survival_data.json (T020)"""

    @pytest.fixture
    def survival_data(self) -> Dict[str, Any]:
        """Load survival_data.json if it exists"""
        file_path = ANALYSIS_DIR / "survival_data.json"
        if not file_path.exists():
            pytest.skip(f"File not found: {file_path}. Run T020 first.")
        
        with open(file_path, 'r') as f:
            return json.load(f)

    def test_required_top_level_keys(self, survival_data: Dict[str, Any]):
        """Survival data must contain model-specific survival curves"""
        required_keys = ["lightweight_model", "baseline_model"]
        for key in required_keys:
            assert key in survival_data, f"Missing required key: {key}"

    def test_survival_curve_structure(self, survival_data: Dict[str, Any]):
        """Each model's survival data must have time_points and survival_probabilities"""
        for model_name in ["lightweight_model", "baseline_model"]:
            model_data = survival_data[model_name]
            assert "time_points" in model_data, f"{model_name} missing time_points"
            assert "survival_probabilities" in model_data, f"{model_name} missing survival_probabilities"
            
            # Validate data types
            assert isinstance(model_data["time_points"], list), "time_points must be a list"
            assert isinstance(model_data["survival_probabilities"], list), "survival_probabilities must be a list"
            
            # Validate lengths match
            assert len(model_data["time_points"]) == len(model_data["survival_probabilities"]), \
                "time_points and survival_probabilities must have same length"
            
            # Validate values are numeric
            for i, (t, p) in enumerate(zip(model_data["time_points"], model_data["survival_probabilities"])):
                assert isinstance(t, (int, float)), f"time_points[{i}] must be numeric"
                assert isinstance(p, (int, float)), f"survival_probabilities[{i}] must be numeric"
                assert 0.0 <= p <= 1.0, f"survival_probabilities[{i}] must be between 0 and 1"

    def test_censoring_info_present(self, survival_data: Dict[str, Any]):
        """Each model must include censoring information"""
        for model_name in ["lightweight_model", "baseline_model"]:
            model_data = survival_data[model_name]
            assert "censoring_indices" in model_data, f"{model_name} missing censoring_indices"
            assert isinstance(model_data["censoring_indices"], list), "censoring_indices must be a list"

    def test_sample_sizes(self, survival_data: Dict[str, Any]):
        """Each model must report the sample size used"""
        for model_name in ["lightweight_model", "baseline_model"]:
            model_data = survival_data[model_name]
            assert "n_samples" in model_data, f"{model_name} missing n_samples"
            assert isinstance(model_data["n_samples"], int), "n_samples must be an integer"
            assert model_data["n_samples"] > 0, "n_samples must be positive"


class TestFinalInflectionReportSchema:
    """Contract tests for data/analysis/final_inflection_report.json (T023a)"""

    @pytest.fixture
    def inflection_report(self) -> Dict[str, Any]:
        """Load final_inflection_report.json if it exists"""
        file_path = ANALYSIS_DIR / "final_inflection_report.json"
        if not file_path.exists():
            pytest.skip(f"File not found: {file_path}. Run T023a first.")
        
        with open(file_path, 'r') as f:
            return json.load(f)

    def test_required_top_level_keys(self, inflection_report: Dict[str, Any]):
        """Inflection report must contain key findings"""
        required_keys = [
            "inflection_point_length",
            "unadjusted_p_value",
            "bonferroni_adjusted_p_value",
            "significance_threshold",
            "is_significant",
            "validity_drop_percentage"
        ]
        for key in required_keys:
            assert key in inflection_report, f"Missing required key: {key}"

    def test_inflection_point_is_integer(self, inflection_report: Dict[str, Any]):
        """Inflection point must be a positive integer"""
        assert isinstance(inflection_report["inflection_point_length"], int), \
            "inflection_point_length must be an integer"
        assert inflection_report["inflection_point_length"] > 0, \
            "inflection_point_length must be positive"

    def test_p_values_are_numeric(self, inflection_report: Dict[str, Any]):
        """P-values must be floats between 0 and 1"""
        for key in ["unadjusted_p_value", "bonferroni_adjusted_p_value"]:
            value = inflection_report[key]
            assert isinstance(value, (int, float)), f"{key} must be numeric"
            assert 0.0 <= value <= 1.0, f"{key} must be between 0 and 1"

    def test_significance_threshold_valid(self, inflection_report: Dict[str, Any]):
        """Significance threshold must be a valid alpha level"""
        threshold = inflection_report["significance_threshold"]
        assert isinstance(threshold, (int, float)), "significance_threshold must be numeric"
        assert 0.0 < threshold < 1.0, "significance_threshold must be between 0 and 1"

    def test_is_significant_consistent(self, inflection_report: Dict[str, Any]):
        """is_significant must match the comparison of adjusted p-value to threshold"""
        adjusted_p = inflection_report["bonferroni_adjusted_p_value"]
        threshold = inflection_report["significance_threshold"]
        expected_significance = adjusted_p < threshold
        
        assert inflection_report["is_significant"] == expected_significance, \
            f"is_significant ({inflection_report['is_significant']}) inconsistent with p-value ({adjusted_p}) and threshold ({threshold})"

    def test_validity_drop_in_range(self, inflection_report: Dict[str, Any]):
        """Validity drop must be a percentage between 0 and 100"""
        drop = inflection_report["validity_drop_percentage"]
        assert isinstance(drop, (int, float)), "validity_drop_percentage must be numeric"
        assert 0.0 <= drop <= 100.0, "validity_drop_percentage must be between 0 and 100"


class TestStatisticalReportSchema:
    """Contract tests for data/analysis/statistical_report.json (T025b)"""

    @pytest.fixture
    def statistical_report(self) -> Dict[str, Any]:
        """Load statistical_report.json if it exists"""
        file_path = ANALYSIS_DIR / "statistical_report.json"
        if not file_path.exists():
            pytest.skip(f"File not found: {file_path}. Run T025b first.")
        
        with open(file_path, 'r') as f:
            return json.load(f)

    def test_required_summary_fields(self, statistical_report: Dict[str, Any]):
        """Statistical report must contain summary statistics"""
        required_keys = [
            "log_rank_test",
            "median_survival_lengths",
            "confidence_intervals",
            "inflection_point_summary",
            "methodology"
        ]
        for key in required_keys:
            assert key in statistical_report, f"Missing required key: {key}"

    def test_log_rank_test_structure(self, statistical_report: Dict[str, Any]):
        """Log-rank test must include statistic and p-value"""
        log_rank = statistical_report["log_rank_test"]
        assert "chi_squared_statistic" in log_rank, "Missing chi_squared_statistic"
        assert "p_value" in log_rank, "Missing p_value"
        assert "degrees_of_freedom" in log_rank, "Missing degrees_of_freedom"
        
        assert isinstance(log_rank["chi_squared_statistic"], (int, float)), \
            "chi_squared_statistic must be numeric"
        assert isinstance(log_rank["p_value"], (int, float)), "p_value must be numeric"
        assert isinstance(log_rank["degrees_of_freedom"], int), "degrees_of_freedom must be integer"

    def test_median_survival_lengths(self, statistical_report: Dict[str, Any]):
        """Median survival lengths must be reported for both models"""
        medians = statistical_report["median_survival_lengths"]
        assert "lightweight_model" in medians, "Missing lightweight_model median"
        assert "baseline_model" in medians, "Missing baseline_model median"
        
        for model, value in medians.items():
            assert isinstance(value, (int, float)), f"{model} median must be numeric"
            assert value > 0, f"{model} median must be positive"

    def test_confidence_intervals_structure(self, statistical_report: Dict[str, Any]):
        """Confidence intervals must have lower and upper bounds"""
        ci = statistical_report["confidence_intervals"]
        assert "lightweight_model" in ci, "Missing lightweight_model CI"
        assert "baseline_model" in ci, "Missing baseline_model CI"
        
        for model, interval in ci.items():
            assert "lower_bound" in interval, f"Missing lower_bound for {model}"
            assert "upper_bound" in interval, f"Missing upper_bound for {model}"
            assert "confidence_level" in interval, f"Missing confidence_level for {model}"
            
            assert isinstance(interval["lower_bound"], (int, float)), \
                f"{model} lower_bound must be numeric"
            assert isinstance(interval["upper_bound"], (int, float)), \
                f"{model} upper_bound must be numeric"
            assert interval["lower_bound"] <= interval["upper_bound"], \
                f"{model} lower_bound must be <= upper_bound"

    def test_inflection_point_summary(self, statistical_report: Dict[str, Any]):
        """Inflection point summary must include key findings"""
        summary = statistical_report["inflection_point_summary"]
        assert "final_inflection_length" in summary, "Missing final_inflection_length"
        assert "adjusted_p_value" in summary, "Missing adjusted_p_value"
        assert "validity_gap_at_inflection" in summary, "Missing validity_gap_at_inflection"
        
        assert isinstance(summary["final_inflection_length"], int), \
            "final_inflection_length must be integer"
        assert isinstance(summary["adjusted_p_value"], (int, float)), \
            "adjusted_p_value must be numeric"
        assert isinstance(summary["validity_gap_at_inflection"], (int, float)), \
            "validity_gap_at_inflection must be numeric"

    def test_methodology_description(self, statistical_report: Dict[str, Any]):
        """Methodology must be a non-empty string"""
        methodology = statistical_report["methodology"]
        assert isinstance(methodology, str), "methodology must be a string"
        assert len(methodology) > 0, "methodology must not be empty"


class TestSchemaFilesExist:
    """Ensure all expected statistical output files exist before running schema tests"""

    def test_survival_data_exists(self):
        """Check survival_data.json exists"""
        file_path = ANALYSIS_DIR / "survival_data.json"
        assert file_path.exists(), f"Missing required file: {file_path}"

    def test_inflection_report_exists(self):
        """Check final_inflection_report.json exists"""
        file_path = ANALYSIS_DIR / "final_inflection_report.json"
        assert file_path.exists(), f"Missing required file: {file_path}"

    def test_statistical_report_exists(self):
        """Check statistical_report.json exists"""
        file_path = ANALYSIS_DIR / "statistical_report.json"
        assert file_path.exists(), f"Missing required file: {file_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
