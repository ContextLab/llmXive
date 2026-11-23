"""
Unit tests for cleanup_utils.py functionality.
Tests for T030: Code cleanup and refactoring.
"""
import ast
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, mock_open

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from cleanup_utils import (
    find_python_files,
    check_for_todos,
    check_for_pass_only_functions,
    check_import_groups,
    analyze_code_quality,
    generate_cleanup_report
)


class TestFindPythonFiles:
    """Tests for find_python_files function."""
    
    def test_find_python_files_basic(self, tmp_path):
        """Test finding Python files in a directory structure."""
        # Create test directory structure
        (tmp_path / 'subdir1').mkdir()
        (tmp_path / 'subdir2').mkdir()
        (tmp_path / '__pycache__').mkdir()
        
        # Create Python files
        (tmp_path / 'file1.py').write_text('# test')
        (tmp_path / 'subdir1' / 'file2.py').write_text('# test')
        (tmp_path / 'subdir2' / 'file3.py').write_text('# test')
        (tmp_path / '__pycache__' / 'cached.py').write_text('# test')
        (tmp_path / 'readme.txt').write_text('not python')
        
        result = find_python_files(tmp_path)
        
        # Should find 3 files, excluding __pycache__
        assert len(result) == 3
        assert all(f.suffix == '.py' for f in result)
        assert not any('__pycache__' in str(f) for f in result)
    
    def test_find_python_files_empty_dir(self, tmp_path):
        """Test finding Python files in an empty directory."""
        result = find_python_files(tmp_path)
        assert len(result) == 0


class TestCheckForTodos:
    """Tests for check_for_todos function."""
    
    def test_check_for_todos_found(self, tmp_path):
        """Test detecting TODO comments in a file."""
        test_file = tmp_path / 'test.py'
        content = """
        # TODO: Fix this later
        def foo():
            pass
        
        # FIXME: This is broken
        def bar():
            pass
        
        # HACK: Temporary workaround
        def baz():
            pass
        
        # Normal comment
        def qux():
            pass
        """
        test_file.write_text(content)
        
        result = check_for_todos(test_file)
        
        assert len(result) == 3
        assert any(item['type'] == 'TODO' for item in result)
        assert any(item['type'] == 'FIXME' for item in result)
        assert any(item['type'] == 'HACK' for item in result)
        
        # Check line numbers
        todo_items = [item for item in result if item['type'] == 'TODO']
        assert len(todo_items) == 1
        assert todo_items[0]['line'] == 2
    
    def test_check_for_todos_not_found(self, tmp_path):
        """Test when no TODO comments are present."""
        test_file = tmp_path / 'test.py'
        content = """
        def foo():
            pass
        
        # This is a normal comment
        """
        test_file.write_text(content)
        
        result = check_for_todos(test_file)
        assert len(result) == 0
    
    def test_check_for_todos_case_insensitive(self, tmp_path):
        """Test that TODO detection is case insensitive."""
        test_file = tmp_path / 'test.py'
        content = """
        # todo: lowercase
        # Todo: mixed case
        # TODO: uppercase
        """
        test_file.write_text(content)
        
        result = check_for_todos(test_file)
        assert len(result) == 3


class TestCheckForPassOnlyFunctions:
    """Tests for check_for_pass_only_functions function."""
    
    def test_check_for_pass_only_functions_found(self, tmp_path):
        """Test detecting empty functions."""
        test_file = tmp_path / 'test.py'
        content = """
        def empty_function():
            pass
        
        class EmptyClass:
            pass
        
        def not_empty():
            x = 1
            return x
        
        async def empty_async():
            pass
        """
        test_file.write_text(content)
        
        result = check_for_pass_only_functions(test_file)
        
        assert len(result) == 3
        names = [item['name'] for item in result]
        assert 'empty_function' in names
        assert 'EmptyClass' in names
        assert 'empty_async' in names
        
        # Check types
        types = {item['name']: item['type'] for item in result}
        assert types['empty_function'] == 'function'
        assert types['EmptyClass'] == 'class'
        assert types['empty_async'] == 'function'
    
    def test_check_for_pass_only_functions_not_found(self, tmp_path):
        """Test when no empty functions are present."""
        test_file = tmp_path / 'test.py'
        content = """
        def foo():
            x = 1
            return x
        
        class Bar:
            def method(self):
                pass  # This is a method with pass, but the class isn't empty
        """
        test_file.write_text(content)
        
        result = check_for_pass_only_functions(test_file)
        assert len(result) == 0
    
    def test_check_for_pass_only_functions_syntax_error(self, tmp_path):
        """Test handling of files with syntax errors."""
        test_file = tmp_path / 'test.py'
        content = """
        def broken(:
            pass
        """
        test_file.write_text(content)
        
        result = check_for_pass_only_functions(test_file)
        assert len(result) == 0


