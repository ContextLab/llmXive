"""
Contract test for T027 – verifies that the generated sensitivity summary
markdown file exists, contains a ``stability`` field, and that the
stability value matches the computed condition based on the source JSON
reports.

The test deliberately creates minimal yet realistic JSON reports in the
``artifacts/reports`` directory before invoking the summary generator.
"""

import json
from pathlib import Path

import pytest

from training.generate_sensitivity_summary import generate_summary, STABILITY_THRESHOLD


@pytest.fixture
def dummy_reports(tmp_path):
    """
    Create temporary ``sensitivity_report.json`` and ``ablation_report.json``
    files with known Pearson r values.
    """
    # Ensure the artifacts/reports directory exists relative to the project root
    root = Path.cwd()
    reports_dir = root / "artifacts" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Sensitivity report with three r values
    sens_report = {
        "sweeps": [
            {"config": {"layers": 1}, "pearson_r": 0.78},
            {"config": {"layers": 2}, "pearson_r": 0.81},
            {"config": {"layers": 3}, "pearson_r": 0.74},
        ]
    }
    (reports_dir / "sensitivity_report.json").write_text(
        json.dumps(sens_report), encoding="utf-8"
    )

    # Ablation report with two r values (gnn and baseline)
    ablat_report = {
        "gnn_pearson_r": 0.79,
        "baseline_pearson_r": 0.68,  # below threshold to trigger 'unstable'
    }
    (reports_dir / "ablation_report.json").write_text(
        json.dumps(ablat_report), encoding="utf-8"
    )

    return reports_dir


def test_sensitivity_summary_produces_file_and_stability(tmp_path, dummy_reports):
    # Run the summary generation
    generate_summary()

    summary_path = dummy_reports / "sensitivity_summary.md"
    assert summary_path.is_file(), "Summary markdown file was not created."

    content = summary_path.read_text(encoding="utf-8")

    # Verify the stability field exists and is correctly set to 'unstable'
    assert "`stability`: `unstable`" in content or "**stability:** `unstable`" in content

    # Compute expected stability manually
    all_r = [0.78, 0.81, 0.74, 0.79, 0.68]
    expected_stable = all(r >= STABILITY_THRESHOLD for r in all_r)
    expected_str = "stable" if expected_stable else "unstable"

    assert f"`stability`: `{expected_str}`" in content or f"**stability:** `{expected_str}`" in content