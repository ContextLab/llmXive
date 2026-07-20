"""
Unit tests for the add_constraint_count module (T014).
"""
import pytest
import pandas as pd
from code.dataset.add_constraint_count import compute_constraint_count, add_constraint_count_column


class TestComputeConstraintCount:
    """Tests for the compute_constraint_count helper function."""

    def test_none_input(self):
        assert compute_constraint_count(None) == 0

    def test_empty_list(self):
        assert compute_constraint_count([]) == 0

    def test_simple_list(self):
        assert compute_constraint_count(["c1", "c2", "c3"]) == 3

    def test_json_string_list(self):
        input_str = '["c1", "c2", "c3"]'
        assert compute_constraint_count(input_str) == 3

    def test_python_literal_string_list(self):
        input_str = "['c1', 'c2']"
        assert compute_constraint_count(input_str) == 2

    def test_empty_string(self):
        assert compute_constraint_count("") == 0

    def test_whitespace_string(self):
        assert compute_constraint_count("   ") == 0

    def test_single_string_constraint(self):
        # If it's a non-empty string that isn't a list, we count as 1
        assert compute_constraint_count("Do not touch the vase") == 1

    def test_invalid_json_and_literal(self):
        input_str = "not a list or json"
        assert compute_constraint_count(input_str) == 1  # Treated as single constraint

class TestAddConstraintCountColumn:
    """Tests for the add_constraint_count_column function."""

    def test_missing_column_raises(self):
        df = pd.DataFrame({"id": [1, 2]})
        with pytest.raises(ValueError, match="must contain 'progressive_constraints'"):
            add_constraint_count_column(df)

    def test_adds_column_correctly(self):
        data = {
            "id": [1, 2, 3],
            "progressive_constraints": [
                ["c1", "c2"],
                '["c3", "c4", "c5"]',
                None
            ]
        }
        df = pd.DataFrame(data)
        result = add_constraint_count_column(df)

        assert "constraint_count" in result.columns
        assert result["constraint_count"].tolist() == [2, 3, 0]

    def test_mixed_types(self):
        data = {
            "task_id": ["A", "B", "C"],
            "progressive_constraints": [
                ["step1", "step2", "step3"],
                "['a', 'b']",
                "single constraint string"
            ]
        }
        df = pd.DataFrame(data)
        result = add_constraint_count_column(df)

        assert result["constraint_count"].tolist() == [3, 2, 1]