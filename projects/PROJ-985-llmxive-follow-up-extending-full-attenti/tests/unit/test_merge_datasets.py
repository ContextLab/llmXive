import pytest
import pandas as pd
import os
import tempfile
import csv
from pathlib import Path

# Add code to path for imports
pytest_plugins = ['tests.conftest']

from data.merge_datasets import load_ground_truth_labels, load_static_features, load_anomalies, merge_datasets, save_merged_dataset

def test_load_ground_truth_labels(tmp_path):
    """Test loading ground truth labels from parquet."""
    file_path = tmp_path / "test_gt.parquet"
    df = pd.DataFrame({
        'document_id': ['doc1', 'doc2'],
        'token_index': [0, 1],
        'rtpurbo_label': [1, 0]
    })
    df.to_parquet(file_path)
    
    loaded = load_ground_truth_labels(str(file_path))
    assert len(loaded) == 2
    assert 'document_id' in loaded.columns
    assert list(loaded['document_id']) == ['doc1', 'doc2']

def test_load_static_features(tmp_path):
    """Test loading static features from CSV."""
    file_path = tmp_path / "test_sf.csv"
    df = pd.DataFrame({
        'document_id': ['doc1', 'doc2'],
        'token_index': [0, 1],
        'entropy': [0.5, 0.8],
        'pos_tag': ['NOUN', 'VERB']
    })
    df.to_csv(file_path, index=False)
    
    loaded = load_static_features(str(file_path))
    assert len(loaded) == 2
    assert 'entropy' in loaded.columns
    assert list(loaded['entropy']) == [0.5, 0.8]

def test_load_anomalies(tmp_path):
    """Test loading anomalies from CSV."""
    file_path = tmp_path / "test_anomalies.csv"
    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['document_id'])
        writer.writerow(['doc1'])
        writer.writerow(['doc3'])
    
    anomalies = load_anomalies(str(file_path))
    assert 'doc1' in anomalies
    assert 'doc3' in anomalies
    assert 'doc2' not in anomalies

def test_merge_datasets_with_anomalies(tmp_path):
    """Test merging datasets with anomaly exclusion."""
    gt_file = tmp_path / "gt.parquet"
    sf_file = tmp_path / "sf.csv"
    anomaly_file = tmp_path / "anomalies.csv"
    output_file = tmp_path / "merged.csv"
    
    # Create ground truth
    gt_df = pd.DataFrame({
        'document_id': ['doc1', 'doc2', 'doc3'],
        'token_index': [0, 1, 2],
        'rtpurbo_label': [1, 0, 1]
    })
    gt_df.to_parquet(gt_file)
    
    # Create static features
    sf_df = pd.DataFrame({
        'document_id': ['doc1', 'doc2', 'doc3'],
        'token_index': [0, 1, 2],
        'entropy': [0.5, 0.8, 0.2],
        'pos_tag': ['NOUN', 'VERB', 'ADJ']
    })
    sf_df.to_csv(sf_file, index=False)
    
    # Create anomalies (exclude doc2)
    with open(anomaly_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['document_id'])
        writer.writerow(['doc2'])
    
    gt = load_ground_truth_labels(str(gt_file))
    sf = load_static_features(str(sf_file))
    anomalies = load_anomalies(str(anomaly_file))
    
    merged = merge_datasets(gt, sf, anomalies)
    
    assert len(merged) == 2  # doc1 and doc3 remain
    assert 'doc2' not in merged['document_id'].values
    assert 'rtpurbo_label' in merged.columns
    assert 'entropy' in merged.columns
    
    # Verify schema
    assert 'document_id' in merged.columns
    assert 'token_index' in merged.columns
    assert 'rtpurbo_label' in merged.columns
    assert 'entropy' in merged.columns
    assert 'pos_tag' in merged.columns

def test_merge_datasets_no_anomalies(tmp_path):
    """Test merging datasets without anomalies."""
    gt_file = tmp_path / "gt.parquet"
    sf_file = tmp_path / "sf.csv"
    
    gt_df = pd.DataFrame({
        'document_id': ['doc1', 'doc2'],
        'token_index': [0, 1],
        'rtpurbo_label': [1, 0]
    })
    gt_df.to_parquet(gt_file)
    
    sf_df = pd.DataFrame({
        'document_id': ['doc1', 'doc2'],
        'token_index': [0, 1],
        'entropy': [0.5, 0.8]
    })
    sf_df.to_csv(sf_file, index=False)
    
    gt = load_ground_truth_labels(str(gt_file))
    sf = load_static_features(str(sf_file))
    
    merged = merge_datasets(gt, sf, set())
    
    assert len(merged) == 2
    assert list(merged['document_id']) == ['doc1', 'doc2']

def test_save_merged_dataset(tmp_path):
    """Test saving merged dataset to CSV."""
    output_file = tmp_path / "merged.csv"
    df = pd.DataFrame({
        'document_id': ['doc1', 'doc2'],
        'rtpurbo_label': [1, 0],
        'entropy': [0.5, 0.8]
    })
    
    save_merged_dataset(df, str(output_file))
    
    assert os.path.exists(output_file)
    loaded = pd.read_csv(output_file)
    assert len(loaded) == 2
    assert list(loaded.columns) == ['document_id', 'rtpurbo_label', 'entropy']
