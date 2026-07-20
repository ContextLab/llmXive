"""
Unit tests for cleanup_utils module.
These tests verify the code quality analysis functions work correctly.
"""
import pytest
import tempfile
import os
from pathlib import Path
from cleanup_utils import (
    find_python_files,
    check_for_todos,
    check_for_pass_only_functions,
    check_import_groups,
    analyze_code_quality,
    generate_cleanup_report
)

class TestFindPythonFiles:
    def test_find_python_files_in_temp_dir(self):
        """Test finding Python files in a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some Python files
            Path(tmpdir, 'test1.py').touch()
            Path(tmpdir, 'test2.py').touch()
            Path(tmpdir, 'not_python.txt').touch()
            
            # Create a subdirectory with a Python file
            subdir = Path(tmpdir, 'subdir')
            subdir.mkdir()
            Path(subdir, 'test3.py').touch()
            
            files = find_python_files(tmpdir)
            file_names = [f.name for f in files]
            
            assert len(files) == 3
            assert 'test1.py' in file_names
            assert 'test2.py' in file_names
            assert 'test3.py' in file_names
            assert 'not_python.txt' not in file_names

class TestCheckForTodos:
    def test_find_todo_markers(self):
        """Test detection of TODO markers."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
# TODO: Implement this function
def my_function():
    pass

# FIXME: This is broken
def another_function():
    pass

# Regular comment
def third_function():
    pass
""")
            f.flush()
            file_path = Path(f.name)
            
            issues = check_for_todos(file_path)
            
            assert len(issues) == 2
            assert issues[0]['type'] == 'TODO'
            assert issues[1]['type'] == 'FIXME'
            
            os.unlink(f.name)

    def test_no_todos(self):
        """Test file with no TODO markers."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def my_function():
    # This is a regular comment
    return 42
""")
            f.flush()
            file_path = Path(f.name)
            
            issues = check_for_todos(file_path)
            
            assert len(issues) == 0
            
            os.unlink(f.name)

class TestCheckForPassOnlyFunctions:
    def test_find_pass_only_functions(self):
        """Test detection of pass-only functions."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def empty_function():
    pass

def function_with_content():
    return 42

class EmptyClass:
    pass
""")
            f.flush()
            file_path = Path(f.name)
            
            issues = check_for_pass_only_functions(file_path)
            
            # Should find the empty_function
            assert len(issues) == 1
            assert issues[0]['function_name'] == 'empty_function'
            
            os.unlink(f.name)

    def test_no_pass_only_functions(self):
        """Test file with no pass-only functions."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def my_function():
    return 42

def another_function(x):
    return x * 2
""")
            f.flush()
            file_path = Path(f.name)
            
            issues = check_for_pass_only_functions(file_path)
            
            assert len(issues) == 0
            
            os.unlink(f.name)

class TestCheckImportGroups:
    def test_proper_import_grouping(self):
        """Test file with properly grouped imports."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import os
import sys

import pandas
import numpy

from .local_module import something
from ..parent_module import something_else
""")
            f.flush()
            file_path = Path(f.name)
            
            issues = check_import_groups(file_path)
            
            # Should have no issues with proper grouping
            assert len(issues) == 0
            
            os.unlink(f.name)

    def test_mixed_import_grouping(self):
        """Test file with improperly mixed imports."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import os
import pandas
import sys
""")
            f.flush()
            file_path = Path(f.name)
            
            issues = check_import_groups(file_path)
            
            # Should detect the grouping issue
            assert len(issues) > 0
            
            os.unlink(f.name)

class TestAnalyzeCodeQuality:
    def test_analyze_code_quality(self):
        """Test the full code quality analysis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file with issues
            test_file = Path(tmpdir, 'test_issues.py')
            test_file.write_text("""
# TODO: Fix this later
import os
import pandas
import sys

def empty_function():
    pass
""")
            
            results = analyze_code_quality(tmpdir)
            
            assert results['total_files'] == 1
            assert results['todo_count'] == 1
            assert results['pass_only_functions'] == 1
            assert results['import_issues'] > 0
            assert len(results['files_with_issues']) == 1

class TestGenerateCleanupReport:
    def test_generate_report(self):
        """Test report generation."""
        results = {
            'total_files': 5,
            'todo_count': 2,
            'pass_only_functions': 1,
            'import_issues': 3,
            'files_with_issues': ['file1.py', 'file2.py'],
            'details': [
                {'type': 'TODO', 'file': 'file1.py', 'line': 10, 'content': '# TODO: fix this'},
                {'type': 'PASS_ONLY_FUNCTION', 'file': 'file2.py', 'line': 25, 'function_name': 'empty_func'}
            ]
        }
        
        report = generate_cleanup_report(results)
        
        assert 'CODE CLEANUP AND REFACTORING REPORT' in report
        assert 'Total Python files analyzed: 5' in report
        assert 'TODO/FIXME/XXX/HACK markers: 2' in report
        assert 'file1.py' in report
        assert 'file2.py' in report

if __name__ == '__main__':
    pytest.main([__file__, '-v'])