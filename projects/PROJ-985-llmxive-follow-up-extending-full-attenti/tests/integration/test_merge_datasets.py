import os
import pytest
import pandas as pd
import numpy as np
import h5py
import tempfile
import shutil

from data.merge_datasets import (
    load_ground_truth_labels,
    load_static_features,
    load_anomalies,
    merge_datasets,
    save_merged_dataset,
    main
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)

@pytest.fixture
def sample_attention_maps(temp_dir):
    """Create a sample attention maps HDF5 file."""
    h5_path = os.path.join(temp_dir, "attention_maps.h5")
    
    with h5py.File(h5_path, 'w') as hf:
        # Document 1
        doc1 = hf.create_group("doc_001")
        doc1.create_dataset("rtpurbo_indices", data=[0, 2, 5, 10])
        stats1 = doc1.create_group("attention_stats")
        stats1.create_dataset("mean_entropy", data=0.75)
        stats1.create_dataset("max_entropy", data=1.2)
        
        # Document 2
        doc2 = hf.create_group("doc_002")
        doc2.create_dataset("rtpurbo_indices", data=[1, 3, 7])
        stats2 = doc2.create_group("attention_stats")
        stats2.create_dataset("mean_entropy", data=0.65)
        stats2.create_dataset("max_entropy", data=1.1)
        
        # Document 3 (will be anomalous)
        doc3 = hf.create_group("doc_003")
        doc3.create_dataset("rtpurbo_indices", data=[])
        stats3 = doc3.create_group("attention_stats")
        stats3.create_dataset("mean_entropy", data=0.5)
    
    return h5_path

@pytest.fixture
def sample_features(temp_dir):
    """Create a sample static features CSV file."""
    csv_path = os.path.join(temp_dir, "static_features.csv")
    
    data = {
        'doc_id': ['doc_001', 'doc_001', 'doc_001', 'doc_001', 'doc_001',
                   'doc_002', 'doc_002', 'doc_002', 'doc_002', 'doc_002',
                   'doc_003', 'doc_003'],
        'token_id': [0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1],
        'entropy': [0.8, 0.5, 0.9, 0.4, 0.6, 0.7, 0.6, 0.8, 0.5, 0.7, 0.5, 0.4],
        'pos_tag': ['NN', 'VB', 'NN', 'DT', 'NN', 'VB', 'NN', 'DT', 'VB', 'NN', 'NN', 'VB'],
        'position': [0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1],
        'kenlm_perplexity': [10.5, 12.3, 9.8, 15.2, 11.1, 10.2, 11.5, 9.9, 14.8, 10.8, 12.0, 13.5]
    }
    
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    
    return csv_path

@pytest.fixture
def sample_anomalies(temp_dir):
    """Create a sample anomalies CSV file."""
    csv_path = os.path.join(temp_dir, "anomalies.csv")
    
    data = {'doc_id': ['doc_003']}
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    
    return csv_path

def test_load_ground_truth_labels(sample_attention_maps):
    """Test loading ground truth labels from HDF5."""
    labels = load_ground_truth_labels(sample_attention_maps)
    
    assert 'doc_001' in labels
    assert 'doc_002' in labels
    assert 'doc_003' in labels
    
    assert labels['doc_001']['rtpurbo_indices'] == [0, 2, 5, 10]
    assert labels['doc_001']['attention_stats']['mean_entropy'] == 0.75
    
    assert labels['doc_002']['rtpurbo_indices'] == [1, 3, 7]
    assert labels['doc_002']['attention_stats']['max_entropy'] == 1.1

def test_load_static_features(sample_features):
    """Test loading static features from CSV."""
    df = load_static_features(sample_features)
    
    assert len(df) == 12
    assert 'doc_id' in df.columns
    assert 'token_id' in df.columns
    assert 'entropy' in df.columns
    assert 'pos_tag' in df.columns
    
    assert df['doc_id'].nunique() == 3

def test_load_anomalies(sample_anomalies):
    """Test loading anomalies from CSV."""
    anomalies = load_anomalies(sample_anomalies)
    
    assert 'doc_003' in anomalies
    assert len(anomalies) == 1

