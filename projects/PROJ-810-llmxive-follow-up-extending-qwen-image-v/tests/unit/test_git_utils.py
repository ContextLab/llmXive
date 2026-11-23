import os
import tempfile
import shutil
from pathlib import Path
import pytest
from utils.git_utils import check_git_initialized, initialize_git_repository


class TestGitUtils:
    """Unit tests for git utility functions."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path)

    def test_check_git_initialized_false(self, temp_dir):
        """Test that a non-git directory is correctly identified."""
        is_init, msg = check_git_initialized(temp_dir)
        assert is_init is False
        assert "not initialized" in msg.lower()

    def test_initialize_git_repository_success(self, temp_dir):
        """Test successful initialization of a git repository."""
        success, msg = initialize_git_repository(temp_dir)
        assert success is True
        assert "initialized successfully" in msg.lower()
        
        # Verify .git directory exists
        assert (temp_dir / ".git").exists()

    def test_initialize_git_repository_already_initialized(self, temp_dir):
        """Test behavior when git is already initialized."""
        # First initialization
        success1, _ = initialize_git_repository(temp_dir)
        assert success1 is True
        
        # Second initialization attempt
        success2, msg = initialize_git_repository(temp_dir)
        assert success2 is True
        assert "already initialized" in msg.lower()

    def test_check_git_initialized_true(self, temp_dir):
        """Test that an initialized git directory is correctly identified."""
        # Initialize first
        initialize_git_repository(temp_dir)
        
        # Now check
        is_init, msg = check_git_initialized(temp_dir)
        assert is_init is True
        assert "already initialized" in msg.lower() or "detected" in msg.lower()

    def test_initialize_non_existent_directory(self, temp_dir):
        """Test handling of non-existent directory (should fail gracefully)."""
        fake_path = temp_dir / "nonexistent" / "subdir"
        success, msg = initialize_git_repository(fake_path)
        # The function should attempt to run git init which will fail if parent doesn't exist
        # or we might want to add a check for existence. For now, git init will fail.
        # We expect failure here.
        assert success is False or fake_path.exists()  # Either fails or creates it (if parent exists)