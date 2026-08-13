"""
Unit tests for T004: Setup state/ and docs/ directories.
Verifies that os.path.isdir returns True for the required paths.
"""
import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_state_docs import setup_state_docs_directories, verify_state_docs_directories


class TestSetupStateDocs:
    """Test cases for state/docs directory setup."""

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory to act as project root."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_setup_creates_state_directory(self, temp_project_root):
        """Test that setup creates the 'state' directory."""
        result = setup_state_docs_directories(temp_project_root)
        state_path = temp_project_root / "state"
        assert state_path.exists(), "state/ directory should exist after setup"
        assert state_path.is_dir(), "state/ should be a directory"
        assert str(state_path) in result, "state/ path should be in created list"

    def test_setup_creates_docs_directory(self, temp_project_root):
        """Test that setup creates the 'docs' directory."""
        result = setup_state_docs_directories(temp_project_root)
        docs_path = temp_project_root / "docs"
        assert docs_path.exists(), "docs/ directory should exist after setup"
        assert docs_path.is_dir(), "docs/ should be a directory"
        assert str(docs_path) in result, "docs/ path should be in created list"

    def test_verify_state_directory_exists(self, temp_project_root):
        """Test verification of existing state directory."""
        # Setup first
        setup_state_docs_directories(temp_project_root)
        # Then verify
        assert verify_state_docs_directories(temp_project_root) is True

    def test_verify_docs_directory_exists(self, temp_project_root):
        """Test verification of existing docs directory."""
        # Setup first
        setup_state_docs_directories(temp_project_root)
        # Then verify
        assert verify_state_docs_directories(temp_project_root) is True

    def test_verify_fails_when_state_missing(self, temp_project_root):
        """Test that verification fails if state directory is missing."""
        # Only create docs, not state
        (temp_project_root / "docs").mkdir()
        assert verify_state_docs_directories(temp_project_root) is False

    def test_verify_fails_when_docs_missing(self, temp_project_root):
        """Test that verification fails if docs directory is missing."""
        # Only create state, not docs
        (temp_project_root / "state").mkdir()
        assert verify_state_docs_directories(temp_project_root) is False

    def test_os_path_isdir_assertions(self, temp_project_root):
        """
        Explicitly test os.path.isdir assertions as required by T004.
        """
        # Setup
        setup_state_docs_directories(temp_project_root)

        state_path = temp_project_root / "state"
        docs_path = temp_project_root / "docs"

        # Assert True for both as per task verification requirement
        assert os.path.isdir(str(state_path)) is True, "os.path.isdir(state/) must be True"
        assert os.path.isdir(str(docs_path)) is True, "os.path.isdir(docs/) must be True"

    def test_setup_idempotent(self, temp_project_root):
        """Test that running setup twice doesn't cause errors."""
        result1 = setup_state_docs_directories(temp_project_root)
        result2 = setup_state_docs_directories(temp_project_root)
        # Both runs should succeed
        assert len(result1) > 0 or (temp_project_root / "state").exists()
        assert len(result2) > 0 or (temp_project_root / "state").exists()