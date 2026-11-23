"""
Unit tests for code/setup_dirs.py (T001 Implementation).

Verifies that the setup script creates the required directory structure
and initializes the state file correctly.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path for imports
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_dirs import ensure_directory, initialize_state_file, REQUIRED_DIRS, PROJECT_NAME

class TestSetupDirs:
    """Test suite for directory setup functionality."""

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory to act as the project root."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_ensure_directory_creates_new(self, temp_project_root):
        """Test that ensure_directory creates a new directory."""
        new_dir = temp_project_root / "test_new_dir"
        assert not new_dir.exists()
        
        result = ensure_directory(new_dir)
        
        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_exists(self, temp_project_root):
        """Test that ensure_directory returns True for existing directory."""
        existing_dir = temp_project_root / "existing_dir"
        existing_dir.mkdir(parents=True)
        
        result = ensure_directory(existing_dir)
        
        assert result is True

    def test_initialize_state_file_creates_new(self, temp_project_root):
        """Test that initialize_state_file creates a new state file."""
        state_dir = temp_project_root / "state" / "projects" / PROJECT_NAME
        state_file = state_dir / "project_state.yaml"
        
        assert not state_file.exists()
        
        result = initialize_state_file(state_file)
        
        assert result is True
        assert state_file.exists()
        assert state_file.stat().st_size > 0
        
        # Check basic content
        content = state_file.read_text()
        assert "project_id" in content
        assert PROJECT_NAME in content

    def test_initialize_state_file_exists(self, temp_project_root):
        """Test that initialize_state_file handles existing files gracefully."""
        state_dir = temp_project_root / "state" / "projects" / PROJECT_NAME
        state_file = state_dir / "project_state.yaml"
        state_dir.mkdir(parents=True)
        state_file.write_text("existing content")
        
        result = initialize_state_file(state_file)
        
        assert result is True
        # Content should remain unchanged
        assert state_file.read_text() == "existing content"

    def test_required_dirs_list_not_empty(self):
        """Test that REQUIRED_DIRS is populated."""
        assert len(REQUIRED_DIRS) > 0
        assert "data/raw" in REQUIRED_DIRS
        assert "data/processed" in REQUIRED_DIRS
        assert "state" in REQUIRED_DIRS
        assert "reports" in REQUIRED_DIRS

    def test_full_structure_creation(self, temp_project_root):
        """Test creating the full structure in a temporary root."""
        # Temporarily override the logic to use our temp root
        # We will manually call ensure_directory for each required dir
        success_count = 0
        for dir_str in REQUIRED_DIRS:
            dir_path = temp_project_root / dir_str
            if ensure_directory(dir_path):
                success_count += 1
        
        # All should succeed
        assert success_count == len(REQUIRED_DIRS)
        
        # Verify a few key directories exist
        assert (temp_project_root / "data" / "raw").exists()
        assert (temp_project_root / "data" / "processed").exists()
        assert (temp_project_root / "reports" / "metrics").exists()
        assert (temp_project_root / "tests" / "unit").exists()
        assert (temp_project_root / "state" / "projects" / PROJECT_NAME).exists()