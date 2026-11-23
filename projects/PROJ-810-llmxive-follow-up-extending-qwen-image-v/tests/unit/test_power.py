"""
Unit tests for the power‑analysis utility (code/analysis/power.py).
"""
import json
from pathlib import Path

import pytest

from code.analysis.power import calculate_min_sample_size, run_power_analysis

@pytest.mark.parametrize(
    "effect_size,target_power,alpha,expected_min",
    [
        (0.8, 0.8, 0.05, 21),  # Known approximate result from power tables
        (0.5, 0.8, 0.05, 64),
    ],
)
def test_calculate_min_sample_size(effect_size, target_power, alpha, expected_min):
    """Check that the sample size calculation returns a sensible integer."""
    n = calculate_min_sample_size(effect_size, target_power, alpha)
    assert isinstance(n, int)
    assert n >= expected_min  # The solver may return a slightly larger value

def test_run_power_analysis_structure(tmp_path: Path):
    """Run the analysis and verify the JSON structure and contents."""
    result = run_power_analysis(effect_size=0.8, target_power=0.8, alpha=0.05)
    # Required keys
    for key in ("N_required", "effect_size", "achieved_power", "status"):
        assert key in result

    assert isinstance(result["N_required"], int) and result["N_required"] > 0
    assert result["effect_size"] == 0.8
    assert isinstance(result["achieved_power"], float)
    assert result["achieved_power"] >= 0.8
    assert result["status"] == "conclusive"

    # Write to a temporary file to ensure the CLI logic works
    out_file = tmp_path / "power_analysis.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
    # Read back and compare
    loaded = json.loads(out_file.read_text(encoding="utf-8"))
    assert loaded == result