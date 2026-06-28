"""
Unit tests for AST clone detection module.

Tests syntax-error handling in Python files as specified in T012.
Must be written before implementation code and verified to fail initially.
"""
import ast
import csv
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
from code.ast_cloner import (
    parse_python_file,
    extract_function_nodes,
    extract_class_nodes,
    compute_node_hash,
    compute_clone_density,
    compute_clone_density_batch,
    save_clone_metrics,
)


class TestSyntaxErrorHandling:
    """Tests for syntax-error handling in Python files."""

    def test_parse_valid_python_file(self, tmp_path):
        """Test that valid Python files parse successfully."""
        # Create a valid Python file
        valid_code = """
        def hello():
            print("Hello, world!")

        class MyClass:
            pass
        """
        test_file = tmp_path / "valid.py"
        test_file.write_text(valid_code)

        # Parse should succeed
        tree = parse_python_file(test_file)
        assert tree is not None
        assert isinstance(tree, ast.AST)

    def test_parse_syntax_error_file(self, tmp_path):
        """Test that syntax errors are handled gracefully."""
        # Create a file with syntax error (missing colon)
        invalid_code = """
        def broken_function()
            print("Missing colon above")
        """
        test_file = tmp_path / "invalid.py"
        test_file.write_text(invalid_code)

        # Parse should return None, not raise exception
        tree = parse_python_file(test_file)
        assert tree is None

    def test_parse_empty_file(self, tmp_path):
        """Test that empty files are handled."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")

        tree = parse_python_file(test_file)
        assert tree is not None  # Empty file is valid Python
        assert len(list(ast.walk(tree))) > 0

    def test_parse_nonexistent_file(self, tmp_path):
        """Test that non-existent files are handled."""
        test_file = tmp_path / "nonexistent.py"

        tree = parse_python_file(test_file)
        assert tree is None

    def test_parse_file_with_unclosed_string(self, tmp_path):
        """Test handling of unclosed string literals."""
        invalid_code = """
        x = "This string is not closed
        """
        test_file = tmp_path / "unclosed_string.py"
        test_file.write_text(invalid_code)

        tree = parse_python_file(test_file)
        assert tree is None

    def test_parse_file_with_invalid_indentation(self, tmp_path):
        """Test handling of invalid indentation (IndentationError)."""
        invalid_code = """
        def func():
            print("Good indent")
        print("Bad indent - should be indented")
        """
        test_file = tmp_path / "bad_indent.py"
        test_file.write_text(invalid_code)

        tree = parse_python_file(test_file)
        assert tree is None

    def test_parse_file_with_tab_mixed_with_spaces(self, tmp_path):
        """Test handling of mixed tabs and spaces."""
        invalid_code = "def func():\n\tprint('tab')\n    print('spaces')"
        test_file = tmp_path / "mixed_indent.py"
        test_file.write_text(invalid_code)

        tree = parse_python_file(test_file)
        # This may or may not parse depending on Python version
        # but should not crash
        assert tree is None or isinstance(tree, ast.AST)

    def test_parse_file_with_unicode_error(self, tmp_path):
        """Test handling of files that can't be decoded as UTF-8."""
        # Create a file with invalid UTF-8 bytes
        test_file = tmp_path / "unicode_error.py"
        # Write invalid UTF-8 sequence
        test_file.write_bytes(b'\xff\xfe invalid utf-8')

        tree = parse_python_file(test_file)
        # Should handle gracefully, not crash
        assert tree is None

    @patch('code.ast_cloner.log_parse_failure')
    def test_syntax_error_is_logged(self, mock_log, tmp_path):
        """Test that syntax errors trigger log_parse_failure calls."""
        invalid_code = """
        def broken()
            pass
        """
        test_file = tmp_path / "logged_error.py"
        test_file.write_text(invalid_code)

        tree = parse_python_file(test_file)
        assert tree is None
        mock_log.assert_called_once()

        # Verify log_parse_failure was called with correct parameters
        call_args = mock_log.call_args
        assert call_args[1]['error_type'] == 'SyntaxError'
        assert 'logged_error.py' in call_args[1]['file_path']

    @patch('code.ast_cloner.log_parse_failure')
    def test_non_syntax_parse_error_is_logged(self, mock_log, tmp_path):
        """Test that non-syntax parse errors are also logged."""
        test_file = tmp_path / "nonexistent.py"
        # Don't create the file

        tree = parse_python_file(test_file)
        assert tree is None
        # Should have logged the failure
        mock_log.assert_called()


class TestNodeExtraction:
    """Tests for AST node extraction."""

    def test_extract_function_nodes(self, tmp_path):
        """Test extraction of function definitions."""
        code = """
        def func1():
            pass

        def func2(x, y):
            return x + y

        class MyClass:
            def method(self):
                pass
        """
        test_file = tmp_path / "funcs.py"
        test_file.write_text(code)

        tree = parse_python_file(test_file)
        assert tree is not None

        functions = extract_function_nodes(tree)
        assert len(functions) == 3  # func1, func2, method

    def test_extract_class_nodes(self, tmp_path):
        """Test extraction of class definitions."""
        code = """
        class MyClass:
            pass

        class AnotherClass:
            def method(self):
                pass
        """
        test_file = tmp_path / "classes.py"
        test_file.write_text(code)

        tree = parse_python_file(test_file)
        assert tree is not None

        classes = extract_class_nodes(tree)
        assert len(classes) == 2


