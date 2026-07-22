"""
Unit Tests for the State Manager Module.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import time

# We need to temporarily override the module's global paths for testing
import src.utils.state_manager as sm

@pytest.fixture
def temp_state_dir():
    """Create a temporary directory to act as the project root for testing."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)

    # Monkeypatch the module's constants to use the temp directory
    sm.STATE_DIR = Path(temp_dir) / "state"
    sm.STATE_FILE_PATH = sm.STATE_DIR / "state.json"

    yield temp_dir

    # Cleanup
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def clean_state(temp_state_dir):
    """Ensure state is reset before each test."""
    sm.reset_state()
    return sm.load_state()


class TestStateManager:

    def test_ensure_state_dir_creation(self, temp_state_dir):
        """Test that the state directory is created if it doesn't exist."""
        # Initially, the dir might not exist if we just created temp dir
        # But calling load_state should trigger creation
        sm.load_state()
        assert sm.STATE_DIR.exists()
        assert sm.STATE_DIR.is_dir()

    def test_compute_file_hash(self, temp_state_dir):
        """Test file hashing functionality."""
        test_file = Path("test_file.txt")
        content = "Hello, World!"
        test_file.write_text(content)

        file_hash = sm.compute_file_hash(test_file)
        assert len(file_hash) == 64  # SHA-256 hex length

        # Verify content change changes hash
        test_file.write_text("Different content")
        new_hash = sm.compute_file_hash(test_file)
        assert file_hash != new_hash

    def test_compute_file_hash_not_found(self, temp_state_dir):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            sm.compute_file_hash(Path("non_existent.txt"))

    def test_compute_directory_hash(self, temp_state_dir):
        """Test directory hashing functionality."""
        # Create a deterministic structure
        Path("subdir").mkdir()
        Path("file1.txt").write_text("A")
        Path("subdir/file2.txt").write_text("B")

        dir_hash = sm.compute_directory_hash(Path("."))
        assert len(dir_hash) == 64

        # Change a file, hash should change
        Path("file1.txt").write_text("C")
        new_dir_hash = sm.compute_directory_hash(Path("."))
        assert dir_hash != new_dir_hash

    def test_load_state_initial(self, clean_state):
        """Test loading initial state."""
        state = clean_state
        assert state["project_id"] == "PROJ-165"
        assert state["task_history"] == []
        assert "data_integrity" in state

    def test_save_and_load_state(self, temp_state_dir):
        """Test saving and loading custom state."""
        custom_state = {
            "project_id": "TEST-001",
            "last_updated": 12345,
            "task_history": [{"task_id": "T001", "status": "completed"}],
            "data_integrity": {},
            "config_hashes": {}
        }
        sm.save_state(custom_state)

        loaded = sm.load_state()
        assert loaded["project_id"] == "TEST-001"
        assert len(loaded["task_history"]) == 1

    def test_update_state(self, temp_state_dir):
        """Test updating state with a task record."""
        sm.update_state("T005", "started", {"start_time": time.time()})
        state = sm.load_state()

        assert len(state["task_history"]) == 1
        assert state["task_history"][0]["task_id"] == "T005"
        assert state["task_history"][0]["status"] == "started"

    def test_log_task_start(self, temp_state_dir):
        """Test logging task start."""
        sm.log_task_start("T010")
        state = sm.load_state()
        assert state["task_history"][0]["status"] == "started"

    def test_log_task_complete(self, temp_state_dir):
        """Test logging task completion."""
        sm.log_task_start("T011")
        time.sleep(0.1) # Small delay to ensure duration > 0
        sm.log_task_complete("T011", duration=0.15)

        history = sm.get_task_history("T011")
        assert len(history) == 2
        assert history[1]["status"] == "completed"
        assert history[1]["details"]["duration_seconds"] == 0.15

    def test_verify_file_integrity(self, temp_state_dir):
        """Test file integrity verification."""
        test_file = Path("verify_test.txt")
        test_file.write_text("integrity check")

        # First, compute and store hash
        h = sm.compute_file_hash(test_file)
        sm.update_state("T000", "completed", {"data_hash": h, "data_file": "verify_test.txt"})

        # Verify should pass
        assert sm.verify_file_integrity(test_file) is True

        # Modify file
        test_file.write_text("tampered")
        assert sm.verify_file_integrity(test_file) is False

    def test_get_state_summary(self, temp_state_dir):
        """Test state summary generation."""
        sm.log_task_start("T001")
        sm.log_task_complete("T001")
        sm.log_task_start("T002")
        sm.log_task_complete("T002", status="failed") # Note: log_task_complete defaults to completed, need to hack or just test counts

        # Actually log_task_complete forces 'completed'. Let's manually add a failed one for variety if needed,
        # but for now just test the counts based on what we have.
        # We have 2 completed tasks from the calls above.

        summary = sm.get_state_summary()
        assert summary["total_tasks"] >= 2
        assert summary["completed"] >= 2

    def test_reset_state(self, temp_state_dir):
        """Test resetting the state."""
        sm.log_task_start("T999")
        sm.reset_state()
        state = sm.load_state()
        assert len(state["task_history"]) == 0
        assert state["project_id"] == "PROJ-165"

    def test_compute_directory_hash_ignore_patterns(self, temp_state_dir):
        """Test directory hash with ignore patterns."""
        Path("keep.txt").write_text("A")
        Path("ignore.tmp").write_text("B")
        Path("__pycache__").mkdir()
        Path("__pycache__/cache.pyc").write_text("C")

        # Without ignore
        h1 = sm.compute_directory_hash(Path("."))

        # With ignore
        h2 = sm.compute_directory_hash(Path("."), ignore_patterns=[".tmp", "__pycache__"])

        # Hashes should differ because ignored files are excluded from calculation
        assert h1 != h2