"""
Unit tests to ensure no hardcoded paths exist in the codebase.
"""
import os
import re
from pathlib import Path
import pytest

from config import PROJECT_ROOT, CODE_DIR
from scripts.cleanup_and_refactor import find_python_files, check_hardcoded_paths

class TestNoHardcodedPaths:
    """Tests to ensure no hardcoded paths exist."""

    def test_no_absolute_paths_in_code(self):
        """Test that no absolute paths are hardcoded."""
        py_files = find_python_files(str(CODE_DIR))
        
        problematic_files = []
        for file_path in py_files:
            issues = check_hardcoded_paths(file_path)
            if issues:
                problematic_files.append((file_path, issues))
        
        if problematic_files:
            error_msg = "Found hardcoded paths in:\n"
            for file_path, issues in problematic_files:
                error_msg += f"\n{file_path}:\n"
                for line_num, pattern, line_content in issues:
                    error_msg += f"  Line {line_num}: {line_content}\n"
            pytest.fail(error_msg)

    def test_all_paths_use_config_constants(self):
        """Test that file paths use config constants."""
        py_files = find_python_files(str(CODE_DIR))
        
        path_patterns = [
            r'["\'](/tmp/|/var/tmp/|/home/\w+/|/Users/\w+/|C:\\Users\\|C:\\Program)',
            r'["\'](/absolute/path|/some/fixed/dir)',
        ]
        
        violations = []
        for file_path in py_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for pattern in path_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    violations.append((file_path, matches))
        
        assert len(violations) == 0, \
            f"Found hardcoded absolute paths: {violations}"

    def test_data_paths_relative_to_project_root(self):
        """Test that data paths are relative to PROJECT_ROOT."""
        # This is a sanity check - we verify that the config module exists
        # and that PROJECT_ROOT is properly defined
        assert PROJECT_ROOT.exists(), "PROJECT_ROOT should be a valid directory"
        assert (PROJECT_ROOT / "data").exists(), "Data directory should exist"
        assert (PROJECT_ROOT / "results").exists(), "Results directory should exist"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])