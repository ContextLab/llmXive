"""
Unit tests for the add_constraint_count functionality.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from dataset.add_constraint_count import compute_constraint_count, add_constraint_count_column

class TestComputeConstraintCount:
    def test_valid_list(self):
        row = pd.Series({'progressive_constraints': ['c1', 'c2', 'c3']})
        assert compute_constraint_count(row) == 3

    def test_empty_list(self):
        row = pd.Series({'progressive_constraints': []})
        assert compute_constraint_count(row) == 0

    def test_json_string(self):
        row = pd.Series({'progressive_constraints': json.dumps(['a', 'b'])})
        assert compute_constraint_count(row) == 2

    def test_invalid_json_string(self):
        row = pd.Series({'progressive_constraints': 'not a json'})
        assert compute_constraint_count(row) == 0

    def test_missing_field(self):
        row = pd.Series({})
        assert compute_constraint_count(row) == 0

    def test_non_list_type(self):
        row = pd.Series({'progressive_constraints': 'string not list'})
        assert compute_constraint_count(row) == 0

class TestAddConstraintCountColumn:
    def test_basic_flow(self):
        # Create a temporary input file
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            # Create sample data
            data = {
                'task_id': ['t1', 't2', 't3'],
                'progressive_constraints': [
                    ['c1', 'c2'],
                    json.dumps(['c3', 'c4', 'c5']),
                    []
                ]
            }
            df_input = pd.DataFrame(data)
            df_input.to_csv(input_path, index=False)

            # Run the function
            df_output = add_constraint_count_column(input_path, output_path)

            # Verify output
            assert output_path.exists()
            df_result = pd.read_csv(output_path)
            assert 'constraint_count' in df_result.columns
            assert df_result['constraint_count'].tolist() == [2, 3, 0]
            assert df_result['constraint_count'].dtype == int

    def test_missing_column_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            # Create sample data missing the required column
            data = {'task_id': ['t1']}
            df_input = pd.DataFrame(data)
            df_input.to_csv(input_path, index=False)

            with pytest.raises(ValueError, match="missing required column"):
                add_constraint_count_column(input_path, output_path)

    def test_file_not_found_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "nonexistent.csv"
            output_path = Path(tmpdir) / "output.csv"

            with pytest.raises(FileNotFoundError):
                add_constraint_count_column(input_path, output_path)
