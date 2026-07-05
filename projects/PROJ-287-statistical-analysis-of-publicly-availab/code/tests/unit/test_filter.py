import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from src.data.preprocess.filter import filter_by_token_count, process_and_filter
from src.data.preprocess.tokenizer import TokenizationResult


class TestFilterLogic(unittest.TestCase):
    """Unit tests for the filtering logic in src/data/preprocess/filter.py"""

    def setUp(self):
        """Set up test fixtures"""
        self.min_tokens = 20

    def test_filter_empty_list(self):
        """Test filtering an empty list returns empty list and 0 excluded"""
        results, excluded = filter_by_token_count([], self.min_tokens)
        self.assertEqual(results, [])
        self.assertEqual(excluded, 0)

    def test_filter_all_pass(self):
        """Test that all records with >= min_tokens are kept"""
        # Create results with exactly 20 and more tokens
        results_data = [
            TokenizationResult(id="1", tokens=["w"] * 20, text="test", source="arxiv"),
            TokenizationResult(id="2", tokens=["w"] * 25, text="test", source="arxiv"),
            TokenizationResult(id="3", tokens=["w"] * 50, text="test", source="pubmed"),
        ]
        
        filtered, excluded = filter_by_token_count(results_data, self.min_tokens)
        
        self.assertEqual(len(filtered), 3)
        self.assertEqual(excluded, 0)

    def test_filter_all_fail(self):
        """Test that all records with < min_tokens are excluded"""
        results_data = [
            TokenizationResult(id="1", tokens=["w"] * 5, text="test", source="arxiv"),
            TokenizationResult(id="2", tokens=["w"] * 19, text="test", source="arxiv"),
        ]
        
        filtered, excluded = filter_by_token_count(results_data, self.min_tokens)
        
        self.assertEqual(len(filtered), 0)
        self.assertEqual(excluded, 2)

    def test_filter_mixed(self):
        """Test filtering with a mix of passing and failing records"""
        results_data = [
            TokenizationResult(id="1", tokens=["w"] * 10, text="test", source="arxiv"),   # Fail
            TokenizationResult(id="2", tokens=["w"] * 20, text="test", source="arxiv"),   # Pass (exact)
            TokenizationResult(id="3", tokens=["w"] * 15, text="test", source="pubmed"),  # Fail
            TokenizationResult(id="4", tokens=["w"] * 30, text="test", source="pubmed"),  # Pass
        ]
        
        filtered, excluded = filter_by_token_count(results_data, self.min_tokens)
        
        self.assertEqual(len(filtered), 2)
        self.assertEqual(excluded, 2)
        
        # Verify IDs are correct
        kept_ids = [r.id for r in filtered]
        self.assertIn("2", kept_ids)
        self.assertIn("4", kept_ids)
        self.assertNotIn("1", kept_ids)
        self.assertNotIn("3", kept_ids)

    @patch('src.data.preprocess.filter.save_tokenized_results')
    @patch('src.data.preprocess.filter.load_preprocessed_data')
    def test_process_and_filter_integration(self, mock_load, mock_save):
        """Test the full process_and_filter pipeline function"""
        
        # Mock input data
        mock_results = [
            TokenizationResult(id="1", tokens=["w"] * 25, text="test", source="arxiv"),
            TokenizationResult(id="2", tokens=["w"] * 5, text="test", source="arxiv"),
        ]
        mock_load.return_value = mock_results
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.jsonl"
            output_path = Path(tmpdir) / "output.jsonl"
            
            # Create a dummy input file so exists() check passes
            input_path.touch()
            
            stats = process_and_filter(str(input_path), str(output_path), min_tokens=20)
            
            # Verify load was called
            mock_load.assert_called_once_with(input_path)
            
            # Verify save was called
            mock_save.assert_called_once()
            
            # Verify stats
            self.assertEqual(stats["total_input"], 2)
            self.assertEqual(stats["kept"], 1)
            self.assertEqual(stats["excluded"], 1)
            self.assertEqual(stats["min_tokens"], 20)
            self.assertTrue(str(stats["output_path"]).endswith("output.jsonl"))


if __name__ == "__main__":
    unittest.main()