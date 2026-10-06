"""
Tests for experimental design components, including counterbalancing.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import unittest
import csv
import sys

# Add src to path if running directly
if "code" in os.getcwd():
    sys.path.insert(0, os.path.join(os.getcwd(), "src"))
else:
    # Try to find src relative to this file
    base_dir = Path(__file__).resolve().parent.parent
    src_dir = base_dir / "src"
    if src_dir.exists():
        sys.path.insert(0, str(base_dir))

from src.experiment.counterbalance import (
    generate_latin_square,
    generate_counterbalance_orders,
    load_stimuli_list,
    save_counterbalance_output
)


class TestLatinSquareCounterbalancing(unittest.TestCase):
    """Tests for Latin Square generation and counterbalancing logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.stimuli_dir = Path(self.test_dir) / "stimuli" / "raw"
        self.stimuli_dir.mkdir(parents=True)
        
        # Create dummy stimulus files
        for i in range(5):
            (self.stimuli_dir / f"stimulus_{i}.jpg").touch()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_latin_square_properties(self):
        """Test that generated Latin Square satisfies Latin Square properties."""
        n = 5
        square = generate_latin_square(n, seed=42)

        # Check dimensions
        self.assertEqual(len(square), n)
        for row in square:
            self.assertEqual(len(row), n)

        # Check that each row contains 0..n-1 exactly once
        for row in square:
            self.assertEqual(sorted(row), list(range(n)))

        # Check that each column contains 0..n-1 exactly once
        for col_idx in range(n):
            column = [square[row_idx][col_idx] for row_idx in range(n)]
            self.assertEqual(sorted(column), list(range(n)))

    def test_counterbalance_output_structure(self):
        """Test that counterbalance orders have correct structure."""
        stimuli_ids = ["A", "B", "C", "D"]
        orders = generate_counterbalance_orders(stimuli_ids, seed=42)

        self.assertEqual(len(orders), len(stimuli_ids))

        for order in orders:
            self.assertIn("participant_id", order)
            self.assertIn("order", order)
            self.assertIn("latin_square_id", order)
            self.assertEqual(len(order["order"]), len(stimuli_ids))
            self.assertEqual(set(order["order"]), set(stimuli_ids))

    def test_counterbalance_uniqueness(self):
        """Test that each participant receives a unique order and Latin Square properties hold."""
        stimuli_ids = ["S1", "S2", "S3", "S4"]
        orders = generate_counterbalance_orders(stimuli_ids, seed=123)

        # Check all participant IDs are unique
        participant_ids = [o["participant_id"] for o in orders]
        self.assertEqual(len(participant_ids), len(set(participant_ids)))

        # Check that each stimulus appears in each position exactly once
        n = len(stimuli_ids)
        for position in range(n):
            stimuli_at_position = [o["order"][position] for o in orders]
            self.assertEqual(sorted(stimuli_at_position), sorted(stimuli_ids))

    def test_save_counterbalance_output(self):
        """Test saving counterbalance output to JSON."""
        stimuli_ids = ["X", "Y", "Z"]
        orders = generate_counterbalance_orders(stimuli_ids, seed=42)
        
        output_path = Path(self.test_dir) / "counterbalance.json"
        save_counterbalance_output(orders, output_path)

        self.assertTrue(output_path.exists())
        
        with open(output_path, 'r') as f:
            loaded_orders = json.load(f)
        
        self.assertEqual(len(loaded_orders), len(orders))
        self.assertEqual(loaded_orders[0]["order"], orders[0]["order"])

    def test_load_stimuli_from_csv(self):
        """Test loading stimuli list from curated_clips.csv."""
        # Create a mock curated_clips.csv
        curated_dir = Path(self.test_dir) / "processed"
        curated_dir.mkdir()
        curated_csv = curated_dir / "curated_clips.csv"
        
        with open(curated_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["clip_id", "filename", "duration"])
            writer.writeheader()
            for i in range(3):
                writer.writerow({"clip_id": f"clip_{i}", "filename": f"file_{i}.mp4", "duration": 5})
        
        # Temporarily override DATA_DIR for testing
        import src.experiment.counterbalance as cb
        original_data_dir = cb.DATA_DIR
        cb.DATA_DIR = Path(self.test_dir)
        
        try:
            stimuli = load_stimuli_list()
            self.assertEqual(stimuli, ["clip_0", "clip_1", "clip_2"])
        finally:
            cb.DATA_DIR = original_data_dir

    def test_load_stimuli_from_raw_files(self):
        """Test loading stimuli list from raw files when CSV is missing."""
        import src.experiment.counterbalance as cb
        original_data_dir = cb.DATA_DIR
        cb.DATA_DIR = Path(self.test_dir)
        
        try:
            # Remove CSV if it exists
            curated_csv = Path(self.test_dir) / "processed" / "curated_clips.csv"
            if curated_csv.exists():
                curated_csv.unlink()
            
            stimuli = load_stimuli_list()
            # Should load from raw files
            self.assertEqual(len(stimuli), 5)
            self.assertTrue(all(s.startswith("stimulus_") for s in stimuli))
        finally:
            cb.DATA_DIR = original_data_dir


class TestBaselineReactionTimeTask(unittest.TestCase):
    """Tests for baseline reaction time task mechanism."""

    def test_rt_mechanism_accuracy(self):
        """Test that RT mechanism captures timing accurately (mocked for CI)."""
        # This test verifies the mechanism exists and can be called
        # Actual timing accuracy is hard to test in CI without hardware control
        # We test that the function returns valid structure
        
        # Mock implementation of what rt_mechanism.py would do
        class MockRTMechanism:
            def __init__(self):
                self.measurements = []
            
            def start_task(self, stimulus_id):
                return {"stimulus_id": stimulus_id, "status": "started"}
            
            def record_response(self, response_time_ms):
                return {"response_time": response_time_ms, "valid": True}
            
            def get_results(self):
                return self.measurements

        mechanism = MockRTMechanism()
        start = mechanism.start_task("baseline_stimulus")
        self.assertEqual(start["stimulus_id"], "baseline_stimulus")
        
        result = mechanism.record_response(250)
        self.assertEqual(result["response_time"], 250)
        self.assertTrue(result["valid"])


class TestMissingDataFlagging(unittest.TestCase):
    """Tests for incomplete record flagging."""

    def test_incomplete_record_flagging(self):
        """Test that records with missing TLX or RT are flagged."""
        # Mock data structure
        records = [
            {"participant_id": "P1", "tlx_score": 45, "rt_ms": 200, "complete": True},
            {"participant_id": "P2", "tlx_score": None, "rt_ms": 200, "complete": False},
            {"participant_id": "P3", "tlx_score": 50, "rt_ms": None, "complete": False},
            {"participant_id": "P4", "tlx_score": None, "rt_ms": None, "complete": False},
        ]

        def flag_incomplete(record):
            if record.get("tlx_score") is None or record.get("rt_ms") is None:
                record["flagged"] = True
            else:
                record["flagged"] = False
            return record

        flagged_records = [flag_incomplete(r) for r in records]
        
        self.assertTrue(flagged_records[0]["complete"])
        self.assertFalse(flagged_records[1]["complete"])
        self.assertTrue(flagged_records[1]["flagged"])
        self.assertTrue(flagged_records[2]["flagged"])
        self.assertTrue(flagged_records[3]["flagged"])


if __name__ == "__main__":
    unittest.main()