class TestCheckImportGroups:
    """Tests for check_import_groups function."""
    
    def test_check_import_groups_good(self, tmp_path):
        """Test when imports are properly grouped."""
        test_file = tmp_path / 'test.py'
        content = """
        import os
        import sys
        
        import numpy as np
        import pandas as pd
        
        from . import local_module
        from .sub import another
        """
        test_file.write_text(content)
        
        result = check_import_groups(test_file)
        assert len(result) == 0
    
    def test_check_import_groups_missing_blank_line(self, tmp_path):
        """Test detecting missing blank lines between import groups."""
        test_file = tmp_path / 'test.py'
        content = """
        import os
        import numpy as np
        
        from . import local
        """
        test_file.write_text(content)
        
        result = check_import_groups(test_file)
        assert len(result) == 1
        assert 'Missing blank line' in result[0]['text']
    
    def test_check_import_groups_no_imports(self, tmp_path):
        """Test file with no imports."""
        test_file = tmp_path / 'test.py'
        content = """
        def foo():
            pass
        """
        test_file.write_text(content)
        
        result = check_import_groups(test_file)
        assert len(result) == 0


class TestAnalyzeCodeQuality:
    """Tests for analyze_code_quality function."""
    
    def test_analyze_code_quality_basic(self, tmp_path):
        """Test basic code quality analysis."""
        # Create test files
        (tmp_path / 'good.py').write_text("""
        def foo():
            return 1
        """)
        
        (tmp_path / 'todo.py').write_text("""
        # TODO: Fix this
        def bar():
            pass
        """)
        
        (tmp_path / 'empty.py').write_text("""
        def empty():
            pass
        """)
        
        result = analyze_code_quality(tmp_path)
        
        assert result['total_files'] == 3
        assert result['total_issues'] > 0
        assert 'todos' in result
        assert 'empty_functions' in result
        assert 'import_issues' in result
        assert 'summary' in result
    
    def test_analyze_code_quality_empty_dir(self, tmp_path):
        """Test analysis of empty directory."""
        result = analyze_code_quality(tmp_path)
        
        assert result['total_files'] == 0
        assert result['total_issues'] == 0
        assert result['summary']['todo_count'] == 0


class TestGenerateCleanupReport:
    """Tests for generate_cleanup_report function."""
    
    def test_generate_cleanup_report_creates_file(self, tmp_path):
        """Test that report file is created."""
        test_dir = tmp_path / 'code'
        test_dir.mkdir()
        (test_dir / 'test.py').write_text('# test')
        
        output_file = tmp_path / 'report.json'
        
        result = generate_cleanup_report(test_dir, output_file)
        
        assert output_file.exists()
        assert result['total_files'] >= 1
        
        # Verify JSON content
        with open(output_file, 'r') as f:
            import json
            loaded = json.load(f)
            assert loaded == result
    
    def test_generate_cleanup_report_creates_directories(self, tmp_path):
        """Test that output directories are created if they don't exist."""
        test_dir = tmp_path / 'code'
        test_dir.mkdir()
        (test_dir / 'test.py').write_text('# test')
        
        output_file = tmp_path / 'deep' / 'nested' / 'report.json'
        
        result = generate_cleanup_report(test_dir, output_file)
        
        assert output_file.exists()
        assert result['total_files'] >= 1


class TestCleanupUtilsIntegration:
    """Integration tests for cleanup_utils module."""
    
    def test_full_workflow(self, tmp_path):
        """Test the full cleanup workflow."""
        # Create a realistic project structure
        code_dir = tmp_path / 'code'
        code_dir.mkdir()
        
        # Create files with various issues
        (code_dir / 'good.py').write_text("""
        import os
        import sys
        
        def good_function():
            return 1
        """)
        
        (code_dir / 'issues.py').write_text("""
        import os
        import numpy as np
        
        # TODO: Implement this
        def broken_function():
            pass
        
        class EmptyClass:
            pass
        """)
        
        output_file = tmp_path / 'report.json'
        
        result = generate_cleanup_report(code_dir, output_file)
        
        # Verify we found the issues
        assert result['total_files'] == 2
        assert result['summary']['todo_count'] == 1
        assert result['summary']['empty_function_count'] == 1
        assert result['summary']['import_issue_count'] == 1  # Missing blank line in issues.py
        
        assert output_file.exists()
        assert output_file.stat().st_size > 0