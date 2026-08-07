import pytest
import os
import json
import sys
import tempfile
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.logging import setup_logging, log_seed_usage, log_blocked_operation, log_execution_step, extract_blocked_operations

class TestLogging:
    def test_setup_logging_creates_file(self, tmp_path):
        """Test that setup_logging creates the log file."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(str(log_file))

        assert log_file.exists()

    def test_log_seed_usage(self, tmp_path):
        """Test that seed usage is logged correctly."""
        log_file = tmp_path / "seed.log"
        logger = setup_logging(str(log_file))

        log_seed_usage(logger, seed=42, run_id=1)

        with open(log_file) as f:
            line = f.readline()
            data = json.loads(line)
            assert data['seed'] == 42
            assert data['run_id'] == 1

    def test_log_blocked_operation(self, tmp_path):
        """Test that blocked operations are logged correctly."""
        log_file = tmp_path / "blocked.log"
        logger = setup_logging(str(log_file))

        log_blocked_operation(logger, "trimesh import", 123.45, "task-123")

        with open(log_file) as f:
            line = f.readline()
            data = json.loads(line)
            assert data['blocked_operation'] == "trimesh import"
            assert data['blocked_time_ms'] == 123.45
            assert data['task_id'] == "task-123"

    def test_extract_blocked_operations(self, tmp_path):
        """Test extraction of blocked operations from log file."""
        log_file = tmp_path / "extract.log"
        logger = setup_logging(str(log_file))

        log_blocked_operation(logger, "op1", 10.0, "t1")
        log_blocked_operation(logger, "op2", 20.0, "t2")

        blocked = extract_blocked_operations(str(log_file))

        assert len(blocked) == 2
        assert blocked[0]['blocked_operation'] == "op1"
        assert blocked[1]['blocked_operation'] == "op2"
