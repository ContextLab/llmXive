"""
Unit tests for path normalization logic (T012).

Tests FR-009 requirements:
- Lowercase conversion
- Stripping .bak, .pyc, .min.js, .lock
- Normalizing slashes
"""
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.path_utils import normalize_path, normalize_paths, is_valid_source_path


class TestPathNormalization:
    """Test cases for normalize_path function."""
    
    def test_lowercase_conversion(self):
        """Test that paths are converted to lowercase."""
        assert normalize_path("Src/Main.Py") == "src/main.py"
        assert normalize_path("README.MD") == "readme.md"
        assert normalize_path("A/B/C.D") == "a/b/c.d"
    
    def test_slash_normalization(self):
        """Test that backslashes are converted to forward slashes."""
        assert normalize_path("src\\main.py") == "src/main.py"
        assert normalize_path("a\\b\\c\\file.txt") == "a/b/c/file.txt"
        assert normalize_path("mixed\\path/here.py") == "mixed/path/here.py"
    
    def test_strip_bak_extension(self):
        """Test stripping .bak extension."""
        assert normalize_path("file.txt.bak") == "file.txt"
        assert normalize_path("src/backup.bak") == "src/backup"
        assert normalize_path("DATA.BAK") == "data"  # Case insensitive
    
    def test_strip_pyc_extension(self):
        """Test stripping .pyc extension."""
        assert normalize_path("module.pyc") == "module"
        assert normalize_path("src/__pycache__/module.pyc") == "src/__pycache__/module"
    
    def test_strip_min_js_extension(self):
        """Test stripping .min.js extension."""
        assert normalize_path("script.min.js") == "script"
        assert normalize_path("assets/app.min.js") == "assets/app"
    
    def test_strip_lock_extension(self):
        """Test stripping .lock extension."""
        assert normalize_path("package.json.lock") == "package.json"
        assert normalize_path("yarn.lock") == "yarn"
    
    def test_multiple_stripped_extensions(self):
        """Test that only the last matching extension is stripped."""
        # If a file ends with .bak, strip it
        assert normalize_path("file.txt.bak") == "file.txt"
        # If a file ends with .min.js, strip it
        assert normalize_path("script.min.js") == "script"
    
    def test_path_object_input(self):
        """Test that Path objects are treated correctly."""
        path_obj = Path("Src/Main.Py")
        assert normalize_path(path_obj) == "src/main.py"
    
    def test_empty_string(self):
        """Test handling of empty string."""
        assert normalize_path("") == ""
    
    def test_trailing_slash_removal(self):
        """Test that trailing slashes are removed (except for root)."""
        assert normalize_path("src/main.py/") == "src/main.py"
        assert normalize_path("a/b/c/") == "a/b/c"
        # Root slash should remain
        assert normalize_path("/") == "/"
    
    def test_double_slash_normalization(self):
        """Test that double slashes are normalized."""
        assert normalize_path("src//main.py") == "src/main.py"
        assert normalize_path("a//b//c.py") == "a/b/c.py"
    
    def test_combined_normalization(self):
        """Test combined transformations."""
        # Mixed case, backslashes, and .bak extension
        assert normalize_path("Src\\File.Txt.Bak") == "src/file.txt"
        assert normalize_path("APP\\SCRIPT.MIN.JS") == "app/script"
    
    def test_no_change_for_clean_path(self):
        """Test that clean paths remain unchanged (except case)."""
        assert normalize_path("src/main.py") == "src/main.py"
        assert normalize_path("data/file.csv") == "data/file.csv"


class TestNormalizePaths:
    """Test cases for normalize_paths function."""
    
    def test_list_normalization(self):
        """Test normalizing a list of paths."""
        paths = ["Src/Main.Py", "data\\file.csv.bak", "README.MD"]
        expected = ["src/main.py", "data/file.csv", "readme.md"]
        assert normalize_paths(paths) == expected
    
    def test_empty_list(self):
        """Test normalizing an empty list."""
        assert normalize_paths([]) == []
    
    def test_mixed_inputs(self):
        """Test normalizing a list with mixed Path and string inputs."""
        paths = [Path("Src/Main.Py"), "data\\file.csv"]
        expected = ["src/main.py", "data/file.csv"]
        assert normalize_paths(paths) == expected


class TestIsValidSourcePath:
    """Test cases for is_valid_source_path function."""
    
    def test_valid_source_files(self):
        """Test that valid source files return True."""
        assert is_valid_source_path("src/main.py") is True
        assert is_valid_source_path("data/file.csv") is True
        assert is_valid_source_path("README.md") is True
    
    def test_stripped_extensions_return_false(self):
        """Test that files with stripped extensions return False."""
        assert is_valid_source_path("file.txt.bak") is False
        assert is_valid_source_path("module.pyc") is False
        assert is_valid_source_path("script.min.js") is False
        assert is_valid_source_path("package.json.lock") is False
    
    def test_empty_path(self):
        """Test that empty paths return False."""
        assert is_valid_source_path("") is False
    
    def test_root_path(self):
        """Test that root path returns False."""
        assert is_valid_source_path("/") is False
    
    def test_case_insensitive_check(self):
        """Test that extension check is case insensitive."""
        assert is_valid_source_path("FILE.TXT.BAK") is False
        assert is_valid_source_path("Module.PYC") is False