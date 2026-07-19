import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
import pytest

from src.sim.exclusion_logger import (
    set_exclusion_path,
    log_excluded_trajectory,
    log_excluded_trajectories,
    get_exclusion_log,
    clear_exclusion_log
)

class TestExclusionLogger:
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_log_path = os.path.join(self.temp_dir, "excluded_log.json")
        clear_exclusion_log()

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        clear_exclusion_log()

    def test_set_exclusion_path_creates_directory(self):
        """Test that set_exclusion_path creates the directory if it doesn't exist."""
        new_path = os.path.join(self.temp_dir, "subdir", "excluded_log.json")
        set_exclusion_path(new_path)
        assert os.path.exists(os.path.dirname(new_path))

    def test_log_excluded_trajectory_adds_entry(self):
        """Test that logging an excluded trajectory adds an entry to the log."""
        set_exclusion_path(self.test_log_path)
        log_excluded_trajectory(
            trajectory_id="test_123",
            exclusion_reason="Test reason",
            ambiguity_reason="test_ambiguity"
        )
        
        log = get_exclusion_log()
        assert len(log) == 1
        assert log[0]["trajectory_id"] == "test_123"
        assert log[0]["exclusion_reason"] == "Test reason"
        assert log[0]["ambiguity_reason"] == "test_ambiguity"
        assert "timestamp" in log[0]

    def test_log_excluded_trajectory_writes_to_disk(self):
        """Test that logging an excluded trajectory writes to the specified file."""
        set_exclusion_path(self.test_log_path)
        log_excluded_trajectory(
            trajectory_id="test_123",
            exclusion_reason="Test reason"
        )
        
        assert os.path.exists(self.test_log_path)
        with open(self.test_log_path, 'r') as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["trajectory_id"] == "test_123"

    def test_log_excluded_trajectories_handles_multiple(self):
        """Test that logging multiple excluded trajectories works correctly."""
        set_exclusion_path(self.test_log_path)
        entries = [
            {
                "trajectory_id": "test_1",
                "exclusion_reason": "Reason 1",
                "ambiguity_reason": "ambig_1"
            },
            {
                "trajectory_id": "test_2",
                "exclusion_reason": "Reason 2",
                "ambiguity_reason": "ambig_2"
            }
        ]
        log_excluded_trajectories(entries)
        
        log = get_exclusion_log()
        assert len(log) == 2
        assert log[0]["trajectory_id"] == "test_1"
        assert log[1]["trajectory_id"] == "test_2"

    def test_clear_exclusion_log_works(self):
        """Test that clearing the exclusion log removes all entries."""
        set_exclusion_path(self.test_log_path)
        log_excluded_trajectory(
            trajectory_id="test_123",
            exclusion_reason="Test reason"
        )
        
        clear_exclusion_log()
        log = get_exclusion_log()
        assert len(log) == 0

    def test_optional_fields_are_handled_correctly(self):
        """Test that optional fields are handled correctly when not provided."""
        set_exclusion_path(self.test_log_path)
        log_excluded_trajectory(
            trajectory_id="test_123",
            exclusion_reason="Test reason"
        )
        
        log = get_exclusion_log()
        assert log[0]["ambiguity_reason"] is None
        assert log[0]["ground_truth_snapshot_id"] is None
        assert log[0]["action_log_preview"] == []

    def test_action_log_preview_is_truncated(self):
        """Test that action log preview is correctly included."""
        set_exclusion_path(self.test_log_path)
        preview = [{"step": 1, "action": "test"}, {"step": 2, "action": "test2"}]
        log_excluded_trajectory(
            trajectory_id="test_123",
            exclusion_reason="Test reason",
            action_log_preview=preview
        )
        
        log = get_exclusion_log()
        assert log[0]["action_log_preview"] == preview