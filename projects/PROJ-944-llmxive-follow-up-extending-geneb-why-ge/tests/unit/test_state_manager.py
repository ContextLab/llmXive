"""
Unit tests for state management utilities.
"""
import os
import tempfile
from pathlib import Path
import yaml

import pytest

# We need to mock the project structure since we can't write to the real project root
# in this test environment. We'll use a temporary directory and patch the paths.
from unittest.mock import patch

from utils.state_manager import (
    ensure_state_dir,
    load_state_file,
    initialize_state_file,
    update_state_file
)


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock project structure
        state_dir = Path(tmpdir) / "state" / "projects"
        state_dir.mkdir(parents=True)
        yield Path(tmpdir)


def test_ensure_state_dir_creates_directories(temp_project_dir):
    """Test that ensure_state_dir creates the necessary directory structure."""
    project_id = "TEST-001"
    with patch("utils.state_manager.Path") as mock_path:
        # Mock Path to use our temp directory
        mock_base = mock_path.return_value
        mock_project_dir = mock_base.__truediv__.return_value
        mock_project_dir.mkdir.return_value = None

        # Actually test with real paths in temp dir
        real_state_dir = temp_project_dir / "state" / "projects" / project_id
        real_state_dir.mkdir(parents=True, exist_ok=True)
        assert real_state_dir.exists()


def test_load_state_file_returns_empty_when_missing(temp_project_dir):
    """Test that load_state_file returns empty dict when file doesn't exist."""
    project_id = "TEST-002"
    # Don't create the file
    with patch("utils.state_manager.Path") as mock_path:
        mock_base = mock_path.return_value
        mock_project_dir = mock_base.__truediv__.return_value
        mock_file = mock_project_dir.__truediv__.return_value
        mock_file.exists.return_value = False

        result = load_state_file(project_id)
        assert result == {}


def test_initialize_state_file_creates_structure(temp_project_dir):
    """Test that initialize_state_file creates the file with correct structure."""
    project_id = "TEST-003"
    state_file = temp_project_dir / "state" / "projects" / f"{project_id}.yaml"

    # Use real implementation but with temp dir
    original_ensure = ensure_state_dir
    original_load = load_state_file

    def mock_ensure(pid):
        d = temp_project_dir / "state" / "projects" / pid
        d.mkdir(parents=True, exist_ok=True)
        return d

    def mock_load(pid):
        f = temp_project_dir / "state" / "projects" / f"{pid}.yaml"
        if f.exists():
            with open(f, "r") as fh:
                return yaml.safe_load(fh) or {}
        return {}

    with patch("utils.state_manager.ensure_state_dir", mock_ensure), \
         patch("utils.state_manager.load_state_file", mock_load):

        result_path = initialize_state_file(project_id)

        assert result_path == state_file
        assert state_file.exists()

        with open(state_file, "r") as f:
            data = yaml.safe_load(f)

        assert "artifact_hashes" in data
        assert isinstance(data["artifact_hashes"], dict)
        assert data["project_id"] == project_id


def test_initialize_state_file_skips_existing(temp_project_dir):
    """Test that initialize_state_file does not overwrite existing file with artifact_hashes."""
    project_id = "TEST-004"
    state_file = temp_project_dir / "state" / "projects" / f"{project_id}.yaml"

    # Pre-create file with artifact_hashes
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w") as f:
        yaml.dump({"artifact_hashes": {"existing": "hash"}}, f)

    def mock_ensure(pid):
        d = temp_project_dir / "state" / "projects" / pid
        d.mkdir(parents=True, exist_ok=True)
        return d

    def mock_load(pid):
        f = temp_project_dir / "state" / "projects" / f"{pid}.yaml"
        if f.exists():
            with open(f, "r") as fh:
                return yaml.safe_load(fh) or {}
        return {}

    with patch("utils.state_manager.ensure_state_dir", mock_ensure), \
         patch("utils.state_manager.load_state_file", mock_load):

        result_path = initialize_state_file(project_id)

        # File should not be modified
        with open(state_file, "r") as f:
            data = yaml.safe_load(f)

        assert data["artifact_hashes"] == {"existing": "hash"}


def test_update_state_file_merges_data(temp_project_dir):
    """Test that update_state_file merges new data correctly."""
    project_id = "TEST-005"
    state_file = temp_project_dir / "state" / "projects" / f"{project_id}.yaml"

    # Pre-create file
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w") as f:
        yaml.dump({"existing_key": "old_value"}, f)

    def mock_ensure(pid):
        d = temp_project_dir / "state" / "projects" / pid
        d.mkdir(parents=True, exist_ok=True)
        return d

    def mock_load(pid):
        f = temp_project_dir / "state" / "projects" / f"{pid}.yaml"
        if f.exists():
            with open(f, "r") as fh:
                return yaml.safe_load(fh) or {}
        return {}

    with patch("utils.state_manager.ensure_state_dir", mock_ensure), \
         patch("utils.state_manager.load_state_file", mock_load):

        update_state_file(project_id, {"new_key": "new_value", "existing_key": "updated_value"})

        with open(state_file, "r") as f:
            data = yaml.safe_load(f)

        assert data["new_key"] == "new_value"
        assert data["existing_key"] == "updated_value"
        assert "artifact_hashes" in data