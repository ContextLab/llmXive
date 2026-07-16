"""
Tests for T036: Code cleanup and refactoring module.

These tests verify that the cleanup script:
1. Correctly identifies Python files
2. Detects common issues (print statements, TODOs, magic numbers)
3. Generates a valid report
4. Handles edge cases gracefully
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cleanup_refactor import CodeRefactorer, main


class TestCodeRefactorer:
    """Test cases for the CodeRefactorer class."""

    @pytest.fixture
    def temp_code_dir(self, tmp_path):
        """Create a temporary directory structure with test Python files."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        # Create a test file with issues
        test_file = code_dir / "test_module.py"
        test_content = """
import os
import pandas as pd

print("Hello world")
print("This is a warning")

# TODO: Fix this later
def my_function():
    x = 42
    y = 3.14159
    return x + y
"""
        test_file.write_text(test_content)
        
        # Create another test file
        another_file = code_dir / "another_module.py"
        another_content = """
import logging
from logging_utils import setup_memory_logger

logger = setup_memory_logger("test")

def another_function():
    logger.info("Processing data")
    return True
"""
        another_file.write_text(another_content)
        
        return tmp_path

    def test_get_python_files(self, temp_code_dir):
        """Test that get_python_files returns correct files."""
        refactorer = CodeRefactorer(str(temp_code_dir))
        files = refactorer.get_python_files()
        
        assert len(files) == 2
        file_names = [f.name for f in files]
        assert "test_module.py" in file_names
        assert "another_module.py" in file_names

    def test_analyze_file_detects_print(self, temp_code_dir):
        """Test that analyze_file detects print statements."""
        refactorer = CodeRefactorer(str(temp_code_dir))
        file_path = temp_code_dir / "code" / "test_module.py"
        
        issues, fixes = refactorer.analyze_file(file_path)
        
        assert any("print" in issue.lower() for issue in issues)
        assert any("fixes" in str(fixes).lower() for fix in fixes if isinstance(fix, str))

    def test_analyze_file_detects_todo(self, temp_code_dir):
        """Test that analyze_file detects TODO comments."""
        refactorer = CodeRefactorer(str(temp_code_dir))
        file_path = temp_code_dir / "code" / "test_module.py"
        
        issues, fixes = refactorer.analyze_file(file_path)
        
        assert any("TODO" in issue for issue in issues)

    def test_analyze_file_detects_magic_numbers(self, temp_code_dir):
        """Test that analyze_file detects magic numbers."""
        refactorer = CodeRefactorer(str(temp_code_dir))
        file_path = temp_code_dir / "code" / "test_module.py"
        
        issues, fixes = refactorer.analyze_file(file_path)
        
        # Should detect 42 and 3.14159
        assert any("magic" in issue.lower() for issue in issues)

    def test_apply_refactoring_replaces_print(self, temp_code_dir):
        """Test that apply_refactoring replaces print statements with logging."""
        refactorer = CodeRefactorer(str(temp_code_dir))
        file_path = temp_code_dir / "code" / "test_module.py"
        
        original_content = file_path.read_text()
        changed = refactorer.apply_refactoring(file_path)
        
        assert changed
        
        new_content = file_path.read_text()
        assert "print(" not in new_content
        assert "logger.info" in new_content or "logger.warning" in new_content

    def test_check_consistency_logging_import(self, temp_code_dir):
        """Test consistency check for logging imports."""
        refactorer = CodeRefactorer(str(temp_code_dir))
        
        inconsistencies = refactorer.check_consistency()
        
        # The test_module.py uses print (which we're checking for logging usage)
        # but after refactoring, it should be fine
        # We're mainly testing the method runs without error
        assert isinstance(inconsistencies, list)

    def test_generate_report_structure(self, temp_code_dir):
        """Test that generate_report returns expected structure."""
        refactorer = CodeRefactorer(str(temp_code_dir))
        refactorer.run()  # Run to populate data
        
        report = refactorer.generate_report()
        
        assert "files_processed" in report
        assert "issues_fixed" in report
        assert "final_memory_mb" in report
        assert "timestamp" in report

    def test_run_completes_successfully(self, temp_code_dir):
        """Test that run() completes without errors."""
        refactorer = CodeRefactorer(str(temp_code_dir))
        
        success = refactorer.run()
        
        assert success is True
        
        # Verify report was created
        report_path = temp_code_dir / "data" / "processed" / "cleanup_report.json"
        assert report_path.exists()
        
        with open(report_path, "r") as f:
            report = json.load(f)
        
        assert "files_processed" in report
        assert report["files_processed"] == 2

class TestMainFunction:
    """Test cases for the main function."""

    def test_main_returns_zero_on_success(self, temp_code_dir):
        """Test that main returns 0 on success."""
        with patch("cleanup_refactor.CodeRefactorer") as mock_refactorer_class:
            mock_instance = MagicMock()
            mock_instance.run.return_value = True
            mock_refactorer_class.return_value = mock_instance
            
            result = main()
            
            assert result == 0

    def test_main_returns_one_on_failure(self, temp_code_dir):
        """Test that main returns 1 on failure."""
        with patch("cleanup_refactor.CodeRefactorer") as mock_refactorer_class:
            mock_instance = MagicMock()
            mock_instance.run.return_value = False
            mock_refactorer_class.return_value = mock_instance
            
            result = main()
            
            assert result == 1

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_code_directory(self, tmp_path):
        """Test handling of empty code directory."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        refactorer = CodeRefactorer(str(tmp_path))
        
        files = refactorer.get_python_files()
        assert len(files) == 0

    def test_nonexistent_code_directory(self, tmp_path):
        """Test handling of nonexistent code directory."""
        refactorer = CodeRefactorer(str(tmp_path / "nonexistent"))
        
        files = refactorer.get_python_files()
        assert len(files) == 0

    def test_file_with_syntax_error(self, tmp_path):
        """Test handling of files with syntax errors."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        bad_file = code_dir / "bad_syntax.py"
        bad_file.write_text("def broken(:")
        
        refactorer = CodeRefactorer(str(tmp_path))
        issues, fixes = refactorer.analyze_file(bad_file)
        
        assert any("Syntax error" in issue for issue in issues)

    def test_large_file_handling(self, tmp_path):
        """Test handling of larger files."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        large_file = code_dir / "large.py"
        # Create a file with many lines
        lines = [f"line_{i} = {i}" for i in range(1000)]
        large_file.write_text("\n".join(lines))
        
        refactorer = CodeRefactorer(str(tmp_path))
        issues, fixes = refactorer.analyze_file(large_file)
        
        # Should complete without error
        assert isinstance(issues, list)
        assert isinstance(fixes, list)