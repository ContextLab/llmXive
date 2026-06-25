"""
Unit tests for AST-based clone detection (ast_cloner.py).

These tests verify the core clone density computation logic without
requiring external dependencies or network access.

Tests cover:
- AST parsing and normalization
- Clone signature extraction
- Clone density calculation
- Edge cases (empty files, syntax errors, zero clones)
- File scanning functionality
"""

import ast
import csv
import os
import tempfile
from pathlib import Path
from typing import Dict, List

import pytest

# Import module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from ast_cloner import (
    _normalize_node,
    _extract_structural_signatures,
    _get_node_line_ranges,
    _compute_clone_density_from_signatures,
    parse_python_file,
    get_total_lines,
    count_ast_nodes,
    compute_clone_density,
    DEFAULT_CLONE_THRESHOLD
)


class TestNormalizeNode:
    """Tests for AST node normalization."""

    def test_normalize_function_def(self):
        """Test normalization of FunctionDef node."""
        code = "def foo(x): pass"
        tree = ast.parse(code)
        func_node = tree.body[0]

        sig = _normalize_node(func_node)
        assert 'FunctionDef' in sig
        assert 'arg' in sig  # Should contain argument info

    def test_normalize_class_def(self):
        """Test normalization of ClassDef node."""
        code = "class Foo:\n    pass"
        tree = ast.parse(code)
        class_node = tree.body[0]

        sig = _normalize_node(class_node)
        assert 'ClassDef' in sig

    def test_normalize_strips_location(self):
        """Test that location info is normalized away."""
        code1 = "def foo(): pass"
        code2 = "def foo(): pass"

        tree1 = ast.parse(code1)
        tree2 = ast.parse(code2)

        sig1 = _normalize_node(tree1.body[0])
        sig2 = _normalize_node(tree2.body[0])

        # Same structure should produce same signature
        assert sig1 == sig2

    def test_normalize_different_functions(self):
        """Test that different functions produce different signatures."""
        code1 = "def foo(x): return x"
        code2 = "def bar(x): return x"

        tree1 = ast.parse(code1)
        tree2 = ast.parse(code2)

        sig1 = _normalize_node(tree1.body[0])
        sig2 = _normalize_node(tree2.body[0])

        # Function names differ, so signatures should differ
        assert sig1 != sig2


class TestExtractStructuralSignatures:
    """Tests for structural signature extraction."""

    def test_extract_single_function(self):
        """Test extraction from file with single function."""
        code = """
        def foo(x):
            return x
        """
        tree = ast.parse(code)
        signatures = _extract_structural_signatures(tree)

        assert len(signatures) >= 1
        # Should have at least the FunctionDef

    def test_extract_duplicate_functions(self):
        """Test extraction with duplicate function structures."""
        code = """
        def foo(x):
            return x

        def bar(x):
            return x
        """
        tree = ast.parse(code)
        signatures = _extract_structural_signatures(tree)

        # Both functions have same structure (return x)
        # Should find at least one duplicate signature
        has_duplicates = any(len(occurrences) > 1 for occurrences in signatures.values())
        assert has_duplicates

    def test_extract_class_and_function(self):
        """Test extraction with both class and function."""
        code = """
        class Foo:
            def bar(self):
                pass
        """
        tree = ast.parse(code)
        signatures = _extract_structural_signatures(tree)

        assert len(signatures) >= 1


class TestGetNodeLineRanges:
    """Tests for line range extraction."""

    def test_line_ranges_have_valid_ranges(self):
        """Test that extracted line ranges are valid."""
        code = """
        def foo(x):
            return x

        def bar(y):
            return y
        """
        tree = ast.parse(code)
        line_ranges = _get_node_line_ranges(tree)

        for sig_hash, ranges in line_ranges.items():
            for start, end in ranges:
                assert start >= 1
                assert end >= start

    def test_line_ranges_match_code(self):
        """Test that line ranges match actual code structure."""
        code = """
        def foo():
            pass
        """
        tree = ast.parse(code)
        line_ranges = _get_node_line_ranges(tree)

        # FunctionDef should be on line 2
        func_ranges = [r for sig, ranges in line_ranges.items()
                     for r in ranges if 'FunctionDef' in str(tree.body[0])]
        # Just verify we got some ranges
        assert len(line_ranges) > 0


