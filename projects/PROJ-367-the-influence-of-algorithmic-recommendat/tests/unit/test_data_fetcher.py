import unittest
import pandas as pd
import os
from code.data_fetcher import fetch_educational_dataset, DataAvailabilityError
from unittest.mock import patch
from datasets import load_dataset

class TestDataFetcher(unittest.TestCase):

    @patch('code.data_fetcher.load_dataset')
    def test_fetch_successful(self, mock_load_dataset):
        # Mock the dataset loading
        mock_dataset = load_dataset("dummy_dataset", split="train")
        mock_load_dataset.return_value = mock_dataset
        mock_df = pd.DataFrame({'recommended_categories': ['A', 'B'], 'enrolled_categories': ['C', 'D']})
        mock_dataset.to_pandas.return_value = mock_df

        # Call the function and assert it returns the DataFrame
        df = fetch_educational_dataset("dummy_dataset")
        self.assertEqual(df.shape, (2, 2))

    @patch('code.data_fetcher.load_dataset')
    def test_fetch_missing_columns(self, mock_load_dataset):
        # Mock the dataset loading to return a DataFrame without the required columns
        mock_dataset = load_dataset("dummy_dataset", split="train")
        mock_load_dataset.return_value = mock_dataset
        mock_df = pd.DataFrame({'other_column': ['A', 'B']})
        mock_dataset.to_pandas.return_value = mock_df

        # Assert that a ValueError is raised
        with self.assertRaises(ValueError):
            fetch_educational_dataset("dummy_dataset")

    def test_fetch_unavailable_dataset(self):
        # Assert that a DataAvailabilityError is raised when the dataset is unavailable
        with self.assertRaises(DataAvailabilityError):
            fetch_educational_dataset("non_existent_dataset")

if __name__ == '__main__':
    unittest.main()