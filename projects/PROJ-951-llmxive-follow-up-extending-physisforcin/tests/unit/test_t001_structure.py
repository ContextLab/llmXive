import os
import sys
import pytest
from pathlib import Path

# Add parent to path to import if needed, though we check filesystem directly
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestT001Structure:
    """
    Verification tests for T001, T001b, T001c directory creation.
    These tests verify that the expected directory structure exists.
    """
    
    @pytest.fixture
    def project_code_root(self):
        """Locate the project code root."""
        current = Path.cwd()
        # Try to find the specific project directory
        # Strategy: Look for 'projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code'
        # relative to cwd, or assume cwd is the code dir if running from there.
        
        if (current / 'projects' / 'PROJ-951-llmxive-follow-up-extending-physisforcin' / 'code').exists():
            return current / 'projects' / 'PROJ-951-llmxive-follow-up-extending-physisforcin' / 'code'
        
        # Fallback: assume cwd is the code root (common in local dev)
        if (current / 'src').exists() and (current / 'data').exists():
            return current
        
        # If not found, create a temporary structure for testing the logic?
        # No, the task is to create real dirs. If they don't exist, the test fails.
        return current / 'projects' / 'PROJ-951-llmxive-follow-up-extending-physisforcin' / 'code'

    def test_t001_project_root_exists(self, project_code_root):
        """Verify T001: The project root and code directory exist."""
        assert project_code_root.exists(), f"Project code root does not exist: {project_code_root}"
        assert project_code_root.is_dir(), f"Project code root is not a directory: {project_code_root}"

    def test_t001b_subdirectories_exist(self, project_code_root):
        """Verify T001b: src, tests, data exist."""
        required = ['src', 'tests', 'data']
        for d in required:
            path = project_code_root / d
            assert path.exists(), f"Missing T001b directory: {path}"
            assert path.is_dir(), f"Not a directory: {path}"

    def test_t001c_data_structure(self, project_code_root):
        """Verify T001c: Data subdirectories."""
        data_dirs = ['raw', 'curated', 'eval', 'validation']
        for d in data_dirs:
            path = project_code_root / 'data' / d
            assert path.exists(), f"Missing data subdirectory: {path}"
            assert path.is_dir(), f"Not a directory: {path}"

    def test_t001c_src_structure(self, project_code_root):
        """Verify T001c: Source subdirectories."""
        src_dirs = ['generation', 'filtering', 'training', 'evaluation', 'augmentation', 'utils']
        for d in src_dirs:
            path = project_code_root / 'src' / d
            assert path.exists(), f"Missing src subdirectory: {path}"
            assert path.is_dir(), f"Not a directory: {path}"

    def test_t001c_test_structure(self, project_code_root):
        """Verify T001c: Test subdirectories."""
        test_dirs = ['unit', 'integration']
        for d in test_dirs:
            path = project_code_root / 'tests' / d
            assert path.exists(), f"Missing tests subdirectory: {path}"
            assert path.is_dir(), f"Not a directory: {path}"

    def test_full_structure_present(self, project_code_root):
        """Comprehensive check of the entire T001-T001c structure."""
        # This aggregates all checks
        checks = [
            (project_code_root, True),
            (project_code_root / 'src', True),
            (project_code_root / 'tests', True),
            (project_code_root / 'data', True),
            (project_code_root / 'data' / 'raw', True),
            (project_code_root / 'data' / 'curated', True),
            (project_code_root / 'data' / 'eval', True),
            (project_code_root / 'data' / 'validation', True),
            (project_code_root / 'src' / 'generation', True),
            (project_code_root / 'src' / 'filtering', True),
            (project_code_root / 'src' / 'training', True),
            (project_code_root / 'src' / 'evaluation', True),
            (project_code_root / 'src' / 'augmentation', True),
            (project_code_root / 'src' / 'utils', True),
            (project_code_root / 'tests' / 'unit', True),
            (project_code_root / 'tests' / 'integration', True),
        ]
        
        for path, should_exist in checks:
            assert path.exists() == should_exist, f"Structure check failed for {path}"