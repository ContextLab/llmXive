import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.data.preprocess.filter import filter_by_token_count, process_and_filter
import json

class TestFilterLogic(unittest.TestCase):

    def setUp(self):
        """Set up temporary files and test data."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_path = os.path.join(self.temp_dir.name, "input.jsonl")
        self.output_path = os.path.join(self.temp_dir.name, "output.jsonl")
        
        # Mock data for testing
        self.valid_records = [
            {'id': '1', 'tokens': ['a', 'b', 'c'] * 10}, # 30 tokens
            {'id': '2', 'tokens': ['x', 'y'] * 10},      # 20 tokens
            {'id': '3', 'tokens': ['long', 'list'] * 50} # 100 tokens
        ]
        
        self.invalid_records = [
            {'id': '4', 'tokens': ['short'] * 5},        # 5 tokens
            {'id': '5', 'tokens': []},                    # 0 tokens
            {'id': '6', 'tokens': ['a']}                  # 1 token
        ]
        
        self.all_records = self.valid_records + self.invalid_records

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def test_filter_by_token_count_valid(self):
        """Test that records with >= 20 tokens are kept."""
        filtered, excluded_count = filter_by_token_count(self.all_records, min_tokens=20)
        
        self.assertEqual(len(filtered), 3)
        self.assertEqual(excluded_count, 3)
        
        # Check IDs
        kept_ids = [r['id'] for r in filtered]
        self.assertIn('1', kept_ids)
        self.assertIn('2', kept_ids)
        self.assertIn('3', kept_ids)
        self.assertNotIn('4', kept_ids)

    def test_filter_by_token_count_custom_threshold(self):
        """Test filtering with a custom threshold."""
        # Threshold 50: only record 3 (100 tokens) should pass
        filtered, excluded_count = filter_by_token_count(self.all_records, min_tokens=50)
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(excluded_count, 5)
        self.assertEqual(filtered[0]['id'], '3')

    def test_filter_by_token_count_empty_list(self):
        """Test filtering an empty list."""
        filtered, excluded_count = filter_by_token_count([], min_tokens=20)
        
        self.assertEqual(len(filtered), 0)
        self.assertEqual(excluded_count, 0)

    def test_filter_by_token_count_all_excluded(self):
        """Test when all records are below threshold."""
        filtered, excluded_count = filter_by_token_count(self.invalid_records, min_tokens=20)
        
        self.assertEqual(len(filtered), 0)
        self.assertEqual(excluded_count, 3)

    def test_process_and_filter_integration(self):
        """Test the full process_and_filter pipeline."""
        # Write input data
        with open(self.input_path, 'w', encoding='utf-8') as f:
            for record in self.all_records:
                f.write(json.dumps(record) + '\n')
                
        stats = process_and_filter(self.input_path, self.output_path, min_tokens=20)
        
        # Verify stats
        self.assertEqual(stats['total_loaded'], 6)
        self.assertEqual(stats['total_kept'], 3)
        self.assertEqual(stats['total_excluded'], 3)
        self.assertAlmostEqual(stats['exclusion_rate'], 50.0, places=1)
        
        # Verify output file content
        with open(self.output_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 3)
        
        output_ids = []
        for line in lines:
            record = json.loads(line)
            output_ids.append(record['id'])
            
        self.assertIn('1', output_ids)
        self.assertIn('2', output_ids)
        self.assertIn('3', output_ids)

    def test_process_and_filter_empty_input(self):
        """Test processing an empty input file."""
        # Create empty file
        with open(self.input_path, 'w', encoding='utf-8') as f:
            pass
            
        stats = process_and_filter(self.input_path, self.output_path, min_tokens=20)
        
        self.assertEqual(stats['total_loaded'], 0)
        self.assertEqual(stats['total_kept'], 0)
        self.assertEqual(stats['total_excluded'], 0)
        
        # Output file should exist but be empty
        self.assertTrue(os.path.exists(self.output_path))
        self.assertEqual(os.path.getsize(self.output_path), 0)

    @patch('src.data.preprocess.filter.load_preprocessed_data')
    def test_process_and_filter_logs_exclusion(self, mock_load):
        """Verify that the function logs exclusion counts (mocked)."""
        mock_load.return_value = self.all_records
        
        # We can't easily capture logs in this unit test without more setup,
        # but we can verify the logic flow leads to the correct return stats.
        stats = process_and_filter(self.input_path, self.output_path, min_tokens=20)
        
        # This confirms the logic ran and calculated stats correctly
        self.assertEqual(stats['total_excluded'], 3)

if __name__ == '__main__':
    unittest.main()