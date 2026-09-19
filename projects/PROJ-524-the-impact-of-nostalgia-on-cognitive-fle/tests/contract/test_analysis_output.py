"""
Contract tests for statistical output schema (User Story 2).

This module validates that the statistical analysis output produced by
code/analysis.py and related task modules adheres to the schema defined
in contracts/output.schema.yaml.

It ensures that:
1. The statistical_report.json file exists and is valid JSON.
2. All required top-level keys are present (p_values, corrected_p_values,
   effect_sizes, power_analysis, sensitivity).
3. Nested structures match the expected format (e.g., dictionaries for
   'perseverative_errors' and 'categories_completed').
4. Numeric fields are valid floats/ints and not None (unless explicitly allowed).
5. Confidence intervals are lists of two numbers.
"""
import os
import json
import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import project utilities if needed for path resolution
# Assuming tests are run from project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
REPORT_PATH = RESULTS_DIR / "statistical_report.json"

# Fallback for testing before generation (optional, but good for CI)
# If the report doesn't exist, we might skip or mark as pending depending on CI strategy.
# For contract tests, we usually assume the pipeline has run or we test against a fixture.
# Here, we will assert the schema structure if the file exists.
# If the file is missing, we raise a clear error indicating the pipeline hasn't run yet.

def load_report() -> Dict[str, Any]:
    """Load the statistical report. Raises FileNotFoundError if missing."""
    if not REPORT_PATH.exists():
        pytest.fail(
            f"Statistical report not found at {REPORT_PATH}. "
            "Please run the analysis pipeline (T018-T022) before running contract tests."
        )
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_numeric(value: Any, field_name: str) -> None:
    """Assert that a value is a valid number (int or float)."""
    if not isinstance(value, (int, float)):
        raise AssertionError(f"Field '{field_name}' must be numeric, got {type(value).__name__}")
    if isinstance(value, float) and (value != value):  # NaN check
        raise AssertionError(f"Field '{field_name}' must not be NaN")

def validate_confidence_interval(ci: Any, field_name: str) -> None:
    """Assert that a confidence interval is a list of two numbers."""
    if not isinstance(ci, list):
        raise AssertionError(f"Field '{field_name}' must be a list, got {type(ci).__name__}")
    if len(ci) != 2:
        raise AssertionError(f"Field '{field_name}' must have exactly 2 elements (lower, upper), got {len(ci)}")
    validate_numeric(ci[0], f"{field_name}[0]")
    validate_numeric(ci[1], f"{field_name}[1]")
    # Optional: ensure lower <= upper
    if ci[0] > ci[1]:
        raise AssertionError(f"Field '{field_name}' lower bound ({ci[0]}) > upper bound ({ci[1]})")

