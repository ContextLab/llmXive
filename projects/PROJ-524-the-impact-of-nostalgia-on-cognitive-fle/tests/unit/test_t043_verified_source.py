import os
import json
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

# Import the module to test
# Note: We are testing the logic in fetcher.py which is imported by ingestion.py
from ingestion.fetcher import fetch_data, DataFetchError

@patch('ingestion.fetcher.load_dataset')
def test_fetch_uses_verified_config(mock_load_dataset):
    """Test that fetch_data uses the verified config when provided."""
    # Setup mock
    mock_ds = MagicMock()
    mock_ds.__iter__ = lambda self: iter([{'age': 70, 'stimulus_type': 'nostalgia', 'perseverative_errors': 5, 'categories_completed': 4}])
    mock_load_dataset.return_value = mock_ds

    # Create a verified config
    verified_config = {
        'type': 'huggingface',
        'path': 'verified/dataset-id',
        'config_name': 'default'
    }

    # Call fetch_data with verified config
    df, source, simulation_mode = fetch_data(verified_config)

    # Verify load_dataset was called with the verified path
    mock_load_dataset.assert_called_once_with('verified/dataset-id', name='default', split='train', streaming=True)
    assert source == 'verified_huggingface:verified/dataset-id'
    assert simulation_mode is False
    assert len(df) == 1

@patch('ingestion.fetcher.fetch_from_huggingface')
def test_fetch_fails_loudly_without_verified_config(mock_fetch_hf):
    """Test that fetch_data raises DataFetchError if no verified config and fetch fails."""
    # Setup mock to fail
    mock_fetch_hf.side_effect = DataFetchError("No data found")

    # Call fetch_data without verified config
    with pytest.raises(DataFetchError):
        fetch_data(None)

@patch('ingestion.fetcher.fetch_from_huggingface')
def test_fetch_fails_loudly_with_verified_config(mock_fetch_hf):
    """Test that fetch_data raises DataFetchError if verified config is provided but fetch fails."""
    # Setup mock to fail
    mock_fetch_hf.side_effect = DataFetchError("Verified source unavailable")

    verified_config = {
        'type': 'huggingface',
        'path': 'verified/dataset-id',
        'config_name': 'default'
    }

    # Call fetch_data with verified config
    with pytest.raises(DataFetchError):
        fetch_data(verified_config)
