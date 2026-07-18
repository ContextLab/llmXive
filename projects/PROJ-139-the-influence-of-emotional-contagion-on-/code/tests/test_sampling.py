"""
Tests for the sampling module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from code.data.sampling import sample_comments, get_vader_label, get_textblob_label, generate_annotations

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        'comment_id': ['c1', 'c2', 'c3', 'c4', 'c5'],
        'text': [
            'This is great!',
            'This is terrible.',
            'It is okay.',
            'I love this!',
            'I hate this.'
        ],
        'thread_id': ['t1', 't1', 't1', 't2', 't2']
    }
    return pd.DataFrame(data)

def test_sample_comments_small_dataset(sample_dataframe):
    """Test sampling when dataset is smaller than sample size."""
    result = sample_comments(sample_dataframe, sample_size=100, seed=42)
    assert len(result) == len(sample_dataframe)
    assert all('comment_id' in item for item in result)

def test_sample_comments_larger_dataset(sample_dataframe):
    """Test sampling when dataset is larger than sample size."""
    # Create a larger dataset
    large_data = pd.concat([sample_dataframe] * 100, ignore_index=True)
    result = sample_comments(large_data, sample_size=50, seed=42)
    assert len(result) == 50
    assert all('comment_id' in item for item in result)

def test_sample_comments_reproducibility(sample_dataframe):
    """Test that sampling is reproducible with same seed."""
    result1 = sample_comments(sample_dataframe, sample_size=3, seed=42)
    result2 = sample_comments(sample_dataframe, sample_size=3, seed=42)
    assert result1 == result2

def test_get_vader_label_positive():
    """Test VADER label for positive text."""
    label = get_vader_label("This is amazing and wonderful!")
    assert label == 'positive'

def test_get_vader_label_negative():
    """Test VADER label for negative text."""
    label = get_vader_label("This is terrible and awful!")
    assert label == 'negative'

def test_get_vader_label_neutral():
    """Test VADER label for neutral text."""
    label = get_vader_label("The weather is okay today.")
    assert label == 'neutral'

def test_get_textblob_label_positive():
    """Test TextBlob label for positive text."""
    label = get_textblob_label("I love this product!")
    assert label == 'positive'

def test_get_textblob_label_negative():
    """Test TextBlob label for negative text."""
    label = get_textblob_label("This is the worst experience ever.")
    assert label == 'negative'

def test_get_textblob_label_neutral():
    """Test TextBlob label for neutral text."""
    label = get_textblob_label("The package was delivered.")
    assert label == 'neutral'

def test_generate_annotations_creates_file():
    """Test that generate_annotations creates the output file."""
    sampled_comments = [
        {'comment_id': 'c1', 'text': 'Test comment 1'},
        {'comment_id': 'c2', 'text': 'Test comment 2'}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "annotations.json"
        generate_annotations(sampled_comments, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            annotations = json.load(f)
        
        assert len(annotations) == 2
        assert all('comment_id' in ann for ann in annotations)
        assert all(ann['label'] == 'neutral' for ann in annotations)
