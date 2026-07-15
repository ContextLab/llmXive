"""
Unit tests for src.utils.state_manager.

These tests verify the state management functionality including:
- File and directory hashing
- State loading and saving
- Task history tracking
- Integrity verification
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path if running standalone
if "code" not in os.getcwd():
    os.chdir(Path(__file__).parent.parent.parent)

from src.utils.state_manager import (
    compute_file_hash,
    compute_directory_hash,
    load_state,
    save_state,
    update_state,
    get_state_summary,
    verify_file_integrity,
    log_task_start,
    log_task_complete,
    reset_state,
    STATE_FILE,
    STATE_DIR
)

class TestStateManager:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Backup existing state if present
        self.backup_state = None
        if STATE_FILE.exists():
            self.backup_state = STATE_FILE.read_text()
        
        # Create a temporary state directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.original_state_dir = STATE_DIR
        
        # Monkeypatch the state directory
        import src.utils.state_manager as sm
        sm.STATE_DIR = Path(self.temp_dir)
        sm.STATE_FILE = Path(self.temp_dir) / "project_state.json"
        sm.CHECKSUM_DIR = Path(self.temp_dir) / "checksums"
        
        yield

        # Restore original state
        if self.backup_state:
            STATE_FILE.write_text(self.backup_state)
        else:
            STATE_FILE.unlink(missing_ok=True)
        
        # Cleanup temp directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_compute_file_hash(self, tmp_path):
        """Test file hash computation."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        hash1 = compute_file_hash(test_file)
        hash2 = compute_file_hash(test_file)
        
        assert len(hash1) == 64  # SHA-256 hex length
        assert hash1 == hash2
        
        # Different content should produce different hash
        test_file.write_bytes(b"Different content")
        hash3 = compute_file_hash(test_file)
        assert hash1 != hash3

    def test_compute_file_hash_not_found(self, tmp_path):
        """Test that computing hash of non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            compute_file_hash(tmp_path / "nonexistent.txt")

    def test_compute_directory_hash(self, tmp_path):
        """Test directory hash computation."""
        # Create files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        
        hash1 = compute_directory_hash(tmp_path)
        
        # Same content should produce same hash
        hash2 = compute_directory_hash(tmp_path)
        assert hash1 == hash2

    def test_compute_directory_hash_empty(self, tmp_path):
        """Test directory hash of empty directory."""
        hash_val = compute_directory_hash(tmp_path)
        assert len(hash_val) == 64

    def test_load_state_empty(self):
        """Test loading state when file doesn't exist."""
        state = load_state()
        assert state["last_updated"] is None
        assert state["task_history"] == []
        assert state["file_checksums"] == {}
        assert state["project_hash"] is None

    def test_save_and_load_state(self, tmp_path):
        """Test saving and loading state."""
        import src.utils.state_manager as sm
        sm.STATE_DIR = Path(tmp_path)
        sm.STATE_FILE = Path(tmp_path) / "project_state.json"
        
        test_state = {
            "last_updated": "2023-01-01T00:00:00",
            "task_history": [{"task_id": "T001", "status": "completed"}],
            "file_checksums": {"file.txt": "abc123"},
            "project_hash": "def456",
            "seed_env": {"seed": 42}
        }
        
        save_state(test_state)
        loaded = load_state()
        
        assert loaded["last_updated"] == "2023-01-01T00:00:00"
        assert len(loaded["task_history"]) == 1
        assert loaded["file_checksums"]["file.txt"] == "abc123"

    def test_update_state(self, tmp_path):
        """Test updating state with artifacts."""
        import src.utils.state_manager as sm
        sm.STATE_DIR = Path(tmp_path)
        sm.STATE_FILE = Path(tmp_path) / "project_state.json"
        
        # Create a test file
        test_file = Path(tmp_path) / "test.txt"
        test_file.write_text("test content")
        
        artifacts = [{"path": str(test_file), "type": "file"}]
        
        updated_state = update_state(
            task_id="T005",
            artifacts=artifacts,
            extra_metadata={"test": "value"}
        )
        
        assert updated_state["last_updated"] is not None
        assert len(updated_state["task_history"]) == 1
        assert updated_state["task_history"][0]["task_id"] == "T005"
        assert updated_state["file_checksums"][str(test_file)]["hash"] is not None
        assert updated_state["project_hash"] is not None
        assert updated_state["seed_env"] is not None

    def test_verify_file_integrity_new_file(self, tmp_path):
        """Test verifying integrity of a new file (not in state)."""
        import src.utils.state_manager as sm
        sm.STATE_DIR = Path(tmp_path)
        sm.STATE_FILE = Path(tmp_path) / "project_state.json"
        
        test_file = Path(tmp_path) / "new.txt"
        test_file.write_text("content")
        
        # File not in state yet
        assert verify_file_integrity(str(test_file)) is False

    def test_verify_file_integrity_valid(self, tmp_path):
        """Test verifying integrity of a valid file."""
        import src.utils.state_manager as sm
        sm.STATE_DIR = Path(tmp_path)
        sm.STATE_FILE = Path(tmp_path) / "project_state.json"
        
        test_file = Path(tmp_path) / "test.txt"
        test_file.write_text("content")
        
        # Add to state
        update_state("T001", [{"path": str(test_file), "type": "file"}])
        
        # Should verify successfully
        assert verify_file_integrity(str(test_file)) is True

    def test_verify_file_integrity_tampered(self, tmp_path):
        """Test verifying integrity of a tampered file."""
        import src.utils.state_manager as sm
        sm.STATE_DIR = Path(tmp_path)
        sm.STATE_FILE = Path(tmp_path) / "project_state.json"
        
        test_file = Path(tmp_path) / "test.txt"
        test_file.write_text("original content")
        
        # Add to state
        update_state("T001", [{"path": str(test_file), "type": "file"}])
        
        # Tamper with file
        test_file.write_text("tampered content")
        
        # Should fail verification
        assert verify_file_integrity(str(test_file)) is False

    def test_log_task_start_and_complete(self, tmp_path):
        """Test logging task start and completion."""
        import src.utils.state_manager as sm
        sm.STATE_DIR = Path(tmp_path)
        sm.STATE_FILE = Path(tmp_path) / "project_state.json"
        
        test_file = Path(tmp_path) / "test.txt"
        test_file.write_text("content")
        
        log_task_start("T005")
        history = get_task_history()
        assert len(history) == 1
        assert history[0]["status"] == "started"
        
        log_task_complete(
            "T005",
            [{"path": str(test_file), "type": "file"}],
            success=True
        )
        
        history = get_task_history()
        assert history[0]["status"] == "completed"
        assert history[0]["success"] is True
        assert "completion_timestamp" in history[0]

    def test_get_state_summary(self, tmp_path):
        """Test getting state summary."""
        import src.utils.state_manager as sm
        sm.STATE_DIR = Path(tmp_path)
        sm.STATE_FILE = Path(tmp_path) / "project_state.json"
        
        summary = get_state_summary()
        
        assert "last_updated" in summary
        assert "total_tasks_run" in summary
        assert "tracked_files" in summary
        assert "project_hash" in summary
        assert "seed_env" in summary

    def test_reset_state(self, tmp_path):
        """Test resetting state."""
        import src.utils.state_manager as sm
        sm.STATE_DIR = Path(tmp_path)
        sm.STATE_FILE = Path(tmp_path) / "project_state.json"
        
        # Add some data
        update_state("T001", [])
        
        # Reset
        reset_state()
        
        # Verify empty
        state = load_state()
        assert state["task_history"] == []
        assert state["file_checksums"] == {}
        assert state["project_hash"] is None

    def test_directory_hash_changes_with_content(self, tmp_path):
        """Test that directory hash changes when content changes."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")
        
        hash1 = compute_directory_hash(tmp_path)
        
        file1.write_text("content2")
        hash2 = compute_directory_hash(tmp_path)
        
        assert hash1 != hash2

    def test_directory_hash_ignores_hidden_files(self, tmp_path):
        """Test that directory hash ignores hidden files."""
        (tmp_path / "visible.txt").write_text("visible")
        (tmp_path / ".hidden.txt").write_text("hidden")
        
        hash1 = compute_directory_hash(tmp_path)
        
        # Add another hidden file
        (tmp_path / ".hidden2.txt").write_text("hidden2")
        hash2 = compute_directory_hash(tmp_path)
        
        # Hash should be the same (hidden files ignored)
        assert hash1 == hash2

    def test_update_state_missing_artifact(self, tmp_path):
        """Test updating state with missing artifact path."""
        import src.utils.state_manager as sm
        sm.STATE_DIR = Path(tmp_path)
        sm.STATE_FILE = Path(tmp_path) / "project_state.json"
        
        # Try to update with non-existent file
        updated = update_state(
            "T005",
            [{"path": str(tmp_path / "nonexistent.txt"), "type": "file"}]
        )
        
        # Should not crash, just skip the missing file
        assert updated is not None
        assert len(updated["file_checksums"]) == 0
