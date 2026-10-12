"""
Unit tests for the target‑dynamic‑range validation (T011).
"""

import json
import os
import tempfile

import pandas as pd
import pytest

from code.preprocessing import compute_dynamic_range, main as preprocessing_main
from llmxive_toolkit import paths

def _write_csv(df: pd.DataFrame, directory: str):
    path = os.path.join(directory, "input.csv")
    df.to_csv(path, index=False)
    return path

def test_compute_dynamic_range_success():
    # Conductivity spans 1e-5 to 1e-1 → log10 range = 4
    df = pd.DataFrame({"smiles": ["C", "CC"], "conductivity": [1e-5, 1e-1]})
    stats = compute_dynamic_range(df, "conductivity")
    assert stats["min"] == 1e-5
    assert stats["max"] == 1e-1
    assert pytest.approx(stats["range_log10"], rel=1e-3) == 4.0

def test_compute_dynamic_range_failure_nonpositive():
    df = pd.DataFrame({"smiles": ["C"], "conductivity": [-1.0]})
    with pytest.raises(ValueError, match="non‑positive"):
        compute_dynamic_range(df, "conductivity")

def test_preprocessing_main_writes_json(tmp_path):
    # Prepare a valid CSV in the expected raw folder
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame({"smiles": ["C", "CC"], "conductivity": [1e-5, 1e-1]})
    csv_path = raw_dir / "input.csv"
    df.to_csv(csv_path, index=False)

    # Run the script
    exit_code = preprocessing_main()
    assert exit_code == 0

    # Verify JSON output
    json_path = paths.data("processed", "target_dynamic_range.json")
    assert json_path.exists()
    with open(json_path) as f:
        payload = json.load(f)
    assert payload["range_log10"] >= 3.0

def test_preprocessing_main_fails_when_range_too_small(tmp_path):
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame({"smiles": ["C"], "conductivity": [1.0, 2.0]})
    csv_path = raw_dir / "input.csv"
    df.to_csv(csv_path, index=False)

    exit_code = preprocessing_main()
    assert exit_code != 0