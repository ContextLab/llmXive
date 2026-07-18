"""
Tests for the WebVid data loader (T009).
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# We mock the actual dataset loading to ensure unit tests run without internet
# and to verify the logic of stratified sampling.
from src.data.loaders import load_webvid_subjects, _get_top_n_categories


def test_get_top_n_categories():
    """Test that top N categories are correctly identified."""
    data = {
        'category': ['A', 'A', 'A', 'B', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K'],
        'id': list(range(14))
    }
    df = pd.DataFrame(data)
    top = _get_top_n_categories(df, n=3)
    assert top == ['A', 'B', 'C']  # A:3, B:2, C:1


@patch('src.data.loaders.load_dataset')
def test_load_webvid_subjects_stratified(mock_load_dataset):
    """Test that the loader performs stratified sampling correctly."""
    # Create a mock dataset
    mock_df = pd.DataFrame({
        'category': ['Cat' + str(i % 10) for i in range(1000)], # 10 categories, 100 each
        'videoid': [f'vid_{i}' for i in range(1000)]
    })
    
    mock_dataset = MagicMock()
    mock_dataset.to_pandas.return_value = mock_df
    mock_dataset.column_names = ['category', 'videoid']
    mock_load_dataset.return_value = mock_dataset

    result = load_webvid_subjects(num_subjects=100, seed=42)

    assert 'subjects_df' in result
    assert 'subject_ids' in result
    assert len(result['subject_ids']) == 100
    
    # Check distribution: 100 subjects / 10 categories = 10 per category
    counts = result['subjects_df']['category'].value_counts()
    assert all(counts == 10), f"Expected 10 per category, got:\n{counts}"


@patch('src.data.loaders.load_dataset')
def test_load_webvid_subjects_fails_on_missing_columns(mock_load_dataset):
    """Test that the loader raises ValueError if columns are missing."""
    mock_df = pd.DataFrame({
        'wrong_col': ['A', 'B'],
        'id': [1, 2]
    })
    
    mock_dataset = MagicMock()
    mock_dataset.to_pandas.return_value = mock_df
    mock_dataset.column_names = ['wrong_col', 'id']
    mock_load_dataset.return_value = mock_dataset

    with pytest.raises(ValueError):
        load_webvid_subjects(num_subjects=100, seed=42)