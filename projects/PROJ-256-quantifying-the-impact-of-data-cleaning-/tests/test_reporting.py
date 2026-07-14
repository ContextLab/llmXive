import json
import os
from pathlib import Path

import pytest

from reporting import (
    calculate_absolute_diff,
    calculate_relative_diff,
    calculate_inconsistency_rate,
)

@pytest.fixture
def dummy_metrics():
    """Two tiny metric dicts mimicking the structure produced by analysis."""
    baseline = {
        "t_test": {"p_value": 0.04, "ci": [0.1, 0.5]},
        "effect_size": 0.8,
    }
    cleaned = {
        "t_test": {"p_value": 0.06, "ci": [0.2, 0.6]},
        "effect_size": 0.5,
    }
    return baseline, cleaned

def test_absolute_diff(dummy_metrics):
    base, clean = dummy_metrics
    diff = calculate_absolute_diff(base, clean)
    assert diff["p_value_abs"] == pytest.approx(0.02, rel=1e-3)
    assert diff["ci_width_change_abs"] == pytest.approx(0.2, rel=1e-3)
    assert diff["effect_size_delta"] == pytest.approx(-0.3, rel=1e-3)

def test_relative_diff(dummy_metrics):
    base, clean = dummy_metrics
    rel = calculate_relative_diff(base, clean)
    # p‑value increase from 0.04 to 0.06 → 50 %
    assert rel["p_value_rel"] == pytest.approx(50.0, rel=1e-3)
    # CI width: base 0.4, clean 0.4 → 0 %
    assert rel["ci_width_rel"] == pytest.approx(0.0, rel=1e-3)
    # Effect size change from 0.8 to 0.5 → -37.5 %
    assert rel["effect_size_rel"] == pytest.approx(-37.5, rel=1e-3)

def test_inconsistency_rate():
    base = {"t_test": {"p_value": 0.03}}
    clean = {"t_test": {"p_value": 0.07}}
    assert calculate_inconsistency_rate(base, clean) == 1.0
    clean2 = {"t_test": {"p_value": 0.02}}
    assert calculate_inconsistency_rate(base, clean2) == 0.0

def test_report_generation(tmp_path, monkeypatch):
    """
    End‑to‑end test that the reporting module writes a comparison JSON file.
    """
    # Create temporary baseline / cleaned JSON files
    baseline_path = tmp_path / "baseline.json"
    cleaned_path = tmp_path / "cleaned.json"
    baseline_path.write_text(json.dumps({"ds.csv": {
        "t_test": {"p_value": 0.04, "ci": [0.1, 0.5]},
        "effect_size": 0.8,
    }}))
    cleaned_path.write_text(json.dumps({"ds.csv": {
        "t_test": {"p_value": 0.06, "ci": [0.2, 0.6]},
        "effect_size": 0.5,
    }}))

    # Patch the paths used inside reporting
    monkeypatch.setattr("reporting.load_baseline_metrics", lambda: json.loads(baseline_path.read_text()))
    monkeypatch.setattr("reporting.load_cleaned_metrics", lambda: json.loads(cleaned_path.read_text()))

    # Run report generation
    from reporting import generate_comparison_report

    report = generate_comparison_report()
    assert "ds.csv" in report
    assert report["ds.csv"]["absolute_diff"]["p_value_abs"] == pytest.approx(0.02, rel=1e-3)

    # Verify file was written to the expected location
    output_file = Path("data/processed/comparison_report.json")
    assert output_file.is_file()
    content = json.loads(output_file.read_text())
    assert content == report

    # Cleanup created file
    output_file.unlink()