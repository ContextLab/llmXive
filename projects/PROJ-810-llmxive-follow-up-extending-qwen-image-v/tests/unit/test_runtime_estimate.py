import json
from pathlib import Path

import pytest

from code.analysis.runtime_estimate import main, load_power_analysis, compute_estimate, write_output

def test_load_power_analysis(tmp_path, monkeypatch):
    # Create a temporary power_analysis.json
    power_path = Path(__file__).parents[2] / "data" / "results" / "power_analysis.json"
    power_path.parent.mkdir(parents=True, exist_ok=True)
    sample_data = {"N_required": 30, "effect_size": 0.8, "achieved_power": 0.81, "status": "conclusive"}
    with power_path.open("w", encoding="utf-8") as f:
        json.dump(sample_data, f)
    # Load using the function
    loaded = load_power_analysis()
    assert loaded == sample_data

def test_compute_estimate():
    # With N_required that stays within budget
    result = compute_estimate(20)
    assert result["estimated_seconds"] == 20 * 60
    assert result["exceeds_budget"] is False
    assert result["status"] == "feasible"

    # With N_required that exceeds budget
    result = compute_estimate(400)  # 400*60 = 24000 > 6*3600 (=21600)
    assert result["exceeds_budget"] is True
    assert result["status"] == "infeasible"

def test_end_to_end_runtime_estimate(tmp_path, monkeypatch):
    # Ensure a known power_analysis.json exists
    power_path = Path(__file__).parents[2] / "data" / "results" / "power_analysis.json"
    power_path.parent.mkdir(parents=True, exist_ok=True)
    sample_data = {"N_required": 26, "effect_size": 0.8, "achieved_power": 0.8075, "status": "conclusive"}
    with power_path.open("w", encoding="utf-8") as f:
        json.dump(sample_data, f)

    # Run main which should write runtime_estimate.json
    main()

    # Verify output file exists and content matches expectation
    out_path = Path(__file__).parents[2] / "data" / "results" / "runtime_estimate.json"
    assert out_path.is_file()
    with out_path.open("r", encoding="utf-8") as f:
        result = json.load(f)

    expected_seconds = sample_data["N_required"] * 60
    assert result["estimated_seconds"] == expected_seconds
    assert result["exceeds_budget"] is False
    assert result["status"] == "feasible"