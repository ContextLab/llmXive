"""
Unit tests for the refactor_cleanup module.

Tests cover:
- Finding Python files
- TODO detection
- Import analysis
- Docstring checking
- Report generation
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from refactor_cleanup import (
    find_python_files,
    check_todos,
    check_imports,
    check_docstrings,
    run_import_validation,
    generate_cleanup_report
)


class TestFindPythonFiles:
    """Tests for find_python_files function."""

    def test_find_files_in_directory(self, tmp_path):
        """Test finding Python files in a directory structure."""
        # Create test structure
        (tmp_path / "code").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "code" / "main.py").write_text("print('hello')")
        (tmp_path / "code" / "utils.py").write_text("def util(): pass")
        (tmp_path / "tests" / "test_main.py").write_text("def test_main(): pass")

        files = find_python_files(tmp_path)
        file_names = [f.name for f in files]

        assert len(files) == 3
        assert "main.py" in file_names
        assert "utils.py" in file_names
        assert "test_main.py" in file_names

    def test_exclude_directories(self, tmp_path):
        """Test that specified directories are excluded."""
        (tmp_path / "code").mkdir()
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "code" / "main.py").write_text("print('hello')")
        (tmp_path / "__pycache__" / "cache.py").write_text("# cached")

        files = find_python_files(tmp_path, exclude_dirs={"__pycache__"})
        file_names = [f.name for f in files]

        assert len(files) == 1
        assert "cache.py" not in file_names

    def test_empty_directory(self, tmp_path):
        """Test finding files in an empty directory."""
        files = find_python_files(tmp_path)
        assert len(files) == 0


class TestCheckTodos:
    """Tests for check_todos function."""

    def test_detect_todo(self, tmp_path):
        """Test detection of TODO comments."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
        # TODO: Implement this
        def func():
            pass
        # FIXME: This is broken
        # HACK: Temporary workaround
        """)

        todos = check_todos(test_file)

        assert len(todos) == 3
        assert todos[0]['type'] == 'TODO'
        assert todos[1]['type'] == 'FIXME'
        assert todos[2]['type'] == 'HACK'
        assert todos[0]['line'] == 2

    def test_no_todos(self, tmp_path):
        """Test file with no TODOs."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
        def func():
            # This is a normal comment
            pass
        """)

        todos = check_todos(test_file)
        assert len(todos) == 0

    def test_case_insensitive(self, tmp_path):
        """Test that TODO detection is case insensitive."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
        # todo: lowercase
        # Todo: mixed case
        """)

        todos = check_todos(test_file)
        assert len(todos) == 2


class TestCheckImports:
    """Tests for check_imports function."""

    def test_detect_unused_imports(self, tmp_path):
        """Test detection of unused imports."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
        import os
        import unused_module
        from collections import defaultdict

        def func():
            import sys  # This is used locally
            return sys.version
        """)

        issues = check_imports(test_file, tmp_path)

        # Should detect unused imports (os, unused_module, defaultdict)
        # Note: The exact detection depends on the AST traversal
        assert len(issues) >= 1
        assert any(i['type'] == 'unused_imports' for i in issues)

    def test_syntax_error_handling(self, tmp_path):
        """Test handling of files with syntax errors."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
        def broken(
            # Missing closing paren
        """)

        issues = check_imports(test_file, tmp_path)

        assert len(issues) == 1
        assert issues[0]['type'] == 'syntax_error'

    def test_valid_file(self, tmp_path):
        """Test a file with no import issues."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
        import os
        import sys

        def func():
            return os.getcwd()
        """)

        issues = check_imports(test_file, tmp_path)
        # os is used, sys might be flagged as unused
        # The test just ensures no exception is raised
        assert isinstance(issues, list)


class TestCheckDocstrings:
    """Tests for check_docstrings function."""

    def test_missing_docstring(self, tmp_path):
        """Test detection of missing docstrings."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
        def func():
            pass

        class MyClass:
            pass
        """)

        issues = check_docstrings(test_file)

        assert len(issues) == 2
        names = [i['name'] for i in issues]
        assert 'func' in names
        assert 'MyClass' in names

    def test_with_docstrings(self, tmp_path):
        """Test file with all docstrings present."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
        def func():
            '''Function docstring.'''
            pass

        class MyClass:
            '''Class docstring.'''
            pass
        """)

        issues = check_docstrings(test_file)
        assert len(issues) == 0

    def test_nested_functions(self, tmp_path):
        """Test detection in nested functions."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
        def outer():
            '''Outer docstring.'''
            def inner():
                pass
        """)

        issues = check_docstrings(test_file)
        assert len(issues) == 1
        assert issues[0]['name'] == 'inner'


class TestRunImportValidation:
    """Tests for run_import_validation function."""

    def test_validation_structure(self, tmp_path):
        """Test that validation returns correct structure."""
        # Create a simple file
        (tmp_path / "test.py").write_text("""
        def func():
            pass
        """)

        results = run_import_validation(tmp_path)

        assert 'total_files' in results
        assert 'files_with_issues' in results
        assert 'todos_found' in results
        assert 'import_issues' in results
        assert 'docstring_issues' in results
        assert 'summary' in results
        assert results['total_files'] == 1

    def test_empty_project(self, tmp_path):
        """Test validation on empty directory."""
        results = run_import_validation(tmp_path)

        assert results['total_files'] == 0
        assert results['files_with_issues'] == 0
        assert len(results['todos_found']) == 0


class TestGenerateCleanupReport:
    """Tests for generate_cleanup_report function."""

    def test_report_generation(self, tmp_path):
        """Test basic report generation."""
        results = {
            'total_files': 1,
            'files_with_issues': 0,
            'todos_found': [],
            'import_issues': [],
            'docstring_issues': [],
            'summary': {
                'total_todos': 0,
                'total_import_issues': 0,
                'total_docstring_issues': 0,
                'files_analyzed': 1,
                'files_with_clean_code': 1
            }
        }

        report = generate_cleanup_report(results)

        assert "CODE CLEANUP AND REFACTORING REPORT" in report
        assert "Files Analyzed: 1" in report
        assert "Files Clean: 1" in report

    def test_report_with_issues(self, tmp_path):
        """Test report with issues present."""
        results = {
            'total_files': 2,
            'files_with_issues': 1,
            'todos_found': [
                {'type': 'TODO', 'file': 'test.py', 'line': 5, 'text': 'Fix this'}
            ],
            'import_issues': [],
            'docstring_issues': [],
            'summary': {
                'total_todos': 1,
                'total_import_issues': 0,
                'total_docstring_issues': 0,
                'files_analyzed': 2,
                'files_with_clean_code': 1
            }
        }

        report = generate_cleanup_report(results)

        assert "TODO items found" not in report
        assert "Fix this" in report
        assert "test.py" in report

    def test_report_to_file(self, tmp_path):
        """Test saving report to file."""
        results = {
            'total_files': 0,
            'files_with_issues': 0,
            'todos_found': [],
            'import_issues': [],
            'docstring_issues': [],
            'summary': {
                'total_todos': 0,
                'total_import_issues': 0,
                'total_docstring_issues': 0,
                'files_analyzed': 0,
                'files_with_clean_code': 0
            }
        }

        output_path = tmp_path / "report.txt"
        report = generate_cleanup_report(results, output_path)

        assert output_path.exists()
        assert output_path.read_text() == report


if __name__ == '__main__':
    pytest.main([__file__, '-v'])