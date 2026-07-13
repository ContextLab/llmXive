"""
Integration tests for problem_loader.py
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from experiment.problem_loader import (
    load_humaneval_problems,
    load_codeforces_problems,
    load_all_problems,
    verify_loading_rate,
    DATA_DIR
)


class TestProblemLoaderIntegration(unittest.TestCase):
    """Integration tests for problem loading functionality."""

    def setUp(self):
        """Set up integration test fixtures with real files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        
        # Create directory structure
        (self.data_dir / 'humaneval').mkdir()
        (self.data_dir / 'codeforces').mkdir()

    def tearDown(self):
        """Clean up integration test fixtures."""
        self.temp_dir.cleanup()

    def test_real_file_loading_humaneval(self):
        """Test loading from a real HumanEval file."""
        # Create a realistic HumanEval dataset
        humaneval_data = [
            {
                'task_id': 'HumanEval/0',
                'prompt': 'from typing import List\n\ndef has_close_elements(numbers: List[float], threshold: float) -> bool:\n    """ Check if in given list of numbers, any two numbers are closer to each other than the given threshold.\n    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)\n    False\n    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)\n    True\n    """\n',
                'canonical_solution': 'for idx, elem in enumerate(numbers):\n    for idx2, elem2 in enumerate(numbers):\n        if idx != idx2:\n            distance = abs(elem - elem2)\n            if distance < threshold:\n                return True\n\nreturn False\n',
                'test': "check(has_close_elements)"
            },
            {
                'task_id': 'HumanEval/1',
                'prompt': 'def separate_paren_groups(paren_string: str) -> List[str]:\n    """ Input to this function is a string containing multiple groups of nested parentheses. Your goal is to separate those group into separate strings and return the list of those.\n    Separate groups are balanced (each open brace is properly closed) and not nested within each other\n    Ignore any spaces in the input string.\n    >>> separate_paren_groups(\'(()()) ((())) () ((())()())\')\n    [\'(()())\', \'((()))\', \'()\', \'((())()())\']\n    """\n',
                'canonical_solution': 'result = []\n    current_string = []\n    current_depth = 0\n\n    for c in paren_string:\n        if c == \'(\':\n            current_depth += 1\n            current_string.append(c)\n        elif c == \')\':\n            current_depth -= 1\n            current_string.append(c)\n\n        if current_depth == 0:\n            result.append(\'\'.join(current_string))\n            current_string = []\n\n    return result\n',
                'test': "check(separate_paren_groups)"
            }
        ]
        
        file_path = self.data_dir / 'humaneval' / 'human_eval.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(humaneval_data, f, indent=2)
        
        # Test loading
        with patch('experiment.problem_loader.HUMANEVAL_DIR', self.data_dir / 'humaneval'):
            problems, count = load_humaneval_problems()
            
            self.assertEqual(count, 2)
            self.assertEqual(len(problems), 2)
            self.assertEqual(problems[0]['task_id'], 'HumanEval/0')
            self.assertEqual(problems[1]['task_id'], 'HumanEval/1')
            self.assertIn('prompt', problems[0])
            self.assertIn('canonical_solution', problems[0])

    def test_real_file_loading_codeforces(self):
        """Test loading from a real Codeforces file."""
        # Create a realistic Codeforces dataset
        codeforces_data = [
            {
                'problem_id': 'CF-1512-A',
                'title': 'Spy Detected!',
                'contest_id': 1512,
                'problem_index': 'A',
                'difficulty': 800,
                'tags': ['brute force', 'implementation'],
                'statement': 'You are given an array a of n integers. Find an element that is different from all other elements.',
                'input': 'The first line contains a single integer t (1≤t≤100) — the number of test cases.\nDescription of the test cases follows.\nThe first line of each test case contains a single integer n (3≤n≤100). It is guaranteed that n is odd.\nThe second line of each test case contains n integers a1,a2,…,an (1≤ai≤100). It is guaranteed that there exists an element that is different from all other elements.',
                'output': 'For each test case print a single integer — the element that is different from all other elements.',
                'examples': [
                    {'input': '5\n3 1 1 2', 'output': '2'},
                    {'input': '7 1 1 1 1 1 1 100', 'output': '100'}
                ]
            },
            {
                'problem_id': 'CF-1512-B',
                'title': 'Almost Rectangle',
                'contest_id': 1512,
                'problem_index': 'B',
                'difficulty': 800,
                'tags': ['geometry', 'implementation'],
                'statement': 'There is a square on the infinite plane. You are given the coordinates of two opposite vertices of this square. Find the coordinates of the other two vertices.',
                'input': 'The first line contains a single integer t (1≤t≤1000) — the number of test cases.\nDescription of the test cases follows.\nThe only line of each test case contains four integers x1,y1,x2,y2 (−100≤x1,y1,x2,y2≤100) — coordinates of the given vertices.',
                'output': 'Print four integers x3,y3,x4,y4 (−100≤x3,y3,x4,y4≤100) — coordinates of the other two vertices.',
                'examples': [
                    {'input': '0 0 1 1', 'output': '0 1 1 0'},
                    {'input': '0 0 0 2', 'output': '0 0 0 2'}
                ]
            }
        ]
        
        file_path = self.data_dir / 'codeforces' / 'codeforces_problems.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(codeforces_data, f, indent=2)
        
        # Test loading
        with patch('experiment.problem_loader.CODEFORCES_DIR', self.data_dir / 'codeforces'):
            problems, count = load_codeforces_problems()
            
            self.assertEqual(count, 2)
            self.assertEqual(len(problems), 2)
            self.assertEqual(problems[0]['problem_id'], 'CF-1512-A')
            self.assertEqual(problems[1]['problem_id'], 'CF-1512-B')
            self.assertIn('title', problems[0])
            self.assertIn('difficulty', problems[0])

    def test_loading_rate_verification_integration(self):
        """Test the loading rate verification with real data."""
        # Create realistic datasets
        humaneval_data = [
            {'task_id': f'HumanEval/{i}', 'prompt': f'code for problem {i}'}
            for i in range(50)
        ]
        
        codeforces_data = [
            {'problem_id': f'CF-{i}', 'title': f'Problem {i}'}
            for i in range(50)
        ]
        
        # Write to files
        he_file = self.data_dir / 'humaneval' / 'human_eval.json'
        cf_file = self.data_dir / 'codeforces' / 'codeforces_problems.json'
        
        with open(he_file, 'w') as f:
            json.dump(humaneval_data, f)
        
        with open(cf_file, 'w') as f:
            json.dump(codeforces_data, f)
        
        # Test verification
        with patch('experiment.problem_loader.HUMANEVAL_DIR', self.data_dir / 'humaneval'), \
             patch('experiment.problem_loader.CODEFORCES_DIR', self.data_dir / 'codeforces'):
            
            result = verify_loading_rate(sample_size=20)
            
            self.assertIn('success', result)
            self.assertIn('load_rate', result)
            self.assertGreaterEqual(result['load_rate'], 0.0)
            self.assertLessEqual(result['load_rate'], 1.0)
            self.assertEqual(result['sample_size'], 20)
            self.assertEqual(result['successful_loads'], 20)
            self.assertEqual(result['failed_loads'], 0)

    def test_malformed_data_handling(self):
        """Test handling of malformed problem data."""
        # Create malformed HumanEval data
        malformed_data = [
            {'task_id': 'valid1', 'prompt': 'valid code'},
            {'incomplete': 'missing required fields'},  # Malformed
            {'task_id': 'valid2', 'prompt': 'valid code 2'},
            {},  # Empty dict
            {'task_id': 'valid3', 'prompt': 'valid code 3'}
        ]
        
        file_path = self.data_dir / 'humaneval' / 'human_eval.json'
        with open(file_path, 'w') as f:
            json.dump(malformed_data, f)
        
        # Test loading with malformed data
        with patch('experiment.problem_loader.HUMANEVAL_DIR', self.data_dir / 'humaneval'):
            problems, count = load_humaneval_problems()
            
            # Should load only valid problems
            self.assertEqual(count, 5)  # Total attempted
            # Valid problems should be filtered
            valid_tasks = [p['task_id'] for p in problems if 'task_id' in p]
            self.assertIn('valid1', valid_tasks)
            self.assertIn('valid2', valid_tasks)
            self.assertIn('valid3', valid_tasks)


if __name__ == '__main__':
    unittest.main()