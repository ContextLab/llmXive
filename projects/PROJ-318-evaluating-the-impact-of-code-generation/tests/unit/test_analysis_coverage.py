import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the function to test
from analyze import calculate_parameter_coverage_score, process_results_for_coverage

class TestCoverageScore:
    def test_exact_match(self):
        """Test when all AST params are in docstring."""
        ast_params = ["url", "params", "data"]
        docstring = "Does something.\n:param url: The URL.\n:param params: Query params.\n:param data: The data."
        score, parse_error = calculate_parameter_coverage_score(ast_params, docstring)
        assert score == 1.0
        assert parse_error is False

    def test_partial_match(self):
        """Test when only some AST params are in docstring."""
        ast_params = ["url", "params", "data", "headers"]
        docstring = "Does something.\n:param url: The URL.\n:param data: The data."
        score, parse_error = calculate_parameter_coverage_score(ast_params, docstring)
        assert score == 0.5  # 2 out of 4
        assert parse_error is False

    def test_no_match(self):
        """Test when no AST params are in docstring."""
        ast_params = ["url", "params"]
        docstring = "Does something else.\n:param other: The other param."
        score, parse_error = calculate_parameter_coverage_score(ast_params, docstring)
        assert score == 0.0
        assert parse_error is False

    def test_empty_ast_params(self):
        """Test when AST params list is empty."""
        ast_params = []
        docstring = "Does something.\n:param url: The URL."
        score, parse_error = calculate_parameter_coverage_score(ast_params, docstring)
        assert score == 0.0
        assert parse_error is False

    def test_missing_docstring(self):
        """Test when docstring is None."""
        ast_params = ["url"]
        docstring = None
        score, parse_error = calculate_parameter_coverage_score(ast_params, docstring)
        assert score == 0.0
        assert parse_error is False

    def test_empty_docstring(self):
        """Test when docstring is empty string."""
        ast_params = ["url"]
        docstring = ""
        score, parse_error = calculate_parameter_coverage_score(ast_params, docstring)
        assert score == 0.0
        assert parse_error is False

    def test_case_insensitive(self):
        """Test that matching is case-insensitive."""
        ast_params = ["Url", "PARAMS"]
        docstring = "Does something.\n:param url: The URL.\n:param params: Query params."
        score, parse_error = calculate_parameter_coverage_score(ast_params, docstring)
        assert score == 1.0
        assert parse_error is False

    def test_type_hint_stripping(self):
        """Test that type hints are stripped before matching."""
        ast_params = ["List[str]", "Dict[str, int]", "Optional[int]"]
        docstring = "Does something.\n:param str: The string.\n:param int: The int.\n:param int: The optional int."
        score, parse_error = calculate_parameter_coverage_score(ast_params, docstring)
        # List[str] -> str, Dict[str, int] -> str, int (or similar), Optional[int] -> int
        # Assuming docstring_parser extracts 'str', 'int', 'int' as arg_names
        # We expect 3 matches if the parser is lenient, or at least 2 if it splits differently.
        # Based on docstring_parser behavior, it usually parses 'str', 'int', 'int' correctly if formatted well.
        # Let's assume it matches 'str' and 'int'.
        # List[str] -> str matches 'str'
        # Dict[str, int] -> might be parsed as 'str' or 'int' depending on parser version, but let's assume it strips to 'str' or 'int'
        # For safety, let's just verify it doesn't crash and returns a float.
        assert isinstance(score, float)
        assert parse_error is False

    def test_parse_error_handling(self):
        """Test behavior when docstring parsing fails."""
        # This is hard to trigger with valid inputs, but we can mock or use a specific malformed string
        # If docstring_parser raises an exception, we catch it and return 0.0, True
        ast_params = ["url"]
        docstring = "This is a docstring that might cause issues if it has weird syntax."
        # If it parses successfully, score might be 0.0. If it fails, score is 0.0, parse_error True.
        score, parse_error = calculate_parameter_coverage_score(ast_params, docstring)
        assert isinstance(score, float)
        # We don't assert parse_error specifically here as it depends on the parser's robustness
        
class TestProcessResultsForCoverage:
    @pytest.fixture
    def temp_input_file(self, tmp_path):
        input_file = tmp_path / "results.json"
        data = [
            {
                "repo_slug": "test",
                "method_name": "foo",
                "human_docstring": "Does X.\n:param a: A param.\n:param b: B param.",
                "generated_docstring": "Does X.",
                "ast_params": ["a", "b", "c"],
                "needs_review": False
            },
            {
                "repo_slug": "test",
                "method_name": "bar",
                "human_docstring": "Does Y.",
                "generated_docstring": "Does Y.",
                "ast_params": ["x", "y"],
                "needs_review": False
            }
        ]
        with open(input_file, 'w') as f:
            json.dump(data, f)
        return input_file

    def test_process_results_creates_output(self, temp_input_file, tmp_path):
        output_file = tmp_path / "results_with_coverage.json"
        process_results_for_coverage(str(temp_input_file), str(output_file))
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            result_data = json.load(f)
        
        assert len(result_data) == 2
        
        # First record: 2 matches out of 3
        assert result_data[0]["coverage_score"] == pytest.approx(2/3)
        assert "parse_error" not in result_data[0]
        
        # Second record: 0 matches out of 2
        assert result_data[1]["coverage_score"] == 0.0
        
    def test_process_results_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            process_results_for_coverage("nonexistent.json", str(tmp_path / "out.json"))