def test_load_anomalies_missing_file(temp_dir):
    """Test loading anomalies when file doesn't exist."""
    anomalies = load_anomalies(os.path.join(temp_dir, "nonexistent.csv"))
    
    assert len(anomalies) == 0

def test_merge_datasets_basic(sample_attention_maps, sample_features, sample_anomalies):
    """Test basic merge functionality."""
    labels = load_ground_truth_labels(sample_attention_maps)
    features_df = load_static_features(sample_features)
    anomalies = load_anomalies(sample_anomalies)
    
    merged_df = merge_datasets(labels, features_df, anomalies)
    
    # Should have 10 rows (5 from doc_001 + 5 from doc_002, excluding doc_003)
    assert len(merged_df) == 10
    
    # Check is_rtpurbo column exists
    assert 'is_rtpurbo' in merged_df.columns
    
    # Check attention stats were added
    assert 'attention_mean_entropy' in merged_df.columns
    assert 'attention_max_entropy' in merged_df.columns
    
    # Verify RTPurbo labels
    doc_001_rtpurbo = merged_df[merged_df['doc_id'] == 'doc_001']['is_rtpurbo'].tolist()
    expected_doc_001 = [True, False, True, False, False]  # indices 0, 2 are RTPurbo
    assert doc_001_rtpurbo == expected_doc_001

def test_merge_datasets_excludes_anomalies(sample_attention_maps, sample_features, sample_anomalies):
    """Test that anomalous documents are excluded."""
    labels = load_ground_truth_labels(sample_attention_maps)
    features_df = load_static_features(sample_features)
    anomalies = load_anomalies(sample_anomalies)
    
    merged_df = merge_datasets(labels, features_df, anomalies)
    
    # doc_003 should not be in merged dataset
    assert 'doc_003' not in merged_df['doc_id'].values

def test_merge_datasets_no_anomalies(sample_attention_maps, sample_features, temp_dir):
    """Test merge without anomalies file."""
    labels = load_ground_truth_labels(sample_attention_maps)
    features_df = load_static_features(sample_features)
    anomalies = set()  # No anomalies
    
    merged_df = merge_datasets(labels, features_df, anomalies)
    
    # Should include all documents (12 rows)
    assert len(merged_df) == 12
    assert 'doc_003' in merged_df['doc_id'].values

def test_save_merged_dataset(temp_dir, sample_attention_maps, sample_features):
    """Test saving merged dataset to CSV."""
    labels = load_ground_truth_labels(sample_attention_maps)
    features_df = load_static_features(sample_features)
    anomalies = set()
    
    merged_df = merge_datasets(labels, features_df, anomalies)
    
    output_path = os.path.join(temp_dir, "merged.csv")
    save_merged_dataset(merged_df, output_path)
    
    assert os.path.exists(output_path)
    
    # Verify saved file
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == len(merged_df)
    assert 'is_rtpurbo' in saved_df.columns

def test_merge_datasets_empty_result(temp_dir):
    """Test that merge fails when result would be empty."""
    # Create empty features
    csv_path = os.path.join(temp_dir, "empty_features.csv")
    pd.DataFrame(columns=['doc_id', 'token_id']).to_csv(csv_path, index=False)
    
    h5_path = os.path.join(temp_dir, "empty_attention.h5")
    with h5py.File(h5_path, 'w') as hf:
        pass  # Empty file
    
    labels = load_ground_truth_labels(h5_path)
    features_df = load_static_features(csv_path)
    anomalies = set()
    
    with pytest.raises(ValueError, match="Merged dataset is empty"):
        merge_datasets(labels, features_df, anomalies)

def test_main_function(temp_dir, sample_attention_maps, sample_features, sample_anomalies):
    """Test the main function end-to-end."""
    output_path = os.path.join(temp_dir, "merged_output.csv")
    
    # Run main with our test files
    import sys
    sys.argv = [
        'merge_datasets.py',
        '--attention-maps', sample_attention_maps,
        '--features', sample_features,
        '--anomalies', sample_anomalies,
        '--output', output_path
    ]
    
    main()
    
    assert os.path.exists(output_path)
    
    # Verify output
    df = pd.read_csv(output_path)
    assert len(df) == 10
    assert 'is_rtpurbo' in df.columns