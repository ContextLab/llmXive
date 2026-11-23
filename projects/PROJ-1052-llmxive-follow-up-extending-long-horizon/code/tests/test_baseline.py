"""
Integration test for User Story 1: Baseline Execution Flow.

Task ID: T011
Description: Verify that `data/processed/baseline_execution_logs.csv` contains 
             at least one row with a non-empty `recovery_segment_id`.

Dependencies:
  - T005: Schema contracts (specs/001-reward-fidelity-error-recovery/contracts)
  - T006: Recovery segment identification logic (code/utils/state_diff.py)
  - T012: Baseline execution runner (produces data/processed/baseline_execution_logs.csv)

Note: This test validates the schema contract and the logic in T006, enabling 
      true Test-Driven Development. It assumes T012 has been executed to generate
      the required data file.
"""
import os
import sys
import unittest
import csv
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

class TestBaselineExecutionFlow(unittest.TestCase):
    """Integration tests for the baseline execution flow and recovery segment logging."""

    @classmethod
    def setUpClass(cls):
        """
        Locate the output file produced by T012 (baseline_execution_logs.csv).
        The path is relative to the project root.
        """
        cls.project_root = Path(__file__).resolve().parents[2]
        cls.output_file = cls.project_root / "data" / "processed" / "baseline_execution_logs.csv"
        
        # Verify the file exists before running tests
        if not cls.output_file.exists():
            raise FileNotFoundError(
                f"Required artifact not found: {cls.output_file}. "
                "Please ensure T012 (baseline execution) has been run successfully to generate this file."
            )

    def test_baseline_execution_flow_logs_recovery_segments(self):
        """
        Assertion: Verify that `data/processed/baseline_execution_logs.csv` 
        contains at least one row with a non-empty `recovery_segment_id`.
        
        This validates that:
        1. The execution runner (T012) successfully wrote the CSV.
        2. The recovery segment tagging logic (T014, relying on T006) 
           successfully populated the `recovery_segment_id` column.
        """
        found_recovery_segment = False
        rows_checked = 0
        
        with open(self.output_file, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Verify the column exists in the header
            self.assertIn('recovery_segment_id', reader.fieldnames, 
                          "CSV header missing 'recovery_segment_id' column. "
                          "Ensure T014 tagging logic is applied.")
            
            for row in reader:
                rows_checked += 1
                segment_id = row.get('recovery_segment_id', '').strip()
                
                # Check for non-empty segment ID
                if segment_id:
                    found_recovery_segment = True
                    # Optional: Log the first found instance for debugging
                    # print(f"Found recovery segment in row {rows_checked}: {segment_id}")
                    break

        self.assertTrue(
            found_recovery_segment,
            f"No rows with a non-empty 'recovery_segment_id' found in {self.output_file}. "
            f"Checked {rows_checked} rows. "
            "This indicates T006 (state_diff) or T014 (tagging) did not successfully "
            "identify or log recovery segments."
        )

    def test_schema_contract_fields_present(self):
        """
        Quick contract test to ensure the CSV contains expected fields from T005 schema.
        """
        with open(self.output_file, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames
            
            # Expected fields based on T005 schema and T012 output requirements
            expected_fields = ['task_id', 'success_status', 'recovery_segment_id']
            
            for field in expected_fields:
                self.assertIn(field, fieldnames, 
                              f"Missing required field '{field}' in execution log CSV.")

if __name__ == '__main__':
    unittest.main()