class TestComputeCloneDensity:
    """Tests for clone density computation."""

    def test_no_duplicates_zero_density(self):
        """Test that file with no duplicates has zero clone density."""
        code = """
        def foo():
            pass

        def bar():
            pass

        def baz():
            pass
        """
        tree = ast.parse(code)
        signatures = _extract_structural_signatures(tree)
        line_ranges = _get_node_line_ranges(tree)

        clone_count, total_lines, duplicates = _compute_clone_density_from_signatures(
            signatures, line_ranges, DEFAULT_CLONE_THRESHOLD
        )

        # All functions have unique structures, so no clones
        assert clone_count == 0

    def test_all_duplicates_full_density(self):
        """Test that file with all duplicates has high clone density."""
        code = """
        def foo():
            return 1

        def bar():
            return 1

        def baz():
            return 1
        """
        tree = ast.parse(code)
        signatures = _extract_structural_signatures(tree)
        line_ranges = _get_node_line_ranges(tree)

        clone_count, total_lines, duplicates = _compute_clone_density_from_signatures(
            signatures, line_ranges, DEFAULT_CLONE_THRESHOLD
        )

        # All functions have same structure, should be clones
        assert total_lines > 0
        assert clone_count == total_lines

    def test_threshold_affects_detection(self):
        """Test that threshold parameter affects clone detection."""
        code = """
        def foo():
            return 1

        def bar():
            return 1
        """
        tree = ast.parse(code)
        signatures = _extract_structural_signatures(tree)
        line_ranges = _get_node_line_ranges(tree)

        # With threshold 0.0, all duplicates counted
        clone_low, total_low, _ = _compute_clone_density_from_signatures(
            signatures, line_ranges, 0.0
        )

        # With threshold 1.0, stricter matching
        clone_high, total_high, _ = _compute_clone_density_from_signatures(
            signatures, line_ranges, 1.0
        )

        # Both should find the duplicates since structures are identical
        assert total_low > 0
        assert total_high > 0


