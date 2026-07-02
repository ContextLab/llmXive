"""
Test suite for T001: Project structure creation.

Validates that the required directory hierarchy exists and
contains the expected __init__.py and README.md files.
"""
import os
import sys
from pathlib import Path
import pytest

# Determine base path relative to this test file
TEST_DIR = Path(__file__).parent
PROJECT_ROOT = TEST_DIR.parent

REQUIRED_DIRECTORIES = [
    "code",
    "code/utils",
    "code/tests",
    "data",
    "data/raw",
    "data/processed",
    "data/results",
    "data/interim",
    "state",
    "state/projects",
    "state/projects/PROJ-036-exploring-the-impact-of-cosmic-microwave",
    "contracts",
    "config",
    "specs",
    "specs/001-cmb-anomaly-lss-impact",
    "figures",
    "docs",
]

REQUIRED_INIT_FILES = [
    "code/__init__.py",
    "code/utils/__init__.py",
    "code/tests/__init__.py",
    "data/__init__.py",
    "state/__init__.py",
    "config/__init__.py",
]

REQUIRED_READMES = [
    "data/README.md",
    "code/README.md",
    "state/README.md",
    "contracts/README.md",
    "config/README.md",
    "specs/README.md",
    "figures/README.md",
    "tests/README.md",
]

class TestProjectStructure:
    """Tests for the project directory structure."""

    @pytest.mark.parametrize("dir_name", REQUIRED_DIRECTORIES)
    def test_directory_exists(self, dir_name):
        """Assert that each required directory exists."""
        dir_path = PROJECT_ROOT / dir_name
        assert dir_path.exists(), f"Directory missing: {dir_path}"
        assert dir_path.is_dir(), f"Not a directory: {dir_path}"

    @pytest.mark.parametrize("init_file", REQUIRED_INIT_FILES)
    def test_init_file_exists(self, init_file):
        """Assert that each required __init__.py file exists."""
        file_path = PROJECT_ROOT / init_file
        assert file_path.exists(), f"Missing __init__.py: {file_path}"
        assert file_path.is_file(), f"Not a file: {file_path}"

    @pytest.mark.parametrize("readme_file", REQUIRED_READMES)
    def test_readme_exists(self, readme_file):
        """Assert that each required README.md file exists."""
        file_path = PROJECT_ROOT / readme_file
        assert file_path.exists(), f"Missing README: {file_path}"
        assert file_path.is_file(), f"Not a file: {file_path}"

    def test_state_project_directory_specific(self):
        """Assert the specific project state directory exists."""
        project_state_dir = (
            PROJECT_ROOT / "state" / "projects" / 
            "PROJ-036-exploring-the-impact-of-cosmic-microwave"
        )
        assert project_state_dir.exists(), f"Project state directory missing: {project_state_dir}"
        assert project_state_dir.is_dir(), f"Not a directory: {project_state_dir}"

    def test_no_unexpected_root_files(self):
        """Ensure no unexpected files are in the root (optional validation)."""
        # This is a soft check; we expect some files like README.md, setup scripts, etc.
        root_files = [f for f in PROJECT_ROOT.iterdir() if f.is_file()]
        # Just log for now; not a hard failure
        print(f"Root files: {[f.name for f in root_files]}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
