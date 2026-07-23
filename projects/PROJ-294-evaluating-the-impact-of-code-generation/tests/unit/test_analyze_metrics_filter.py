import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analyze_metrics import aggregate_metrics_to_json, apply_pairwise_exclusion

class TestT042aFilterNullCoverage(unittest.TestCase):
    """Test that samples with null branch_coverage_pct are filtered out (T042a)."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_data = [
            {
                "task_id": "HumanEval/0",
                "source_type": "human",
                "cyclomatic_complexity": 1,
                "halstead_volume": 10.5,
                "pass_rate": 1.0,
                "branch_coverage_pct": 85.0
            },
            {
                "task_id": "HumanEval/0",
                "source_type": "llm",
                "cyclomatic_complexity": 2,
                "halstead_volume": 15.2,
                "pass_rate": 0.0,
                "branch_coverage_pct": None  # This should be filtered out
            },
            {
                "task_id": "HumanEval/1",
                "source_type": "human",
                "cyclomatic_complexity": 3,
                "halstead_volume": 20.1,
                "pass_rate": 1.0,
                "branch_coverage_pct": 90.0
            },
            {
                "task_id": "HumanEval/1",
                "source_type": "llm",
                "cyclomatic_complexity": 2,
                "halstead_volume": 18.0,
                "pass_rate": 1.0,
                "branch_coverage_pct": 75.0
            },
            {
                "task_id": "HumanEval/2",
                "source_type": "human",
                "cyclomatic_complexity": 4,
                "halstead_volume": 25.5,
                "pass_rate": 0.0,
                "branch_coverage_pct": None  # This should be filtered out
            },
            {
                "task_id": "HumanEval/2",
                "source_type": "llm",
                "cyclomatic_complexity": 3,
                "halstead_volume": 22.0,
                "pass_rate": 0.0,
                "branch_coverage_pct": None  # This should be filtered out
            }
        ]

    def test_filter_null_coverage(self):
        """Test that aggregate_metrics_to_json filters out null branch_coverage_pct."""
        # Create a temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            # Call the function
            result = aggregate_metrics_to_json(self.test_data, output_path)

            # Verify the result
            self.assertEqual(len(result), 3, "Should have 3 samples after filtering null coverage")
            
            # Verify no null coverage in result
            for r in result:
                self.assertIsNotNone(r.get('branch_coverage_pct'), 
                                    f"Sample {r['task_id']} should not have null coverage")

            # Verify the file was created and contains correct data
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(len(saved_data), 3, "Saved file should have 3 samples")
            
            # Verify specific samples
            task_ids = {r['task_id'] for r in saved_data}
            self.assertIn("HumanEval/0", task_ids)
            self.assertIn("HumanEval/1", task_ids)
            self.assertNotIn("HumanEval/2", task_ids)  # Both samples had null coverage

        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_pairwise_exclusion_after_filtering(self):
        """Test that pairwise exclusion works correctly after filtering null coverage."""
        # Filter data first (simulating T042a)
        filtered_data = [r for r in self.test_data if r.get('branch_coverage_pct') is not None]
        
        # Apply pairwise exclusion (T042b)
        result = apply_pairwise_exclusion(filtered_data)
        
        # Verify that HumanEval/2 is excluded (both samples had null coverage)
        task_ids = {r['task_id'] for r in result}
        self.assertNotIn("HumanEval/2", task_ids)
        
        # Verify HumanEval/0 and HumanEval/1 are included
        self.assertIn("HumanEval/0", task_ids)
        self.assertIn("HumanEval/1", task_ids)
        
        # Verify we have 2 samples per task (human and llm)
        self.assertEqual(len(result), 4, "Should have 4 samples (2 tasks * 2 sources)")

    def test_all_null_coverage(self):
        """Test behavior when all samples have null coverage."""
        all_null_data = [
            {
                "task_id": "HumanEval/3",
                "source_type": "human",
                "cyclomatic_complexity": 1,
                "halstead_volume": 10.0,
                "pass_rate": 0.0,
                "branch_coverage_pct": None
            },
            {
                "task_id": "HumanEval/3",
                "source_type": "llm",
                "cyclomatic_complexity": 2,
                "halstead_volume": 15.0,
                "pass_rate": 0.0,
                "branch_coverage_pct": None
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            result = aggregate_metrics_to_json(all_null_data, output_path)
            
            # Should return empty list
            self.assertEqual(len(result), 0, "Should have no samples when all have null coverage")
            
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(len(saved_data), 0, "Saved file should be empty")
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_no_null_coverage(self):
        """Test behavior when no samples have null coverage."""
        no_null_data = [
            {
                "task_id": "HumanEval/4",
                "source_type": "human",
                "cyclomatic_complexity": 1,
                "halstead_volume": 10.0,
                "pass_rate": 1.0,
                "branch_coverage_pct": 80.0
            },
            {
                "task_id": "HumanEval/4",
                "source_type": "llm",
                "cyclomatic_complexity": 2,
                "halstead_volume": 15.0,
                "pass_rate": 1.0,
                "branch_coverage_pct": 75.0
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            result = aggregate_metrics_to_json(no_null_data, output_path)
            
            # Should return all samples
            self.assertEqual(len(result), 2, "Should have all samples when none have null coverage")
            
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(len(saved_data), 2, "Saved file should have all samples")
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

if __name__ == '__main__':
    unittest.main()
