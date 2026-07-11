"""
Unit tests for the Bounded Exhaustive Search Solver.
"""
import pytest
import json
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.oracle.solver import BoundedExhaustiveSolver, run_oracle_on_dataset

class TestBoundedExhaustiveSolver:
    def test_initialization(self):
        solver = BoundedExhaustiveSolver()
        assert solver.token_budget > 0
        assert solver.max_turns > 0
        assert solver.seed == 42

    def test_estimate_tokens(self):
        solver = BoundedExhaustiveSolver()
        # Heuristic: 1 token ≈ 4 chars
        assert solver._estimate_tokens("Hello") > 0
        assert solver._estimate_tokens("") == 0

    def test_solve_simple_task(self):
        solver = BoundedExhaustiveSolver()
        task = {
            "id": "test_task",
            "prompt": "Simple test",
            "solution_found": True
        }
        result = solver.solve(task)
        assert result["task_id"] == "test_task"
        assert result["possible"] is True
        assert result["tokens_used"] > 0

    def test_solve_impossible_task(self):
        solver = BoundedExhaustiveSolver()
        # Task that requires more turns than allowed
        task = {
            "id": "hard_task",
            "prompt": "Hard test",
            "solution_found": False
        }
        result = solver.solve(task)
        assert result["possible"] is False
        assert result["reason"].startswith("No solution found")

class TestRunOracleOnDataset:
    def test_run_oracle_on_json(self, tmp_path):
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.json"
        
        tasks = [
            {"id": "t1", "prompt": "p1", "solution_found": True},
            {"id": "t2", "prompt": "p2", "solution_found": False}
        ]
        with open(input_file, 'w') as f:
            json.dump(tasks, f)

        run_oracle_on_dataset(str(input_file), str(output_file))

        assert output_file.exists()
        with open(output_file, 'r') as f:
            results = json.load(f)
        
        assert len(results) == 2
        assert results[0]["possible"] is True
        assert results[1]["possible"] is False

    def test_run_oracle_on_parquet(self, tmp_path):
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not installed")

        input_file = tmp_path / "input.parquet"
        output_file = tmp_path / "output.parquet"
        
        tasks = [
            {"id": "t1", "prompt": "p1", "solution_found": True},
            {"id": "t2", "prompt": "p2", "solution_found": False}
        ]
        df = pd.DataFrame(tasks)
        df.to_parquet(input_file)

        run_oracle_on_dataset(str(input_file), str(output_file))

        assert output_file.exists()
        df_out = pd.read_parquet(output_file)
        assert len(df_out) == 2
        assert df_out.iloc[0]["possible"] is True