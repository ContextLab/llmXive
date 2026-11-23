"""
Unit tests for the filter module.
"""
import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data.preprocess.filter import filter_by_token_count, process_and_filter
from src.data.preprocess.tokenizer import TokenizationResult


class TestFilterLogic(unittest.TestCase):
    """Test cases for filter_by_token_count and process_and_filter functions."""

    def test_filter_by_token_count_keeps_valid_records(self):
        """Test that records with >= 20 tokens are kept."""
        # Create test data with varying token counts
        test_results = [
            TokenizationResult(
                id="1",
                source="arxiv",
                original_text="Short text",
                tokens=["word" * 25],
                token_count=25,
                window="2000-2004",
                year=2002
            ),
            TokenizationResult(
                id="2",
                source="pubmed",
                original_text="Another text",
                tokens=["word" * 30],
                token_count=30,
                window="2005-2009",
                year=2007
            ),
        ]

        filtered, excluded_count = filter_by_token_count(test_results)

        self.assertEqual(len(filtered), 2)
        self.assertEqual(excluded_count, 0)
        self.assertEqual(filtered[0].id, "1")
        self.assertEqual(filtered[1].id, "2")

    def test_filter_by_token_count_excludes_short_records(self):
        """Test that records with < 20 tokens are excluded."""
        # Create test data with some short records
        test_results = [
            TokenizationResult(
                id="1",
                source="arxiv",
                original_text="Short",
                tokens=["word" * 10],
                token_count=10,
                window="2000-2004",
                year=2002
            ),
            TokenizationResult(
                id="2",
                source="pubmed",
                original_text="Another",
                tokens=["word" * 15],
                token_count=15,
                window="2005-2009",
                year=2007
            ),
        ]

        filtered, excluded_count = filter_by_token_count(test_results)

        self.assertEqual(len(filtered), 0)
        self.assertEqual(excluded_count, 2)

    def test_filter_by_token_count_mixed_results(self):
        """Test filtering with a mix of valid and invalid records."""
        # Create test data with mixed token counts
        test_results = [
            TokenizationResult(
                id="1",
                source="arxiv",
                original_text="Short",
                tokens=["word" * 10],
                token_count=10,
                window="2000-2004",
                year=2002
            ),
            TokenizationResult(
                id="2",
                source="pubmed",
                original_text="Valid text",
                tokens=["word" * 20],
                token_count=20,
                window="2005-2009",
                year=2007
            ),
            TokenizationResult(
                id="3",
                source="arxiv",
                original_text="Another valid",
                tokens=["word" * 25],
                token_count=25,
                window="2010-2014",
                year=2012
            ),
            TokenizationResult(
                id="4",
                source="pubmed",
                original_text="Too short",
                tokens=["word" * 5],
                token_count=5,
                window="2015-2019",
                year=2017
            ),
        ]

        filtered, excluded_count = filter_by_token_count(test_results)

        self.assertEqual(len(filtered), 2)
        self.assertEqual(excluded_count, 2)
        
        # Check that valid records are kept
        kept_ids = [r.id for r in filtered]
        self.assertIn("2", kept_ids)
        self.assertIn("3", kept_ids)
        
        # Check that excluded records are not in the result
        self.assertNotIn("1", kept_ids)
        self.assertNotIn("4", kept_ids)

    def test_filter_by_token_count_boundary_case(self):
        """Test the exact boundary case (20 tokens)."""
        # Create test data with exactly 20 tokens
        test_results = [
            TokenizationResult(
                id="1",
                source="arxiv",
                original_text="Boundary case",
                tokens=["word" * 20],
                token_count=20,
                window="2000-2004",
                year=2002
            ),
        ]

        filtered, excluded_count = filter_by_token_count(test_results)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(excluded_count, 0)
        self.assertEqual(filtered[0].token_count, 20)

    def test_filter_by_token_count_empty_input(self):
        """Test filtering with empty input."""
        filtered, excluded_count = filter_by_token_count([])

        self.assertEqual(len(filtered), 0)
        self.assertEqual(excluded_count, 0)

    @patch('src.data.preprocess.filter.load_preprocessed_data')
    @patch('src.data.preprocess.filter.get_logger')
    def test_process_and_filter(self, mock_logger, mock_load_data):
        """Test the full process_and_filter function."""
        # Setup mock data
        mock_results = [
            TokenizationResult(
                id="1",
                source="arxiv",
                original_text="Valid text",
                tokens=["word" * 25],
                token_count=25,
                window="2000-2004",
                year=2002
            ),
            TokenizationResult(
                id="2",
                source="pubmed",
                original_text="Short text",
                tokens=["word" * 10],
                token_count=10,
                window="2005-2009",
                year=2007
            ),
        ]
        mock_load_data.return_value = mock_results

        # Create temporary files for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.jsonl"
            output_path = Path(temp_dir) / "output.jsonl"

            # Create dummy input file (not actually used due to mock)
            input_path.touch()

            # Run the function
            stats = process_and_filter(str(input_path), str(output_path))

            # Verify results
            self.assertEqual(stats["total_loaded"], 2)
            self.assertEqual(stats["total_kept"], 1)
            self.assertEqual(stats["total_excluded"], 1)
            self.assertAlmostEqual(stats["exclusion_rate"], 50.0, places=2)

            # Verify output file was created
            self.assertTrue(output_path.exists())

    @patch('src.data.preprocess.filter.load_preprocessed_data')
    @patch('src.data.preprocess.filter.get_logger')
    def test_process_and_filter_empty_data(self, mock_logger, mock_load_data):
        """Test process_and_filter with empty data."""
        mock_load_data.return_value = []

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.jsonl"
            output_path = Path(temp_dir) / "output.jsonl"
            input_path.touch()

            stats = process_and_filter(str(input_path), str(output_path))

            self.assertEqual(stats["total_loaded"], 0)
            self.assertEqual(stats["total_kept"], 0)
            self.assertEqual(stats["total_excluded"], 0)
            self.assertEqual(stats["exclusion_rate"], 0.0)

    @patch('src.data.preprocess.filter.get_logger')
    def test_process_and_filter_missing_input(self, mock_logger):
        """Test process_and_filter with missing input file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "nonexistent.jsonl"
            output_path = Path(temp_dir) / "output.jsonl"

            # Run the function (should log error and return early)
            # Note: This test verifies the logging behavior, not the actual return value
            # since the function returns early when input is missing
            stats = process_and_filter(str(input_path), str(output_path))

            # Verify error was logged
            mock_logger.return_value.error.assert_called()


if __name__ == "__main__":
    unittest.main()