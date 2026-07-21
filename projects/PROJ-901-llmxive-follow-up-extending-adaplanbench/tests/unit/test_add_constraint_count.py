"""
Unit tests for T014: add_constraint_count logic.
"""
import pytest
import json
from pathlib import Path
import sys
import tempfile
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.dataset.add_constraint_count import compute_constraint_count, add_constraint_count_column
import pandas as pd


class TestComputeConstraintCount:
    def test_valid_list(self):
        row = {
            "task_id": "test_1",
            "progressive_constraints": ["c1", "c2", "c3"]
        }
        assert compute_constraint_count(row) == 3

    def test_empty_list(self):
        row = {
            "task_id": "test_2",
            "progressive_constraints": []
        }
        assert compute_constraint_count(row) == 0

    def test_missing_column(self):
        row = {"task_id": "test_3"}
        with pytest.raises(ValueError, match="Row missing 'progressive_constraints'"):
            compute_constraint_count(row)

    def test_invalid_type_not_list_or_string(self):
        row = {
            "task_id": "test_4",
            "progressive_constraints": "not a list" # This will try JSON parse and fail
        }
        # The function tries json.loads on strings. If it's not a valid JSON list string, it raises.
        with pytest.raises(ValueError):
            compute_constraint_count(row)

    def test_string_json_list(self):
        row = {
            "task_id": "test_5",
            "progressive_constraints": '["c1", "c2"]'
        }
        assert compute_constraint_count(row) == 2

    def test_non_list_type(self):
        row = {
            "task_id": "test_6",
            "progressive_constraints": 123
        }
        with pytest.raises(ValueError, match="must be a list"):
            compute_constraint_count(row)


class TestAddConstraintCountColumn:
    def test_full_flow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            # Create input data
            data = {
                "task_id": ["t1", "t2"],
                "progressive_constraints": [
                    json.dumps(["a", "b"]), 
                    json.dumps(["x", "y", "z"])
                ]
            }
            df_input = pd.DataFrame(data)
            df_input.to_csv(input_path, index=False)
            
            # Run function
            add_constraint_count_column(input_path, output_path)
            
            # Verify output
            assert output_path.exists()
            df_out = pd.read_csv(output_path)
            
            assert "constraint_count" in df_out.columns
            assert df_out.loc[0, "constraint_count"] == 2
            assert df_out.loc[1, "constraint_count"] == 3
            assert df_out["constraint_count"].dtype in [int, "int64", "int32"]