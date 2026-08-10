"""
Unit tests for the code cleanup and refactoring utilities.
"""

import ast
import tempfile
import os
from pathlib import Path
import pytest

from code.cleanup_refactor import (
    extract_imports_from_file,
    analyze_file_for_cleanup,
    validate_apis,
    CodeCleanupError
)

def test_extract_imports_from_file_valid():
    """Test extraction of imports from a valid Python file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
import numpy as np
from scipy import stats
import os
from .local_module import helper
from ..parent import something
""")
        f.flush()
        file_path = Path(f.name)

    try:
        std_lib, local = extract_imports_from_file(file_path)

        assert 'numpy' in std_lib
        assert 'scipy' in std_lib
        assert 'os' in std_lib
        assert '.local_module' in local
        assert '..parent' in local
    finally:
        os.unlink(file_path)

def test_extract_imports_from_file_empty():
    """Test extraction from a file with no imports."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def hello():
    pass
""")
        f.flush()
        file_path = Path(f.name)

    try:
        std_lib, local = extract_imports_from_file(file_path)
        assert len(std_lib) == 0
        assert len(local) == 0
    finally:
        os.unlink(file_path)

def test_analyze_file_for_cleanup_todos():
    """Test that TODOs are detected in file analysis."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
# TODO: Implement this function
def todo_func():
    pass

# FIXME: This is broken
def broken_func():
    pass
""")
        f.flush()
        file_path = Path(f.name)

    try:
        analysis = analyze_file_for_cleanup(file_path)
        assert analysis["todo_count"] == 2
        assert len(analysis["todos"]) == 2
        assert "TODO" in analysis["todos"][0][0]
        assert "FIXME" in analysis["todos"][1][0]
    finally:
        os.unlink(file_path)

def test_analyze_file_for_cleanup_missing_file():
    """Test analysis of a non-existent file."""
    file_path = Path("/non/existent/file.py")
    analysis = analyze_file_for_cleanup(file_path)
    assert "error" in analysis

def test_validate_apis_structure():
    """Test that validate_apis returns expected structure."""
    # Create a temporary project structure
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        code_dir = project_root / "code"
        code_dir.mkdir()

        # Create a dummy Python file
        (code_dir / "dummy.py").write_text("def test(): pass\n")

        result = validate_apis(project_root)

        assert "validated_files" in result
        assert "issues" in result
        assert "total_files" in result
        assert result["total_files"] == 1

def test_code_cleanup_error():
    """Test that CodeCleanupError can be raised and caught."""
    try:
        raise CodeCleanupError("Test error message")
    except CodeCleanupError as e:
        assert str(e) == "Test error message"
    except Exception:
        pytest.fail("CodeCleanupError was not raised correctly")