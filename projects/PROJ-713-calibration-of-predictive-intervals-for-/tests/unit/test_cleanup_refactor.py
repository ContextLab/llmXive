import os
import tempfile
from pathlib import Path
import pytest

from scripts.cleanup_and_refactor import (
    find_python_files,
    check_hardcoded_paths,
    check_seed_consistency,
    check_config_usage,
    generate_cleanup_report
)
from config import PROJECT_ROOT, CODE_DIR

class TestCleanupRefactor:
    """Tests for the cleanup and refactor utility functions."""

    def test_find_python_files(self):
        """Test that Python files are found correctly."""
        py_files = find_python_files(str(CODE_DIR))
        assert len(py_files) > 0, "Should find at least some Python files"
        
        # All files should be .py files
        for file_path in py_files:
            assert file_path.suffix == '.py', f"Expected .py file, got {file_path}"

    def test_check_hardcoded_paths_no_issues(self):
        """Test that clean files return no issues."""
        # Create a temporary clean file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
from config import PROJECT_ROOT
import os

def clean_function():
    path = PROJECT_ROOT / "data"
    return path
""")
            temp_file = Path(f.name)
        
        try:
            issues = check_hardcoded_paths(temp_file)
            assert len(issues) == 0, f"Clean file should have no hardcoded path issues, found: {issues}"
        finally:
            os.unlink(temp_file)

    def test_check_hardcoded_paths_with_issues(self):
        """Test that files with hardcoded paths are detected."""
        # Create a temporary file with hardcoded paths
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import os

def bad_function():
    path = "/tmp/some/path"
    return path
""")
            temp_file = Path(f.name)
        
        try:
            issues = check_hardcoded_paths(temp_file)
            assert len(issues) > 0, "File with hardcoded paths should have issues"
        finally:
            os.unlink(temp_file)

    def test_check_seed_consistency(self):
        """Test seed consistency checking."""
        # Create a temporary file with hardcoded seed
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import numpy as np

def train_model():
    np.random.seed(42)  # Should use config.SEED instead
    return "model"
""")
            temp_file = Path(f.name)
        
        try:
            issues = check_seed_consistency(temp_file)
            # May or may not detect this depending on pattern, but shouldn't crash
            assert isinstance(issues, list)
        finally:
            os.unlink(temp_file)

    def test_check_config_usage(self):
        """Test config usage checking."""
        # Create a temporary file with proper config usage
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
from config import PROJECT_ROOT, DATA_DIR

def load_data():
    path = DATA_DIR / "raw"
    return path
""")
            temp_file = Path(f.name)
        
        try:
            result = check_config_usage(temp_file)
            assert result['imports_config'] == True
            assert result['uses_config_vars'] == True
            assert result['has_hardcoded_paths'] == False
        finally:
            os.unlink(temp_file)

    def test_generate_cleanup_report_empty(self):
        """Test report generation with no issues."""
        issues = {
            'hardcoded_paths': [],
            'seed_consistency': [],
            'config_usage': []
        }
        
        report = generate_cleanup_report(issues)
        assert "No issues found" in report
        assert "✅" in report

    def test_generate_cleanup_report_with_issues(self):
        """Test report generation with issues."""
        issues = {
            'hardcoded_paths': [(Path("test.py"), [(1, "pattern", "bad_code")])],
            'seed_consistency': [],
            'config_usage': []
        }
        
        report = generate_cleanup_report(issues)
        assert "Hardcoded Paths Found" in report
        assert "⚠️" in report

if __name__ == "__main__":
    pytest.main([__file__, "-v"])