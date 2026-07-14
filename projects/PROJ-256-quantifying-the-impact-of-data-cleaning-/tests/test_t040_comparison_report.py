import json
import os
from pathlib import Path

import pytest

from t040_create_comparison_report import main as generate_report

@pytest.fixture
def dummy_metrics(tmp_path):
    """Create dummy baseline and cleaned metric JSON files."""
    baseline = {
        "p_value": 0.123,
        "ci_lower": 0.1,
        "ci_upper": 0.2,
        "effect_size_r2": 0.45,
    }
    cleaned = {
        "p_value": 0.067,
        "ci_lower": 0.05,
        "ci_upper": 0.15,
        "effect_size_r2": 0.55,
    }
    # Write files
    raw_dir = Path("data/processed")
    raw_dir.mkdir(parents=True, exist_ok=True)
    with open(raw_dir / "baseline_metrics.json", "w", encoding="utf-8") as f:
        json.dump(baseline, f)
    with open(raw_dir / "cleaned_metrics.json", "w", encoding="utf-8") as f:
        json.dump(cleaned, f)
    return raw_dir

def test_comparison_report_creation(tmp_path, monkeypatch, dummy_metrics):
    """
    Verify that the comparison report script creates a JSON file with the
    expected structure and that the numeric differences are computed.
    """
    # Ensure the script sees the dummy files
    monkeypatch.chdir(tmp_path)

    # Run the script
    generate_report()

    report_path = Path("data/processed/comparison_report.json")
    assert report_path.is_file(), "Report file was not created"

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    # Basic structure checks
    assert "baseline_metrics" in report
    assert "cleaned_metrics" in report
    assert "absolute_diff" in report
    assert "relative_diff" in report

    # Verify a known absolute difference
    assert report["absolute_diff"]["p_value"] == pytest.approx(0.056, rel=1e-3)

    # Verify relative difference calculation
    expected_rel = (0.067 - 0.123) / 0.123
    assert report["relative_diff"]["p_value"] == pytest.approx(expected_rel, rel=1e-3)