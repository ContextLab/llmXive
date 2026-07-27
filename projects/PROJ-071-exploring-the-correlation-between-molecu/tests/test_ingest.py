"""Tests for the ingest module."""
import pytest
import pandas as pd
from pathlib import Path
import json

from code.ingest import (
    validate_smiles_series,
    check_degradation_columns,
    DataFetchError,
    DataInsufficiencyError
)


def test_validate_smiles_series_valid():
    """Test validation with valid SMILES."""
    smiles = pd.Series(["CCO", "c1ccccc1", "CC(=O)Oc1ccccc1C(=O)O"])
    mask = validate_smiles_series(smiles)
    assert mask.all()


def test_validate_smiles_series_invalid():
    """Test validation with invalid SMILES."""
    smiles = pd.Series(["invalid_smiles", "CCO", ""])
    mask = validate_smiles_series(smiles)
    assert not mask.iloc[0]
    assert mask.iloc[1]
    assert not mask.iloc[2]


def test_check_degradation_columns_present():
    """Test column check when degradation column exists."""
    df = pd.DataFrame({"smiles": ["CCO"], "half_life": [10.0]})
    assert check_degradation_columns(df)


def test_check_degradation_columns_missing():
    """Test column check when degradation column is missing."""
    df = pd.DataFrame({"smiles": ["CCO"], "mw": [46.0]})
    assert not check_degradation_columns(df)
