"""
tests/test_evaluation.py

Tests for code/evaluation.py
"""

import os
import json
import tempfile
import csv
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.evaluation import (
    load_raw_results, 
    load_problems, 
    evaluate_solution, 
    write_results_to_csv,
    DATA_RAW_DIR, 
    DATA_PROCESSED_DIR
)

class TestEvaluation(unittest.TestCase):

    def setUp(self):
        # Create temporary directories for test data
        self.test_raw_dir = tempfile.mkdtemp()
        self.test_processed_dir = tempfile.mkdtemp()
        
        # Mock the global paths
        self.original_raw_dir = DATA_RAW_DIR
        self.original_processed_dir = DATA_PROCESSED_DIR
        
        # We cannot easily mock module-level constants in the imported module
        # So we will create test files in temp dirs and pass them to functions
        # or patch the module's attributes.
        # For simplicity, we will test the functions that don't rely on global paths
        # by passing explicit paths or mocking the file operations.

    def tearDown(self):
        # Cleanup
        import shutil
        if os.path.exists(self.test_raw_dir):
            shutil.rmtree(self.test_raw_dir)
        if os.path.exists(self.test_processed_dir):
            shutil.rmtree(self.test_processed_dir)

    @patch('code.evaluation.DATA_RAW_DIR')
    @patch('code.evaluation.DATA_PROCESSED_DIR')
    def test_load_raw_results_missing_file(self, mock_processed, mock_raw):
        """Test that load_raw_results raises FileNotFoundError if input is missing."""
        from code import evaluation
        evaluation.DATA_PROCESSED_DIR = self.test_processed_dir
        evaluation.DATA_RAW_DIR = self.test_raw_dir
        
        with self.assertRaises(FileNotFoundError):
            load_raw_results()

    def test_load_problems_empty_file(self):
        """Test loading problems from an empty file."""
        test_file = os.path.join(self.test_raw_dir, "test.jsonl")
        with open(test_file, 'w') as f:
            f.write("")
        
        # We need to patch the function to use our test file
        # Since load_problems uses a hardcoded path, we must mock the path
        with patch('code.evaluation.HUMAN_EVAL_DATA_FILE', test_file):
            problems = load_problems()
            self.assertEqual(len(problems), 0)

    def test_load_problems_valid_file(self):
        """Test loading problems from a valid JSONL file."""
        test_file = os.path.join(self.test_raw_dir, "test.jsonl")
        problem_data = {
            "task_id": "test/0",
            "prompt": "def add(a, b):\n    return a + b",
            "test": "assert add(1, 2) == 3"
        }
        with open(test_file, 'w') as f:
            f.write(json.dumps(problem_data) + "\n")
        
        with patch('code.evaluation.HUMAN_EVAL_DATA_FILE', test_file):
            problems = load_problems()
            self.assertEqual(len(problems), 1)
            self.assertIn("test/0", problems)
            self.assertEqual(problems["test/0"]["task_id"], "test/0")

    def test_evaluate_solution_empty(self):
        """Test that empty solution returns False."""
        problem = {
            "task_id": "test/0",
            "prompt": "",
            "test": "assert 1 == 1"
        }
        result = evaluate_solution(problem, "")
        self.assertFalse(result)

    def test_evaluate_solution_valid(self):
        """Test evaluation with a valid solution (mocked)."""
        problem = {
            "task_id": "test/0",
            "prompt": "def add(a, b):",
            "test": "assert add(1, 2) == 3"
        }
        solution = "    return a + b"
        
        # Mock the subprocess call to simulate a successful evaluation
        with patch('code.evaluation.subprocess.run') as mock_run:
            # Create a mock output file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as tmp_out:
                json.dump({"results": {"test/0": {"pass@1": 1.0}}}, tmp_out)
                tmp_out_path = tmp_out.name
            
            # Mock the return value
            mock_run.return_value = MagicMock(returncode=0)
            
            # We need to mock the file reading as well since the function reads the temp file
            # The function creates a temp file, runs command, then reads the output file.
            # We can mock the open function for the output file.
            with patch('builtins.open', side_effect=open) as mock_open:
                # This is tricky because the function uses tempfile.
                # Let's just test the logic flow by mocking the entire subprocess and file read.
                pass
        
        # Simpler approach: Mock the whole function logic for subprocess and file IO
        with patch('code.evaluation.subprocess.run') as mock_run:
            with patch('code.evaluation.json.dump') as mock_dump:
                with patch('code.evaluation.json.load') as mock_load:
                    with patch('code.evaluation.os.remove'):
                        mock_load.return_value = {"results": {"test/0": {"pass@1": 1.0}}}
                        result = evaluate_solution(problem, solution)
                        self.assertTrue(result)

    def test_write_results_to_csv(self):
        """Test writing results to CSV."""
        results = [
            {
                "model_id": "test_model",
                "problem_id": "test/0",
                "tokens_generated": 10,
                "energy_kwh": 0.001,
                "runtime_seconds": 1.0,
                "solution": "return 1",
                "pass_fail_status": 1
            }
        ]
        
        output_file = os.path.join(self.test_processed_dir, "test_output.csv")
        write_results_to_csv(results, output_file)
        
        self.assertTrue(os.path.exists(output_file))
        
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["pass_fail_status"], "1")

if __name__ == '__main__':
    unittest.main()
