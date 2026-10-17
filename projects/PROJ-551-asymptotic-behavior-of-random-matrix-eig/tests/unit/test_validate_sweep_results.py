"""Unit tests for T003 (FR-004 outlier rule application)."""
import csv
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parent.parent.parent / "code"
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from analysis.validate_sweep_results import (
    compute_outlier_flag,
    validate_sweep_results,
    OUTLIER_TOLERANCE,
)

def test_outlier_rule_basic():
    # exactly at the tolerance boundary -> not an outlier (strict >)
    assert compute_outlier_flag(2.05, 2.0) is False
    assert compute_outlier_flag(2.0501, 2.0) is True
    assert compute_outlier_flag(2.0, 2.0) is False
    assert compute_outlier_flag(1.9, 2.0) is False

def test_tolerance_value():
    assert OUTLIER_TOLERANCE == 0.05

def test_validate_sweep_results_end_to_end(tmp_path):
    inp = tmp_path / "mc_results.csv"
    rows = [
        {"run_id": "r1", "N": "100", "k": "1", "pattern_type": "diagonal",
         "theta": "2.5", "seed": "42", "eigenvalue_top": "3.4",
         "empirical_bulk_edge": "1.3", "computation_time_ms": "1.0"},
        {"run_id": "r2", "N": "100", "k": "1", "pattern_type": "diagonal",
         "theta": "0.8", "seed": "42", "eigenvalue_top": "1.31",
         "empirical_bulk_edge": "1.3", "computation_time_ms": "1.0"},
    ]
    with open(inp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    out = tmp_path / "validated_sweep_results.csv"
    n = validate_sweep_results(inp, out)
    assert n == 2
    with open(out, newline="") as f:
        result = list(csv.DictReader(f))
    assert len(result) == 2
    assert result[0]["outlier_flag"] == "True"
    assert result[1]["outlier_flag"] == "False"
    # original columns preserved
    assert result[0]["run_id"] == "r1"
    assert result[1]["eigenvalue_top"] == "1.31"

def test_missing_input_fails_loudly(tmp_path):
    import pytest
    with pytest.raises(FileNotFoundError):
        validate_sweep_results(tmp_path / "nope.csv", tmp_path / "out.csv")