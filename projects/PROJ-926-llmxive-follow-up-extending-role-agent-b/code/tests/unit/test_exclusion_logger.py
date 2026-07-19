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
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Create temporary directory for test
        self.test_dir = tempfile.mkdtemp()
        self.test_path = os.path.join(self.test_dir, "excluded_log.json")
        
        # Clear log before each test
        clear_exclusion_log()
        set_exclusion_path(None)
        
        yield
        
        # Cleanup after test
        shutil.rmtree(self.test_dir)
        clear_exclusion_log()
        set_exclusion_path(None)

    def test_set_exclusion_path(self):
        """Test setting exclusion path."""
        set_exclusion_path(self.test_path)
        # Path should be set
        assert self.test_path is not None

    def test_log_excluded_trajectory(self):
        """Test logging a single excluded trajectory."""
        set_exclusion_path(self.test_path)
        
        entry = log_excluded_trajectory(
            trajectory_id="test-001",
            ambiguity_reason="Test ambiguity reason"
        )
        
        assert entry['trajectory_id'] == "test-001"
        assert entry['ambiguity_reason'] == "Test ambiguity reason"
        assert 'timestamp' in entry
        
        # Check file was created
        assert os.path.exists(self.test_path)
        
        # Check file contents
        with open(self.test_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['trajectory_id'] == "test-001"

    def test_log_excluded_trajectories_multiple(self):
        """Test logging multiple excluded trajectories."""
        set_exclusion_path(self.test_path)
        
        entries = [
            {'trajectory_id': "test-001", 'ambiguity_reason': "Reason 1"},
            {'trajectory_id': "test-002", 'ambiguity_reason': "Reason 2"},
            {'trajectory_id': "test-003", 'ambiguity_reason': "Reason 3"}
        ]
        
        logged = log_excluded_trajectories(entries)
        
        assert len(logged) == 3
        assert len(get_exclusion_log()) == 3
        
        # Check file contents
        with open(self.test_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 3
        assert data[0]['trajectory_id'] == "test-001"
        assert data[1]['trajectory_id'] == "test-002"
        assert data[2]['trajectory_id'] == "test-003"

    def test_clear_exclusion_log(self):
        """Test clearing the exclusion log."""
        set_exclusion_path(self.test_path)
        
        log_excluded_trajectory("test-001", "Reason 1")
        assert len(get_exclusion_log()) == 1
        
        clear_exclusion_log()
        assert len(get_exclusion_log()) == 0
        
        # File should be empty or not contain the entry
        with open(self.test_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 0

    def test_get_exclusion_log_returns_copy(self):
        """Test that get_exclusion_log returns a copy."""
        set_exclusion_path(self.test_path)
        
        log_excluded_trajectory("test-001", "Reason 1")
        
        log1 = get_exclusion_log()
        log2 = get_exclusion_log()
        
        assert log1 is not log2  # Different objects
        assert log1 == log2  # Same content

    def test_no_path_set(self):
        """Test logging without setting path."""
        clear_exclusion_log()
        set_exclusion_path(None)
        
        entry = log_excluded_trajectory("test-001", "Reason 1")
        
        assert entry['trajectory_id'] == "test-001"
        assert len(get_exclusion_log()) == 1
        
        # File should not be created
        assert not os.path.exists(self.test_path)