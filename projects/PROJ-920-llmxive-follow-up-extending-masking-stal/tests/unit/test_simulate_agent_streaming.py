import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path if running as script
sys_path = Path(__file__).parent.parent / "code"
if str(sys_path) not in __import__('sys').path:
    __import__('sys').path.insert(0, str(sys_path))

from simulate_agent import (
    sigmoid,
    heuristic_solver_success,
    check_evidence_visibility,
    load_trajectories_streaming,
    run_simulation_batch,
    write_batch_to_file,
    BATCH_SIZE
)

class TestSigmoid(unittest.TestCase):
    def test_positive(self):
        self.assertAlmostEqual(sigmoid(0), 0.5, places=5)
        self.assertAlmostEqual(sigmoid(10), 1.0, places=3)
        self.assertAlmostEqual(sigmoid(-10), 0.0, places=3)

class TestHeuristicSolver(unittest.TestCase):
    def test_success_probability(self):
        # With high density and positive alpha, probability should be high
        # We mock random to control the outcome
        random.seed(42)
        # If prob is high, success should be True often
        # Just testing that it returns a boolean
        result = heuristic_solver_success(0.9, 1.0, 0.5)
        self.assertIsInstance(result, bool)

class TestCheckEvidenceVisibility(unittest.TestCase):
    def test_visible(self):
        # Current turn 10, horizon 5 -> window starts at 10 - 5 + 1 = 6
        # Critical turn 8 is >= 6 -> Visible
        self.assertTrue(check_evidence_visibility(8, 10, 5))
    
    def test_not_visible(self):
        # Current turn 10, horizon 5 -> window starts at 6
        # Critical turn 5 is < 6 -> Not Visible
        self.assertFalse(check_evidence_visibility(5, 10, 5))
    
    def test_edge_case_last_turn(self):
        # Critical evidence at last turn (T)
        # Horizon 1 should see it
        self.assertTrue(check_evidence_visibility(10, 10, 1))

class TestRunSimulationBatch(unittest.TestCase):
    def test_batch_processing(self):
        traj = {
            'id': 'test-1',
            'density': 0.8,
            'critical_evidence_turn_index': 9,
            'total_turns': 10
        }
        results = run_simulation_batch([traj], retention_horizon=5, alpha=1.0, threshold=0.5)
        self.assertEqual(len(results), 1)
        self.assertIn('success', results[0])
        self.assertIn('trajectory_id', results[0])

class TestWriteBatchToFile(unittest.TestCase):
    def test_write_jsonl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.jsonl"
            results = [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}]
            
            write_batch_to_file(results, output_path, first_write=True)
            
            with open(output_path, 'r') as f:
                lines = f.readlines()
            
            self.assertEqual(len(lines), 2)
            # Verify JSON validity
            for line in lines:
                json.loads(line)

class TestLoadTrajectoriesStreaming(unittest.TestCase):
    def test_load_valid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "data.json"
            data = [{"id": 1}, {"id": 2}]
            with open(input_path, 'w') as f:
                json.dump(data, f)
            
            loaded = list(load_trajectories_streaming(str(input_path)))
            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[0]['id'], 1)

if __name__ == '__main__':
    unittest.main()
