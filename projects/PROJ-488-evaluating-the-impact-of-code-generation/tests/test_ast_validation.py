"""
Tests for AST Validation Module (T018).
"""
import pytest
import ast
from code.ast_validation import parse_snippet, validate_datasets

class TestParseSnippet:
    def test_valid_python(self):
        code = "def hello():\n    return 'world'"
        assert parse_snippet(code) is True

    def test_valid_python_complex(self):
        code = """
        import os
        def calculate(x, y):
            if x > y:
                return x - y
            else:
                return y - x
        """
        assert parse_snippet(code) is True

    def test_invalid_python_syntax(self):
        code = "def broken(:"
        assert parse_snippet(code) is False

    def test_empty_string(self):
        assert parse_snippet("") is True  # Empty is valid AST (Module with no body)

    def test_invalid_syntax_random(self):
        code = "this is not code @#$%"
        # This might parse as a string or fail depending on context, but usually fails if not valid python
        # Actually "this is not code" is not valid python statement
        assert parse_snippet(code) is False

class TestValidateDatasets:
    def test_all_valid(self):
        data = [
            {"id": "1", "code": "x = 1"},
            {"id": "2", "code": "y = 2"}
        ]
        report, success = validate_datasets(data, [])
        assert report["groups"]["human_written"]["parse_rate"] == 1.0
        assert success is False # Because second group is empty/failed in logic if not handled
        # Note: The logic in validate_datasets checks for empty groups and marks as failed.
        # To test success=True, we need both groups to have data and pass.
    
    def test_mixed_validity(self):
        data_human = [
            {"id": "1", "code": "x = 1"},
            {"id": "2", "code": "def bad("} # Invalid
        ]
        data_llm = [
            {"id": "3", "code": "y = 2"},
            {"id": "4", "code": "z = 3"}
        ]
        report, success = validate_datasets(data_human, data_llm)
        assert report["groups"]["human_written"]["parse_rate"] == 0.5
        assert report["groups"]["llm_generated"]["parse_rate"] == 1.0
        # Success should be False because 0.5 < 0.95
        assert success is False
        
    def test_threshold_met(self):
        # Create 20 items, 19 valid (95%)
        data_human = [{"id": str(i), "code": "x=1"} for i in range(19)] + [{"id": "19", "code": "def bad("}]
        data_llm = [{"id": str(i), "code": "y=2"} for i in range(20)]
        report, success = validate_datasets(data_human, data_llm)
        assert report["groups"]["human_written"]["parse_rate"] == 0.95
        assert success is True
        
    def test_threshold_not_met(self):
        # Create 20 items, 18 valid (90%)
        data_human = [{"id": str(i), "code": "x=1"} for i in range(18)] + [{"id": "18", "code": "def bad("}, {"id": "19", "code": "def bad2("}]
        data_llm = [{"id": str(i), "code": "y=2"} for i in range(20)]
        report, success = validate_datasets(data_human, data_llm)
        assert report["groups"]["human_written"]["parse_rate"] == 0.90
        assert success is False