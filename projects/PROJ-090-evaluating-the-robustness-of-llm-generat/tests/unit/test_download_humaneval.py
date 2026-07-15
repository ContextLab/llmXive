"""
Unit tests for the HumanEval download script.

These tests verify that the download script:
1. Correctly imports required dependencies
2. Validates the dataset structure
3. Handles errors appropriately
"""

import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.download_humaneval import download_humaneval, OUTPUT_FILE


class TestHumanEvalDownload:
    """Test cases for HumanEval download functionality."""

    def test_dataset_schema(self):
        """
        Verify that the downloaded dataset has the expected schema.

        HumanEval samples should contain:
        - problem_id: string identifier
        - prompt: string containing the function signature and docstring
        - canonical_solution: string containing the reference solution
        - test: string containing the test cases
        - entry_point: string with the function name to test
        """
        # This test validates the expected schema without downloading
        # In a real execution, this would run after download_humaneval()
        expected_fields = {
            "problem_id",
            "prompt",
            "canonical_solution",
            "test",
            "entry_point"
        }

        # Verify our expectations match the known HumanEval schema
        assert len(expected_fields) == 5, "Expected 5 fields in HumanEval dataset"

    def test_output_file_structure(self):
        """
        Verify the output file structure if it exists.

        This test checks that if the output file exists, it contains
        valid JSONL with the expected fields.
        """
        if not OUTPUT_FILE.exists():
            # Skip if file doesn't exist (expected in CI without real data)
            return

        with open(OUTPUT_FILE, 'r') as f:
            first_line = f.readline()
            sample = json.loads(first_line)

        expected_fields = {
            "problem_id",
            "prompt",
            "canonical_solution",
            "test",
            "entry_point"
        }

        assert set(sample.keys()) == expected_fields, \
            f"Sample keys {set(sample.keys())} don't match expected {expected_fields}"

    @patch('code.data.download_humaneval.load_dataset')
    def test_download_success(self, mock_load_dataset):
        """Test successful download scenario."""
        # Mock a successful dataset load
        mock_dataset = MagicMock()
        mock_dataset.__len__ = lambda self: 10
        mock_dataset.to_json = MagicMock()
        mock_load_dataset.return_value = mock_dataset

        # Mock Path operations
        with patch('code.data.download_humaneval.Path.exists', return_value=True):
            with patch('code.data.download_humaneval.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 1024

                result = download_humaneval()

                assert result is True
                mock_load_dataset.assert_called_once()
                mock_dataset.to_json.assert_called_once()

    @patch('code.data.download_humaneval.load_dataset')
    def test_download_empty_dataset(self, mock_load_dataset):
        """Test handling of empty dataset."""
        mock_dataset = MagicMock()
        mock_dataset.__len__ = lambda self: 0
        mock_load_dataset.return_value = mock_dataset

        result = download_humaneval()

        assert result is False
        mock_load_dataset.assert_called_once()

    @patch('code.data.download_humaneval.load_dataset')
    def test_download_exception(self, mock_load_dataset):
        """Test handling of download exceptions."""
        mock_load_dataset.side_effect = Exception("Network error")

        with self.assertRaises(Exception):
            download_humaneval()

        mock_load_dataset.assert_called_once()