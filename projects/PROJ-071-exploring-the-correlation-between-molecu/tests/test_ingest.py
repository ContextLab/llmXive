"""
Tests for code/ingest.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingest import (
    validate_smiles_series,
    filter_valid_records,
    check_degradation_columns,
    generate_insufficiency_report,
    run_data_availability_gate
)
from logging_config import setup_logging

setup_logging()

@pytest.fixture
def sample_df_with_valid_smiles():
    data = {
        'smiles': ['CCO', 'c1ccccc1', 'CC(=O)Oc1ccccc1C(=O)O', 'invalid_smiles_string'],
        'degradation_half_life': [10.0, 20.0, 5.5, np.nan],
        'degradation_rate': [0.1, 0.2, 0.3, 0.4]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_df_missing_degradation():
    data = {
        'smiles': ['CCO', 'c1ccccc1'],
        'other_col': [1, 2]
    }
    return pd.DataFrame(data)

def test_validate_smiles_series(sample_df_with_valid_smiles):
    valid_idx, error_idx = validate_smiles_series(sample_df_with_valid_smiles['smiles'])
    
    # CCO, c1ccccc1, Aspirin are valid. 'invalid_smiles_string' is not.
    assert len(valid_idx) == 3
    assert len(error_idx) == 1
    assert error_idx.iloc[0] == 3  # Index of invalid string

def test_filter_valid_records(sample_df_with_valid_smiles):
    result = filter_valid_records(sample_df_with_valid_smiles)
    
    # Should exclude index 3 (invalid smiles) and potentially rows with NaN degradation
    # In sample: Index 3 is invalid smiles. Index 3 also has NaN degradation.
    # Valid smiles: 0, 1, 2. All have non-NaN degradation.
    assert len(result) == 3
    assert 'smiles' in result.columns
    assert 'degradation_half_life' in result.columns

def test_check_degradation_columns_true(sample_df_with_valid_smiles):
    assert check_degradation_columns(sample_df_with_valid_smiles) is True

def test_check_degradation_columns_false(sample_df_missing_degradation):
    assert check_degradation_columns(sample_df_missing_degradation) is False

def test_run_data_availability_gate_insufficient():
    # Create a small dataframe
    small_df = pd.DataFrame({'smiles': ['CCO'] * 20, 'half_life': [1.0] * 20})
    result = run_data_availability_gate(small_df, min_records=30)
    assert result is False
    assert Path("data/data_insufficiency_report.md").exists()

def test_run_data_availability_gate_sufficient():
    # Create a large enough dataframe
    large_df = pd.DataFrame({'smiles': ['CCO'] * 35, 'half_life': [1.0] * 35})
    result = run_data_availability_gate(large_df, min_records=30)
    assert result is True
    # Clean up report if it was created in previous test
    report_path = Path("data/data_insufficiency_report.md")
    if report_path.exists():
        report_path.unlink()