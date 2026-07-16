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
    clear_exclusion_log,
    run,
)


class TestExclusionLogger:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # Setup: create temp dir for test output
        self.temp_dir = tempfile.mkdtemp()
        self.test_log_path = os.path.join(self.temp_dir, "test_excluded.json")
        
        # Reset state
        clear_exclusion_log()
        set_exclusion_path(self.test_log_path)
        
        yield
        
        # Teardown: remove temp dir
        shutil.rmtree(self.temp_dir)

    def test_log_single_trajectory(self):
        log_excluded_trajectory(
            trajectory_id="traj-123",
            reason="ambiguous root cause",
            details={"step": 5, "action": "pick"}
        )
        
        log = get_exclusion_log()
        assert len(log) == 1
        assert log[0]["trajectory_id"] == "traj-123"
        assert log[0]["reason"] == "ambiguous root cause"
        assert "timestamp" in log[0]

    def test_log_multiple_trajectories(self):
        entries = [
            {"trajectory_id": "traj-1", "reason": "ambiguous", "details": {}},
            {"trajectory_id": "traj-2", "reason": "validation fail", "details": {}},
        ]
        log_excluded_trajectories(entries)
        
        log = get_exclusion_log()
        assert len(log) == 2
        assert log[0]["trajectory_id"] == "traj-1"
        assert log[1]["trajectory_id"] == "traj-2"

    def test_missing_required_fields(self):
        with pytest.raises(ValueError):
            log_excluded_trajectories([{"trajectory_id": "traj-1"}])

    def test_clear_log(self):
        log_excluded_trajectory("traj-1", "reason")
        assert len(get_exclusion_log()) == 1
        
        clear_exclusion_log()
        assert len(get_exclusion_log()) == 0

    def test_persist_to_disk(self):
        log_excluded_trajectory("traj-1", "ambiguous root cause")
        
        run()
        
        assert os.path.exists(self.test_log_path)
        with open(self.test_log_path, "r") as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["trajectory_id"] == "traj-1"

    def test_persist_creates_directories(self):
        deep_path = os.path.join(self.temp_dir, "sub", "deep", "excluded.json")
        set_exclusion_path(deep_path)
        log_excluded_trajectory("traj-1", "reason")
        
        run()
        
        assert os.path.exists(deep_path)