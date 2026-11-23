"""
Unit tests for Parameter Coverage Score calculation edge cases.
Specifically targets complex type hints and edge cases in docstring parsing.
"""
import pytest
from unittest.mock import patch
from docstring_parser import parse
from utils.coverage import (
    parse_docstring_parameters,
    calculate_parameter_coverage,
    CoverageException
)
from utils.exceptions import CoverageException as InternalCoverageException


class TestComplexTypeHints:
    """Tests for handling complex type hints in parameter coverage calculation."""

    def test_complex_nested_types_unmatched_but_no_crash(self):
        """
        Test that complex nested types like List[Dict[str, Any]] do not crash
        the parser and are handled gracefully (unmatched but non-crashing).
        """
        # AST params include a complex type hint
        ast_params = [
            {"name": "data", "type": "List[Dict[str, Any]]"},
            {"name": "callback", "type": "Callable[[int], bool]"}
        ]

        # Docstring has simple parameter description without complex type
        docstring_text = """
        Process the data.

        Args:
            data: The input data dictionary.
            callback: A function to call.
        """

        # This should not raise an exception
        try:
            doc_params = parse_docstring_parameters(docstring_text)
            score = calculate_parameter_coverage(ast_params, doc_params)
            
            # Verify we got a valid score (0.0 since types don't match by name/structure logic)
            # or partial match if names match. The key is no crash.
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0
        except Exception as e:
            pytest.fail(f"Complex type hints caused a crash: {e}")

    def test_mixed_complex_and_simple_types(self):
        """
        Test a mix of simple and complex type hints.
        Simple types should match if names align; complex ones might not.
        """
        ast_params = [
            {"name": "x", "type": "int"},
            {"name": "y", "type": "str"},
            {"name": "config", "type": "Dict[str, int]"}
        ]

        docstring_text = """
        Calculate values.

        Args:
            x: An integer value.
            y: A string value.
            config: A configuration dictionary.
        """

        doc_params = parse_docstring_parameters(docstring_text)
        score = calculate_parameter_coverage(ast_params, doc_params)

        # 'x' and 'y' should match. 'config' might match by name if logic is name-based.
        # The critical part is that the complex type 'Dict[str, int]' doesn't break the logic.
        assert isinstance(score, float)
        assert score > 0.0  # At least some parameters should match by name

    def test_missing_type_in_ast(self):
        """
        Test when AST param has no type hint but docstring implies one.
        """
        ast_params = [
            {"name": "value", "type": None},
            {"name": "items", "type": "list"}
        ]

        docstring_text = """
        Process items.

        Args:
            value: The value to process.
            items: A list of items.
        """

        doc_params = parse_docstring_parameters(docstring_text)
        score = calculate_parameter_coverage(ast_params, doc_params)

        assert isinstance(score, float)
        assert score >= 0.0

    def test_empty_ast_params(self):
        """
        Test coverage calculation when there are no AST parameters.
        """
        ast_params = []
        docstring_text = """
        No args function.
        """
        doc_params = parse_docstring_parameters(docstring_text)
        
        # Should handle division by zero or return 1.0 (perfect coverage of nothing)
        # Depending on implementation, usually 1.0 or 0.0. Let's assume 1.0 for empty set.
        score = calculate_parameter_coverage(ast_params, doc_params)
        assert isinstance(score, float)

    def test_empty_docstring_params(self):
        """
        Test coverage calculation when docstring has no parameters.
        """
        ast_params = [
            {"name": "x", "type": "int"}
        ]
        docstring_text = """
        Does something.
        """
        doc_params = parse_docstring_parameters(docstring_text)
        
        score = calculate_parameter_coverage(ast_params, doc_params)
        assert score == 0.0

    def test_complex_generic_types_with_spaces(self):
        """
        Test handling of generic types with extra spaces which might occur in formatting.
        """
        ast_params = [
            {"name": "matrix", "type": "List [ List [ int ] ]"}
        ]

        docstring_text = """
        Matrix operation.

        Args:
            matrix: A nested list of integers.
        """

        doc_params = parse_docstring_parameters(docstring_text)
        score = calculate_parameter_coverage(ast_params, doc_params)
        
        # Should not crash
        assert isinstance(score, float)

    def test_return_type_in_docstring_ignored_for_param_coverage(self):
        """
        Ensure return types in docstring do not interfere with parameter coverage.
        """
        ast_params = [
            {"name": "a", "type": "int"}
        ]

        docstring_text = """
        Add numbers.

        Args:
            a: First number.

        Returns:
            int: The sum.
        """

        doc_params = parse_docstring_parameters(docstring_text)
        score = calculate_parameter_coverage(ast_params, doc_params)
        
        # Should match 'a' correctly
        assert score > 0.0

    def test_kwargs_and_args_handling(self):
        """
        Test handling of *args and **kwargs in AST vs docstring.
        """
        ast_params = [
            {"name": "args", "type": "tuple"},
            {"name": "kwargs", "type": "dict"}
        ]

        docstring_text = """
        Flexible function.

        Args:
            args: Variable length argument list.
            kwargs: Arbitrary keyword arguments.
        """

        doc_params = parse_docstring_parameters(docstring_text)
        score = calculate_parameter_coverage(ast_params, doc_params)
        
        assert isinstance(score, float)