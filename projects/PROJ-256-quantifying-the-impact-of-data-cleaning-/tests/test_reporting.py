import json
import os
import tempfile
from pathlib import Path

from reporting import (
    calculate_absolute_diff,
    calculate_relative_diff,
    calculate_inconsistency_rate,
    aggregate_metrics_for_comparison,
    generate_comparison_report,
)


def _make_dummy_metrics(tmp_dir: Path, name: str, p_value: float, ci_low: float, ci_high: float, r2: float):
    data = {
        "datasets": [
            {
                "dataset_name": name,
                "t_test": {"p_value": p_value, "ci": [ci_low, ci_high]},
                "regression": {"r_squared": r2, "coefficients": []},
            }
        ]
    }
    path = tmp_dir / f"{name}_{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


def test_absolute_and_relative_differences(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    cleaned_path = tmp_path / "cleaned.json"

    baseline = {
        "datasets": [
            {
                "dataset_name": "ds1",
                "t_test": {"p_value": 0.10, "ci": [0.5, 1.5]},
                "regression": {"r_squared": 0.30, "coefficients": []},
            }
        ]
    }
    cleaned = {
        "datasets": [
            {
                "dataset_name": "ds1",
                "t_test": {"p_value": 0.08, "ci": [0.6, 1.4]},
                "regression": {"r_squared": 0.35, "coefficients": []},
            }
        ]
    }

    with baseline_path.open("w", encoding="utf-8") as f:
        json.dump(baseline, f)
    with cleaned_path.open("w", encoding="utf-8") as f:
        json.dump(cleaned, f)

    abs_diff = calculate_absolute_diff(baseline, cleaned)
    rel_diff = calculate_relative_diff(baseline, cleaned)
    inc_rate = calculate_inconsistency_rate(baseline, cleaned, alpha=0.05)

    assert abs_diff[0]["p_value_abs_diff"] == round(abs(0.08 - 0.10), 3)
    assert abs_diff[0]["ci_width_abs_diff"] == round(abs((1.4 - 0.6) - (1.5 - 0.5)), 2)
    assert rel_diff[0]["p_value_rel_diff_pct"] == round(abs(0.08 - 0.10) / 0.10 * 100, 2)
    # Since both p-values are > 0.05, significance does not change -> rate 0.0
    assert inc_rate == 0.0


def test_generate_comparison_report_writes_file(tmp_path):
    baseline = {
        "datasets": [
            {
                "dataset_name": "ds1",
                "t_test": {"p_value": 0.12, "ci": [0.4, 1.2]},
                "regression": {"r_squared": 0.25, "coefficients": []},
            }
        ]
    }
    cleaned = {
        "datasets": [
            {
                "dataset_name": "ds1",
                "t_test": {"p_value": 0.09, "ci": [0.5, 1.1]},
                "regression": {"r_squared": 0.28, "coefficients": []},
            }
        ]
    }

    baseline_path = tmp_path / "baseline_metrics.json"
    cleaned_path = tmp_path / "cleaned_metrics.json"
    output_path = tmp_path / "comparison_report.json"

    baseline_path.write_text(json.dumps(baseline))
    cleaned_path.write_text(json.dumps(cleaned))

    generate_comparison_report(
        baseline_path=str(baseline_path),
        cleaned_path=str(cleaned_path),
        output_path=str(output_path),
    )

    assert output_path.exists()
    report = json.loads(output_path.read_text())
    assert "absolute_differences" in report
    assert "relative_differences" in report
    assert "inconsistency_rate" in report