class TestStatisticalReportSchema:
    """Contract tests for the statistical_report.json schema."""

    def test_report_exists(self):
        """Verify that the statistical report file exists."""
        assert REPORT_PATH.exists(), f"File {REPORT_PATH} does not exist"

    def test_top_level_keys(self):
        """Verify all required top-level keys are present."""
        report = load_report()
        required_keys = [
            "p_values",
            "corrected_p_values",
            "effect_sizes",
            "power_analysis",
            "sensitivity"
        ]
        missing_keys = [k for k in required_keys if k not in report]
        assert not missing_keys, f"Missing required top-level keys: {missing_keys}"

    def test_p_values_structure(self):
        """Verify p_values structure for both metrics."""
        report = load_report()
        p_values = report["p_values"]
        
        required_metrics = ["perseverative_errors", "categories_completed"]
        for metric in required_metrics:
            assert metric in p_values, f"Missing metric '{metric}' in p_values"
            val = p_values[metric]
            validate_numeric(val, f"p_values.{metric}")
            # p-value must be between 0 and 1
            assert 0 <= val <= 1, f"p_value for {metric} ({val}) is out of range [0, 1]"

    def test_corrected_p_values_structure(self):
        """Verify corrected_p_values structure (Bonferroni)."""
        report = load_report()
        corrected = report["corrected_p_values"]
        
        required_metrics = ["perseverative_errors", "categories_completed"]
        for metric in required_metrics:
            assert metric in corrected, f"Missing metric '{metric}' in corrected_p_values"
            val = corrected[metric]
            validate_numeric(val, f"corrected_p_values.{metric}")
            # Corrected p-value must be between 0 and 1
            assert 0 <= val <= 1, f"corrected p_value for {metric} ({val}) is out of range [0, 1]"

    def test_effect_sizes_structure(self):
        """Verify effect_sizes structure (Cohen's d with CIs)."""
        report = load_report()
        effects = report["effect_sizes"]
        
        required_metrics = ["perseverative_errors", "categories_completed"]
        for metric in required_metrics:
            assert metric in effects, f"Missing metric '{metric}' in effect_sizes"
            effect_data = effects[metric]
            
            # Check for Cohen's d
            assert "cohen_d" in effect_data, f"Missing 'cohen_d' in effect_sizes.{metric}"
            validate_numeric(effect_data["cohen_d"], f"effect_sizes.{metric}.cohen_d")
            
            # Check for 95% CI
            assert "ci_95" in effect_data, f"Missing 'ci_95' in effect_sizes.{metric}"
            validate_confidence_interval(effect_data["ci_95"], f"effect_sizes.{metric}.ci_95")

    def test_power_analysis_structure(self):
        """Verify power_analysis structure (Power and MDES)."""
        report = load_report()
        power_data = report["power_analysis"]
        
        required_metrics = ["perseverative_errors", "categories_completed"]
        for metric in required_metrics:
            assert metric in power_data, f"Missing metric '{metric}' in power_analysis"
            metric_power = power_data[metric]
            
            assert "power" in metric_power, f"Missing 'power' in power_analysis.{metric}"
            validate_numeric(metric_power["power"], f"power_analysis.{metric}.power")
            assert 0 <= metric_power["power"] <= 1, f"Power for {metric} ({metric_power['power']}) out of range [0, 1]"
            
            assert "mdes" in metric_power, f"Missing 'mdes' in power_analysis.{metric}"
            validate_numeric(metric_power["mdes"], f"power_analysis.{metric}.mdes")
            # MDES is typically a positive number (effect size magnitude)
            assert metric_power["mdes"] >= 0, f"MDES for {metric} ({metric_power['mdes']}) is negative"

    def test_sensitivity_structure(self):
        """Verify sensitivity analysis structure."""
        report = load_report()
        sensitivity = report["sensitivity"]
        
        # Expected keys based on T026-T030
        # Should contain threshold sweep results and stability flags
        assert "threshold_sweep" in sensitivity, "Missing 'threshold_sweep' in sensitivity"
        assert "is_sensitive_to_threshold" in sensitivity, "Missing 'is_sensitive_to_threshold' in sensitivity"
        
        # threshold_sweep should be a list of results
        sweep = sensitivity["threshold_sweep"]
        assert isinstance(sweep, list), f"'threshold_sweep' must be a list, got {type(sweep).__name__}"
        
        # Check at least one entry exists if not empty
        if len(sweep) > 0:
            entry = sweep[0]
            assert "threshold" in entry, "Missing 'threshold' in sweep entry"
            validate_numeric(entry["threshold"], "threshold_sweep[0].threshold")
            assert "significant" in entry, "Missing 'significant' in sweep entry"
            assert isinstance(entry["significant"], bool), f"'significant' must be bool, got {type(entry['significant'])}"

    def test_is_sensitive_to_threshold_type(self):
        """Verify the binary flag type."""
        report = load_report()
        sensitivity = report["sensitivity"]
        flag = sensitivity["is_sensitive_to_threshold"]
        assert isinstance(flag, bool), f"is_sensitive_to_threshold must be bool, got {type(flag).__name__}"

    def test_no_nulls_in_required_fields(self):
        """Ensure no critical fields are None."""
        report = load_report()
        
        # Recursively check for None in required structures
        def check_no_none(obj: Any, path: str = ""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if v is None:
                        # Allow None only in specific optional fields if defined
                        # For now, strict check on numeric fields
                        if k in ["cohen_d", "power", "mdes", "threshold", "significant"]:
                            raise AssertionError(f"Field '{path}.{k}' is None")
                    check_no_none(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    check_no_none(v, f"{path}[{i}]")

        check_no_none(report, "root")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])