"""
Unit tests for the ``t040_create_comparison_report`` script.

The tests create minimal baseline and cleaned metric JSON files, invoke the
``generate_comparison_report`` function and verify that:

* The returned object is an instance of ``ComparisonReport``.
* The output JSON file exists and contains the expected keys.
* Absolute and relative differences are computed correctly for a simple
  numeric example.
"""

import json
from pathlib import Path

import pytest

from t040_create_comparison_report import generate_comparison_report
from models import ComparisonReport


@pytest.fixture
def baseline_file(tmp_path: Path) -> Path:
    data = {
        "t_test": {"p_value": 0.04, "ci": [0.1, 0.5], "effect_size": 0.8},
        "linear_regression": {"p_value": 0.03, "ci": [0.2, 0.6], "r_squared": 0.55},
    }
    path = tmp_path / "baseline_metrics.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture
def cleaned_file(tmp_path: Path) -> Path:
    data = {
        "t_test": {"p_value": 0.08, "ci": [0.15, 0.55], "effect_size": 0.6},
        "linear_regression": {"p_value": 0.07, "ci": [0.25, 0.65], "r_squared": 0.50},
    }
    path = tmp_path / "cleaned_metrics.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture
def output_file(tmp_path: Path) -> Path:
    return tmp_path / "comparison_report.json"


def test_generate_comparison_report(
    baseline_file: Path,
    cleaned_file: Path,
    output_file: Path,
) -> None:
    # Run the function with the temporary paths
    report: ComparisonReport = generate_comparison_report(
        baseline_path=baseline_file,
        cleaned_path=cleaned_file,
        output_path=output_file,
    )

    # Verify the returned type
    assert isinstance(report, ComparisonReport)

    # Verify the output file exists and is non‑empty
    assert output_file.is_file()
    content = json.loads(output_file.read_text(encoding="utf-8"))
    expected_keys = {
        "baseline_metrics",
        "cleaned_metrics",
        "absolute_diff",
        "relative_diff",
        "sensitivity_analysis",
    }
    assert set(content.keys()) == expected_keys

    # Spot‑check a computed absolute difference (p_value shift for t_test)
    # The helper ``calculate_absolute_diff`` is expected to compute the simple
    # difference between the two metric values.
    abs_diff = content["absolute_diff"]
    assert "t_test" in abs_diff
    # Expected absolute difference for p_value = 0.08 - 0.04 = 0.04
    assert abs(abs_diff["t_test"]["p_value"] - 0.04) < 1e-6

    # Spot‑check a relative difference (effect_size change for t_test)
    rel_diff = content["relative_diff"]
    assert "t_test" in rel_diff
    # Relative change = (0.6 - 0.8) / 0.8 = -0.25
    assert abs(rel_diff["t_test"]["effect_size"] + 0.25) < 1e-6

    # Sensitivity analysis placeholder should be an empty dict
    assert content["sensitivity_analysis"] == {}