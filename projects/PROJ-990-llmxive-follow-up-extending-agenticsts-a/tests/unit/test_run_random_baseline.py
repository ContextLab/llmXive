import os
import sys
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from run_random_baseline import load_test_set_ids, run_random_baseline_simulation

class TestRunRandomBaseline(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / "data"
        self.processed_dir = self.data_dir / "processed"
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir.mkdir(parents=True)
        self.raw_dir.mkdir(parents=True)

        # Mock config
        self.config = {"K_RANDOM_BASELINE": 2}

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('run_random_baseline.PROJECT_ROOT')
    def test_load_test_set_ids_success(self, mock_root):
        mock_root.return_value = Path(self.test_dir)
        
        # Create mock test_set.csv
        test_set_path = self.processed_dir / "test_set.csv"
        test_set_path.write_text("trajectory_id\n123\n456\n789\n")
        
        ids = load_test_set_ids()
        self.assertEqual(ids, ['123', '456', '789'])

    @patch('run_random_baseline.PROJECT_ROOT')
    def test_load_test_set_ids_missing_file(self, mock_root):
        mock_root.return_value = Path(self.test_dir)
        
        with self.assertRaises(FileNotFoundError):
            load_test_set_ids()

    @patch('run_random_baseline.PROJECT_ROOT')
    @patch('run_random_baseline.load_test_set_ids')
    def test_run_random_baseline_simulation(self, mock_load_ids, mock_root):
        mock_root.return_value = Path(self.test_dir)
        mock_load_ids.return_value = ['t1']

        # Create mock raw data
        raw_file = self.raw_dir / "agenticsts_trajectories.jsonl"
        mock_traj = {
            "trajectory_id": "t1",
            "turns": [
                {
                    "available_layers": ["layer_a", "layer_b", "layer_c"],
                    "tokens": 100
                },
                {
                    "available_layers": ["layer_x", "layer_y"],
                    "tokens": 50
                }
            ]
        }
        raw_file.write_text(json.dumps(mock_traj))

        # Mock the ensure_directories
        with patch('run_random_baseline.ensure_directories'):
            results = run_random_baseline_simulation(self.config, ['t1'], k=2)
            
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['trajectory_id'], 't1')
            self.assertEqual(results[0]['baseline_type'], 'random')
            self.assertEqual(len(results[0]['turns']), 2)
            
            # Check that k layers were selected (or all if less than k)
            for turn in results[0]['turns']:
                self.assertLessEqual(turn['k_selected'], 2)
                self.assertLessEqual(turn['k_selected'], turn['available_layers_count'])

    @patch('run_random_baseline.PROJECT_ROOT')
    @patch('run_random_baseline.load_test_set_ids')
    def test_run_random_baseline_missing_raw(self, mock_load_ids, mock_root):
        mock_root.return_value = Path(self.test_dir)
        mock_load_ids.return_value = ['t1']
        
        with self.assertRaises(FileNotFoundError):
            run_random_baseline_simulation(self.config, ['t1'], k=2)

if __name__ == '__main__':
    unittest.main()
