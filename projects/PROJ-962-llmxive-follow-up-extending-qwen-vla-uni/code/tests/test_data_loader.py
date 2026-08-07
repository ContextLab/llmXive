"""
Unit tests for the hardened data loader.

This module verifies that the data loader strictly adheres to the "Fail Loudly"
principle and does not contain any synthetic data fallback mechanisms.
"""
import unittest
import sys
import os
from unittest.mock import patch, MagicMock, call
from datasets import Dataset
from utils.data_loader import load_qwen_vla_dataset, DataFetchError, validate_dataset_structure

class TestDataLoaderHardening(unittest.TestCase):
    """
    Tests to ensure the data loader raises DataFetchError on failure
    and does not silently generate synthetic data.
    """

    def test_load_qwen_vla_dataset_success(self):
        """Test that the loader successfully returns a dataset when the source is available."""
        mock_dataset = MagicMock(spec=Dataset)
        mock_dataset.features = {"text": "string", "action": "float[]"}
        
        with patch('utils.data_loader.load_dataset', return_value=mock_dataset) as mock_load:
            result = load_qwen_vla_dataset("Qwen-VLA/Hy-Embodied", streaming=True)
            
            # Verify the real load_dataset was called with correct arguments
            mock_load.assert_called_once_with(
                "Qwen-VLA/Hy-Embodied",
                split=None,
                streaming=True
            )
            
            # Verify we got the mock back
            self.assertEqual(result, mock_dataset)

    def test_load_qwen_vla_dataset_connection_error_raises_data_fetch_error(self):
        """
        Verify that if datasets.load_dataset raises a ConnectionError (or any exception),
        the script raises a DataFetchError and NOT a generic Exception or returning synthetic data.
        """
        # Mock load_dataset to raise a ConnectionError simulating network failure
        with patch('utils.data_loader.load_dataset', side_effect=ConnectionError("Network unreachable")):
            with self.assertRaises(DataFetchError) as context:
                load_qwen_vla_dataset("Qwen-VLA/Hy-Embodied", streaming=True)
            
            # Verify the error message contains the specific details
            self.assertIn("Failed to fetch dataset from HuggingFace", str(context.exception))
            self.assertIn("Qwen-VLA/Hy-Embodied", str(context.exception))
            self.assertIn("https://huggingface.co/datasets/Qwen-VLA/Hy-Embodied", str(context.exception))
            
            # Ensure the exception chain preserves the original cause
            self.assertIsInstance(context.exception.__cause__, ConnectionError)

    def test_load_qwen_vla_dataset_no_synthetic_fallback(self):
        """
        Verify that the loader does NOT attempt to generate synthetic data when the real fetch fails.
        This test ensures there are no 'try/except' blocks that return mock data on failure.
        """
        # We verify the behavior by checking that the exception propagates.
        # If there were a fallback to synthetic data, the function would return a Dataset
        # instead of raising DataFetchError.
        with patch('utils.data_loader.load_dataset', side_effect=ConnectionError("Simulated failure")):
            with self.assertRaises(DataFetchError):
                # This call MUST raise DataFetchError. If it returns a dataset (synthetic),
                # the test will fail because we expect an exception.
                load_qwen_vla_dataset("Qwen-VLA/Hy-Embodied", streaming=True)
            
            # Additional check: ensure no synthetic generation function was called.
            # Since we are not mocking a 'generate_synthetic' function (which shouldn't exist),
            # the mere fact that DataFetchError is raised confirms no fallback occurred.

    def test_validate_dataset_structure_missing_columns_raises_error(self):
        """Test that validate_dataset_structure raises DataFetchError if columns are missing."""
        mock_dataset = MagicMock(spec=Dataset)
        mock_dataset.features = {"text": "string"} # Missing required 'action' column
        
        with self.assertRaises(DataFetchError) as context:
            validate_dataset_structure(mock_dataset, ["text", "action"])
        
        self.assertIn("missing required columns", str(context.exception))
        self.assertIn("action", str(context.exception))

    def test_load_qwen_vla_dataset_invalid_dataset_id(self):
        """Test that invalid dataset_id raises DataFetchError immediately."""
        with self.assertRaises(DataFetchError) as context:
            load_qwen_vla_dataset("")
        
        self.assertIn("Invalid dataset_id", str(context.exception))

    def test_load_qwen_vla_dataset_none_return_raises_error(self):
        """Test that if load_dataset returns None, DataFetchError is raised."""
        with patch('utils.data_loader.load_dataset', return_value=None):
            with self.assertRaises(DataFetchError) as context:
                load_qwen_vla_dataset("Qwen-VLA/Hy-Embodied")
            
            self.assertIn("Dataset loaded but returned None", str(context.exception))

if __name__ == '__main__':
    unittest.main()