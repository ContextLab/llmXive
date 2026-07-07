"""
Unit tests for refactor_utils module.

Tests the cleanup and refactoring utilities to ensure they work correctly
on various code patterns.
"""
import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from refactor_utils import (
    clean_unused_imports,
    refactor_variable_names,
    standardize_logging_calls,
    remove_duplicate_imports,
    run_code_cleanup
)


@pytest.fixture
def temp_python_file():
    """Create a temporary Python file for testing."""
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix='.py', 
        delete=False,
        dir=tempfile.gettempdir()
    ) as f:
        yield Path(f.name)
    
    # Cleanup after test
    if os.path.exists(f.name):
        os.unlink(f.name)


def test_clean_unused_imports(temp_python_file):
    """Test unused import detection."""
    # Create a file with unused imports
    content = """
import os
import sys
import numpy as np
import pandas as pd

def hello():
    print("Hello")
    return os.getcwd()
"""
    temp_python_file.write_text(content)
    
    result = clean_unused_imports(temp_python_file)
    
    assert result["file"] == str(temp_python_file)
    assert result["total_imports"] == 4
    # sys and pandas should be unused
    assert "sys" in result["unused_imports"]
    assert "pd" in result["unused_imports"]
    # os and numpy are used
    assert "os" not in result["unused_imports"]
    assert "np" not in result["unused_imports"]


def test_refactor_variable_names(temp_python_file):
    """Test variable name refactoring."""
    content = """
def calculate_data(data):
    result = process_data(data)
    old_var = 10
    return result + old_var
"""
    temp_python_file.write_text(content)
    
    patterns = [
        {"old_pattern": "old_var", "new_name": "new_var"}
    ]
    
    result = refactor_variable_names(temp_python_file, patterns)
    
    assert result["changes_made"] == 2
    
    # Verify file was updated
    updated_content = temp_python_file.read_text()
    assert "new_var" in updated_content
    assert "old_var" not in updated_content


def test_standardize_logging_calls(temp_python_file):
    """Test logging call standardization."""
    content = """
import logging

def my_function():
    logging.info("Info message")
    logging.warning("Warning message")
    logging.error("Error message")
"""
    temp_python_file.write_text(content)
    
    result = standardize_logging_calls(temp_python_file)
    
    assert result["changes_made"] == 3
    
    # Verify file was updated
    updated_content = temp_python_file.read_text()
    assert "logger.info" in updated_content
    assert "logger.warning" in updated_content
    assert "logger.error" in updated_content
    assert "logging.info" not in updated_content


def test_remove_duplicate_imports(temp_python_file):
    """Test duplicate import removal."""
    content = """
import os
import sys
import os
from pathlib import Path
import sys
"""
    temp_python_file.write_text(content)
    
    result = remove_duplicate_imports(temp_python_file)
    
    assert result["duplicates_removed"] == 2
    
    # Verify file was updated
    updated_content = temp_python_file.read_text()
    lines = [line.strip() for line in updated_content.split('\n') if line.strip()]
    
    # Should have only 3 unique imports now
    import_lines = [l for l in lines if l.startswith('import ') or l.startswith('from ')]
    assert len(import_lines) == 3


def test_run_code_cleanup(temp_python_file):
    """Test running cleanup on a directory."""
    # Create a test directory structure
    test_dir = Path(tempfile.mkdtemp())
    code_dir = test_dir / 'code'
    code_dir.mkdir()
    
    # Create a test file
    test_file = code_dir / 'test_module.py'
    test_file.write_text("""
import os
import sys
import os

def test():
    logging.info("test")
    return os.getcwd()
""")
    
    result = run_code_cleanup(test_dir)
    
    assert result["directory"] == str(test_dir)
    assert result["files_processed"] == 1
    assert result["total_changes"] > 0
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)


def test_clean_unused_imports_nonexistent_file():
    """Test handling of non-existent file."""
    result = clean_unused_imports(Path("/nonexistent/file.py"))
    
    assert result["errors"]
    assert "not found" in result["errors"][0].lower()


def test_refactor_variable_names_empty_patterns(temp_python_file):
    """Test refactoring with empty patterns."""
    content = "def test(): pass"
    temp_python_file.write_text(content)
    
    result = refactor_variable_names(temp_python_file, [])
    
    assert result["changes_made"] == 0
    assert result["errors"] == []


def test_standardize_logging_calls_no_changes(temp_python_file):
    """Test standardization when no logging calls exist."""
    content = "def test(): pass"
    temp_python_file.write_text(content)
    
    result = standardize_logging_calls(temp_python_file)
    
    assert result["changes_made"] == 0
    assert result["errors"] == []