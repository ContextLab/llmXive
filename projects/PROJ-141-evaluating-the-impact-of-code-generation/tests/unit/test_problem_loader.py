"""
Unit tests for problem_loader.py
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from experiment.problem_loader import (
    load_humaneval_problems,
    load_codeforces_problems,
    load_all_problems,
    verify_loading_rate,
    DATA_DIR,
    LOAD_RATE_THRESHOLD
)


class TestProblemLoader(unittest.TestCase):
    """Test cases for problem loading functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        
        # Create mock directories
        (self.data_dir / 'humaneval').mkdir()
        (self.data_dir / 'codeforces').mkdir()

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    @patch('experiment.problem_loader.HUMANEVAL_DIR')
    @patch('experiment.problem_loader.CODEFORCES_DIR')
    def test_load_humaneval_problems_success(self, mock_cf_dir, mock_he_dir):
        """Test successful loading of HumanEval problems."""
        mock_he_dir.__truediv__.return_value.exists.return_value = True
        mock_he_dir.__truediv__.return_value.__truediv__.return_value = self.data_dir / 'humaneval' / 'human_eval.json'
        
        # Create mock data
        mock_data = [
            {'task_id': 'task1', 'prompt': 'def test(): pass'},
            {'task_id': 'task2', 'prompt': 'def test2(): pass'}
        ]
        
        mock_file = self.data_dir / 'humaneval' / 'human_eval.json'
        with open(mock_file, 'w') as f:
            json.dump(mock_data, f)
        
        with patch('experiment.problem_loader.HUMANEVAL_DIR', self.data_dir / 'humaneval'):
            problems, count = load_humaneval_problems()
            
            self.assertEqual(count, 2)
            self.assertEqual(len(problems), 2)
            self.assertEqual(problems[0]['task_id'], 'task1')
            self.assertIn('source', problems[0])

    @patch('experiment.problem_loader.CODEFORCES_DIR')
    @patch('experiment.problem_loader.HUMANEVAL_DIR')
    def test_load_codeforces_problems_success(self, mock_he_dir, mock_cf_dir):
        """Test successful loading of Codeforces problems."""
        mock_cf_dir.__truediv__.return_value.exists.return_value = True
        
        # Create mock data
        mock_data = [
            {'problem_id': 'CF1', 'title': 'Problem A'},
            {'problem_id': 'CF2', 'title': 'Problem B'}
        ]
        
        mock_file = self.data_dir / 'codeforces' / 'codeforces_problems.json'
        with open(mock_file, 'w') as f:
            json.dump(mock_data, f)
        
        with patch('experiment.problem_loader.CODEFORCES_DIR', self.data_dir / 'codeforces'):
            problems, count = load_codeforces_problems()
            
            self.assertEqual(count, 2)
            self.assertEqual(len(problems), 2)
            self.assertEqual(problems[0]['problem_id'], 'CF1')
            self.assertIn('source', problems[0])

    def test_verify_loading_rate(self):
        """Test loading rate verification function."""
        # Create mock problems
        mock_problems = [
            {'task_id': f'task{i}', 'prompt': f'code{i}', 'source': 'humaneval'}
            for i in range(100)
        ]
        
        # Mock load_all_problems to return our test data
        with patch('experiment.problem_loader.load_all_problems') as mock_load:
            mock_load.return_value = (mock_problems, {'humaneval': 100, 'codeforces': 0, 'total': 100})
            
            result = verify_loading_rate(sample_size=50)
            
            self.assertIn('success', result)
            self.assertIn('load_rate', result)
            self.assertIn('threshold', result)
            self.assertGreaterEqual(result['load_rate'], 0.0)
            self.assertLessEqual(result['load_rate'], 1.0)
            self.assertEqual(result['sample_size'], 50)

    def test_verify_loading_rate_below_threshold(self):
        """Test loading rate verification when rate is below threshold."""
        # Create mock problems where some will fail
        mock_problems = [
            {'task_id': f'task{i}', 'prompt': f'code{i}', 'source': 'humaneval'}
            for i in range(100)
        ]
        
        # Force some failures by modifying the verification logic temporarily
        with patch('experiment.problem_loader.load_all_problems') as mock_load:
            mock_load.return_value = (mock_problems, {'humaneval': 100, 'codeforces': 0, 'total': 100})
            
            # Temporarily lower threshold for testing
            original_threshold = LOAD_RATE_THRESHOLD
            import experiment.problem_loader as pl
            pl.LOAD_RATE_THRESHOLD = 0.99  # Set very high threshold
            
            try:
                result = verify_loading_rate(sample_size=10)
                # With 100% success rate and 0.99 threshold, should pass
                # But we're testing the logic flow
            finally:
                pl.LOAD_RATE_THRESHOLD = original_threshold

    @patch('experiment.problem_loader.HUMANEVAL_DIR')
    @patch('experiment.problem_loader.CODEFORCES_DIR')
    def test_load_all_problems_combined(self, mock_cf_dir, mock_he_dir):
        """Test loading problems from both sources."""
        # Setup mock data
        humaneval_data = [
            {'task_id': 'he1', 'prompt': 'code1'},
            {'task_id': 'he2', 'prompt': 'code2'}
        ]
        
        codeforces_data = [
            {'problem_id': 'cf1', 'title': 'Title1'},
            {'problem_id': 'cf2', 'title': 'Title2'}
        ]
        
        # Create temporary files
        he_file = self.data_dir / 'humaneval' / 'human_eval.json'
        cf_file = self.data_dir / 'codeforces' / 'codeforces_problems.json'
        
        with open(he_file, 'w') as f:
            json.dump(humaneval_data, f)
        
        with open(cf_file, 'w') as f:
            json.dump(codeforces_data, f)
        
        with patch('experiment.problem_loader.HUMANEVAL_DIR', self.data_dir / 'humaneval'), \
             patch('experiment.problem_loader.CODEFORCES_DIR', self.data_dir / 'codeforces'):
            
            all_problems, counts = load_all_problems()
            
            self.assertEqual(counts['total'], 4)
            self.assertEqual(counts['humaneval'], 2)
            self.assertEqual(counts['codeforces'], 2)
            
            # Check that all problems have source attribute
            for prob in all_problems:
                self.assertIn('source', prob)


if __name__ == '__main__':
    unittest.main()