class TestCloneDensityComputation:
    """Tests for clone density computation."""

    def test_compute_clone_density_valid_file(self, tmp_path):
        """Test clone density computation on valid file."""
        code = """
        def hello():
            print("Hello")

        def hello2():
            print("Hello")
        """
        test_file = tmp_path / "clone.py"
        test_file.write_text(code)

        result = compute_clone_density(test_file)

        assert result['file_path'] == str(test_file)
        assert result['parse_error'] is False
        assert result['clone_density'] >= 0.0
        assert result['total_nodes'] > 0

    def test_compute_clone_density_syntax_error_file(self, tmp_path):
        """Test clone density computation on file with syntax error."""
        invalid_code = """
        def broken()
            pass
        """
        test_file = tmp_path / "broken.py"
        test_file.write_text(invalid_code)

        result = compute_clone_density(test_file)

        assert result['file_path'] == str(test_file)
        assert result['parse_error'] is True
        assert result['clone_density'] is None
        assert result['total_nodes'] == 0

    def test_compute_clone_density_empty_file(self, tmp_path):
        """Test clone density computation on empty file."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")

        result = compute_clone_density(test_file)

        assert result['file_path'] == str(test_file)
        assert result['parse_error'] is False
        assert result['clone_density'] == 0.0
        assert result['total_nodes'] == 0

    def test_compute_clone_density_batch(self, tmp_path):
        """Test batch clone density computation."""
        # Create multiple files
        files = []
        for i in range(3):
            test_file = tmp_path / f"file{i}.py"
            test_file.write_text(f"def func{i}():\n    pass\n")
            files.append(test_file)

        results = compute_clone_density_batch(files)

        assert len(results) == 3
        for result in results:
            assert result['parse_error'] is False
            assert result['clone_density'] >= 0.0


class TestSaveCloneMetrics:
    """Tests for saving clone metrics to CSV."""

    def test_save_clone_metrics_creates_csv(self, tmp_path):
        """Test that save_clone_metrics creates a valid CSV file."""
        metrics = [
            {
                'file_path': '/test/file1.py',
                'clone_density': 0.5,
                'total_nodes': 10,
                'duplicate_nodes': 5,
                'parse_error': False,
                'timestamp': '2024-01-01T00:00:00'
            },
            {
                'file_path': '/test/file2.py',
                'clone_density': 0.0,
                'total_nodes': 5,
                'duplicate_nodes': 0,
                'parse_error': False,
                'timestamp': '2024-01-01T00:00:00'
            }
        ]

        output_path = tmp_path / "output.csv"
        save_clone_metrics(metrics, output_path)

        assert output_path.exists()

        # Verify CSV content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]['file_path'] == '/test/file1.py'
        assert rows[0]['clone_density'] == '0.5'
        assert rows[1]['parse_error'] == 'False'

    def test_save_clone_metrics_creates_parent_directories(self, tmp_path):
        """Test that save_clone_metrics creates parent directories."""
        metrics = [
            {
                'file_path': '/test/file.py',
                'clone_density': 0.0,
                'total_nodes': 0,
                'duplicate_nodes': 0,
                'parse_error': False,
                'timestamp': '2024-01-01T00:00:00'
            }
        ]

        output_path = tmp_path / "subdir" / "nested" / "output.csv"
        save_clone_metrics(metrics, output_path)

        assert output_path.exists()
        assert output_path.parent.exists()


class TestNodeHashing:
    """Tests for node hashing."""

    def test_compute_node_hash_function(self):
        """Test hashing of function nodes."""
        func_node = ast.FunctionDef(
            name='test_func',
            args=ast.arguments(
                args=[],
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[]
            ),
            body=[],
            decorator_list=[]
        )

        hash1 = compute_node_hash(func_node)
        assert isinstance(hash1, str)
        assert len(hash1) == 8

    def test_compute_node_hash_different_functions(self):
        """Test that different functions have different hashes."""
        func1 = ast.FunctionDef(
            name='func1',
            args=ast.arguments(args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
            body=[],
            decorator_list=[]
        )
        func2 = ast.FunctionDef(
            name='func2',
            args=ast.arguments(args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
            body=[],
            decorator_list=[]
        )

        hash1 = compute_node_hash(func1)
        hash2 = compute_node_hash(func2)

        assert hash1 != hash2

    def test_compute_node_hash_same_functions(self):
        """Test that same functions have same hashes."""
        func = ast.FunctionDef(
            name='same_func',
            args=ast.arguments(args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
            body=[],
            decorator_list=[]
        )

        hash1 = compute_node_hash(func)
        hash2 = compute_node_hash(func)

        assert hash1 == hash2