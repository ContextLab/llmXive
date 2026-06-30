"""
Unit tests for Task T001a: Project Structure Verification.
Ensures the directory structure created by setup_project_structure.py is correct.
"""
import os
import pytest

PROJECT_ROOT = "projects/PROJ-628-foundation-protocol-a-coordination-layer"

REQUIRED_DIRS = [
    PROJECT_ROOT,
    os.path.join(PROJECT_ROOT, "code"),
    os.path.join(PROJECT_ROOT, "code", "foundation_protocol"),
    os.path.join(PROJECT_ROOT, "code", "agents"),
    os.path.join(PROJECT_ROOT, "code", "benchmarks"),
    os.path.join(PROJECT_ROOT, "code", "experiments"),
    os.path.join(PROJECT_ROOT, "code", "reports"),
    os.path.join(PROJECT_ROOT, "code", "data"),
    os.path.join(PROJECT_ROOT, "code", "tests"),
    os.path.join(PROJECT_ROOT, "data"),
    os.path.join(PROJECT_ROOT, "results"),
    os.path.join(PROJECT_ROOT, "state"),
    os.path.join(PROJECT_ROOT, "docs"),
    os.path.join(PROJECT_ROOT, "contracts"),
    os.path.join(PROJECT_ROOT, "specs"),
    os.path.join(PROJECT_ROOT, "specs", "feature-001-foundation-protocol"),
    os.path.join(PROJECT_ROOT, "tests"),
    os.path.join(PROJECT_ROOT, "scripts"),
    os.path.join(PROJECT_ROOT, "ideas"),
    os.path.join(PROJECT_ROOT, "reviews"),
]

class TestProjectStructure:
    def test_root_directory_exists(self):
        """Verify the root project directory exists."""
        assert os.path.isdir(PROJECT_ROOT), f"Root directory {PROJECT_ROOT} does not exist"

    def test_all_required_directories_exist(self):
        """Verify all required subdirectories exist."""
        missing = []
        for dir_path in REQUIRED_DIRS:
            if not os.path.isdir(dir_path):
                missing.append(dir_path)
        
        assert not missing, f"The following directories are missing: {missing}"

    def test_no_files_in_directory_placeholders(self):
        """Verify that directory paths are not actually files."""
        file_conflicts = []
        for dir_path in REQUIRED_DIRS:
            if os.path.isfile(dir_path):
                file_conflicts.append(dir_path)
        
        assert not file_conflicts, f"The following paths are files, not directories: {file_conflicts}"

    def test_code_subdirectory_structure(self):
        """Specific test for the code/ hierarchy as per T001b."""
        code_dirs = [
            "code",
            "code/foundation_protocol",
            "code/agents",
            "code/benchmarks",
            "code/experiments",
            "code/reports",
            "code/data",
            "code/tests",
        ]
        for subdir in code_dirs:
            full_path = os.path.join(PROJECT_ROOT, subdir)
            assert os.path.isdir(full_path), f"Missing code subdirectory: {subdir}"

    def test_data_and_results_directories(self):
        """Verify data and results directories exist at root level."""
        data_dir = os.path.join(PROJECT_ROOT, "data")
        results_dir = os.path.join(PROJECT_ROOT, "results")
        state_dir = os.path.join(PROJECT_ROOT, "state")
        
        assert os.path.isdir(data_dir), "Missing data/ directory"
        assert os.path.isdir(results_dir), "Missing results/ directory"
        assert os.path.isdir(state_dir), "Missing state/ directory"
