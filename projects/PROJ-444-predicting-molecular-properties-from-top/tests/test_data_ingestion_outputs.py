"""
Test suite to verify that Task T001 produced all required output artifacts
and that they conform to the expected basic properties.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

# Paths to artifacts produced by 01_data_ingestion.py
CHECKSUMS_PATH = Path("data/checksums.txt")
POWER_REPORT_PATH = Path("data/processed/power_analysis_report.json")
SCAFFOLD_COUNTS_PATH = Path("data/processed/scaffold_counts.json")
FILTERED_DATA_PATH = Path("data/processed/filtered_esol.csv")
SPLITS_PATH = Path("data/processed/splits.json")
EXCLUSION_LOG_PATH = Path("data/logs/large_molecule_exclusions.log")

def test_checksums_file_exists():
    assert CHECKSUMS_PATH.is_file(), "checksums.txt should exist"

def test_power_analysis_report():
    assert POWER_REPORT_PATH.is_file(), "Power analysis report missing"
    with POWER_REPORT_PATH.open() as f:
        data = json.load(f)
    assert "min_n" in data and "actual_n" in data and "passes" in data
    assert isinstance(data["passes"], bool)
    assert data["passes"] is True, "Power analysis should pass with the dataset size"

def test_scaffold_counts():
    assert SCAFFOLD_COUNTS_PATH.is_file(), "Scaffold counts JSON missing"
    with SCAFFOLD_COUNTS_PATH.open() as f:
        data = json.load(f)
    assert data.get("status") == "PASSED", "Scaffold count check must pass"

def test_filtered_dataset():
    assert FILTERED_DATA_PATH.is_file(), "Filtered ESOL CSV missing"
    df = pd.read_csv(FILTERED_DATA_PATH)
    # Must contain at least the minimum required rows (128 from power analysis)
    assert df.shape[0] >= 128, "Filtered dataset has fewer rows than required"
    # Columns must be exactly 'smiles', 'logP', 'molecule_id'
    expected_cols = {"smiles", "logP", "molecule_id"}
    assert set(df.columns) == expected_cols

def test_splits_file():
    assert SPLITS_PATH.is_file(), "Splits JSON missing"
    with SPLITS_PATH.open() as f:
        data = json.load(f)
    assert "splits" in data and isinstance(data["splits"], list)
    assert len(data["splits"]) == 5, "There should be 5 folds"

def test_large_molecule_exclusions_log():
    # The log file should exist; it may be empty if no exclusions occurred
    assert EXCLUSION_LOG_PATH.is_file(), "Exclusions log missing"
    # If the file is non‑empty, ensure it contains SMILES strings
    content = EXCLUSION_LOG_PATH.read_text().strip()
    if content:
        lines = content.splitlines()
        assert all(line for line in lines), "Exclusion log contains empty lines"