"""
Integration test for the baseline analysis pipeline (T010 / T012 / T013).

The test executes the ``t013_record_baseline_metrics`` script and then checks
that ``data/processed/baseline_metrics.json`` exists and contains at least one
dataset with a p‑value in the open interval (0, 1) and finite confidence‑interval
bounds.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

@pytest.mark.integration
def test_baseline_metrics_generated(tmp_path, monkeypatch):
    """
    Run the baseline recording script in an isolated temporary directory and
    validate the produced JSON.
    """
    # Ensure we are running from the repository root
    repo_root = Path(__file__).resolve().parents[2]
    os.chdir(repo_root)

    # Execute the script – it will abort with a non‑zero exit code if something
    # goes wrong, causing the test to fail.
    result = subprocess.run(
        [sys.executable, "code/t013_record_baseline_metrics.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stdout}\\n{result.stderr}"

    metrics_path = Path("data/processed/baseline_metrics.json")
    assert metrics_path.is_file(), "baseline_metrics.json was not created"

    with metrics_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # At least one dataset must be present
    assert isinstance(data, dict) and len(data) > 0, "No datasets recorded"

    # Validate each entry contains the required numeric fields
    for ds_name, ds_metrics in data.items():
        t_test = ds_metrics.get("t_test", {})
        p = t_test.get("p_value")
        ci = t_test.get("ci", [])
        assert isinstance(p, float) and 0.0 < p < 1.0, f"Invalid p‑value for {ds_name}"
        assert (
            isinstance(ci, list)
            and len(ci) == 2
            and all(isinstance(v, float) and np.isfinite(v) for v in ci)
        ), f"Invalid confidence interval for {ds_name}"

        effect = ds_metrics.get("effect_size", {})
        # Cohen's d may be zero but must be a float; R² must be between 0 and 1
        cohen_d = effect.get("cohen_d")
        r2 = effect.get("r_squared")
        assert isinstance(cohen_d, float), f"Cohen's d missing for {ds_name}"
        assert isinstance(r2, float) and 0.0 <= r2 <= 1.0, f"R² out of bounds for {ds_name}"
