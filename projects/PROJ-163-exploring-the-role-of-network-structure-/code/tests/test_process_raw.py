"""
Basic sanity test for the ``process_raw`` module.

The test checks that the CSV is created and that the numeric columns
contain finite values.  It does not depend on external services.
"""
import pathlib

import pandas as pd
import pytest

from code.process_raw import generate_performance_csv

@pytest.fixture(scope="module")
def csv_path():
    # Run the generator before the test suite executes.
    generate_performance_csv()
    return pathlib.Path("data/processed/performance_metrics.csv")

def test_csv_exists(csv_path):
    assert csv_path.is_file(), f"Expected CSV at {csv_path}"

def test_csv_non_empty(csv_path):
    df = pd.read_csv(csv_path)
    assert len(df) > 0, "CSV should contain at least one data row"

def test_numeric_columns_finite(csv_path):
    df = pd.read_csv(csv_path)
    for col in ["t1_mean", "t2_mean", "cx_error_mean", "readout_error_mean"]:
        series = pd.to_numeric(df[col], errors="coerce")
        assert not series.isnull().any(), f"{col} contains NaN"
        assert not series.isin([float("inf"), float("-inf")]).any(), f"{col} contains infinite values"