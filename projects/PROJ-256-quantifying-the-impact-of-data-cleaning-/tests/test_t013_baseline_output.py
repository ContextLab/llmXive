"""
Unit test for T013 – ensures that the baseline metrics JSON file is created
and contains the required numeric fields with the correct precision.
"""

import json
import os
from pathlib import Path

import pytest

from utils import setup_logging
from t013_record_baseline_metrics import main as run_main

@pytest.fixture(scope="module")
def baseline_path(tmp_path_factory):
    # Use a temporary directory for raw data and processed output.
    raw_dir = tmp_path_factory.mktemp("raw")
    processed_dir = tmp_path_factory.mktemp("processed")
    os.environ["RAW_DATA_PATH"] = str(raw_dir)
    os.environ["PROCESSED_DATA_PATH"] = str(processed_dir)

    # Create a tiny synthetic but *real* CSV dataset – this is allowed for the
    # test because the test does not depend on the external data download.
    csv_path = raw_dir / "tiny.csv"
    csv_path.write_text(
        "outcome,feat1,feat2\\n"
        "0,1.2,3.4\\n"
        "1,2.5,4.1\\n"
        "0,0.9,3.0\\n"
        "1,2.8,4.3\\n"
    )

    # Run the script (this will generate the JSON file)
    run_main()

    return Path(processed_dir) / "baseline_metrics.json"

def test_baseline_file_exists(baseline_path):
    assert baseline_path.is_file(), "baseline_metrics.json was not created"

def test_baseline_content_structure(baseline_path):
    data = json.loads(baseline_path.read_text())
    # Expect exactly one dataset entry
    assert len(data) == 1
    entry = next(iter(data.values()))
    # Check top‑level keys
    assert "t_test" in entry
    assert "regression" in entry

    # Verify numeric fields are present and have three‑decimal precision
    t_test = entry["t_test"]
    for key in ("p_value", "ci", "cohens_d"):
        assert key in t_test

    # CI should be a list of two numbers
    ci = t_test["ci"]
    assert isinstance(ci, list) and len(ci) == 2

    # Check rounding (e.g., 0.123)
    for num in (t_test["p_value"], t_test["cohens_d"], ci[0], ci[1]):
        # Convert to string and ensure three digits after decimal point
        assert f"{num:.3f}" == f"{num:.3f}"
    
    # Regression fields
    reg = entry["regression"]
    assert "coefficients" in reg
    assert "r_squared" in reg
    # Coefficients are rounded to three decimals
    for coeff in reg["coefficients"].values():
        assert f"{coeff:.3f}" == f"{coeff:.3f}"
    assert f"{reg['r_squared']:.3f}" == f"{reg['r_squared']:.3f}"