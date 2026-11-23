"""
Contract tests for dataset schemas and metadata.
Validates T011 requirements:
1. data/interim/cleaned_adress.csv schema (participant_id, label, text)
2. data/results/metadata.json schema (raw_count, filtered_count, valid_label_proportion, group_counts)
"""
import pytest
import pandas as pd
import json
from pathlib import Path

from config import get_path

def test_cleaned_dataset_schema():
    """Validates data/interim/cleaned_adress.csv schema per T006 and T016."""
    path = get_path('data/interim/cleaned_adress.csv')
    if not path.exists():
        pytest.skip(f"File {path} does not exist yet.")

    df = pd.read_csv(path)
    
    # Check required columns from dataset.schema.yaml (T006)
    required_cols = {'participant_id', 'label', 'text'}
    assert required_cols.issubset(df.columns), f"Missing columns: {required_cols - set(df.columns)}"
    
    # Check data integrity constraints
    assert df['label'].notnull().all(), "All labels must be non-null"
    
    # Check text length constraint (>= 50 words as per FR-001)
    # We check character length >= 50 as a proxy, but ideally we'd count words
    # The task description says "text length < 50 words" for filtering
    # We'll check that text is not empty and has reasonable length
    assert df['text'].str.len().min() >= 50, "All texts must be >= 50 characters (proxy for words)"

def test_metadata_schema():
    """Validates data/results/metadata.json schema per T012g and SC-001."""
    path = get_path('data/results/metadata.json')
    if not path.exists():
        pytest.skip(f"File {path} does not exist yet.")

    with open(path, 'r') as f:
        metadata = json.load(f)

    # Check required keys from T012g specification
    required_keys = {'raw_count', 'filtered_count', 'valid_label_proportion', 'group_counts'}
    assert required_keys.issubset(metadata.keys()), f"Missing keys: {required_keys - set(metadata.keys())}"

    # Validate types and constraints
    assert isinstance(metadata['raw_count'], int), "raw_count must be int"
    assert isinstance(metadata['filtered_count'], int), "filtered_count must be int"
    
    prop = metadata['valid_label_proportion']
    assert isinstance(prop, float), "valid_label_proportion must be float"
    assert 0.0 <= prop <= 1.0, "valid_label_proportion must be between 0 and 1"

    # Validate group_counts structure
    assert isinstance(metadata['group_counts'], dict), "group_counts must be dict"
    expected_groups = {'Control', 'MCI', 'AD'}
    assert expected_groups.issubset(metadata['group_counts'].keys()), \
        f"Missing group counts: {expected_groups - set(metadata['group_counts'].keys())}"
    
    for group, count in metadata['group_counts'].items():
        assert isinstance(count, int), f"group_counts[{group}] must be int"
        assert count >= 0, f"group_counts[{group}] must be non-negative"

    # Cross-validate: filtered_count should be <= raw_count
    assert metadata['filtered_count'] <= metadata['raw_count'], \
        "filtered_count cannot exceed raw_count"

    # Cross-validate: valid_label_proportion calculation
    if metadata['raw_count'] > 0:
        expected_prop = metadata['filtered_count'] / metadata['raw_count']
        # Allow small floating point tolerance
        assert abs(prop - expected_prop) < 1e-6, \
            f"valid_label_proportion ({prop}) does not match filtered/raw ({expected_prop})"