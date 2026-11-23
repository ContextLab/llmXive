"""
Unit tests for the cleanup utilities in code/utils/cleanup.py.
"""
import pytest
import tempfile
import os
from pathlib import Path

# Import the functions to test
from code.utils.cleanup import standardize_docstring, check_imports, remove_unused_imports


class TestStandardizeDocstring:
    """Tests for standardize_docstring function."""

    def test_empty_docstring(self):
        """Test with empty string."""
        assert standardize_docstring("") == ""

    def test_none_docstring(self):
        """Test with None."""
        assert standardize_docstring(None) == ""

    def test_single_line(self):
        """Test with a single line docstring."""
        doc = "This is a docstring."
        assert standardize_docstring(doc) == "This is a docstring."

    def test_multi_line(self):
        """Test with multi-line docstring."""
        doc = """
        This is a multi-line
        docstring.
        """
        expected = "This is a multi-line\ndocstring."
        assert standardize_docstring(doc) == expected

    def test_whitespace_handling(self):
        """Test that leading/trailing whitespace is removed."""
        doc = "   This has whitespace   "
        assert standardize_docstring(doc) == "This has whitespace"


class TestCheckImports:
    """Tests for check_imports function."""

    def test_no_imports(self):
        """Test file with no imports."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def hello():\n    return 'world'\n")
            f_path = f.name

        try:
            result = check_imports(f_path)
            assert len(result['imported_names']) == 0
            assert len(result['unused_imports']) == 0
        finally:
            os.unlink(f_path)

    def test_used_import(self):
        """Test that used imports are detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\n\ndef hello():\n    return os.getcwd()\n")
            f_path = f.name

        try:
            result = check_imports(f_path)
            assert 'os' in result['imported_names']
            assert 'os' in result['used_names']
            assert len(result['unused_imports']) == 0
        finally:
            os.unlink(f_path)

    def test_unused_import(self):
        """Test that unused imports are detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nimport json\n\ndef hello():\n    return 'world'\n")
            f_path = f.name

        try:
            result = check_imports(f_path)
            assert 'os' in result['imported_names']
            assert 'json' in result['imported_names']
            assert 'os' not in result['used_names']
            assert 'json' not in result['used_names']
            assert len(result['unused_imports']) == 2
        finally:
            os.unlink(f_path)

    def test_from_import(self):
        """Test from...import statements."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("from pathlib import Path, PurePath\n\ndef hello():\n    p = Path('.')\n")
            f_path = f.name

        try:
            result = check_imports(f_path)
            assert 'Path' in result['imported_names']
            assert 'PurePath' in result['imported_names']
            assert 'Path' in result['used_names']
            assert 'PurePath' not in result['used_names']
            assert len(result['unused_imports']) == 1
        finally:
            os.unlink(f_path)


class TestRemoveUnusedImports:
    """Tests for remove_unused_imports function."""

    def test_dry_run(self):
        """Test dry run mode."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nimport json\n\ndef hello():\n    return 'world'\n")
            f_path = f.name

        try:
            success, message = remove_unused_imports(f_path, dry_run=True)
            assert success is True
            assert "Would remove" in message
            assert "2 unused imports" in message
            # File should be unchanged
            with open(f_path, 'r') as rf:
                content = rf.read()
                assert 'import json' in content
        finally:
            os.unlink(f_path)

    def test_actual_removal(self):
        """Test actual removal of unused imports."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nimport json\n\ndef hello():\n    return 'world'\n")
            f_path = f.name

        try:
            success, message = remove_unused_imports(f_path, dry_run=False)
            assert success is True
            assert "Removed" in message
            # File should be changed
            with open(f_path, 'r') as rf:
                content = rf.read()
                assert 'import json' not in content
                assert 'import os' in content
        finally:
            os.unlink(f_path)

    def test_no_unused_imports(self):
        """Test file with no unused imports."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\n\ndef hello():\n    return os.getcwd()\n")
            f_path = f.name

        try:
            success, message = remove_unused_imports(f_path, dry_run=True)
            assert success is True
            assert "No unused imports" in message
        finally:
            os.unlink(f_path)

    def test_file_not_found(self):
        """Test with non-existent file."""
        success, message = remove_unused_imports("/nonexistent/file.py")
        assert success is False
        assert "Error" in message
