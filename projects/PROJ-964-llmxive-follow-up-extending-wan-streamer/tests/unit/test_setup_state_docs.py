import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

from setup_state_docs import setup_state_docs_directories


class TestSetupStateDocs:
    """Unit tests for T004: Create state/ and docs/ directories."""

    def test_state_directory_created(self, tmp_path: Path):
        """Verify that the state/ directory is created."""
        setup_state_docs_directories(tmp_path)
        assert (tmp_path / "state").exists()
        assert (tmp_path / "state").is_dir()

    def test_docs_directory_created(self, tmp_path: Path):
        """Verify that the docs/ directory is created."""
        setup_state_docs_directories(tmp_path)
        assert (tmp_path / "docs").exists()
        assert (tmp_path / "docs").is_dir()

    def test_state_subdirectories_created(self, tmp_path: Path):
        """Verify that state/ subdirectories are created."""
        setup_state_docs_directories(tmp_path)
        assert (tmp_path / "state" / "projects").exists()
        assert (tmp_path / "state" / "artifacts").exists()

    def test_docs_subdirectories_created(self, tmp_path: Path):
        """Verify that docs/ subdirectories are created."""
        setup_state_docs_directories(tmp_path)
        assert (tmp_path / "docs" / "api").exists()
        assert (tmp_path / "docs" / "design").exists()

    def test_readme_files_created(self, tmp_path: Path):
        """Verify that README.md files are created in state/ and docs/."""
        setup_state_docs_directories(tmp_path)
        assert (tmp_path / "state" / "README.md").exists()
        assert (tmp_path / "docs" / "README.md").exists()

    def test_readme_content(self, tmp_path: Path):
        """Verify that README.md files contain expected content."""
        setup_state_docs_directories(tmp_path)
        state_readme = (tmp_path / "state" / "README.md").read_text()
        docs_readme = (tmp_path / "docs" / "README.md").read_text()
        
        assert "Project State" in state_readme
        assert "state/projects" in state_readme
        assert "Project Documentation" in docs_readme
        assert "docs/api" in docs_readme

    def test_idempotent_creation(self, tmp_path: Path):
        """Verify that running the function twice doesn't cause errors."""
        setup_state_docs_directories(tmp_path)
        # Second call should not raise
        setup_state_docs_directories(tmp_path)
        assert (tmp_path / "state").exists()
        assert (tmp_path / "docs").exists()