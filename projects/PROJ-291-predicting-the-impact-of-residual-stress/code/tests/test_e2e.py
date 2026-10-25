"""
test_e2e.py
-------------
End‑to‑end pipeline integration test for task T003.

The test runs the full pipeline via ``src.run_e2e.main()`` and checks that
the expected artefacts are created and contain the required fields.
"""

import json
from pathlib import Path

import pytest

# Import the entry point of the e2e runner
from src.run_e2e import main as run_e2e_main

# Directories where artefacts are written
RESULTS_DIR = Path("data/results")
PROCESSED_DIR = Path("data/processed")

@pytest.fixture(scope="module")
def run_pipeline():
    """
    Execute the end‑to‑end pipeline once for the whole test module.
    Returns a mapping of artefact names to their pathlib.Path objects.
    """
    # Run the pipeline; any exception will cause the test suite to fail.
    run_e2e_main()

    return {
        "unified_fatigue": PROCESSED_DIR / "unified_fatigue.csv",
        "proxy_agreement": RESULTS_DIR / "proxy_agreement.csv",
        "e2e_summary": RESULTS_DIR / "e2e_summary.json",
        "runtime_summary": RESULTS_DIR / "runtime_summary.csv",
    }

def test_outputs_exist(run_pipeline):
    """
    Verify that all declared output files exist after the pipeline runs.
    """
    for name, path in run_pipeline.items():
        assert path.is_file(), f"Expected {name} at {path} to exist"

def test_e2e_summary_content(run_pipeline):
    """
    The JSON summary must contain the required keys.
    """
    summary_path = run_pipeline["e2e_summary"]
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    required_keys = {
        "total_rows",
        "proxy_rows",
        "percent_proxy_rows",
        "pearson_r",
        "r_squared",
    }
    assert required_keys.issubset(data.keys()), "Missing keys in e2e_summary.json"

def test_runtime_summary_nonempty(run_pipeline):
    """
    Ensure that the runtime summary CSV has at least a header and one data row.
    """
    runtime_path = run_pipeline["runtime_summary"]
    lines = runtime_path.read_text(encoding="utf-8").strip().splitlines()
    # Header + at least one phase entry
    assert len(lines) >= 2, "runtime_summary.csv should contain header and data rows"

def test_proxy_agreement_structure(run_pipeline):
    """
    Basic sanity check that the proxy agreement CSV contains the expected columns.
    """
    import pandas as pd
    
    df = pd.read_csv(run_pipeline["proxy_agreement"])
    expected_columns = {"pearson_r", "r_squared", "caveat"}
    assert expected_columns.issubset(set(df.columns)), "proxy_agreement.csv missing expected columns"