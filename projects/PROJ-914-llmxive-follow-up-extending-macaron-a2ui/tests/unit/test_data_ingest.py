"""
Unit tests for data ingestion logic.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.ingest import load_dataset_from_hf, validate_dataframe, save_raw_csv

@patch('code.data.ingest.load_dataset')
def test_load_dataset_from_hf_success(mock_load_dataset):
    """Test successful loading of dataset."""
    # Mock the dataset object
    mock_dataset = MagicMock()
    mock_dataset.to_pandas.return_value = pd.DataFrame({"query": ["test"], "intent": ["int"], "context": ["ctx"]})
    mock_load_dataset.return_value = mock_dataset

    df = load_dataset_from_hf()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert "query" in df.columns

@patch('code.data.ingest.load_dataset')
def test_load_dataset_from_hf_failure(mock_load_dataset):
    """Test that loading fails loudly when dataset is unavailable."""
    mock_load_dataset.side_effect = Exception("Connection failed")

    with pytest.raises(RuntimeError, match="Failed to fetch or process dataset"):
        load_dataset_from_hf()

def test_validate_dataframe_valid():
    """Test validation with a valid DataFrame."""
    df = pd.DataFrame({"query": ["test"], "intent": ["int"]})
    assert validate_dataframe(df) is True

def test_validate_dataframe_empty():
    """Test validation with an empty DataFrame."""
    df = pd.DataFrame()
    assert validate_dataframe(df) is False

def test_validate_dataframe_missing_query():
    """Test validation when query column is missing but text exists."""
    df = pd.DataFrame({"text_query": ["test"], "intent": ["int"]})
    # Should map text_query to query and return True
    result = validate_dataframe(df)
    assert result is True
    assert "query" in df.columns

def test_validate_dataframe_no_query_or_text():
    """Test validation when no query-like column exists."""
    df = pd.DataFrame({"col1": ["test"], "col2": ["int"]})
    assert validate_dataframe(df) is False