"""
test_fetch_data.py
------------------
Unit tests for the three fetch functions defined in ``code/src/fetch_data.py``.
"""

import json
import os
import pandas as pd
import pytest
from llmxive_toolkit import paths

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
    return {
        "metabolights": fetch_metabolights(),
        "pmn": fetch_pmn(),
        "hpid": fetch_hpid(),
    }

def _check_dataframe(df: pd.DataFrame):
    assert isinstance(df, pd.DataFrame)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    assert not missing, f"Missing required columns: {missing}"
    assert not df[REQUIRED_COLUMNS].isnull().any().any(), "NaNs found in required columns"
    assert len(df) >= 1, "DataFrame is empty"

def test_fetch_metabolights(fetched_data):
    _check_dataframe(fetched_data["metabolights"])

def test_fetch_pmn(fetched_data):
    _check_dataframe(fetched_data["pmn"])

def test_fetch_hpid(fetched_data):
    _check_dataframe(fetched_data["hpid"])

def test_fetch_log_written(fetched_data):
    import subprocess
    import sys
    script_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src", "fetch_data.py")
    )
    subprocess.check_call([sys.executable, script_path])

    log_path = paths.outputs("fetch_log.txt")
    assert log_path.is_file()
    with log_path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    assert len(lines) >= 3