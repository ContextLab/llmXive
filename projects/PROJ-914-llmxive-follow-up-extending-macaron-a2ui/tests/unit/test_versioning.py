"""
Unit tests for code/utils/versioning.py.
"""

import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
# We need to add the parent of 'code' to sys.path to import 'code.utils.versioning'
import sys
from pathlib import Path

# Get the project root (parent of 'code')
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.utils.versioning import (
    _should_exclude,
    _compute_file_hash,
    _compute_directory_hash,
    compute_version_state,
    update_state_file,
    get_latest_state,
    EXCLUDED_PATTERNS
)


class TestShouldExclude:
    def test_excludes_pycache(self):
        path = Path("code/utils/__pycache__/module.cpython-311.pyc")
        assert _should_exclude(path) is True

    def test_excludes_git_dir(self):
        path = Path("code/.git/config")
        assert _should_exclude(path) is True

    def test_excludes_hidden_files(self):
        path = Path("code/.env")
        assert _should_exclude(path) is True

    def test_includes_gitkeep(self):
        path = Path("data/.gitkeep")
        assert _should_exclude(path) is False

    def test_includes_normal_file(self):
        path = Path("code/utils/versioning.py")
        assert _should_exclude(path) is False


class TestComputeFileHash:
    def test_hash_consistency(self, tmp_path):
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        hash1 = _compute_file_hash(test_file)
        hash2 = _compute_file_hash(test_file)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_hash_changes_with_content(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Content A")
        hash_a = _compute_file_hash(test_file)

        test_file.write_bytes(b"Content B")
        hash_b = _compute_file_hash(test_file)

        assert hash_a != hash_b


class TestComputeDirectoryHash:
    def test_empty_directory(self, tmp_path):
        # Create an empty directory
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        dir_hash = _compute_directory_hash(empty_dir)
        # Should be hash of empty string effectively
        assert len(dir_hash) == 64

    def test_directory_with_files(self, tmp_path):
        dir_a = tmp_path / "dir_a"
        dir_a.mkdir()
        (dir_a / "file1.txt").write_text("Content 1")
        (dir_a / "file2.txt").write_text("Content 2")

        hash1 = _compute_directory_hash(dir_a)

        # Change order or content
        (dir_a / "file2.txt").write_text("Modified Content 2")
        hash2 = _compute_directory_hash(dir_a)

        assert hash1 != hash2

    def test_deterministic_ordering(self, tmp_path):
        dir_a = tmp_path / "dir_a"
        dir_a.mkdir()
        (dir_a / "b_file.txt").write_text("B")
        (dir_a / "a_file.txt").write_text("A")

        hash1 = _compute_directory_hash(dir_a)
        hash2 = _compute_directory_hash(dir_a)
        assert hash1 == hash2


class TestComputeVersionState:
    @patch("code.utils.versioning.PROJECT_ROOT")
    @patch("code.utils.versioning.CODE_DIR")
    @patch("code.utils.versioning.DATA_DIR")
    def test_returns_expected_keys(self, mock_data_dir, mock_code_dir, mock_project_root, tmp_path):
        # Setup mocks to point to temp dirs
        mock_project_root.__truediv__.return_value = tmp_path
        mock_code_dir.__truediv__.return_value = tmp_path / "code"
        mock_data_dir.__truediv__.return_value = tmp_path / "data"

        (tmp_path / "code").mkdir()
        (tmp_path / "data").mkdir()

        state = compute_version_state()

        assert "timestamp" in state
        assert "code_hash" in state
        assert "data_hash" in state
        assert "git_commit" in state
        assert len(state["code_hash"]) == 64
        assert len(state["data_hash"]) == 64


class TestUpdateStateFile:
    def test_creates_file_if_not_exists(self, tmp_path):
        state_dir = tmp_path / "state"
        state_file = state_dir / "version_state.yaml"

        # Patch the constants
        with patch("code.utils.versioning.STATE_DIR", state_dir), \
             patch("code.utils.versioning.STATE_FILE", state_file):
            state = {
                "timestamp": "2023-01-01T00:00:00Z",
                "code_hash": "a" * 64,
                "data_hash": "b" * 64,
                "git_commit": None
            }
            result_path = update_state_file(state, append_history=False)

            assert result_path == state_file
            assert state_file.exists()

            with open(state_file, "r") as f:
                data = yaml.safe_load(f)

            assert data["code_hash"] == "a" * 64
            assert data["data_hash"] == "b" * 64

    def test_appends_to_history(self, tmp_path):
        state_dir = tmp_path / "state"
        state_file = state_dir / "version_state.yaml"
        state_dir.mkdir()

        # Create initial state
        initial_state = {
            "latest": {"code_hash": "initial", "data_hash": "initial", "timestamp": "T1", "git_commit": None},
            "history": [{"run_id": "old", "code_hash": "initial"}]
        }
        with open(state_file, "w") as f:
            yaml.dump(initial_state, f)

        new_state = {
            "timestamp": "2023-01-02T00:00:00Z",
            "code_hash": "new_code",
            "data_hash": "new_data",
            "git_commit": "abc123"
        }

        with patch("code.utils.versioning.STATE_DIR", state_dir), \
             patch("code.utils.versioning.STATE_FILE", state_file):
            update_state_file(new_state, append_history=True)

        with open(state_file, "r") as f:
            data = yaml.safe_load(f)

        assert len(data["history"]) == 2
        assert data["history"][-1]["code_hash"] == "new_code"
        assert data["latest"]["code_hash"] == "new_code"


class TestGetLatestState:
    def test_returns_none_if_not_exists(self, tmp_path):
        state_dir = tmp_path / "state"
        state_file = state_dir / "version_state.yaml"

        with patch("code.utils.versioning.STATE_FILE", state_file):
            result = get_latest_state()
            assert result is None

    def test_returns_latest(self, tmp_path):
        state_dir = tmp_path / "state"
        state_file = state_dir / "version_state.yaml"
        state_dir.mkdir()

        data = {
            "latest": {"code_hash": "test", "data_hash": "test", "timestamp": "T1", "git_commit": None}
        }
        with open(state_file, "w") as f:
            yaml.dump(data, f)

        with patch("code.utils.versioning.STATE_FILE", state_file):
            result = get_latest_state()
            assert result["code_hash"] == "test"