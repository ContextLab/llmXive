import pytest
import pandas as pd
import os
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import functions to test
from ingest import (
    fetch_fda_drugs,
    check_degradation_columns,
    validate_smiles_series,
    run_data_availability_gate,
    filter_valid_records,
    calculate_checksums,
    save_merged_dataset
)

@pytest.fixture
def sample_df_with_degradation():
    data = {
        'smiles': ['CC(=O)Oc1ccccc1C(=O)O', 'CC(C)C1=CC=C(C=C1)C(C)C(=O)O', 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C', 'invalid_smiles'],
        'half_life': [24.5, 12.0, 8.5, 15.0],
        'name': ['Aspirin', 'Ibuprofen', 'Caffeine', 'Unknown']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_df_missing_degradation():
    data = {
        'smiles': ['CC(=O)Oc1ccccc1C(=O)O', 'CC(C)C1=CC=C(C=C1)C(C)C(=O)O'],
        'name': ['Aspirin', 'Ibuprofen']
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir(tmp_path):
    processed = tmp_path / "processed"
    processed.mkdir()
    return tmp_path

def test_check_degradation_columns_positive(sample_df_with_degradation):
    assert check_degradation_columns(sample_df_with_degradation) is True

def test_check_degradation_columns_negative(sample_df_missing_degradation):
    assert check_degradation_columns(sample_df_missing_degradation) is False

def test_validate_smiles_series(sample_df_with_degradation):
    result = validate_smiles_series(sample_df_with_degradation['smiles'])
    # First 3 are valid, 4th is invalid
    assert result.iloc[0] is True
    assert result.iloc[3] is False

def test_run_data_availability_gate_valid(sample_df_with_degradation):
    # Should not raise
    result = run_data_availability_gate(sample_df_with_degradation)
    assert len(result) > 0

def test_run_data_availability_gate_insufficient_count():
    data = {
        'smiles': ['CC(=O)Oc1ccccc1C(=O)O'] * 29,
        'half_life': [24.5] * 29
    }
    df = pd.DataFrame(data)
    with pytest.raises(ValueError, match="Insufficient valid records"):
        run_data_availability_gate(df)

def test_filter_valid_records(sample_df_with_degradation):
    # Contains one invalid SMILES
    filtered = filter_valid_records(sample_df_with_degradation)
    assert len(filtered) == 3
    assert 'invalid_smiles' not in filtered['smiles'].values

def test_save_merged_dataset(temp_output_dir):
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    output_path = temp_output_dir / "test.csv"
    save_merged_dataset(df, output_path)
    assert output_path.exists()
    loaded = pd.read_csv(output_path)
    assert len(loaded) == 2

def test_calculate_checksums(temp_output_dir):
    # Create a dummy file
    test_file = temp_output_dir / "dummy.txt"
    test_file.write_text("hello world")
    
    checksum_path = temp_output_dir / "checksums.txt"
    calculate_checksums([test_file], checksum_path)
    
    assert checksum_path.exists()
    content = checksum_path.read_text()
    assert "dummy.txt" in content
    
    # Verify hash
    expected_hash = hashlib.sha256(b"hello world").hexdigest()
    assert expected_hash in content
