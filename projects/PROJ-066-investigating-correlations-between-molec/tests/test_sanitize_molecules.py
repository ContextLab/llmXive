"""Unit tests for sanitize_molecules (T010)."""

import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.preprocess import sanitize_molecules  # noqa: E402


def test_sanitize_removes_salts():
    df = pd.DataFrame([{"SMILES": "CC(=O)Oc1ccccc1C(=O)O.[Na+]"}])
    out = sanitize_molecules(df)
    assert len(out) == 1
    assert "[Na]" not in out.iloc[0]["SMILES"]


def test_sanitize_removes_invalid_valence():
    df = pd.DataFrame([
        {"SMILES": "CCO"},
        {"SMILES": "C(C)(C)(C)(C)C"},  # invalid valence for carbon
    ])
    out = sanitize_molecules(df)
    assert len(out) == 1
    assert out.iloc[0]["SMILES"] == "CCO"


def test_sanitize_keeps_valid_molecules():
    df = pd.DataFrame([
        {"SMILES": "CCO"},
        {"SMILES": "c1ccccc1"},
        {"SMILES": "CC(=O)O"},
    ])
    out = sanitize_molecules(df)
    assert len(out) == 3


def test_sanitize_empty_smiles_excluded():
    df = pd.DataFrame([{"SMILES": ""}, {"SMILES": "CCO"}])
    out = sanitize_molecules(df)
    assert len(out) == 1


def test_sanitize_all_invalid_raises():
    df = pd.DataFrame([{"SMILES": "not_a_smiles"}])
    with pytest.raises(Exception):
        sanitize_molecules(df)