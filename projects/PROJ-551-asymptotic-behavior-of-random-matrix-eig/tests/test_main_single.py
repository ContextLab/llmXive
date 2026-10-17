"""
Integration test for the single‑run end‑to‑end pipeline (T001).

The test invokes ``code/main.py`` with a small problem size,
checks that the expected JSON artifact is written, validates the
schema‑required fields, and verifies reproducibility of the top
eigenvalue within 1e‑6.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def output_path(tmp_path_factory):
    """Path to the JSON result file for the test run."""
    return tmp_path_factory.getbasetemp() / "single_run_results.json"


def run_main(output_path: Path):
    """
    Execute ``code/main.py`` with deterministic arguments.
    The command mirrors the Quickstart example but points the
    output to the temporary location provided by the fixture.
    """
    cmd = [
        sys.executable,
        str(Path("code") / "main.py"),
        "--mode",
        "single",
        "--N",
        "200",          # small enough for the CI environment
        "--seed",
        "42",
        "--theta",
        "2.5",
        "--k",
        "1",
        "--pattern",
        "diagonal",
        "--output",
        str(output_path),
    ]
    # ``check=True`` raises if the script exits with a non‑zero status.
    subprocess.run(cmd, check=True)


def test_single_run_creates_json(output_path):
    """Run the pipeline and assert that the JSON file exists and is valid."""
    run_main(output_path)
    assert output_path.is_file(), "Result JSON was not created."

    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Required top‑level keys (according to the contract)
    required_keys = {
        "run_id",
        "timestamp",
        "seed",
        "N",
        "k",
        "theta",
        "pattern_type",
        "support_density",
        "computation_time_ms",
        "empirical_bulk_edge",
        "eigenvalues",
    }
    missing = required_keys - data.keys()
    assert not missing, f"Missing required keys in JSON: {missing}"

    # Basic type / value checks
    assert isinstance(data["run_id"], str) and data["run_id"]
    assert isinstance(data["timestamp"], str) and data["timestamp"]
    assert data["seed"] == 42
    assert data["N"] == 200
    assert data["k"] == 1
    assert data["theta"] == 2.5
    assert data["pattern_type"] == "diagonal"
    assert data["support_density"] is None
    assert isinstance(data["computation_time_ms"], (float, int))
    assert isinstance(data["empirical_bulk_edge"], float)

    eigenvalues = data["eigenvalues"]
    assert isinstance(eigenvalues, list) and len(eigenvalues) == 10, \
        "Exactly 10 eigenvalue entries are required."

    eigen_keys = {
        "run_id",
        "eigenvalue_index",
        "value",
        "is_outlier",
        "theoretical_bbp",
        "deviation",
    }
    for ev in eigenvalues:
        missing_ev = eigen_keys - ev.keys()
        assert not missing_ev, f"Eigenvalue entry missing keys: {missing_ev}"
        assert ev["run_id"] == data["run_id"]
        assert isinstance(ev["eigenvalue_index"], int)
        assert isinstance(ev["value"], float)
        assert isinstance(ev["is_outlier"], bool)
        assert isinstance(ev["theoretical_bbp"], float)
        assert isinstance(ev["deviation"], float)

def test_reproducibility(output_path):
    """
    Re‑run the same command and compare the top eigenvalue.
    The difference must be ≤ 1e‑6.
    """
    # First run
    run_main(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        first = json.load(f)
    top1 = first["eigenvalues"][0]["value"]

    # Second run (overwrite the same file)
    run_main(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        second = json.load(f)
    top2 = second["eigenvalues"][0]["value"]

    assert abs(top1 - top2) <= 1e-6, (
        f"Top eigenvalue not reproducible: {top1} vs {top2}"
    )
