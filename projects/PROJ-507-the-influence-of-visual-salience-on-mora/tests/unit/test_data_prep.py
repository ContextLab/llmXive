import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data_prep import filter_candidates, DataFetchError, ingest_dataset

class TestDataPrep(unittest.TestCase):

    def test_filter_candidates_social_tag(self):
        """Test that rows with 'social' tag are kept."""
        data = [
            {'image_id': 1, 'tags': 'social, nature'},
            {'image_id': 2, 'tags': 'nature, landscape'},
            {'image_id': 3, 'tags': 'conflict, war'},
            {'image_id': 4, 'tags': 'peace, calm'},
        ]
        df = pd.DataFrame(data)
        result = filter_candidates(df)
        
        self.assertIn(1, result['image_id'].values)
        self.assertIn(3, result['image_id'].values)
        self.assertNotIn(2, result['image_id'].values)
        self.assertNotIn(4, result['image_id'].values)
        self.assertEqual(len(result), 2)

    def test_filter_candidates_conflict_tag(self):
        """Test that rows with 'conflict' tag are kept."""
        data = [
            {'image_id': 10, 'labels': 'conflict'},
            {'image_id': 11, 'labels': 'harmony'},
        ]
        df = pd.DataFrame(data)
        result = filter_candidates(df)
        
        self.assertIn(10, result['image_id'].values)
        self.assertNotIn(11, result['image_id'].values)

    def test_filter_candidates_empty(self):
        """Test that empty input returns empty output."""
        df = pd.DataFrame(columns=['image_id', 'tags'])
        result = filter_candidates(df)
        self.assertTrue(result.empty)

    @patch('data_prep.load_dataset')
    def test_ingest_dataset_failure(self, mock_load):
        """Test that DataFetchError is raised when ingestion fails."""
        mock_load.side_effect = Exception("Network error")
        with self.assertRaises(DataFetchError):
            ingest_dataset()

    @patch('data_prep.load_dataset')
    def test_ingest_dataset_success(self, mock_load):
        """Test successful ingestion of a sample."""
        mock_data = [
            {'id': 1, 'tags': 'social'},
            {'id': 2, 'tags': 'nature'}
        ]
        # Mock streaming iterator
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter(mock_data))
        mock_load.return_value = mock_ds
        
        df = ingest_dataset()
        self.assertEqual(len(df), 2)
        self.assertIn('id', df.columns)

if __name__ == '__main__':
    unittest.main()
