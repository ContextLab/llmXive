"""
code/tests/test_fetch_heas.py
-----------------------------

Integration test for the HEA dataset fetcher.
"""

import os
import pathlib
import json
import pytest
import pandas as pd

from llmxive_toolkit import paths
from code.data.fetch_heas import fetch_heas, _load_schema, _validate_row

def test_fetch_heas_creates_file():
    """
    The fetcher should download a real dataset and write it to
    `data/raw/heas_raw.csv`.
    """
    output_path = fetch_heas()
    assert output_path.is_file(), "HEA raw CSV was not created"

    df = pd.read_csv(output_path)
    assert not df.empty, "Downloaded dataset is empty"
    assert "yield_strength" in df.columns, "Dataset missing target column"

def test_missing_yield_strength_raises():
    """
    Verify that a row missing the required `yield_strength` field triggers
    a `ValueError` during validation.
    """
    schema = _load_schema()
    # Construct a minimal invalid row (no `yield_strength`)
    invalid_row = {
        "alloy_id": "test-001",
        "composition": {"Fe": 0.5, "Ni": 0.5},
    }
    with pytest.raises(ValueError) as excinfo:
        _validate_row(invalid_row, schema)
    assert "yield_strength" in str(excinfo.value)