import pytest
import json
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analyze import calculate_parameter_coverage_score, process_results_for_coverage
from code.utils.exceptions import CoverageException

class TestParameterCoverageScore:
    """Unit tests for T033: Parameter Coverage Score calculation."""

    def test_perfect_match(self):
        """Test case where all AST params are in docstring."""
        record = {
            "ast_params": ["a", "b", "c"],
            "generated_docstring": "Args:\n    a: param a\n    b: param b\n    c: param c"
        }
        score = calculate_parameter_coverage_score(record)
        assert score == 1.0, f"Expected 1.0, got {score}"

    def test_partial_match(self):
        """Test case where only some AST params are in docstring."""
        record = {
            "ast_params": ["a", "b", "c"],
            "generated_docstring": "Args:\n    a: param a\n    b: param b"
        }
        score = calculate_parameter_coverage_score(record)
        assert score == pytest.approx(2.0 / 3.0), f"Expected ~0.66, got {score}"

    def test_no_match(self):
        """Test case where no AST params are in docstring."""
        record = {
            "ast_params": ["a", "b", "c"],
            "generated_docstring": "Args:\n    x: param x"
        }
        score = calculate_parameter_coverage_score(record)
        assert score == 0.0, f"Expected 0.0, got {score}"

    def test_empty_docstring(self):
        """Test case with empty or None docstring."""
        record = {
            "ast_params": ["a", "b"],
            "generated_docstring": ""
        }
        score = calculate_parameter_coverage_score(record)
        assert score == 0.0, f"Expected 0.0, got {score}"

        record_none = {
            "ast_params": ["a", "b"],
            "generated_docstring": None
        }
        score_none = calculate_parameter_coverage_score(record_none)
        assert score_none == 0.0, f"Expected 0.0, got {score_none}"

    def test_no_ast_params(self):
        """Test case with no AST parameters (vacuously true)."""
        record = {
            "ast_params": [],
            "generated_docstring": "Args:\n    a: param a"
        }
        score = calculate_parameter_coverage_score(record)
        assert score == 1.0, f"Expected 1.0 for empty params, got {score}"

    def test_complex_type_hints_ignored(self):
        """Test that complex type hints in AST are handled gracefully."""
        # AST might have 'List[Dict[str, Any]]' as a param name if parsing is naive,
        # but usually AST gives the name. The docstring parser handles the text.
        record = {
            "ast_params": ["data", "config"],
            "generated_docstring": "Args:\n    data: List of items\n    config: Dict settings"
        }
        score = calculate_parameter_coverage_score(record)
        assert score == 1.0

    def test_case_sensitivity(self):
        """Test that parameter matching is case-sensitive (standard behavior)."""
        record = {
            "ast_params": ["Data", "Config"],
            "generated_docstring": "Args:\n    data: list\n    config: dict"
        }
        score = calculate_parameter_coverage_score(record)
        # 'Data' != 'data', so 0 matches
        assert score == 0.0

class TestProcessResultsForCoverage:
    """Integration tests for the file processing logic."""

    def test_process_results_creates_output(self, tmp_path):
        """Test that process_results_for_coverage writes the output file."""
        input_data = [
            {
                "ast_params": ["x"],
                "generated_docstring": "Args:\n    x: value"
            },
            {
                "ast_params": ["y", "z"],
                "generated_docstring": "Args:\n    y: val"
            }
        ]
        
        input_file = tmp_path / "results.json"
        output_file = tmp_path / "results_with_scores.json"
        
        with open(input_file, 'w') as f:
            json.dump(input_data, f)
        
        count = process_results_for_coverage(input_file, output_file)
        
        assert count == 2
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            output_data = json.load(f)
        
        assert len(output_data) == 2
        assert output_data[0]['parameter_coverage_score'] == 1.0
        assert output_data[1]['parameter_coverage_score'] == pytest.approx(0.5)

    def test_process_results_handles_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing input."""
        input_file = tmp_path / "nonexistent.json"
        output_file = tmp_path / "output.json"
        
        with pytest.raises(FileNotFoundError):
            process_results_for_coverage(input_file, output_file)

    def test_process_results_handles_malformed_input(self, tmp_path):
        """Test that ValueError is raised if input is not a list."""
        input_file = tmp_path / "results.json"
        output_file = tmp_path / "output.json"
        
        with open(input_file, 'w') as f:
            json.dump({"not": "a list"}, f)
        
        with pytest.raises(ValueError):
            process_results_for_coverage(input_file, output_file)
