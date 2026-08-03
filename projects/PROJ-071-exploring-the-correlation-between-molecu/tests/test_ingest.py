"""
Tests for ingestion module.
"""
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from code.ingest import (
    SchemaError,
    DataFetchError,
    check_degradation_columns,
    update_gate_status,
    run_data_availability_gate,
    validate_smiles_column,
    fetch_fda_drugs,
    GATE_STATUS_PATH,
    DEGRADATION_COLUMNS,
)

@pytest.fixture
def sample_df_with_smiles():
    """Create a sample dataframe with smiles column."""
    return pd.DataFrame({
        "smiles": ["CCO", "CC(=O)O", "c1ccccc1"],
        "name": ["Ethanol", "Acetic Acid", "Benzene"],
        "half_life": [10.0, 20.0, 30.0]
    })

@pytest.fixture
def sample_df_without_smiles():
    """Create a sample dataframe without smiles column."""
    return pd.DataFrame({
        "name": ["Ethanol", "Acetic Acid", "Benzene"],
        "half_life": [10.0, 20.0, 30.0]
    })

@pytest.fixture
def sample_df_no_degradation():
    """Create a sample dataframe without degradation columns."""
    return pd.DataFrame({
        "smiles": ["CCO", "CC(=O)O", "c1ccccc1"],
        "name": ["Ethanol", "Acetic Acid", "Benzene"],
        "molecular_weight": [46.0, 60.0, 78.0]
    })

def test_check_degradation_columns_found(sample_df_with_smiles):
    """Test that degradation column is correctly identified."""
    result = check_degradation_columns(sample_df_with_smiles)
    assert result == "half_life"

def test_check_degradation_columns_not_found(sample_df_no_degradation):
    """Test that None is returned when no degradation column is found."""
    result = check_degradation_columns(sample_df_no_degradation)
    assert result is None

def test_update_gate_status_pass(tmp_path, sample_df_with_smiles):
    """Test updating gate status to PASS."""
    # Mock the path
    with patch("code.ingest.GATE_STATUS_PATH", tmp_path / "gate_status.json"):
        result = update_gate_status("PASS", "Test reason", "half_life", 3)
        
        assert result["status"] == "PASS"
        assert result["reason"] == "Test reason"
        assert result["column_found"] == "half_life"
        assert result["N"] == 3
        
        # Verify file was written
        assert os.path.exists(tmp_path / "gate_status.json")
        with open(tmp_path / "gate_status.json", "r") as f:
            data = json.load(f)
            assert data["status"] == "PASS"

def test_update_gate_status_fail(tmp_path):
    """Test updating gate status to FAIL."""
    with patch("code.ingest.GATE_STATUS_PATH", tmp_path / "gate_status.json"):
        result = update_gate_status("FAIL", "No column", None)
        
        assert result["status"] == "FAIL"
        assert result["column_found"] is None

def test_run_data_availability_gate_pass(sample_df_with_smiles, tmp_path):
    """Test that gate passes when smiles and degradation columns are present."""
    with patch("code.ingest.GATE_STATUS_PATH", tmp_path / "gate_status.json"):
        result = run_data_availability_gate(sample_df_with_smiles)
        assert result is True

def test_run_data_availability_gate_fail_no_smiles(sample_df_without_smiles, tmp_path):
    """Test that gate fails when smiles column is missing."""
    with patch("code.ingest.GATE_STATUS_PATH", tmp_path / "gate_status.json"):
        with pytest.raises(SchemaError):
            run_data_availability_gate(sample_df_without_smiles)

def test_run_data_availability_gate_fail_no_degradation(sample_df_no_degradation, tmp_path):
    """Test that gate fails when no degradation column is found."""
    with patch("code.ingest.GATE_STATUS_PATH", tmp_path / "gate_status.json"):
        with pytest.raises(DataFetchError):
            run_data_availability_gate(sample_df_no_degradation)

def test_validate_smiles_column_true(sample_df_with_smiles):
    """Test validation when smiles column exists and has data."""
    assert validate_smiles_column(sample_df_with_smiles) is True

def test_validate_smiles_column_false(sample_df_without_smiles):
    """Test validation when smiles column is missing."""
    assert validate_smiles_column(sample_df_without_smiles) is False

def test_validate_smiles_column_empty(tmp_path):
    """Test validation when smiles column exists but is empty."""
    df = pd.DataFrame({
        "smiles": [None, None, None],
        "name": ["A", "B", "C"]
    })
    assert validate_smiles_column(df) is False
