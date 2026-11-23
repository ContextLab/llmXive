"""
Tests for the constitutional check module.
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import sys

# Import the module under test
# We need to add the parent directory of code/src to sys.path to import it
# assuming the tests are run from the project root or code/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from constitutional_check import verify_amendment_artifact, ConstitutionalBlockError, main


def test_amendment_exists(tmp_path):
    """Test that verification passes when amendment file exists."""
    # Create a temporary directory structure
    specs_dir = tmp_path / "specs" / "001-code-complexity-bug-prediction"
    specs_dir.mkdir(parents=True)
    amendment_file = specs_dir / "amendment_ratified.md"
    amendment_file.write_text("# Ratified Amendment")
    
    # Mock the path resolution to use our temp directory
    with patch("constitutional_check.Path.resolve") as mock_resolve:
        # Make resolve return the temp path's parent structure
        # We need to mock the __file__ resolution indirectly
        original_path = Path
        
        def mock_path_cls(path=None):
            result = original_path(path)
            if path is None or path == "":
                # This is the __file__ case
                class MockPath:
                    def resolve(self):
                        return tmp_path / "code" / "src"
                    def parent(self):
                        return tmp_path / "code" / "src"
                return MockPath()
            return result
        
        with patch("constitutional_check.Path", mock_path_cls):
            result = verify_amendment_artifact()
            assert result is True


def test_amendment_missing_raises_error(tmp_path):
    """Test that verification raises error when amendment file is missing."""
    # Create a temporary directory structure WITHOUT the amendment file
    specs_dir = tmp_path / "specs" / "001-code-complexity-bug-prediction"
    specs_dir.mkdir(parents=True)
    # Do NOT create amendment_ratified.md
    
    with patch("constitutional_check.Path") as mock_path_cls:
        original_path = Path
        
        def mock_path_constructor(path=None):
            if path is None or path == "":
                class MockPath:
                    def resolve(self):
                        return tmp_path / "code" / "src"
                    def __truediv__(self, other):
                        if other == "specs":
                            return tmp_path / "specs"
                        elif other == "amendment_ratified.md":
                            return tmp_path / "specs" / "001-code-complexity-bug-prediction" / "amendment_ratified.md"
                        return tmp_path / other
                    def exists(self):
                        return False
                return MockPath()
            return original_path(path)
        
        mock_path_cls.side_effect = mock_path_constructor
        
        with pytest.raises(ConstitutionalBlockError) as excinfo:
            verify_amendment_artifact()
        
        assert "ConstitutionalBlockError" in str(excinfo.value)
        assert "missing" in str(excinfo.value).lower()


def test_main_returns_zero_on_success(tmp_path, capsys):
    """Test that main returns 0 when amendment exists."""
    specs_dir = tmp_path / "specs" / "001-code-complexity-bug-prediction"
    specs_dir.mkdir(parents=True)
    amendment_file = specs_dir / "amendment_ratified.md"
    amendment_file.write_text("# Ratified")
    
    with patch("constitutional_check.Path") as mock_path_cls:
        original_path = Path
        
        def mock_path_constructor(path=None):
            if path is None or path == "":
                class MockPath:
                    def resolve(self):
                        return tmp_path / "code" / "src"
                    def __truediv__(self, other):
                        if other == "specs":
                            return tmp_path / "specs"
                        elif other == "amendment_ratified.md":
                            return tmp_path / "specs" / "001-code-complexity-bug-prediction" / "amendment_ratified.md"
                        return tmp_path / other
                    def exists(self):
                        return True
                return MockPath()
            return original_path(path)
        
        mock_path_cls.side_effect = mock_path_constructor
        
        exit_code = main()
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "SUCCESS" in captured.out


def test_main_returns_one_on_failure(tmp_path, capsys):
    """Test that main returns 1 when amendment is missing."""
    specs_dir = tmp_path / "specs" / "001-code-complexity-bug-prediction"
    specs_dir.mkdir(parents=True)
    
    with patch("constitutional_check.Path") as mock_path_cls:
        original_path = Path
        
        def mock_path_constructor(path=None):
            if path is None or path == "":
                class MockPath:
                    def resolve(self):
                        return tmp_path / "code" / "src"
                    def __truediv__(self, other):
                        if other == "specs":
                            return tmp_path / "specs"
                        elif other == "amendment_ratified.md":
                            return tmp_path / "specs" / "001-code-complexity-bug-prediction" / "amendment_ratified.md"
                        return tmp_path / other
                    def exists(self):
                        return False
                return MockPath()
            return original_path(path)
        
        mock_path_cls.side_effect = mock_path_constructor
        
        exit_code = main()
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "FAILURE" in captured.err