"""
Contract tests for code/analysis/statistical_tests.py output.

These tests validate that the statistical analysis module produces
output conforming to the expected schema defined in the project contracts.
"""

import json
import os
import sys
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_path, get_config

# Expected schema structure for statistical report output
STATISTICAL_REPORT_SCHEMA = {
    "required_fields": [
        "ks_test",
        "mann_whitney_u_test",
        "survival_analysis",
        "threshold_sensitivity",
        "collinearity_diagnostics",
        "summary"
    ],
    "ks_test": {
        "required_fields": ["statistic", "pvalue", "null_hypothesis", "rejection_result"],
        "field_types": {
            "statistic": (float, int),
            "pvalue": (float, int),
            "null_hypothesis": str,
            "rejection_result": bool
        }
    },
    "mann_whitney_u_test": {
        "required_fields": ["statistic", "pvalue", "null_hypothesis", "rejection_result"],
        "field_types": {
            "statistic": (float, int),
            "pvalue": (float, int),
            "null_hypothesis": str,
            "rejection_result": bool
        }
    },
    "survival_analysis": {
        "required_fields": ["median_survival_time", "survival_curve_data", "logrank_test"],
        "field_types": {
            "median_survival_time": (float, int, type(None)),
            "survival_curve_data": list,
            "logrank_test": dict
        }
    },
    "threshold_sensitivity": {
        "required_fields": ["thresholds", "false_positive_rates", "false_negative_rates"],
        "field_types": {
            "thresholds": list,
            "false_positive_rates": list,
            "false_negative_rates": list
        }
    },
    "collinearity_diagnostics": {
        "required_fields": ["vif_scores"],
        "field_types": {
            "vif_scores": dict
        }
    },
    "summary": {
        "required_fields": ["null_hypothesis_rejected", "effect_size_cohen_d", "significance_level"],
        "field_types": {
            "null_hypothesis_rejected": bool,
            "effect_size_cohen_d": (float, int),
            "significance_level": (float, int)
        }
    }
}

def validate_schema_compliance(data: Dict[str, Any], schema: Dict[str, Any], path_prefix: str = "") -> List[str]:
    """
    Validate that the statistical report output conforms to the expected schema.

    Args:
        data: The statistical report data to validate
        schema: The expected schema definition
        path_prefix: Current path prefix for error messages

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Check required fields
    for field in schema.get("required_fields", []):
        if field not in data:
            errors.append(f"Missing required field: {path_prefix}.{field}")

    # Check field types
    if "field_types" in schema:
        for field, expected_types in schema["field_types"].items():
            if field in data:
                if not isinstance(data[field], expected_types):
                    errors.append(
                        f"Type mismatch for {path_prefix}.{field}: "
                        f"expected {expected_types}, got {type(data[field])}"
                    )
                # Recursively validate nested structures
                if isinstance(expected_types, dict) and isinstance(data[field], dict):
                    nested_errors = validate_schema_compliance(
                        data[field], expected_types, f"{path_prefix}.{field}"
                    )
                    errors.extend(nested_errors)

    return errors

def load_statistical_report() -> Dict[str, Any]:
    """
    Load the statistical report from the expected output location.

    Returns:
        The statistical report data as a dictionary

    Raises:
        FileNotFoundError: If the report file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    config = get_config()
    report_path = get_path(config, "statistical_report_path")

    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Statistical report not found at: {report_path}")

    with open(report_path, 'r') as f:
        return json.load(f)

def test_statistical_report_schema_compliance():
    """
    Contract test: Verify that the statistical report output conforms to the expected schema.
    """
    try:
        report = load_statistical_report()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        pytest.fail(f"Failed to load statistical report: {e}")

    errors = validate_schema_compliance(report, STATISTICAL_REPORT_SCHEMA, "root")

    if errors:
        pytest.fail(f"Statistical report schema validation failed:\n" + "\n".join(errors))

def test_ks_test_validity():
    """
    Contract test: Verify that the Kolmogorov-Smirnov test output contains valid values.
    """
    try:
        report = load_statistical_report()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        pytest.fail(f"Failed to load statistical report: {e}")

    if "ks_test" not in report:
        pytest.fail("Missing 'ks_test' field in statistical report")

    ks_test = report["ks_test"]

    # Validate statistic is non-negative
    if not isinstance(ks_test.get("statistic"), (int, float)) or ks_test["statistic"] < 0:
        pytest.fail(f"Invalid KS test statistic: {ks_test.get('statistic')}")

    # Validate p-value is in [0, 1]
    if not isinstance(ks_test.get("pvalue"), (int, float)) or not (0 <= ks_test["pvalue"] <= 1):
        pytest.fail(f"Invalid KS test p-value: {ks_test.get('pvalue')}")

    # Validate rejection result is boolean
    if not isinstance(ks_test.get("rejection_result"), bool):
        pytest.fail(f"Invalid KS test rejection_result: {ks_test.get('rejection_result')}")

