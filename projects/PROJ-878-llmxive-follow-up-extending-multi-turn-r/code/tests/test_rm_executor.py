import unittest
import os
from pathlib import Path
import json

# Import the executor and helper functions
from code.rm_executor import ReflectiveMaskingExecutor, load_puzzles, write_results

class TestRMExecutor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure a minimal .env exists with a small model
        env_path = Path(".env")
        if not env_path.is_file():
            env_path.write_text("MODEL_PATH=distilbert-base-uncased\\n")

    def setUp(self):
        # Create a tiny synthetic puzzle for testing
        self.puzzle = {
            "instance_id": "test_puzzle_001",
            "text": "Puzzle ID: 0\\nNodes: [A, B, C]\\nEdges: [(A, B), (B, C)]\\nFind a path from A to C that is NOT the longest path (2 steps).\\nGround‑truth path (perturbed): [A, B, C]\\n",
            "ground_truth_path": ["A", "B", "C"],
            "nesting_depth": 2,
            "branching_factor": 1.0,
            "graph_structure": {"nodes": ["A", "B", "C"], "edges": [["A", "B"], ["B", "C"]]},
            "is_acyclic": True,
            "is_solvable": True,
            "text_generation_method": "template_based",
            "is_orthogonal": True,
            "seed": None
        }
        self.input_path = Path("data/raw/test_puzzle.jsonl")
        self.input_path.parent.mkdir(parents=True, exist_ok=True)
        with self.input_path.open("w", encoding="utf-8") as f:
            json.dump(self.puzzle, f)
            f.write("\\n")

    def tearDown(self):
        if self.input_path.is_file():
            self.input_path.unlink()
        output_path = Path("data/processed/test_execution_log.csv")
        if output_path.is_file():
            output_path.unlink()

    def test_load_puzzles(self):
        puzzles = load_puzzles(str(self.input_path))
        self.assertEqual(len(puzzles), 1)
        self.assertEqual(puzzles[0]["instance_id"], "test_puzzle_001")

    def test_executor_successful_run(self):
        executor = ReflectiveMaskingExecutor(
            model_path="distilbert-base-uncased",
            device="cpu",
            max_turns=10
        )
        result = executor.run(
            puzzle_text=self.puzzle["text"],
            ground_truth_path=self.puzzle["ground_truth_path"],
            nesting_depth=self.puzzle["nesting_depth"]
        )
        self.assertIn("turns_to_converge", result)
        self.assertIn("convergence_status", result)
        self.assertIn("final_path", result)

    def test_write_results(self):
        executor = ReflectiveMaskingExecutor(
            model_path="distilbert-base-uncased",
            device="cpu",
            max_turns=5
        )
        result = executor.run(
            puzzle_text=self.puzzle["text"],
            ground_truth_path=self.puzzle["ground_truth_path"],
            nesting_depth=self.puzzle["nesting_depth"]
        )
        result["instance_id"] = self.puzzle["instance_id"]
        write_results([result], "data/processed/test_execution_log.csv")
        self.assertTrue(Path("data/processed/test_execution_log.csv").is_file())

if __name__ == "__main__":
    unittest.main()
