import json
import os
import tempfile
from pathlib import Path
import pytest
import sys
from unittest.mock import patch, MagicMock
from scripts.download_gold_standard import download_gold_standard

def test_download_gold_standard_creates_file():
    """Test that the download function creates the expected JSON file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "test_annotations.json"
        
        # Mock the load_dataset to avoid network calls in unit test
        # but verify the logic that processes the data
        mock_data = {
            "text": ["Sample text 1", "Sample text 2"],
            "label": [0, 1]
        }
        
        with patch('scripts.download_gold_standard.load_dataset') as mock_load:
            mock_load.return_value = mock_data
            # We need to mock the split behavior
            mock_dataset = MagicMock()
            mock_dataset.__getitem__ = lambda self, key: mock_data if key == slice(None, 20, None) else None
            mock_load.return_value = mock_dataset
            
            # Actually, the function expects a dataset object that supports slicing
            # Let's mock the return value of load_dataset to be a dict-like object
            # that supports slicing for the first 20 items
            def mock_load_side_effect(*args, **kwargs):
                class MockDataset:
                    def __init__(self, data):
                        self.data = data
                    def __getitem__(self, key):
                        if isinstance(key, slice):
                            # Return a dict with lists for the slice range
                            start = key.start or 0
                            stop = key.stop or len(self.data['text'])
                            return {
                                'text': self.data['text'][start:stop],
                                'label': self.data['label'][start:stop]
                            }
                        return self.data['text'][key]
                return MockDataset(mock_data)
            
            with patch('scripts.download_gold_standard.load_dataset', side_effect=mock_load_side_effect):
                download_gold_standard(str(output_path))
        
        # Verify file exists
        assert output_path.exists()
        
        # Verify content structure
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) == 2 # We mocked 2 items
        assert 'id' in data[0]
        assert 'scenario' in data[0]
        assert 'human_annotation' in data[0]
        assert data[0]['human_annotation'] in [1.0, 5.0] # From the mapping logic

def test_download_fails_loudly_on_error():
    """Test that the function raises an error if the dataset load fails."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "test_fail.json"
        
        with patch('scripts.download_gold_standard.load_dataset', side_effect=Exception("Network Error")):
            with pytest.raises(RuntimeError, match="Gold Standard download failed"):
                download_gold_standard(str(output_path))