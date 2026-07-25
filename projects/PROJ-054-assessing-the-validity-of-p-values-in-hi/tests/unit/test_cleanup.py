"""
Unit tests for the code cleanup and refactoring module (T035).

These tests verify that the cleanup process correctly identifies and
fixes common code quality issues without breaking valid code.
"""

import ast
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from cleanup_refactor import (
    analyze_file_for_cleanup,
    refactor_file,
    extract_imports_from_file,
    CodeCleanupError,
    TODO_PATTERN,
    DEBUG_PATTERN,
    DEAD_CODE_PATTERN
)


class TestPatternMatching:
    """Tests for regex pattern matching in cleanup."""

    def test_todo_pattern_matches_todo(self):
        """TODO comments should be detected."""
        assert TODO_PATTERN.search("# TODO: fix this") is not None
        assert TODO_PATTERN.search("# TODO: implement feature") is not None
        assert TODO_PATTERN.search("# FIXME: broken") is not None
        assert TODO_PATTERN.search("# XXX: temporary") is not None

    def test_todo_pattern_ignores_normal_comments(self):
        """Normal comments should not be matched."""
        assert TODO_PATTERN.search("# This is a normal comment") is None
        assert TODO_PATTERN.search("# TODO is just a word") is None

    def test_debug_pattern_matches_print(self):
        """Print statements should be detected."""
        assert DEBUG_PATTERN.search("print('debug')") is not None
        assert DEBUG_PATTERN.search("print(x)") is not None

    def test_debug_pattern_matches_pdb(self):
        """Pdb breakpoints should be detected."""
        assert DEBUG_PATTERN.search("pdb.set_trace()") is not None
        assert DEBUG_PATTERN.search("breakpoint()") is not None

    def test_dead_code_pattern_matches(self):
        """Dead code blocks should be detected."""
        assert DEAD_CODE_PATTERN.search("if False:") is not None
        assert DEAD_CODE_PATTERN.search("if 0:") is not None
        assert DEAD_CODE_PATTERN.search("pass  # dead code") is not None


class TestExtractImports:
    """Tests for import extraction."""

    def test_extract_simple_import(self):
        """Should extract simple import statements."""
        code = "import numpy\nimport pandas as pd"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            filepath = Path(f.name)

        try:
            imports, lines = extract_imports_from_file(filepath)
            assert 'numpy' in imports
            assert 'pandas' in imports
            assert len(imports) == 2
        finally:
            filepath.unlink()

    def test_extract_from_import(self):
        """Should extract from imports."""
        code = "from scipy import stats\nfrom utils.exceptions import AnalysisError"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            filepath = Path(f.name)

        try:
            imports, lines = extract_imports_from_file(filepath)
            assert 'scipy' in imports
            assert 'utils' in imports
        finally:
            filepath.unlink()

    def test_syntax_error_raises(self):
        """Syntax errors should raise CodeCleanupError."""
        code = "def broken("  # Invalid syntax
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            filepath = Path(f.name)

        try:
            with pytest.raises(CodeCleanupError):
                extract_imports_from_file(filepath)
        finally:
            filepath.unlink()


class TestAnalyzeFile:
    """Tests for file analysis."""

    def test_analyze_file_with_todo(self):
        """Files with TODO comments should be flagged."""
        code = """
        # TODO: implement this
        def my_function():
            pass
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            filepath = Path(f.name)

        try:
            logger = MagicMock()
            results = analyze_file_for_cleanup(filepath, logger)

            assert results['lines_analyzed'] > 0
            assert any(issue['type'] == 'todo_comment' for issue in results['issues_found'])
        finally:
            filepath.unlink()

    def test_analyze_file_with_debug(self):
        """Files with debug code should be flagged."""
        code = """
        def my_function():
            print('debug')
            return True
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            filepath = Path(f.name)

        try:
            logger = MagicMock()
            results = analyze_file_for_cleanup(filepath, logger)

            assert any(issue['type'] == 'debug_artifact' for issue in results['issues_found'])
        finally:
            filepath.unlink()

    def test_analyze_non_python_file(self):
        """Non-Python files should be skipped."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Not Python code")
            f.flush()
            filepath = Path(f.name)

        try:
            logger = MagicMock()
            results = analyze_file_for_cleanup(filepath, logger)

            assert results['skipped'] is True
        finally:
            filepath.unlink()


class TestRefactorFile:
    """Tests for file refactoring."""

    def test_refactor_removes_todo(self):
        """TODO comments should be removed."""
        code = """
        # TODO: fix this
        def my_function():
            pass
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            filepath = Path(f.name)

        try:
            logger = MagicMock()
            results = refactor_file(filepath, logger)

            with open(filepath, 'r') as f:
                new_content = f.read()

            assert '# TODO' not in new_content
            assert 'def my_function()' in new_content
        finally:
            filepath.unlink()

    def test_refactor_removes_debug(self):
        """Debug code should be removed."""
        code = """
        def my_function():
            print('debug')
            return True
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            filepath = Path(f.name)

        try:
            logger = MagicMock()
            results = refactor_file(filepath, logger)

            with open(filepath, 'r') as f:
                new_content = f.read()

            assert 'print(' not in new_content
            assert 'def my_function()' in new_content
        finally:
            filepath.unlink()

    def test_refactor_no_changes_needed(self):
        """Files without issues should report no changes."""
        code = """
        def my_function():
            \"\"\"A proper function.\"\"\"
            return True
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            filepath = Path(f.name)

        try:
            logger = MagicMock()
            results = refactor_file(filepath, logger)

            assert results['actions_taken'] == ['No changes needed']
        finally:
            filepath.unlink()

    def test_refactor_handles_syntax_error(self):
        """Syntax errors should be caught and reported."""
        code = "def broken("  # Invalid syntax
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            filepath = Path(f.name)

        try:
            logger = MagicMock()
            results = refactor_file(filepath, logger)

            assert len(results['errors']) > 0
        finally:
            filepath.unlink()


class TestCleanupIntegration:
    """Integration tests for the cleanup process."""

    def test_cleanup_preserves_valid_code(self):
        """Cleanup should not break valid code."""
        code = '''
        """Module docstring."""
        import numpy as np
        from scipy import stats

        def calculate_mean(data):
            """Calculate the mean of data."""
            return np.mean(data)

        if __name__ == '__main__':
            print(calculate_mean([1, 2, 3]))
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            filepath = Path(f.name)

        try:
            logger = MagicMock()
            # Analyze first
            analysis = analyze_file_for_cleanup(filepath, logger)

            # Refactor
            refactor_file(filepath, logger)

            # Verify file is still valid Python
            with open(filepath, 'r') as f:
                new_content = f.read()

            ast.parse(new_content)  # Should not raise

            # Verify key elements preserved
            assert 'import numpy' in new_content
            assert 'def calculate_mean' in new_content
            assert '"""Module docstring."""' in new_content
        finally:
            filepath.unlink()

    def test_cleanup_normalizes_line_endings(self):
        """Cleanup should normalize line endings to Unix style."""
        code = "def test():\r\n    pass\r\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            filepath = Path(f.name)

        try:
            logger = MagicMock()
            refactor_file(filepath, logger)

            with open(filepath, 'r') as f:
                new_content = f.read()

            assert '\r\n' not in new_content
            assert '\n' in new_content
        finally:
            filepath.unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])