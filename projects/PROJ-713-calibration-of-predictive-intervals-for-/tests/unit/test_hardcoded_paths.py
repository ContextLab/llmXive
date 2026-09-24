"""
Unit tests for the hardcoded path audit functionality.
Verifies that the audit script correctly identifies hardcoded paths.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the audit functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from scripts.audit_hardcoded_paths import (
    find_python_files,
    check_hardcoded_paths,
    check_config_usage,
    HARDCODED_PATTERNS
)

class TestFindPythonFiles:
    def test_find_python_files(self, tmp_path):
        """Test finding Python files in a directory."""
        # Create test structure
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        (code_dir / "test1.py").write_text("print('hello')")
        (code_dir / "subdir").mkdir()
        (code_dir / "subdir" / "test2.py").write_text("print('world')")
        (code_dir / "readme.txt").write_text("not python")
        
        files = find_python_files(code_dir)
        assert len(files) == 2
        assert any("test1.py" in str(f) for f in files)
        assert any("test2.py" in str(f) for f in files)

class TestCheckHardcodedPaths:
    def test_detects_absolute_path(self, tmp_path):
        """Test detection of absolute paths."""
        test_file = tmp_path / "test.py"
        test_file.write_text('path = "/home/user/data.csv"\n')
        
        issues = check_hardcoded_paths(test_file)
        assert len(issues) > 0
        assert any("Hardcoded data/results path" in desc for _, _, desc in issues)

    def test_detects_relative_data_path(self, tmp_path):
        """Test detection of relative data paths without config."""
        test_file = tmp_path / "test.py"
        test_file.write_text('path = "data/raw/m4.csv"\n')
        
        issues = check_hardcoded_paths(test_file)
        assert len(issues) > 0

    def test_allows_config_import(self, tmp_path):
        """Test that files with config imports are not flagged for missing config."""
        test_file = tmp_path / "test.py"
        test_file.write_text('from config import DATA_DIR\npath = DATA_DIR / "raw/m4.csv"\n')
        
        # This should not raise issues for the path since it uses config
        issues = check_hardcoded_paths(test_file)
        # The relative path "raw/m4.csv" might still be caught, but the import check should pass
        assert check_config_usage(test_file) is True

    def test_allows_safe_paths(self, tmp_path):
        """Test that safe paths are not flagged."""
        test_file = tmp_path / "test.py"
        test_file.write_text('config_file = "config.yaml"\n')
        
        issues = check_hardcoded_paths(test_file)
        # Should not flag config.yaml as it's in SAFE_PATHS
        assert len([i for i in issues if "config.yaml" in i[2]]) == 0

    def test_no_issues_for_config_based_code(self, tmp_path):
        """Test code that properly uses config doesn't flag data paths."""
        test_file = tmp_path / "test.py"
        test_file.write_text('''
from config import DATA_RAW_DIR
path = DATA_RAW_DIR / "m4.csv"
''')
        
        issues = check_hardcoded_paths(test_file)
        # Should not flag this as it uses config
        assert len(issues) == 0

class TestCheckConfigUsage:
    def test_detects_config_import(self, tmp_path):
        """Test detection of config import."""
        test_file = tmp_path / "test.py"
        test_file.write_text('from config import DATA_DIR\n')
        
        assert check_config_usage(test_file) is True

    def test_detects_config_module_import(self, tmp_path):
        """Test detection of config module import."""
        test_file = tmp_path / "test.py"
        test_file.write_text('import config\n')
        
        assert check_config_usage(test_file) is True

    def test_no_config_import(self, tmp_path):
        """Test file without config import."""
        test_file = tmp_path / "test.py"
        test_file.write_text('path = "/some/path"\n')
        
        assert check_config_usage(test_file) is False

class TestAuditIntegration:
    def test_audit_passes_for_clean_code(self, tmp_path):
        """Test audit passes when code uses config properly."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        # Create a file that uses config
        (code_dir / "clean.py").write_text('''
from config import DATA_DIR, RESULTS_DIR
def process():
    data_path = DATA_DIR / "raw"
    result_path = RESULTS_DIR / "output.csv"
    return data_path, result_path
''')
        
        from scripts.audit_hardcoded_paths import audit_codebase
        results = audit_codebase(code_dir)
        
        # Should not have issues for clean code
        assert len(results) == 0

    def test_audit_fails_for_hardcoded_paths(self, tmp_path):
        """Test audit detects hardcoded paths."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        # Create a file with hardcoded path
        (code_dir / "dirty.py").write_text('path = "/tmp/data.csv"\n')
        
        from scripts.audit_hardcoded_paths import audit_codebase
        results = audit_codebase(code_dir)
        
        # Should detect the hardcoded path
        assert len(results) > 0
        assert any("dirty.py" in k for k in results.keys())