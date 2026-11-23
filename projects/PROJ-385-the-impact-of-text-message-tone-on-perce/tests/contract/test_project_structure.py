"""
Contract test to verify project structure exists as required.
Checks that code/, data/, tests/ directories exist and README.md contains required sections.
"""
import os
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import get_project_root, get_data_dir, get_raw_data_dir, get_processed_data_dir
from config import get_consent_dir, get_results_dir, get_figures_dir
from config import get_code_dir, get_tests_dir, get_specs_dir


class TestProjectStructure:
    """Test suite for project structure validation."""

    def test_project_root_exists(self):
        """Verify project root directory exists."""
        project_root = get_project_root()
        assert project_root.exists(), f"Project root does not exist: {project_root}"
        assert project_root.is_dir(), f"Project root is not a directory: {project_root}"

    def test_code_directory_exists(self):
        """Verify code/ directory exists."""
        code_dir = get_code_dir()
        assert code_dir.exists(), f"code/ directory does not exist: {code_dir}"
        assert code_dir.is_dir(), f"code/ is not a directory: {code_dir}"

    def test_data_directory_exists(self):
        """Verify data/ directory exists."""
        data_dir = get_data_dir()
        assert data_dir.exists(), f"data/ directory does not exist: {data_dir}"
        assert data_dir.is_dir(), f"data/ is not a directory: {data_dir}"

    def test_data_subdirectories_exist(self):
        """Verify all required data subdirectories exist."""
        data_dir = get_data_dir()
        subdirs = [
            get_raw_data_dir(),
            get_processed_data_dir(),
            get_consent_dir(),
            get_results_dir(),
            get_figures_dir(),
        ]
        
        for subdir in subdirs:
            assert subdir.exists(), f"Data subdirectory does not exist: {subdir}"
            assert subdir.is_dir(), f"Data subdirectory is not a directory: {subdir}"

    def test_tests_directory_exists(self):
        """Verify tests/ directory exists."""
        tests_dir = get_tests_dir()
        assert tests_dir.exists(), f"tests/ directory does not exist: {tests_dir}"
        assert tests_dir.is_dir(), f"tests/ is not a directory: {tests_dir}"

    def test_readme_exists(self):
        """Verify README.md exists at project root."""
        project_root = get_project_root()
        readme_path = project_root / "README.md"
        assert readme_path.exists(), f"README.md does not exist at: {readme_path}"
        assert readme_path.is_file(), f"README.md is not a file: {readme_path}"

    def test_readme_contains_project_overview(self):
        """Verify README.md contains 'Project Overview' section."""
        project_root = get_project_root()
        readme_path = project_root / "README.md"
        
        content = readme_path.read_text(encoding="utf-8")
        assert "Project Overview" in content, (
            "README.md must contain 'Project Overview' section"
        )

    def test_readme_contains_cli_usage(self):
        """Verify README.md contains 'CLI Usage' section."""
        project_root = get_project_root()
        readme_path = project_root / "README.md"
        
        content = readme_path.read_text(encoding="utf-8")
        assert "CLI Usage" in content, (
            "README.md must contain 'CLI Usage' section"
        )

    def test_readme_contains_reproducibility(self):
        """Verify README.md contains 'Reproducibility' section."""
        project_root = get_project_root()
        readme_path = project_root / "README.md"
        
        content = readme_path.read_text(encoding="utf-8")
        assert "Reproducibility" in content, (
            "README.md must contain 'Reproducibility' section"
        )

    def test_gitkeep_files_exist(self):
        """Verify .gitkeep files exist in data subdirectories."""
        data_subdirs = [
            get_raw_data_dir(),
            get_processed_data_dir(),
            get_consent_dir(),
            get_results_dir(),
            get_figures_dir(),
        ]
        
        for subdir in data_subdirs:
            gitkeep = subdir / ".gitkeep"
            assert gitkeep.exists(), (
                f".gitkeep file missing in {subdir}"
            )
