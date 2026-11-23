"""
Unit tests for the data availability gate implemented in
``code/data/downloader.py``.
"""
import json
from pathlib import Path

import pandas as pd
import pytest

from data.downloader import run_data_availability_gate

@pytest.fixture
def phenotype_with_all_columns(tmp_path):
    """Create a phenotype CSV containing all required columns."""
    cols = [
        "sample_id",
        "bmi",
        "fasting_glucose",
        "triglycerides",
        "hdl",
        "systolic_bp",
        "diastolic_bp",
    ]
    df = pd.DataFrame({c: [] for c in cols})
    out = tmp_path / "gtex_v8_phenotype.csv"
    df.to_csv(out, index=False)
    return out

@pytest.fixture
def phenotype_missing_columns(tmp_path):
    """Create a phenotype CSV missing a subset of required columns."""
    cols = ["sample_id", "bmi", "hdl"]  # missing glucose, TG, BP
    df = pd.DataFrame({c: [] for c in cols})
    out = tmp_path / "gtex_v8_phenotype.csv"
    df.to_csv(out, index=False)
    return out

def test_gate_all_columns_present(monkeypatch, phenotype_with_all_columns):
    """Gate should report success when all columns exist."""
    # Redirect the expected raw path to the temporary fixture
    monkeypatch.setattr(
        "pathlib.Path.is_file", lambda self: True if self == Path("data/raw/gtex_v8_phenotype.csv") else Path.is_file(self)
    )
    monkeypatch.setattr(
        "pandas.read_csv",
        lambda *args, **kwargs: pd.read_csv(phenotype_with_all_columns, **kwargs),
    )
    run_data_availability_gate()
    report_path = Path("data/processed/data_availability_gate.json")
    assert report_path.is_file()
    report = json.loads(report_path.read_text())
    assert report["status"] == "All columns present"
    assert report["missing_columns"] == []

def test_gate_missing_columns(monkeypatch, phenotype_missing_columns):
    """Gate should list missing columns and set exploratory status."""
    monkeypatch.setattr(
        "pathlib.Path.is_file", lambda self: True if self == Path("data/raw/gtex_v8_phenotype.csv") else Path.is_file(self)
    )
    monkeypatch.setattr(
        "pandas.read_csv",
        lambda *args, **kwargs: pd.read_csv(phenotype_missing_columns, **kwargs),
    )
    run_data_availability_gate()
    report_path = Path("data/processed/data_availability_gate.json")
    assert report_path.is_file()
    report = json.loads(report_path.read_text())
    assert report["status"] == "Exploratory - Missing Columns"
    # Expected missing columns (order may vary)
    expected_missing = {"fasting_glucose", "triglycerides", "systolic_bp", "diastolic_bp"}
    assert set(report["missing_columns"]) == expected_missing