def test_mann_whitney_u_test_validity():
    """
    Contract test: Verify that the Mann-Whitney U test output contains valid values.
    """
    try:
        report = load_statistical_report()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        pytest.fail(f"Failed to load statistical report: {e}")

    if "mann_whitney_u_test" not in report:
        pytest.fail("Missing 'mann_whitney_u_test' field in statistical report")

    mw_test = report["mann_whitney_u_test"]

    # Validate statistic is non-negative
    if not isinstance(mw_test.get("statistic"), (int, float)) or mw_test["statistic"] < 0:
        pytest.fail(f"Invalid Mann-Whitney U test statistic: {mw_test.get('statistic')}")

    # Validate p-value is in [0, 1]
    if not isinstance(mw_test.get("pvalue"), (int, float)) or not (0 <= mw_test["pvalue"] <= 1):
        pytest.fail(f"Invalid Mann-Whitney U test p-value: {mw_test.get('pvalue')}")

    # Validate rejection result is boolean
    if not isinstance(mw_test.get("rejection_result"), bool):
        pytest.fail(f"Invalid Mann-Whitney U test rejection_result: {mw_test.get('rejection_result')}")

def test_survival_analysis_structure():
    """
    Contract test: Verify that the survival analysis output has the correct structure.
    """
    try:
        report = load_statistical_report()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        pytest.fail(f"Failed to load statistical report: {e}")

    if "survival_analysis" not in report:
        pytest.fail("Missing 'survival_analysis' field in statistical report")

    survival = report["survival_analysis"]

    # Validate survival_curve_data is a list
    if not isinstance(survival.get("survival_curve_data"), list):
        pytest.fail(f"Invalid survival_curve_data type: {type(survival.get('survival_curve_data'))}")

    # Validate logrank_test is a dict
    if not isinstance(survival.get("logrank_test"), dict):
        pytest.fail(f"Invalid logrank_test type: {type(survival.get('logrank_test'))}")

def test_threshold_sensitivity_arrays():
    """
    Contract test: Verify that threshold sensitivity analysis has matching array lengths.
    """
    try:
        report = load_statistical_report()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        pytest.fail(f"Failed to load statistical report: {e}")

    if "threshold_sensitivity" not in report:
        pytest.fail("Missing 'threshold_sensitivity' field in statistical report")

    sensitivity = report["threshold_sensitivity"]

    thresholds = sensitivity.get("thresholds", [])
    fpr = sensitivity.get("false_positive_rates", [])
    fnr = sensitivity.get("false_negative_rates", [])

    # Validate all arrays have the same length
    if not (len(thresholds) == len(fpr) == len(fnr)):
        pytest.fail(
            f"Threshold sensitivity arrays have mismatched lengths: "
            f"thresholds={len(thresholds)}, FPR={len(fpr)}, FNR={len(fnr)}"
        )

    # Validate thresholds are sorted
    if thresholds != sorted(thresholds):
        pytest.fail("Thresholds are not sorted in ascending order")

def test_collinearity_diagnostics_vif():
    """
    Contract test: Verify that VIF scores are present and valid.
    """
    try:
        report = load_statistical_report()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        pytest.fail(f"Failed to load statistical report: {e}")

    if "collinearity_diagnostics" not in report:
        pytest.fail("Missing 'collinearity_diagnostics' field in statistical report")

    collinearity = report["collinearity_diagnostics"]

    if "vif_scores" not in collinearity:
        pytest.fail("Missing 'vif_scores' in collinearity_diagnostics")

    vif_scores = collinearity["vif_scores"]

    # Validate VIF scores are a dict with numeric values
    if not isinstance(vif_scores, dict):
        pytest.fail(f"Invalid vif_scores type: {type(vif_scores)}")

    for var_name, vif_value in vif_scores.items():
        if not isinstance(vif_value, (int, float)) or vif_value < 1:
            pytest.fail(f"Invalid VIF score for {var_name}: {vif_value}")

def test_summary_conclusion_consistency():
    """
    Contract test: Verify that the summary conclusion is consistent with test results.
    """
    try:
        report = load_statistical_report()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        pytest.fail(f"Failed to load statistical report: {e}")

    if "summary" not in report:
        pytest.fail("Missing 'summary' field in statistical report")

    summary = report["summary"]

    # Check that null_hypothesis_rejected is a boolean
    if not isinstance(summary.get("null_hypothesis_rejected"), bool):
        pytest.fail(f"Invalid null_hypothesis_rejected type: {type(summary.get('null_hypothesis_rejected'))}")

    # Check that effect_size_cohen_d is numeric
    if not isinstance(summary.get("effect_size_cohen_d"), (int, float)):
        pytest.fail(f"Invalid effect_size_cohen_d type: {type(summary.get('effect_size_cohen_d'))}")

    # Check significance level is in (0, 1]
    sig_level = summary.get("significance_level")
    if not isinstance(sig_level, (int, float)) or not (0 < sig_level <= 1):
        pytest.fail(f"Invalid significance_level: {sig_level}")