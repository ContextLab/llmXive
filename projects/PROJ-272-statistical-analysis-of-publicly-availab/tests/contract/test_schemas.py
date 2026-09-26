"""
Contract tests for dataset schemas and metadata.
"""
import pytest
import pandas as pd
import json
from pathlib import Path

from config import get_path

def test_cleaned_dataset_schema():
    """Validates data/interim/cleaned_adress.csv schema."""
    path = get_path('data/interim/cleaned_adress.csv')
    if not path.exists():
        pytest.skip(f"File {path} does not exist yet.")

    df = pd.read_csv(path)
    required_cols = {'participant_id', 'label', 'text'}
    assert required_cols.issubset(df.columns), f"Missing columns: {required_cols - set(df.columns)}"
    assert df['label'].notnull().all(), "All labels must be non-null"
    assert df['text'].str.len().min() >= 50, "All texts must be >= 50 words"

def test_metadata_schema():
    """Validates data/results/metadata.json schema and SC-001."""
    path = get_path('data/results/metadata.json')
    if not path.exists():
        pytest.skip(f"File {path} does not exist yet.")

    with open(path, 'r') as f:
        metadata = json.load(f)

    assert 'valid_label_proportion' in metadata, "Missing valid_label_proportion"
    prop = metadata['valid_label_proportion']
    assert isinstance(prop, float), "valid_label_proportion must be float"
    assert 0.0 <= prop <= 1.0, "valid_label_proportion must be between 0 and 1"

    # Check optional low_power flag
    if 'low_power' in metadata:
        assert isinstance(metadata['low_power'], bool)
