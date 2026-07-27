"""
Unit tests for the reporting module (code/reporting.py).

The tests use a tiny fabricated metric dictionary that mimics the structure
produced by the baseline and cleaned analysis scripts. They verify that the
absolute‑difference, relative‑difference and inconsistency‑rate calculations
behave as specified.
"""

import json
import os
from pathlib import Path

import pytest

# Import the functions directly from the module under test
from reporting import (
    calculate_absolute_diff,
    calculate_relative_diff,
    calculate_inconsistency_rate,
    generate_comparison_report,
    save_json_file,
    load_json_file,
)

# --------------------------------------------------------------------------- #
# Helper fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def fake_metrics(tmp_path: Path):
    """Create fake baseline and cleaned metric JSON files."""
    baseline = {
        "ds1": {
            "t_test": {"p_value": 0.040, "ci": [0.10, 0.30]},
            "cohen_d": 0.50,
        },
        "ds2": {
            "t_test": {"p_value": 0.200, "ci": [0.05, 0.25]},
            "cohen_d": 0.20,
        },
    }
    cleaned = {
        "ds1": {
            "t_test": {"p_value": 0.060, "ci": [0.12, 0.32]},
            "cohen_d": 0.55,
        },
        "ds2": {
            "t_test": {"p_value": 0.180, "ci": [0.04, 0.24]},
            "cohen_d": 0.18,
        },
    }
    # Write files where the reporting module expects them
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    baseline_path = processed_dir / "baseline_metrics.json"
    cleaned_path = processed_dir / "cleaned_metrics.json"
    with baseline_path.open("w", encoding="utf-8") as f:
        json.dump(baseline, f)
    with cleaned_path.open("w", encoding="utf-8") as f:
        json.dump(cleaned, f)
    return {"baseline": baseline_path, "cleaned": cleaned_path}

# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
def test_absolute_diff_calculation():
    baseline = {
        "ds": {"t_test": {"p_value": 0.100, "ci": [0.1, 0.5]}, "cohen_d": 0.4}
    }
    cleaned = {
        "ds": {"t_test": {"p_value": 0.150, "ci": [0.2, 0.6]}, "cohen_d": 0.6}
    }
    diffs = calculate_absolute_diff(baseline, cleaned)
    assert diffs["ds"]["p_value_diff"] == pytest.approx(0.050, rel=1e-3)
    # CI width: baseline 0.4, cleaned 0.4 → diff 0.00
    assert diffs["ds"]["ci_width_diff"] == 0.00
    assert diffs["ds"]["effect_size_diff"] == pytest.approx(0.200, rel=1e-3)

def test_relative_diff_calculation():
    baseline = {
        "ds": {"t_test": {"p_value": 0.200, "ci": [0.0, 0.4]}, "cohen_d": 0.5}
    }
    cleaned = {
        "ds": {"t_test": {"p_value": 0.100, "ci": [0.0, 0.2]}, "cohen_d": 0.25}
    }
    rel = calculate_relative_diff(baseline, cleaned)
    # |0.1| / 0.2 = 0.5
    assert rel["ds"]["p_value_rel"] == pytest.approx(0.5, rel=1e-3)
    # CI width baseline 0.4, cleaned 0.2 → diff 0.2 / 0.4 = 0.5
    assert rel["ds"]["ci_width_rel"] == pytest.approx(0.5, rel=1e-3)
    # effect size diff 0.25 / 0.5 = 0.5
    assert rel["ds"]["effect_size_rel"] == pytest.approx(0.5, rel=1e-3)

def test_inconsistency_rate():
    baseline = {
        "a": {"t_test": {"p_value": 0.01}},
        "b": {"t_test": {"p_value": 0.20}},
    }
    cleaned = {
        "a": {"t_test": {"p_value": 0.10}},  # flips from significant to non‑significant
        "b": {"t_test": {"p_value": 0.30}},  # stays non‑significant
    }
    rate = calculate_inconsistency_rate(baseline, cleaned, alpha=0.05)
    # One of two datasets changed significance → 0.5
    assert rate == pytest.approx(0.5, rel=1e-3)

def test_generate_comparison_report_writes_file(fake_metrics):
    # Ensure the function runs without error and produces a file.
    report = generate_comparison_report()
    assert "absolute_diff" in report
    assert "relative_diff" in report
    assert "inconsistency_rate" in report

    out_path = Path("data/processed/comparison_report.json")
    # The function itself writes the file; we verify its existence.
    assert out_path.is_file()
    # Load back and check consistency
    loaded = load_json_file(out_path)
    assert loaded == report