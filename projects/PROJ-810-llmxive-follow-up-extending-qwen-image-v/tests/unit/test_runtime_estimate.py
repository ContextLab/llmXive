import json
from pathlib import Path

from llmxive_toolkit import paths
from analysis.runtime_estimate import load_power_analysis, compute_estimate, write_output

def test_load_power_analysis(tmp_path, monkeypatch):
    # Prepare a temporary power_analysis.json
    sample = {"N_required": 10, "effect_size": 0.8, "achieved_power": 0.81, "status": "conclusive"}
    power_path = paths.results("power_analysis.json")
    power_path.parent.mkdir(parents=True, exist_ok=True)
    with power_path.open("w", encoding="utf-8") as f:
        json.dump(sample, f)

    data = load_power_analysis()
    assert data == sample

def test_compute_estimate():
    result = compute_estimate(5)
    assert result["estimated_seconds"] == 5 * 60
    assert result["exceeds_budget"] is False
    assert result["status"] == "feasible"

    # Test a value that exceeds the 6‑hour budget
    large_n = (6 * 3600) // 60 + 1  # just over the budget
    result = compute_estimate(large_n)
    assert result["exceeds_budget"] is True
    assert result["status"] == "infeasible"

def test_write_output(tmp_path):
    # Ensure the function writes to the expected location
    out_path = paths.results("runtime_estimate.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    result = {"estimated_seconds": 120, "exceeds_budget": False, "status": "feasible"}
    write_output(result)

    with out_path.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded == result