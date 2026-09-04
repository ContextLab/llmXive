"""
Unit tests for the syntax validation module.
"""
import pytest
import pandas as pd
import tempfile
import json
from pathlib import Path
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.feature_extraction.syntax_validator import (
    validate_snippet_syntax,
    validate_dataset,
    main
)

class TestValidateSnippetSyntax:
    """Tests for the validate_snippet_syntax function."""

    def test_valid_simple_code(self):
        """Test valid simple Python code."""
        code = "x = 1"
        is_valid, error = validate_snippet_syntax(code)
        assert is_valid is True
        assert error is None

    def test_valid_function_definition(self):
        """Test valid function definition."""
        code = """
        def hello_world():
            print("Hello, World!")
        """
        is_valid, error = validate_snippet_syntax(code)
        assert is_valid is True
        assert error is None

    def test_valid_class_definition(self):
        """Test valid class definition."""
        code = """
        class MyClass:
            def __init__(self):
                self.value = 0
        """
        is_valid, error = validate_snippet_syntax(code)
        assert is_valid is True
        assert error is None

    def test_invalid_syntax_missing_colon(self):
        """Test invalid syntax - missing colon."""
        code = "def hello_world()"
        is_valid, error = validate_snippet_syntax(code)
        assert is_valid is False
        assert error is not None
        assert "SyntaxError" in error

    def test_invalid_syntax_unclosed_parenthesis(self):
        """Test invalid syntax - unclosed parenthesis."""
        code = "x = (1 + 2"
        is_valid, error = validate_snippet_syntax(code)
        assert is_valid is False
        assert error is not None
        assert "SyntaxError" in error

    def test_empty_string(self):
        """Test empty string input."""
        is_valid, error = validate_snippet_syntax("")
        assert is_valid is False
        assert error is not None

    def test_none_input(self):
        """Test None input."""
        is_valid, error = validate_snippet_syntax(None)
        assert is_valid is False
        assert error is not None

    def test_valid_complex_code(self):
        """Test valid complex code with multiple statements."""
        code = """
        import os
        import sys

        def calculate_sum(numbers):
            total = 0
            for num in numbers:
                total += num
            return total

        if __name__ == '__main__':
            result = calculate_sum([1, 2, 3, 4, 5])
            print(f"Sum: {result}")
        """
        is_valid, error = validate_snippet_syntax(code)
        assert is_valid is True
        assert error is None

class TestValidateDataset:
    """Tests for the validate_dataset function."""

    def test_all_valid_snippets(self):
        """Test dataset with all valid snippets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.parquet"
            output_path = Path(temp_dir) / "output.json"

            # Create test dataset
            data = {
                'code_snippet': [
                    "x = 1",
                    "def foo(): pass",
                    "class Bar: pass"
                ]
            }
            df = pd.DataFrame(data)
            df.to_parquet(input_path)

            # Run validation
            report = validate_dataset(
                input_path=str(input_path),
                output_path=str(output_path),
                code_column='code_snippet',
                success_threshold=0.95
            )

            assert report['total_snippets'] == 3
            assert report['valid_snippets'] == 3
            assert report['invalid_snippets'] == 0
            assert report['success_rate'] == 1.0
            assert report['meets_threshold'] is True

            # Check output file exists
            assert output_path.exists()
            with open(output_path, 'r') as f:
                saved_report = json.load(f)
            assert saved_report['success_rate'] == 1.0

    def test_mixed_snippets_above_threshold(self):
        """Test dataset with mixed valid/invalid snippets (above threshold)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.parquet"
            output_path = Path(temp_dir) / "output.json"

            # Create test dataset: 19 valid, 1 invalid = 95% success rate
            valid_snippets = ["x = " + str(i) for i in range(19)]
            invalid_snippets = ["def broken"]  # Missing colon
            all_snippets = valid_snippets + invalid_snippets

            data = {'code_snippet': all_snippets}
            df = pd.DataFrame(data)
            df.to_parquet(input_path)

            # Run validation
            report = validate_dataset(
                input_path=str(input_path),
                output_path=str(output_path),
                code_column='code_snippet',
                success_threshold=0.95
            )

            assert report['total_snippets'] == 20
            assert report['valid_snippets'] == 19
            assert report['invalid_snippets'] == 1
            assert abs(report['success_rate'] - 0.95) < 0.001
            assert report['meets_threshold'] is True

    def test_mixed_snippets_below_threshold(self):
        """Test dataset with mixed valid/invalid snippets (below threshold)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.parquet"
            output_path = Path(temp_dir) / "output.json"

            # Create test dataset: 9 valid, 11 invalid = 45% success rate
            valid_snippets = ["x = " + str(i) for i in range(9)]
            invalid_snippets = ["def broken"] * 11
            all_snippets = valid_snippets + invalid_snippets

            data = {'code_snippet': all_snippets}
            df = pd.DataFrame(data)
            df.to_parquet(input_path)

            # Should raise ValueError
            with pytest.raises(ValueError) as exc_info:
                validate_dataset(
                    input_path=str(input_path),
                    output_path=str(output_path),
                    code_column='code_snippet',
                    success_threshold=0.95
                )

            assert "Validation failed" in str(exc_info.value)
            assert "0.45" in str(exc_info.value) or "0.4" in str(exc_info.value)

    def test_missing_input_file(self):
        """Test with missing input file."""
        with pytest.raises(FileNotFoundError):
            validate_dataset(
                input_path="/nonexistent/path/input.parquet",
                output_path="/tmp/output.json"
            )

    def test_missing_code_column(self):
        """Test with missing code column."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.parquet"
            output_path = Path(temp_dir) / "output.json"

            # Create dataset with wrong column name
            data = {'wrong_column': ["x = 1"]}
            df = pd.DataFrame(data)
            df.to_parquet(input_path)

            with pytest.raises(ValueError) as exc_info:
                validate_dataset(
                    input_path=str(input_path),
                    output_path=str(output_path),
                    code_column='code_snippet'
                )

            assert "not found in dataset" in str(exc_info.value)

class TestMain:
    """Tests for the main CLI function."""

    def test_main_successful_validation(self, capsys):
        """Test main function with successful validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.parquet"
            output_path = Path(temp_dir) / "output.json"

            # Create test dataset
            data = {'code_snippet': ["x = 1", "y = 2"]}
            df = pd.DataFrame(data)
            df.to_parquet(input_path)

            # Mock sys.argv
            import sys
            original_argv = sys.argv
            sys.argv = [
                'syntax_validator.py',
                '--input', str(input_path),
                '--output', str(output_path),
                '--threshold', '0.95'
            ]

            try:
                main()
            except SystemExit as e:
                assert e.code == 0

            finally:
                sys.argv = original_argv

            # Check output
            captured = capsys.readouterr()
            assert "Validation complete" in captured.out or "Summary" in captured.out
            assert output_path.exists()

    def test_main_file_not_found(self):
        """Test main function with missing input file."""
        import sys
        original_argv = sys.argv
        sys.argv = [
            'syntax_validator.py',
            '--input', '/nonexistent/file.parquet',
            '--output', '/tmp/output.json'
        ]

        try:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
        finally:
            sys.argv = original_argv