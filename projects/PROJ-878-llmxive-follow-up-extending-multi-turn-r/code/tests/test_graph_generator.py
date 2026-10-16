import json
import os
import random
import unittest
from pathlib import Path

# Import the generator function
from code.graph_generator import generate_batch, _write_jsonl

class TestGraphGenerator(unittest.TestCase):
    def setUp(self):
        # Use a deterministic seed for reproducibility
        self.seed = 12345
        random.seed(self.seed)

        # Temporary output path
        self.output_path = Path("data/raw/test_synthetic_puzzles.jsonl")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        # Clean up generated file
        if self.output_path.is_file():
            self.output_path.unlink()

    def test_generate_batch_size_and_range(self):
        # Generate a small batch for quick testing
        puzzles = generate_batch(
            num_instances=20,
            min_depth=3,
            max_depth=6,
            min_branching=1.0,
            max_branching=5.0,
            max_correlation=0.2,
            seed=self.seed,
        )
        self.assertEqual(len(puzzles), 20, "Should generate exactly 20 puzzles")
        for p in puzzles:
            self.assertIn("nesting_depth", p)
            self.assertIn("branching_factor", p)
            self.assertGreaterEqual(p["nesting_depth"], 3)
            self.assertLessEqual(p["nesting_depth"], 6)
            self.assertGreaterEqual(p["branching_factor"], 1.0)
            self.assertLessEqual(p["branching_factor"], 5.0)

    def test_jsonl_write_and_read(self):
        puzzles = generate_batch(
            num_instances=5,
            min_depth=3,
            max_depth=6,
            min_branching=1.0,
            max_branching=5.0,
            max_correlation=0.2,
            seed=self.seed,
        )
        _write_jsonl(puzzles, self.output_path)

        # Verify that the file exists and contains the expected number of lines
        self.assertTrue(self.output_path.is_file(), "JSONL output file should exist")
        with self.output_path.open("r", encoding="utf-8") as f:
            lines = [line for line in f if line.strip()]
        self.assertEqual(len(lines), 5, "JSONL file should contain 5 records")

        # Verify that each line is valid JSON and contains required fields
        for line in lines:
            record = json.loads(line)
            self.assertIn("instance_id", record)
            self.assertIn("nesting_depth", record)
            self.assertIn("branching_factor", record)

if __name__ == "__main__":
    unittest.main()
