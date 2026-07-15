"""
Unit tests for the reporting module introduced in Task T027.
The tests use a tiny synthetic baseline / cleaned metric structure that mimics the
shape produced by the analysis step.
"""

import json
from pathlib import Path

import pytest

from reporting import (
    calculate_absolute_diff,
    calculate_relative_diff,
    calculate_inconsistency_rate,
    generate_comparison_report,
    save_json_file,
)

@pytest.fixture
def synthetic_metrics(tmp_path: Path):
    """Create minimal baseline / cleaned metric JSON files for testing."""
    baseline = {
        "ds1": {
            "t_test": {
                "p_value": 0.04,
                "ci": [0.1, 0.5],
                "effect_size": 0.8,
            }
        },
        "ds2": {
            "t_test": {
                "p_value": 0.20,
                "ci": [0.2, 0.6],
                "effect_size": 0.3,
            }
        },
    }
    cleaned = {
        "ds1": {
            "t_test": {
                "p_value": 0.07,  # flips significance
                "ci": [0.15, 0.55],
                "effect_size": 0.75,
            }
        },
        "ds2": {
            "t_test": {
                "p_value": 0.18,  # still non‑significant
                "ci": [0.25, 0.65],
                "effect_size": 0.35,
            }
        },
    }

    # write files where the reporting module expects them
    baseline_path = Path("data/processed/baseline_metrics.json")
    cleaned_path = Path("data/processed/cleaned_metrics.json")
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_path.parent.mkdir(parents=True, exist_ok=True)

    with baseline_path.open("w", encoding="utf-8") as f:
        json.dump(baseline, f)
    with cleaned_path.open("w", encoding="utf-8") as f:
        json.dump(cleaned, f)

    return baseline, cleaned

def test_absolute_diff():
    baseline = {
        "ds": {"t_test": {"p_value": 0.05, "ci": [0.0, 1.0], "effect_size": 0.5}}
    }
    cleaned = {
        "ds": {"t_test": {"p_value": 0.10, "ci": [0.2, 1.2], "effect_size": 0.6}}
    }
    diff = calculate_absolute_diff(baseline, cleaned)
    assert diff["ds"]["p_value_diff"] == 0.05  # rounded to 3 decimals
    assert diff["ds"]["ci_width_change"] == 0.40  # (1.0-0.2) - (1.0-0.0) = 0.4
    assert diff["ds"]["effect_size_delta"] == 0.1

def test_relative_diff():
    baseline = {
        "ds": {"t_test": {"p_value": 0.05, "ci": [0.0, 1.0], "effect_size": 0.5}}
    }
    cleaned = {
        "ds": {"t_test": {"p_value": 0.10, "ci": [0.2, 1.2], "effect_size": 0.6}}
    }
    rel = calculate_relative_diff(baseline, cleaned)
    assert rel["ds"]["p_value_rel_change"] == 1.0  # (0.10‑0.05)/0.05 = 1.0
    # CI width baseline =1.0, cleaned =1.0, relative change =0.0
    assert rel["ds"]["ci_width_rel_change"] == 0.0
    assert rel["ds"]["effect_size_rel_change"] == 0.2  # (0.6‑0.5)/0.5 = 0.2

def test_inconsistency_rate():
    # ds1 flips significance, ds2 does not
    baseline = {
        "ds1": {"t_test": {"p_value": 0.04}},
        "ds2": {"t_test": {"p_value": 0.20}},
    }
    cleaned = {
        "ds1": {"t_test": {"p_value": 0.07}},
        "ds2": {"t_test": {"p_value": 0.18}},
    }
    rate = calculate_inconsistency_rate(baseline, cleaned, alpha=0.05)
    assert rate == 0.5  # one of two datasets changed significance

def test_generate_report_writes_file(tmp_path: Path, synthetic_metrics):
    # Ensure the function creates a report file at the expected location.
    report = generate_comparison_report()
    assert "metric_shifts" in report
    assert "inconsistency_rate" in report

    output_path = Path("data/processed/comparison_report.json")
    assert output_path.is_file()
    with output_path.open() as f:
        loaded = json.load(f)
    assert loaded == report

def test_save_json_file_creates_path(tmp_path: Path):
    data = {"a": 1}
    target = Path(tmp_path / "nested" / "out.json")
    save_json_file(data, target)
    assert target.is_file()
    with target.open() as f:
        assert json.load(f) == data