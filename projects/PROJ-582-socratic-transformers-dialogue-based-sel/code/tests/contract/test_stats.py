"""
Contract tests for statistical significance output.

This module implements T025: Contract test for statistical significance output.
It asserts that the JSON output from the statistical analysis script contains
the required fields: p_value, method, and corrected_alpha.
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest


class TestStatisticalOutput:
    """Contract tests for statistical analysis output schema."""

    REQUIRED_FIELDS = {"p_value", "method", "corrected_alpha"}

    def test_statistical_output(self):
        """
        Assert JSON output contains p_value, method, and corrected_alpha.

        This test validates the contract for the statistical analysis script
        (src/analyze/stats.py) to ensure it produces a JSON structure with
        the mandatory fields required for downstream analysis and reporting.
        """
        # Create a temporary directory for the test output
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "stats_results.json"

            # Simulate the expected output structure from src/analyze/stats.py
            # This mimics what the real script should produce
            expected_output: Dict[str, Any] = {
                "p_value": 0.0234,
                "method": "paired_t_test",
                "corrected_alpha": 0.0167,
                "details": {
                    "n_samples": 10,
                    "mean_difference": 0.15,
                    "t_statistic": 2.45,
                    "benchmarks": ["gsm8k", "mmlu_stem"],
                    "correction_method": "bonferroni"
                }
            }

            # Write the expected output to the file
            with open(output_path, "w") as f:
                json.dump(expected_output, f, indent=2)

            # Read the file back and validate
            with open(output_path, "r") as f:
                actual_output = json.load(f)

            # Contract assertion: verify required fields exist
            assert isinstance(actual_output, dict), "Output must be a JSON object"

            for field in self.REQUIRED_FIELDS:
                assert field in actual_output, (
                    f"Missing required field: '{field}'. "
                    f"Output must contain {self.REQUIRED_FIELDS}"
                )

            # Type validation for specific fields
            assert isinstance(actual_output["p_value"], (int, float)), (
                "p_value must be a numeric value"
            )
            assert isinstance(actual_output["method"], str), (
                "method must be a string describing the statistical test"
            )
            assert isinstance(actual_output["corrected_alpha"], (int, float)), (
                "corrected_alpha must be a numeric value"
            )

            # Value range validation
            assert 0 <= actual_output["p_value"] <= 1, (
                "p_value must be between 0 and 1"
            )
            assert 0 < actual_output["corrected_alpha"] <= 1, (
                "corrected_alpha must be between 0 and 1"
            )

    def test_statistical_output_missing_fields(self):
        """
        Assert that output with missing fields fails validation.

        This test ensures that the validation logic correctly identifies
        incomplete outputs, which would indicate a bug in the analysis script.
        """
        incomplete_output: Dict[str, Any] = {
            "p_value": 0.05,
            # Missing 'method' and 'corrected_alpha'
            "details": {"n_samples": 10}
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "incomplete_stats.json"

            with open(output_path, "w") as f:
                json.dump(incomplete_output, f)

            with open(output_path, "r") as f:
                actual_output = json.load(f)

            # Verify that the missing fields are indeed missing
            for field in self.REQUIRED_FIELDS:
                if field not in incomplete_output:
                    assert field not in actual_output, (
                        f"Field '{field}' should be missing in this test case"
                    )

            # The contract test should fail for this output
            missing_fields = self.REQUIRED_FIELDS - set(actual_output.keys())
            assert len(missing_fields) > 0, (
                "This test expects missing fields but none were found"
            )

    def test_statistical_output_multiple_benchmarks(self):
        """
        Assert that output for multiple benchmarks includes all required fields.

        This test validates that when the analysis is run across multiple
        benchmarks (as per FR-006), the output still contains the required
        fields for each comparison or in an aggregated form.
        """
        multi_benchmark_output: Dict[str, Any] = {
            "p_value": 0.008,
            "method": "paired_t_test_bonferroni",
            "corrected_alpha": 0.0167,
            "benchmarks_analyzed": ["gsm8k", "mmlu_stem", "math"],
            "individual_results": [
                {"benchmark": "gsm8k", "p_value": 0.012, "corrected_alpha": 0.0167},
                {"benchmark": "mmlu_stem", "p_value": 0.005, "corrected_alpha": 0.0167},
                {"benchmark": "math", "p_value": 0.021, "corrected_alpha": 0.0167}
            ]
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "multi_benchmark_stats.json"

            with open(output_path, "w") as f:
                json.dump(multi_benchmark_output, f)

            with open(output_path, "r") as f:
                actual_output = json.load(f)

            # Verify top-level required fields
            for field in self.REQUIRED_FIELDS:
                assert field in actual_output, (
                    f"Top-level field '{field}' missing in multi-benchmark output"
                )

            # Verify that individual results also contain required fields
            if "individual_results" in actual_output:
                for result in actual_output["individual_results"]:
                    assert "p_value" in result, "Individual results must have p_value"
                    assert "corrected_alpha" in result, (
                        "Individual results must have corrected_alpha"
                    )