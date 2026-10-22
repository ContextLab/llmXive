"""
test_fetch_data.py
------------------
Unit tests for the three fetch functions defined in ``code/src/fetch_data.py``.
The tests verify that:

1. Each function returns a ``pandas.DataFrame``.
2. All required columns are present.
3. No missing values exist in required columns.
4. At least one species (row) is retrieved.
5. A small fetch‑log file is written containing a sample of species IDs.
"""

import json
import os

import pandas as pd
import pytest

from llmxive_toolkit import paths

# Import the fetch functions from the module under test
from code.src.fetch_data import fetch_metabolights, fetch_pmn, fetch_hpid

REQUIRED_COLUMNS = [
    "species_id",
    "species_name",
    "family",
    "alkaloids",
    "terpenes",
    "phenolics",
    "benzoxazinoids",
    "herbivory_score",
]

@pytest.fixture(scope="module")
def fetched_data():
    """Fetch all three datasets once for the test session."""
    return {
        "metabolights": fetch_metabolights(),
        "pmn": fetch_pmn(),
        "hpid": fetch_hpid(),
    }

def _check_dataframe(df: pd.DataFrame):
    """Common assertions applied to each fetched DataFrame."""
    # 1. Must be a DataFrame
    assert isinstance(df, pd.DataFrame), "Returned object is not a DataFrame"

    # 2. Required columns present
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    assert not missing, f"Missing required columns: {missing}"

    # 3. No missing values in required columns
    assert not df[REQUIRED_COLUMNS].isnull().any().any(), "NaNs found in required columns"

    # 4. At least one row (species) present
    assert len(df) >= 1, "DataFrame is empty – no species retrieved"

def test_fetch_metabolights(fetched_data):
    df = fetched_data["metabolights"]
    _check_dataframe(df)

def test_fetch_pmn(fetched_data):
    df = fetched_data["pmn"]
    _check_dataframe(df)

def test_fetch_hpid(fetched_data):
    df = fetched_data["hpid"]
    _check_dataframe(df)

def test_fetch_log_written(fetched_data):
    """
    After the three fetch functions have been called, the module's
    ``__main__`` block (executed when the script is run directly) writes a
    log file.  Here we invoke the module as a script to generate that file
    and then verify its contents.
    """
    # Run the module as a script – this will create the log file.
    import subprocess
    import sys

    script_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "code", "src", "fetch_data.py")
    )
    subprocess.check_call([sys.executable, script_path])

    log_path = paths.outputs("fetch_log.txt")
    assert log_path.is_file(), "fetch_log.txt was not created"

    # Ensure the log contains at least one entry with a non‑empty list of IDs
    with log_path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    assert lines, "fetch_log.txt is empty"
    for line in lines:
        src, ids_json = line.split(":", 1)
        ids = json.loads(ids_json.strip())
        assert isinstance(ids, list) and len(ids) > 0, f"No IDs logged for {src}"
