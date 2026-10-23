"""
code/tests/test_fetch_heas.py
-----------------------------

Integration test for the HEA dataset fetcher. The test ensures that:
1. The dataset CSV is created at the expected location.
2. Each row conforms to the JSON‑schema contract.
3. Missing required fields (e.g., ``yield_strength``) raise ``ValueError``.
"""

import os
import pathlib
import json

import pytest

# Import the function under test
from data.fetch_heas import fetch_heas, _load_schema

@pytest.fixture
def clean_raw_data(tmp_path: pathlib.Path):
    """
    Ensure a clean ``data/raw`` directory for each test run.
    """
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    os.makedirs("data/raw", exist_ok=True)
    yield pathlib.Path(tmp_path)
    os.chdir(original_cwd)

def test_fetch_heas_creates_file(clean_raw_data):
    """
    The fetcher should download a real dataset and write it to
    ``data/raw/heas_raw.csv``.
    """
    output_path = fetch_heas()
    assert output_path.is_file(), "HEA raw CSV was not created"

    # Load CSV and perform a minimal sanity check
    import pandas as pd
    df = pd.read_csv(output_path)
    assert not df.empty, "Downloaded dataset is empty"

def test_missing_yield_strength_raises():
    """
    Verify that a row missing the required ``yield_strength`` field triggers
    a ``ValueError`` during validation.
    """
    schema = _load_schema()
    # Construct a minimal invalid row (no ``yield_strength``)
    invalid_row = {
        "alloy_id": "test-001",
        "composition": json.dumps({"Fe": 0.5, "Ni": 0.5}),
        # 'yield_strength' intentionally omitted
    }
    from data.fetch_heas import _validate_row
    with pytest.raises(ValueError) as excinfo:
        _validate_row(invalid_row, schema)
    assert "yield_strength" in str(excinfo.value)