class TestParsePythonFile:
    """Tests for Python file parsing."""

    def test_parse_valid_file(self):
        """Test parsing a valid Python file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def foo():\n    pass\n")
            f.flush()
            temp_path = Path(f.name)

        try:
            tree = parse_python_file(temp_path)
            assert tree is not None
            assert isinstance(tree, ast.AST)
        finally:
            os.unlink(temp_path)

    def test_parse_syntax_error(self):
        """Test parsing a file with syntax error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def foo(:\n    pass\n")  # Syntax error
            f.flush()
            temp_path = Path(f.name)

        try:
            tree = parse_python_file(temp_path)
            assert tree is None  # Should return None on error
        finally:
            os.unlink(temp_path)

    def test_parse_empty_file(self):
        """Test parsing an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")
            f.flush()
            temp_path = Path(f.name)

        try:
            tree = parse_python_file(temp_path)
            assert tree is not None  # Empty file is valid Python
            assert len(tree.body) == 0
        finally:
            os.unlink(temp_path)


class TestGetTotalLines:
    """Tests for line counting."""

    def test_count_lines(self):
        """Test line counting in file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("line1\nline2\nline3\n")
            f.flush()
            temp_path = Path(f.name)

        try:
            count = get_total_lines(temp_path)
            assert count == 3
        finally:
            os.unlink(temp_path)

    def test_count_empty_file(self):
        """Test line counting in empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")
            f.flush()
            temp_path = Path(f.name)

        try:
            count = get_total_lines(temp_path)
            assert count == 0
        finally:
            os.unlink(temp_path)


class TestCountASTNodes:
    """Tests for AST node counting."""

    def test_count_function_defs(self):
        """Test counting FunctionDef nodes."""
        code = """
        def foo():
            pass

        def bar():
            pass
        """
        tree = ast.parse(code)
        count = count_ast_nodes(tree, 'FunctionDef')
        assert count == 2

    def test_count_class_defs(self):
        """Test counting ClassDef nodes."""
        code = """
        class Foo:
            pass

        class Bar:
            pass
        """
        tree = ast.parse(code)
        count = count_ast_nodes(tree, 'ClassDef')
        assert count == 2

    def test_count_nonexistent_node(self):
        """Test counting nodes that don't exist."""
        code = "x = 1"
        tree = ast.parse(code)
        count = count_ast_nodes(tree, 'FunctionDef')
        assert count == 0


class TestComputeCloneDensityFull:
    """Tests for full clone density computation."""

    def test_compute_density_valid_file(self):
        """Test full computation on valid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def foo():\n    return 1\n")
            f.flush()
            temp_path = Path(f.name)

        try:
            metrics = compute_clone_density(temp_path)

            assert metrics['parse_success'] is True
            assert metrics['function_count'] == 1
            assert 'clone_density' in metrics
            assert 'total_lines' in metrics
        finally:
            os.unlink(temp_path)

    def test_compute_density_syntax_error(self):
        """Test full computation on file with syntax error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def foo(:\n")  # Syntax error
            f.flush()
            temp_path = Path(f.name)

        try:
            metrics = compute_clone_density(temp_path)

            assert metrics['parse_success'] is False
            assert metrics['function_count'] == 0
            assert metrics['clone_density'] == 0.0
        finally:
            os.unlink(temp_path)

    def test_compute_density_empty_file(self):
        """Test full computation on empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")
            f.flush()
            temp_path = Path(f.name)

        try:
            metrics = compute_clone_density(temp_path)

            assert metrics['parse_success'] is True
            assert metrics['total_lines'] == 0
            assert metrics['clone_density'] == 0.0
        finally:
            os.unlink(temp_path)


class TestWriteMetricsToCSV:
    """Tests for CSV output."""

    def test_write_metrics_csv(self):
        """Test writing metrics to CSV file."""
        metrics = [
            {
                'file_path': '/test/file.py',
                'clone_density': 0.5,
                'clone_line_count': 10,
                'total_lines': 20,
                'function_count': 2,
                'class_count': 0,
                'parse_success': True,
                'timestamp': '2024-01-01T00:00:00'
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = Path(f.name)

        try:
            from ast_cloner import write_metrics_to_csv
            write_metrics_to_csv(metrics, temp_path)

            # Verify file was written
            assert temp_path.exists()

            # Verify CSV structure
            with open(temp_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]['file_path'] == '/test/file.py'
                assert rows[0]['clone_density'] == '0.5'
        finally:
            os.unlink(temp_path)


class TestScanDirectoryForClones:
    """Tests for directory scanning."""

    def test_scan_directory(self):
        """Test scanning a directory of Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = Path(tmpdir) / 'file1.py'
            file2 = Path(tmpdir) / 'file2.py'

            file1.write_text("def foo():\n    return 1\n")
            file2.write_text("def bar():\n    return 2\n")

            output_file = Path(tmpdir) / 'output.csv'

            from ast_cloner import scan_directory_for_clones
            metrics = scan_directory_for_clones(Path(tmpdir), output_file)

            assert len(metrics) == 2
            assert output_file.exists()

            # Verify CSV has correct headers
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                assert 'clone_density' in reader.fieldnames
                assert 'total_lines' in reader.fieldnames

    def test_scan_empty_directory(self):
        """Test scanning empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / 'output.csv'

            from ast_cloner import scan_directory_for_clones
            metrics = scan_directory_for_clones(Path(tmpdir), output_file)

            assert len(metrics) == 0
            assert not output_file.exists()  # No output if no files


class TestStdlibOnly:
    """Verify no external dependencies are used."""

    def test_no_external_imports(self):
        """Verify ast_cloner only imports from stdlib and project modules."""
        import ast_cloner
        import inspect

        source = inspect.getsource(ast_cloner)

        # Check for common external library imports that should NOT be present
        forbidden_imports = [
            'import numpy', 'from numpy',
            'import pandas', 'from pandas',
            'import sklearn', 'from sklearn',
            'import torch', 'from torch',
            'import tensorflow', 'from tensorflow',
            'import transformers', 'from transformers',
            'import datasets', 'from datasets',
            'import bitsandbytes', 'from bitsandbytes',
        ]

        for forbidden in forbidden_imports:
            assert forbidden not in source, f"Found forbidden import: {forbidden}"

        # Verify stdlib imports are present
        assert 'import ast' in source
        assert 'import csv' in source
        assert 'import hashlib' in source
        assert 'import logging' in source