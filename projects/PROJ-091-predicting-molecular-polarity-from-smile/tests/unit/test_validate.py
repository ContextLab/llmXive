"""
Unit tests for code/data/validate.py (T103).

These tests build small temporary parquet fixtures and a matching
descriptor_names.json, then verify:
  * exit-code 0 on a correct descriptor matrix
  * non-zero exit on a corrupted column name
  * non-zero exit on missing JSON / missing parquet / extra columns
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "code" / "data" / "validate.py"

sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.validate import validate_processed_descriptors, _load_descriptor_names_json


@pytest.fixture
def valid_dataset(tmp_path):
    """Create a valid descriptors.parquet + descriptor_names.json pair."""
    names = ["MolWt", "HeavyAtomCount", "RingCount", "BalabanJ"]
    n = 20
    data = {f"desc_{n_}": np.random.RandomState(0).rand(n) for n_ in names}
    data["smiles"] = ["CCO"] * n
    data["target"] = np.linspace(0.0, 2.5, n)
    data["stereochemistry_flag"] = [False] * n
    data["flexible_flag"] = [False] * n
    df = pd.DataFrame(data)
    parquet = tmp_path / "descriptors.parquet"
    df.to_parquet(parquet)
    (tmp_path / "descriptor_names.json").write_text(json.dumps(names))
    return parquet, names

def test_valid_matrix_passes(valid_dataset):
    parquet, _ = valid_dataset
    ok, msg = validate_processed_descriptors(str(parquet))
    assert ok, msg

def test_corrupted_column_fails(valid_dataset):
    parquet, _ = valid_dataset
    df = pd.read_parquet(parquet).rename(columns={"desc_MolWt": "desc_MolWtX"})
    df.to_parquet(parquet)
    ok, msg = validate_processed_descriptors(str(parquet))
    assert not ok
    assert "mismatch" in msg.lower()

def test_extra_descriptor_fails(valid_dataset):
    parquet, _ = valid_dataset
    df = pd.read_parquet(parquet)
    df["desc_Extra"] = 1.0
    df.to_parquet(parquet)
    ok, _msg = validate_processed_descriptors(str(parquet))
    assert not ok

def test_missing_required_column_fails(valid_dataset):
    parquet, _ = valid_dataset
    df = pd.read_parquet(parquet).drop(columns=["flexible_flag"])
    df.to_parquet(parquet)
    ok, msg = validate_processed_descriptors(str(parquet))
    assert not ok
    assert "flexible_flag" in msg

def test_tpsa_column_rejected(tmp_path):
    names = ["MolWt", "TPSA"]
    n = 5
    data = {"desc_MolWt": np.arange(n, dtype=float), "desc_TPSA": np.arange(n, dtype=float),
            "smiles": ["CCO"] * n, "target": np.arange(n, dtype=float),
            "stereochemistry_flag": [False] * n, "flexible_flag": [False] * n}
    parquet = tmp_path / "descriptors.parquet"
    pd.DataFrame(data).to_parquet(parquet)
    (tmp_path / "descriptor_names.json").write_text(json.dumps(names))
    ok, msg = validate_processed_descriptors(str(parquet))
    assert not ok
    assert "TPSA" in msg

def test_missing_json_fails(tmp_path):
    n = 5
    data = {"desc_MolWt": np.arange(n, dtype=float), "smiles": ["CCO"] * n,
            "target": np.arange(n, dtype=float),
            "stereochemistry_flag": [False] * n, "flexible_flag": [False] * n}
    parquet = tmp_path / "descriptors.parquet"
    pd.DataFrame(data).to_parquet(parquet)
    ok, msg = validate_processed_descriptors(str(parquet))
    assert not ok
    assert "descriptor_names.json" in msg.lower()

def test_missing_parquet_fails(tmp_path):
    ok, msg = validate_processed_descriptors(str(tmp_path / "nope.parquet"))
    assert not ok

def test_load_descriptor_names_json(tmp_path):
    p = tmp_path / "descriptor_names.json"
    p.write_text(json.dumps(["A", "B"]))
    assert _load_descriptor_names_json(p) == ["A", "B"]
    p.write_text(json.dumps({"not": "a list"}))
    with pytest.raises(ValueError):
        _load_descriptor_names_json(p)

def test_cli_exit_codes(valid_dataset):
    """The script must exit 0 on a valid matrix and non-zero on corruption."""
    parquet, _ = valid_dataset
    r_ok = subprocess.run(
        [sys.executable, str(SCRIPT), str(parquet)],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert r_ok.returncode == 0, r_ok.stderr

    # Corrupt a column name -> non-zero exit
    df = pd.read_parquet(parquet).rename(columns={"desc_RingCount": "desc_RingCountBad"})
    df.to_parquet(parquet)
    r_bad = subprocess.run(
        [sys.executable, str(SCRIPT), str(parquet)],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert r_bad.returncode != 0