import json
import os
import pandas as pd
import pytest
from pathlib import Path

# Import config to get paths
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from config import get_path

def test_cleaned_dataset_schema():
    """
    Contract test for T016: Verify data/interim/cleaned_adress.csv exists and has required columns.
    """
    path = get_path("data/interim/cleaned_adress.csv")
    assert os.path.exists(path), f"Cleaned dataset file not found: {path}"
    
    df = pd.read_csv(path)
    
    # Verify required columns (based on T013/T014/T015 requirements)
    required_cols = ['participant_id', 'text', 'label', 'cognitive_status']
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Verify no null labels (T014 constraint)
    assert df['label'].notnull().all(), "Found null labels in cleaned dataset"
    
    # Verify text length >= 50 words (T014 constraint)
    if 'text' in df.columns:
        word_counts = df['text'].astype(str).apply(lambda x: len(x.split()))
        assert (word_counts >= 50).all(), "Found text entries with < 50 words"

def test_success_criterion_sc001():
    """
    Contract test for T012h: Verify data/results/metadata.json contains valid_label_proportion.
    """
    path = get_path("data/results/metadata.json")
    assert os.path.exists(path), f"Metadata file not found: {path}"
    
    with open(path, 'r') as f:
        metadata = json.load(f)
    
    assert 'valid_label_proportion' in metadata, "Missing key 'valid_label_proportion' in metadata"
    
    proportion = metadata['valid_label_proportion']
    assert 0 <= proportion <= 1, f"valid_label_proportion must be between 0 and 1, got {proportion}"

def test_exclusions_log_exists():
    """
    Contract test for T014: Verify exclusions log exists.
    """
    path = get_path("data/interim/exclusions.log")
    assert os.path.exists(path), f"Exclusions log not found: {path}"
    
    # File should not be empty if exclusions occurred, but even if empty, it must exist.
    with open(path, 'r') as f:
        content = f.read()
    # We don't assert content is non-empty because a perfect dataset might have no exclusions.
    # But the file must exist.
