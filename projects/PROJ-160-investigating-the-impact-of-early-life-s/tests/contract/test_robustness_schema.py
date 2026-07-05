"""Contract tests for robustness output schema.

This module validates that the robustness analysis outputs
strictly adhere to the defined schema in contracts/robustness.schema.yaml.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Add project root to path for imports if running from different location
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import get_project_root

# Expected schema structure based on contracts/robustness.schema.yaml
# This reflects the outputs from T035 (permutation), T037 (sensitivity),
# T038 (ICV restricted), and T039 (aggregate report)

REQUIRED_TOP_LEVEL_KEYS = {
    "permutation_results",
    "sensitivity_analysis",
    "icv_restricted_analysis",
    "primary_model_comparison",
    "metadata"
}

PERMUTATION_RESULT_KEYS = {
    "subfield",
    "observed_statistic",
    "permutation_p_value",
    "num_permutations",
    "null_distribution_mean",
    "null_distribution_std",
    "significant"
}

SENSITIVITY_ANALYSIS_KEYS = {
    "threshold",
    "significant_count",
    "total_tests",
    "variation_metric"
}

ICV_RESTRICTED_KEYS = {
    "subset_criteria",
    "subset_n",
    "effect_size_change_percent",
    "original_effect_size",
    "restricted_effect_size"
}

METADATA_KEYS = {
    "timestamp",
    "permutation_count",
    "alpha_thresholds",
    "random_seed"
}


def load_robustness_report() -> Dict[str, Any]:
    """Load the robustness report JSON file."""
    project_root = get_project_root()
    report_path = project_root / "data" / "processed" / "robustness_report.json"

    if not report_path.exists():
        pytest.fail(f"Robustness report not found at {report_path}. "
                   "Run the robustness pipeline first (T035-T039).")

    with open(report_path, "r") as f:
        return json.load(f)


class TestRobustnessSchema:
    """Contract tests for robustness output schema."""

    def test_top_level_structure(self):
        """Verify the report contains all required top-level keys."""
        report = load_robustness_report()

        missing_keys = REQUIRED_TOP_LEVEL_KEYS - set(report.keys())
        assert not missing_keys, f"Missing top-level keys: {missing_keys}"

    def test_permutation_results_structure(self):
        """Verify permutation results match expected schema."""
        report = load_robustness_report()
        perm_results = report["permutation_results"]

        # Should be a list of results, one per subfield
        assert isinstance(perm_results, list), "permutation_results must be a list"
        assert len(perm_results) > 0, "permutation_results must not be empty"

        for result in perm_results:
            missing = PERMUTATION_RESULT_KEYS - set(result.keys())
            assert not missing, f"Missing keys in permutation result: {missing}"

            # Type checks
            assert isinstance(result["subfield"], str)
            assert isinstance(result["observed_statistic"], (int, float))
            assert isinstance(result["permutation_p_value"], (int, float))
            assert isinstance(result["num_permutations"], int)
            assert isinstance(result["significant"], bool)

    def test_sensitivity_analysis_structure(self):
        """Verify sensitivity analysis matches expected schema."""
        report = load_robustness_report()
        sensitivity = report["sensitivity_analysis"]

        # Should be a list of threshold analyses
        assert isinstance(sensitivity, list), "sensitivity_analysis must be a list"
        assert len(sensitivity) > 0, "sensitivity_analysis must not be empty"

        for entry in sensitivity:
            missing = SENSITIVITY_ANALYSIS_KEYS - set(entry.keys())
            assert not missing, f"Missing keys in sensitivity entry: {missing}"

            # Type checks
            assert isinstance(entry["threshold"], (int, float))
            assert isinstance(entry["significant_count"], int)
            assert isinstance(entry["total_tests"], int)
            assert isinstance(entry["variation_metric"], (int, float))

    def test_icv_restricted_analysis_structure(self):
        """Verify ICV restricted analysis matches expected schema."""
        report = load_robustness_report()
        icv_analysis = report["icv_restricted_analysis"]

        missing = ICV_RESTRICTED_KEYS - set(icv_analysis.keys())
        assert not missing, f"Missing keys in ICV analysis: {missing}"

        # Type checks
        assert isinstance(icv_analysis["subset_criteria"], str)
        assert isinstance(icv_analysis["subset_n"], int)
        assert isinstance(icv_analysis["effect_size_change_percent"], (int, float))
        assert isinstance(icv_analysis["original_effect_size"], (int, float))
        assert isinstance(icv_analysis["restricted_effect_size"], (int, float))

    def test_metadata_structure(self):
        """Verify metadata matches expected schema."""
        report = load_robustness_report()
        metadata = report["metadata"]

        missing = METADATA_KEYS - set(metadata.keys())
        assert not missing, f"Missing keys in metadata: {missing}"

        # Type checks
        assert isinstance(metadata["timestamp"], str)
        assert isinstance(metadata["permutation_count"], int)
        assert isinstance(metadata["alpha_thresholds"], list)
        assert isinstance(metadata["random_seed"], int)

    def test_permutation_p_value_range(self):
        """Verify permutation p-values are within valid range [0, 1]."""
        report = load_robustness_report()

        for result in report["permutation_results"]:
            p_val = result["permutation_p_value"]
            assert 0.0 <= p_val <= 1.0, f"Invalid p-value: {p_val}"

    def test_effect_size_change_calculation(self):
        """Verify effect size change is calculated correctly."""
        report = load_robustness_report()
        icv = report["icv_restricted_analysis"]

        # effect_size_change_percent = ((restricted - original) / original) * 100
        original = icv["original_effect_size"]
        restricted = icv["restricted_effect_size"]
        reported_change = icv["effect_size_change_percent"]

        if original != 0:
            expected_change = ((restricted - original) / original) * 100
            # Allow small floating point tolerance
            assert abs(reported_change - expected_change) < 0.01, \
                f"Effect size change mismatch: reported {reported_change}, expected {expected_change}"

    def test_sensitivity_thresholds_match_config(self):
        """Verify sensitivity thresholds match those in config."""
        from code.config_env import get_alpha_thresholds

        report = load_robustness_report()
        report_thresholds = sorted([entry["threshold"] for entry in report["sensitivity_analysis"]])
        config_thresholds = sorted(get_alpha_thresholds())

        assert report_thresholds == config_thresholds, \
            f"Threshold mismatch: report {report_thresholds} vs config {config_thresholds}"

    def test_primary_model_comparison_structure(self):
        """Verify primary model comparison exists and has expected structure."""
        report = load_robustness_report()
        comparison = report["primary_model_comparison"]

        # Should contain comparison between parametric and permutation results
        assert isinstance(comparison, dict), "primary_model_comparison must be a dict"
        assert "parametric_p_values" in comparison
        assert "permutation_p_values" in comparison
        assert "concordance" in comparison

        assert isinstance(comparison["parametric_p_values"], dict)
        assert isinstance(comparison["permutation_p_values"], dict)
        assert isinstance(comparison["concordance"], (int, float))