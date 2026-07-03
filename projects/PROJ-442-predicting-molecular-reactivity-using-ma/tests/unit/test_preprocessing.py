import pytest
import pandas as pd
import os
import tempfile
from pathlib import Path
import shutil

from src.data.preprocessing import (
    save_feature_matrix,
    load_feature_matrix,
    preprocess_and_save_features,
    compute_file_checksum
)

@pytest.fixture
def temp_dir():
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def sample_feature_df():
    data = {
        'feat_mw': [100.5, 200.3, 150.7],
        'feat_atom_count': [10, 20, 15],
        'feat_logp': [1.2, 2.5, 1.8],
        'yield_pct': [80.0, 90.0, 85.0]  # Target column
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_filtered_csv(temp_dir):
    csv_path = os.path.join(temp_dir, "filtered_reactions.csv")
    data = {
        'smiles_reactants': ['C1=CC=CC=C1', 'CCO', 'CC(=O)O'],
        'smiles_products': ['C1=CC=CC=C1', 'CCOC', 'CC(=O)OC'],
        'reaction_type': ['SN1', 'SN2', 'Diels-Alder'],
        'yield_pct': [80.0, 90.0, 85.0],
        'feat_mw': [100.5, 200.3, 150.7],
        'feat_atom_count': [10, 20, 15],
        'feat_logp': [1.2, 2.5, 1.8],
        'feat_hba': [2, 1, 3],
        'feat_hbd': [1, 2, 1]
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path

def test_save_and_load_feature_matrix(temp_dir, sample_feature_df):
    output_path = os.path.join(temp_dir, "test_features.parquet")
    checksum_path = os.path.join(temp_dir, "test_features.parquet.checksum")

    # Save
    saved_path, checksum = save_feature_matrix(sample_feature_df, output_path, checksum_path)
    
    assert os.path.exists(saved_path)
    assert os.path.exists(checksum_path)
    
    # Verify checksum file content
    with open(checksum_path, 'r') as f:
        saved_checksum = f.read()
    assert saved_checksum == checksum
    
    # Load
    loaded_df = load_feature_matrix(saved_path)
    
    assert loaded_df.shape == sample_feature_df.shape
    assert list(loaded_df.columns) == list(sample_feature_df.columns)
    pd.testing.assert_frame_equal(loaded_df, sample_feature_df)

def test_compute_file_checksum(temp_dir, sample_feature_df):
    output_path = os.path.join(temp_dir, "test.parquet")
    save_feature_matrix(sample_feature_df, output_path)
    
    checksum1 = compute_file_checksum(output_path)
    checksum2 = compute_file_checksum(output_path)
    
    assert checksum1 == checksum2
    assert len(checksum1) == 64  # SHA256 hex length

def test_preprocess_and_save_features(temp_dir, sample_filtered_csv):
    output_parquet = os.path.join(temp_dir, "processed_features.parquet")
    
    result = preprocess_and_save_features(sample_filtered_csv, output_parquet)
    
    assert os.path.exists(result["output_path"])
    assert "checksum" in result
    assert result["feature_count"] > 0
    assert result["row_count"] == 3
    
    # Verify the saved file can be loaded
    loaded_df = load_feature_matrix(result["output_path"])
    assert not loaded_df.empty
    # Check that target columns were excluded
    assert 'yield_pct' not in loaded_df.columns
    assert 'reaction_type' not in loaded_df.columns

def test_preprocess_missing_file():
    with pytest.raises(FileNotFoundError):
        preprocess_and_save_features("nonexistent.csv", "output.parquet")

def test_preprocess_empty_features(temp_dir):
    csv_path = os.path.join(temp_dir, "empty_features.csv")
    data = {
        'smiles_reactants': ['C'],
        'reaction_type': ['SN1'],
        'yield_pct': [50.0]
    }
    pd.DataFrame(data).to_csv(csv_path, index=False)
    
    output_path = os.path.join(temp_dir, "out.parquet")
    with pytest.raises(ValueError, match="No feature columns found"):
        preprocess_and_save_features(csv_path, output_path)