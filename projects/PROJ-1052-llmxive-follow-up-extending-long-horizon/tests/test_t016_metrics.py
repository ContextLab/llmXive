import unittest
import pandas as pd
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.metrics import calculate_recovery_metrics

class TestT016Metrics(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.baseline_path = os.path.join(self.test_dir, "baseline.csv")
        self.injected_path = os.path.join(self.test_dir, "injected.csv")
        self.output_path = os.path.join(self.test_dir, "metrics.csv")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_exclude_baseline_failures(self):
        """
        Test that tasks which failed in the baseline are excluded from the
        recovery success rate denominator but logged as unrecoverable.
        """
        # Create baseline data: Task A succeeded, Task B failed
        baseline_data = [
            {"task_id": "task_A", "success_status": "success"},
            {"task_id": "task_B", "success_status": "failure"}
        ]
        pd.DataFrame(baseline_data).to_csv(self.baseline_path, index=False)

        # Create injected data:
        # Task A: succeeded (recovered)
        # Task B: failed (unrecoverable, because baseline was failure)
        # Task C: succeeded (recovered) - Note: Task C was not in baseline, assume success or handle missing?
        # For this test, let's assume Task C exists in baseline as success too.
        baseline_data.append({"task_id": "task_C", "success_status": "success"})
        pd.DataFrame(baseline_data).to_csv(self.baseline_path, index=False)

        injected_data = [
            {"task_id": "task_A", "success_status": "success"}, # Recovered
            {"task_id": "task_B", "success_status": "failure"}, # Unrecoverable
            {"task_id": "task_C", "success_status": "success"}  # Recovered
        ]
        pd.DataFrame(injected_data).to_csv(self.injected_path, index=False)

        result = calculate_recovery_metrics(self.baseline_path, self.injected_path, self.output_path)

        # Expected:
        # Total Injected: 3
        # Unrecoverable: 1 (task_B)
        # Recoverable: 2 (task_A, task_C)
        # Successful Recoveries: 2
        # Rate: 2/2 = 1.0

        self.assertEqual(result['total_injected'], 3)
        self.assertEqual(result['unrecoverable_count'], 1)
        self.assertEqual(result['recoverable_count'], 2)
        self.assertEqual(result['successful_recoveries'], 2)
        self.assertAlmostEqual(result['recovery_success_rate'], 1.0)

        # Verify output file exists and has correct rows
        self.assertTrue(os.path.exists(self.output_path))
        output_df = pd.read_csv(self.output_path)
        self.assertEqual(len(output_df), 3)
        
        # Check status column
        statuses = set(output_df['status'])
        self.assertIn('recovered', statuses)
        self.assertIn('unrecoverable', statuses)

    def test_all_baseline_failures(self):
        """
        Test case where all injected tasks were baseline failures.
        Rate should be 0.0 (or handled gracefully).
        """
        baseline_data = [
            {"task_id": "task_X", "success_status": "failure"}
        ]
        pd.DataFrame(baseline_data).to_csv(self.baseline_path, index=False)

        injected_data = [
            {"task_id": "task_X", "success_status": "failure"}
        ]
        pd.DataFrame(injected_data).to_csv(self.injected_path, index=False)

        result = calculate_recovery_metrics(self.baseline_path, self.injected_path, self.output_path)

        self.assertEqual(result['total_injected'], 1)
        self.assertEqual(result['unrecoverable_count'], 1)
        self.assertEqual(result['recoverable_count'], 0)
        self.assertEqual(result['successful_recoveries'], 0)
        self.assertEqual(result['recovery_success_rate'], 0.0)

    def test_no_baseline_failures(self):
        """
        Test case where no baseline failures exist. All injected tasks are recoverable.
        """
        baseline_data = [
            {"task_id": "task_Y", "success_status": "success"}
        ]
        pd.DataFrame(baseline_data).to_csv(self.baseline_path, index=False)

        injected_data = [
            {"task_id": "task_Y", "success_status": "failure"} # Failed injection
        ]
        pd.DataFrame(injected_data).to_csv(self.injected_path, index=False)

        result = calculate_recovery_metrics(self.baseline_path, self.injected_path, self.output_path)

        self.assertEqual(result['total_injected'], 1)
        self.assertEqual(result['unrecoverable_count'], 0)
        self.assertEqual(result['recoverable_count'], 1)
        self.assertEqual(result['successful_recoveries'], 0)
        self.assertEqual(result['recovery_success_rate'], 0.0)

if __name__ == '__main__':
    unittest.main()