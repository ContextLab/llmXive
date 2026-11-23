"""
Unit tests for code/utils/verify_run.py
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils.verify_run import (
    load_yaml_config,
    load_json,
    get_task_ids_from_dataset,
    get_baseline_task_ids,
    get_2d_run_task_ids,
    verify_integrity
)


class TestVerifyRun(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.dataset_path = os.path.join(self.temp_dir, "dataset.json")
        self.baseline_path = os.path.join(self.temp_dir, "baseline.json")
        self.runs_dir = os.path.join(self.temp_dir, "runs")
        self.config_path = os.path.join(self.temp_dir, "config.yaml")
        self.output_path = os.path.join(self.temp_dir, "report.json")

        os.makedirs(self.runs_dir, exist_ok=True)

        # Mock Config
        self.config_data = {
            "n_runs": 3,
            "effect_size": 0.5
        }
        with open(self.config_path, 'w') as f:
            import yaml
            yaml.dump(self.config_data, f)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_load_yaml_config(self):
        config = load_yaml_config(self.config_path)
        self.assertEqual(config['n_runs'], 3)

    def test_load_json(self):
        data = {"key": "value"}
        path = os.path.join(self.temp_dir, "test.json")
        with open(path, 'w') as f:
            json.dump(data, f)
        
        result = load_json(path)
        self.assertEqual(result['key'], 'value')

    def test_get_task_ids_from_dataset_list(self):
        data = [{"task_id": "t1"}, {"task_id": "t2"}, {"task_id": "t1"}]
        with open(self.dataset_path, 'w') as f:
            json.dump(data, f)
        
        ids = get_task_ids_from_dataset(self.dataset_path)
        self.assertEqual(ids, {"t1", "t2"})

    def test_get_task_ids_from_dataset_dict(self):
        data = {"tasks": [{"task_id": "t3"}, {"task_id": "t4"}]}
        with open(self.dataset_path, 'w') as f:
            json.dump(data, f)
        
        ids = get_task_ids_from_dataset(self.dataset_path)
        self.assertEqual(ids, {"t3", "t4"})

    def test_get_baseline_task_ids(self):
        data = [{"task_id": "t1"}, {"task_id": "t2"}]
        with open(self.baseline_path, 'w') as f:
            json.dump(data, f)
        
        ids = get_baseline_task_ids(self.baseline_path)
        self.assertEqual(ids, {"t1", "t2"})

    def test_get_2d_run_task_ids(self):
        # Create run files
        run1 = {"task_id": "t1", "run": 1}
        run2 = {"task_id": "t1", "run": 2}
        run3 = {"task_id": "t2", "run": 1}
        
        with open(os.path.join(self.runs_dir, "run_1.json"), 'w') as f:
            json.dump(run1, f)
        with open(os.path.join(self.runs_dir, "run_2.json"), 'w') as f:
            json.dump(run2, f)
        with open(os.path.join(self.runs_dir, "run_3.json"), 'w') as f:
            json.dump(run3, f)

        counts = get_2d_run_task_ids(self.runs_dir, 3)
        self.assertEqual(counts["t1"], 2)
        self.assertEqual(counts["t2"], 1)
        self.assertNotIn("t3", counts)

    def test_verify_integrity_complete(self):
        # Setup: 2 tasks, 3 runs each, baseline present for both
        dataset_data = [{"task_id": "t1"}, {"task_id": "t2"}]
        baseline_data = [{"task_id": "t1"}, {"task_id": "t2"}]
        
        with open(self.dataset_path, 'w') as f:
            json.dump(dataset_data, f)
        with open(self.baseline_path, 'w') as f:
            json.dump(baseline_data, f)

        # Create 3 runs for each task
        for i in range(1, 4):
            with open(os.path.join(self.runs_dir, f"run_{i}.json"), 'w') as f:
                json.dump({"task_id": "t1", "run": i}, f)
            with open(os.path.join(self.runs_dir, f"run_{i+3}.json"), 'w') as f:
                json.dump({"task_id": "t2", "run": i}, f)

        success = verify_integrity(
            self.dataset_path,
            self.baseline_path,
            self.runs_dir,
            self.config_path,
            self.output_path
        )

        self.assertTrue(success)
        
        # Verify report content
        with open(self.output_path, 'r') as f:
            report = json.load(f)
        
        self.assertEqual(report['status'], 'COMPLETE')
        self.assertEqual(report['total_tasks'], 2)
        self.assertEqual(report['tasks_with_full_coverage'], 2)
        self.assertEqual(len(report['missing_runs']), 0)

    def test_verify_integrity_incomplete(self):
        # Setup: 2 tasks, missing 1 run for t2, missing baseline for t1
        dataset_data = [{"task_id": "t1"}, {"task_id": "t2"}]
        baseline_data = [{"task_id": "t2"}] # Missing t1
        
        with open(self.dataset_path, 'w') as f:
            json.dump(dataset_data, f)
        with open(self.baseline_path, 'w') as f:
            json.dump(baseline_data, f)

        # Create 3 runs for t1, only 2 for t2
        for i in range(1, 4):
            with open(os.path.join(self.runs_dir, f"run_{i}.json"), 'w') as f:
                json.dump({"task_id": "t1", "run": i}, f)
        
        for i in range(1, 3):
            with open(os.path.join(self.runs_dir, f"run_{i+3}.json"), 'w') as f:
                json.dump({"task_id": "t2", "run": i}, f)

        success = verify_integrity(
            self.dataset_path,
            self.baseline_path,
            self.runs_dir,
            self.config_path,
            self.output_path
        )

        self.assertFalse(success)

        with open(self.output_path, 'r') as f:
            report = json.load(f)
        
        self.assertEqual(report['status'], 'INCOMPLETE')
        self.assertEqual(report['tasks_with_full_coverage'], 0) # t1 missing baseline, t2 missing run
        self.assertEqual(len(report['missing_runs']), 2)

        # Check specific missing details
        missing_ids = [m['task_id'] for m in report['missing_runs']]
        self.assertIn('t1', missing_ids)
        self.assertIn('t2', missing_ids)


if __name__ == '__main__':
    unittest.main()