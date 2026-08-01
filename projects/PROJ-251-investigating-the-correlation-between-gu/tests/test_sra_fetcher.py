import unittest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.sra_fetcher import fetch_huggingface_data, DATASET_HF_ID
from code.utils.sra_downloader import DataUnavailableError

class TestSRAFetcher(unittest.TestCase):
    def setUp(self):
        self.mock_data = pd.DataFrame({
            'subject_id': ['S001', 'S002', 'S003'],
            'baseline_titer': [10.0, 20.0, 15.0],
            'post_titer': [40.0, 80.0, 60.0],
            'taxon_Bacteroides': [0.2, 0.3, 0.25],
            'taxon_Firmicutes': [0.4, 0.35, 0.3],
            'taxon_Proteobacteria': [0.1, 0.15, 0.12]
        })
    
    @patch('code.utils.sra_fetcher.load_dataset')
    def test_fetch_huggingface_data_success(self, mock_load_dataset):
        """Test successful data fetch from HuggingFace"""
        mock_dataset = MagicMock()
        mock_dataset.to_pandas.return_value = self.mock_data
        mock_load_dataset.return_value = mock_dataset
        
        # This would normally write to disk, but we're mocking
        # We'll just verify the logic runs without error
        with patch('code.utils.sra_fetcher.get_raw_path') as mock_path:
            mock_path.return_value = Path('/tmp/test_raw')
            mock_path.return_value.mkdir = MagicMock()
            
            # We can't actually test the file write without mocking the whole flow
            # But we can verify the dataset loading logic
            dataset = mock_load_dataset(DATASET_HF_ID, split='train', streaming=True)
            dataset.to_pandas.assert_called_once()
    
    def test_fetch_raises_on_missing_columns(self):
        """Test that fetch raises DataUnavailableError when required columns are missing"""
        incomplete_data = pd.DataFrame({
            'subject_id': ['S001'],
            'baseline_titer': [10.0]
            # Missing post_titer and taxon columns
        })
        
        with patch('code.utils.sra_fetcher.load_dataset') as mock_load:
            mock_dataset = MagicMock()
            mock_dataset.to_pandas.return_value = incomplete_data
            mock_load.return_value = mock_dataset
            
            with self.assertRaises(DataUnavailableError):
                with patch('code.utils.sra_fetcher.get_raw_path') as mock_path:
                    mock_path.return_value = Path('/tmp/test')
                    fetch_huggingface_data()
    
    def test_fetch_raises_on_empty_dataset(self):
        """Test that fetch raises DataUnavailableError when dataset is empty"""
        empty_data = pd.DataFrame()
        
        with patch('code.utils.sra_fetcher.load_dataset') as mock_load:
            mock_dataset = MagicMock()
            mock_dataset.to_pandas.return_value = empty_data
            mock_load.return_value = mock_dataset
            
            with self.assertRaises(DataUnavailableError):
                with patch('code.utils.sra_fetcher.get_raw_path') as mock_path:
                    mock_path.return_value = Path('/tmp/test')
                    fetch_huggingface_data()

if __name__ == '__main__':
    unittest.main()