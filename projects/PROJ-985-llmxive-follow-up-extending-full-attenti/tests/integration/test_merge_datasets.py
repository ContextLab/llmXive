import os
import tempfile
import h5py
import pandas as pd
import pytest

from code.data.merge_datasets import (
    load_ground_truth_labels,
    load_static_features,
    load_anomalies,
    merge_datasets,
    save_merged_dataset
)
from code.lib.logging_config import get_anomalies_path

@pytest.fixture
def temp_h5_file(tmp_path):
    """Create a temporary HDF5 file with ground truth data."""
    h5_path = tmp_path / "attention_maps.h5"
    
    with h5py.File(h5_path, 'w') as f:
        doc_group = f.create_group("docs/doc_001")
        tokens_group = doc_group.create_group("tokens")
        
        # Add token 0
        token_0 = tokens_group.create_group("0")
        token_0.create_dataset("is_rtpurbo", data=1)
        token_0.create_dataset("attention_score", data=0.85)
        
        # Add token 1
        token_1 = tokens_group.create_group("1")
        token_1.create_dataset("is_rtpurbo", data=0)
        token_1.create_dataset("attention_score", data=0.12)
        
        # Add token 2
        token_2 = tokens_group.create_group("2")
        token_2.create_dataset("is_rtpurbo", data=1)
        token_2.create_dataset("attention_score", data=0.92)
    
    return str(h5_path)

@pytest.fixture
def temp_features_csv(tmp_path):
    """Create a temporary CSV file with static features."""
    csv_path = tmp_path / "static_features.csv"
    
    data = {
        'doc_id': ['doc_001', 'doc_001', 'doc_001'],
        'token_idx': [0, 1, 2],
        'entropy': [0.5, 0.3, 0.8],
        'pos_tag': ['NOUN', 'VERB', 'ADJ'],
        'kenlm_perplexity': [1.2, 1.5, 1.1]
    }
    
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    
    return str(csv_path)

@pytest.fixture
def temp_anomalies_csv(tmp_path):
    """Create a temporary CSV file with anomalies."""
    csv_path = tmp_path / "anomalies.csv"
    
    data = {
        'doc_id': ['doc_002'],
        'reason': ['zero_rtpurbo_tokens']
    }
    
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    
    return str(csv_path)

def test_load_ground_truth_labels(temp_h5_file):
    """Test loading ground truth from HDF5."""
    df = load_ground_truth_labels(temp_h5_file)
    
    assert len(df) == 3
    assert 'doc_id' in df.columns
    assert 'token_idx' in df.columns
    assert 'is_rtpurbo' in df.columns
    assert 'attention_score' in df.columns
    
    assert df['doc_id'].iloc[0] == 'doc_001'
    assert df['token_idx'].iloc[0] == 0
    assert df['is_rtpurbo'].iloc[0] == 1
    assert abs(df['attention_score'].iloc[0] - 0.85) < 0.001

def test_load_static_features(temp_features_csv):
    """Test loading static features from CSV."""
    df = load_static_features(temp_features_csv)
    
    assert len(df) == 3
    assert 'doc_id' in df.columns
    assert 'token_idx' in df.columns
    assert 'entropy' in df.columns
    assert 'pos_tag' in df.columns
    assert 'kenlm_perplexity' in df.columns

def test_load_anomalies(temp_anomalies_csv, tmp_path):
    """Test loading anomalies from CSV."""
    # Temporarily override the anomalies path
    original_get_anomalies_path = get_anomalies_path
    
    def mock_get_anomalies_path():
        return temp_anomalies_csv
    
    import code.data.merge_datasets as merge_module
    merge_module.get_anomalies_path = mock_get_anomalies_path
    
    try:
        df = load_anomalies()
        assert len(df) == 1
        assert df['doc_id'].iloc[0] == 'doc_002'
        assert df['reason'].iloc[0] == 'zero_rtpurbo_tokens'
    finally:
        merge_module.get_anomalies_path = original_get_anomalies_path

def test_merge_datasets_excludes_anomalies(temp_h5_file, temp_features_csv, temp_anomalies_csv, tmp_path):
    """Test that merge correctly excludes anomalous documents."""
    # Create a scenario where doc_001 is NOT anomalous, but we have another doc
    # that IS anomalous and should be excluded
    
    # Load data
    gt_df = load_ground_truth_labels(temp_h5_file)
    features_df = load_static_features(temp_features_csv)
    
    # Create anomalies with a different doc_id to ensure filtering works
    anomalies_data = {
        'doc_id': ['doc_002'],
        'reason': ['zero_rtpurbo_tokens']
    }
    anomalies_df = pd.DataFrame(anomalies_data)
    
    # Merge
    merged_df = merge_datasets(gt_df, features_df, anomalies_df)
    
    # Should have all 3 records from doc_001 (none excluded)
    assert len(merged_df) == 3
    assert 'doc_001' in merged_df['doc_id'].values
    assert 'doc_002' not in merged_df['doc_id'].values

def test_merge_datasets_preserves_columns(temp_h5_file, temp_features_csv, tmp_path):
    """Test that merged dataset has all expected columns."""
    gt_df = load_ground_truth_labels(temp_h5_file)
    features_df = load_static_features(temp_features_csv)
    anomalies_df = pd.DataFrame(columns=['doc_id', 'reason'])
    
    merged_df = merge_datasets(gt_df, features_df, anomalies_df)
    
    expected_cols = [
        'doc_id', 'token_idx', 'is_rtpurbo', 'attention_score',
        'entropy', 'pos_tag', 'kenlm_perplexity'
    ]
    
    for col in expected_cols:
        assert col in merged_df.columns

def test_save_merged_dataset(temp_h5_file, temp_features_csv, tmp_path):
    """Test saving merged dataset to CSV."""
    gt_df = load_ground_truth_labels(temp_h5_file)
    features_df = load_static_features(temp_features_csv)
    anomalies_df = pd.DataFrame(columns=['doc_id', 'reason'])
    
    merged_df = merge_datasets(gt_df, features_df, anomalies_df)
    
    output_path = tmp_path / "merged_dataset.csv"
    save_merged_dataset(merged_df, str(output_path))
    
    assert os.path.exists(output_path)
    
    # Verify saved content
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == len(merged_df)
    assert list(saved_df.columns) == list(merged_df.columns)
