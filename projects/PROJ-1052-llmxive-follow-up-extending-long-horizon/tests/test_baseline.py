import os
import sys
import unittest
import csv
import json
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

class TestBaselineExecutionFlow(unittest.TestCase):
    """
    Integration test to verify that baseline execution produces valid logs
    with recovery segment IDs (once T014 is run).
    """

    def setUp(self):
        self.data_dir = Path("data/processed")
        self.logs_file = self.data_dir / "baseline_execution_logs.csv"
        self.tasks_file = self.data_dir / "baseline_tasks.jsonl"

    def test_baseline_execution_logs_exist(self):
        """
        Verify that the baseline execution logs file exists.
        """
        self.assertTrue(self.logs_file.exists(), 
                        f"Expected file {self.logs_file} to exist after baseline execution.")

    def test_baseline_logs_contain_required_columns(self):
        """
        Verify that the baseline execution logs contain required columns:
        task_id, success, trajectory.
        """
        if not self.logs_file.exists():
            self.fail(f"{self.logs_file} does not exist. Run T012 first.")
        
        with open(self.logs_file, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            required_columns = ['task_id', 'success', 'trajectory']
            for col in required_columns:
                self.assertIn(col, headers, f"Missing required column: {col}")

    def test_baseline_logs_have_data(self):
        """
        Verify that the baseline execution logs contain at least one row.
        """
        if not self.logs_file.exists():
            self.fail(f"{self.logs_file} does not exist. Run T012 first.")
        
        with open(self.logs_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            self.assertGreater(len(rows), 0, 
                               "Expected at least one row in baseline_execution_logs.csv")

    def test_baseline_logs_trajectory_is_valid_json(self):
        """
        Verify that the trajectory column contains valid JSON.
        """
        if not self.logs_file.exists():
            self.fail(f"{self.logs_file} does not exist. Run T012 first.")
        
        with open(self.logs_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    trajectory = json.loads(row['trajectory'])
                    self.assertIsInstance(trajectory, list, 
                                          "Trajectory should be a list")
                except json.JSONDecodeError as e:
                    self.fail(f"Invalid JSON in trajectory column: {e}")

    def test_baseline_logs_success_is_boolean(self):
        """
        Verify that the success column contains boolean-like values.
        """
        if not self.logs_file.exists():
            self.fail(f"{self.logs_file} does not exist. Run T012 first.")
        
        with open(self.logs_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                success_val = row['success']
                self.assertIn(success_val.lower(), ['true', 'false', '1', '0', 'yes', 'no'],
                              f"Invalid success value: {success_val}")

if __name__ == '__main__':
    unittest.main()