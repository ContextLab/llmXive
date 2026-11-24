import unittest
import pandas as pd
from code.data_fetcher import fetch_educational_dataset, _validate_schema
from ingestion import DataAvailabilityError, DataSchemaError
from unittest.mock import patch, MagicMock

class TestDataFetcher(unittest.TestCase):

    @patch('code.data_fetcher.load_dataset')
    def test_fetch_successful(self, mock_load_dataset):
        # Mock the dataset loading from Hugging Face
        mock_dataset = MagicMock()
        mock_df = pd.DataFrame({
            'recommended_categories': [['A'], ['B']], 
            'enrolled_categories': [['C'], ['D']]
        })
        mock_dataset.to_pandas.return_value = mock_df
        mock_load_dataset.return_value = mock_dataset

        df = fetch_educational_dataset("dummy_dataset")
        self.assertEqual(df.shape, (2, 2))

    def test_schema_error(self):
        """Verify that _validate_schema raises the exact error message required."""
        # Create a dataframe missing one of the required columns
        df_malformed = pd.DataFrame({
            'user_id': [1, 2],
            'recommended_categories': [['A'], ['B']]
            # missing enrolled_categories
        })
        
        with self.assertRaises(DataSchemaError) as cm:
            _validate_schema(df_malformed)
        
        self.assertEqual(
            str(cm.exception), 
            "Required columns [recommended_categories, enrolled_categories] missing. Dataset does not support the specified experimental design."
        )

    @patch('code.data_fetcher.load_dataset')
    def test_fetch_missing_columns(self, mock_load_dataset):
        mock_dataset = MagicMock()
        mock_df = pd.DataFrame({'other_column': ['A', 'B']})
        mock_dataset.to_pandas.return_value = mock_df
        mock_load_dataset.return_value = mock_dataset

        with self.assertRaises(ValueError):
            fetch_educational_dataset("dummy_dataset")

    @patch('code.data_fetcher.load_dataset')
    def test_fetch_unavailable_dataset(self, mock_load_dataset):
        # Simulate HF failure
        mock_load_dataset.side_effect = Exception("Not found")
        with self.assertRaises(DataAvailabilityError):
            fetch_educational_dataset("non_existent_dataset")

if __name__ == '__main__':
    unittest.main()