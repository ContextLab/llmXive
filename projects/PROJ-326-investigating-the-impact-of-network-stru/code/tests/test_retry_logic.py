"""
Unit tests for T018b: Retry Logic for Disconnected Networks
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from code.src.generators.retry_logic import (
    load_retry_config,
    log_retry_failure,
    should_proceed_to_next_graph,
    get_retry_limit,
    DISCONNECTED_NETWORK_FAILURE_FLAG
)


class TestRetryConfig:
    def test_load_retry_config_defaults(self, tmp_path):
        """Test that defaults are returned when config.yaml is missing."""
        # Run in a temp directory to ensure no config.yaml is found
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        try:
            config = load_retry_config()
            assert config["max_attempts"] == 10
            assert config["failure_threshold"] == 5
        finally:
            os.chdir(original_dir)

    def test_load_retry_config_from_file(self, tmp_path):
        """Test loading config from a specific file."""
        config_file = tmp_path / "config.yaml"
        config_content = """
        generator_params:
          retry:
            max_attempts: 20
            failure_threshold: 8
        """
        config_file.write_text(config_content)

        config = load_retry_config(str(config_file))
        assert config["max_attempts"] == 20
        assert config["failure_threshold"] == 8


class TestLogRetryFailure:
    def test_log_retry_failure_creates_file(self, tmp_path):
        """Test that log_retry_failure creates data/run_log.json if it doesn't exist."""
        log_dir = tmp_path / "data"
        log_dir.mkdir()
        log_file = log_dir / "run_log.json"

        # Patch Path to use tmp_path
        with patch('code.src.generators.retry_logic.Path', return_value=log_file):
            with patch('code.src.generators.retry_logic.log_run._get_timestamp', return_value="2023-01-01T00:00:00"):
                log_retry_failure("run-123", "graph-456", 10, str(tmp_path / "config.yaml"))

        assert log_file.exists()
        with open(log_file, 'r') as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["status"] == DISCONNECTED_NETWORK_FAILURE_FLAG
            assert data[0]["graph_id"] == "graph-456"

    def test_log_retry_failure_appends(self, tmp_path):
        """Test that log_retry_failure appends to existing log."""
        log_dir = tmp_path / "data"
        log_dir.mkdir()
        log_file = log_dir / "run_log.json"
        initial_data = [{"event_type": "start", "run_id": "run-000"}]
        log_file.write_text(json.dumps(initial_data))

        with patch('code.src.generators.retry_logic.Path', return_value=log_file):
            with patch('code.src.generators.retry_logic.log_run._get_timestamp', return_value="2023-01-01T00:00:00"):
                log_retry_failure("run-123", "graph-456", 10, str(tmp_path / "config.yaml"))

        with open(log_file, 'r') as f:
            data = json.load(f)
            assert len(data) == 2
            assert data[1]["status"] == DISCONNECTED_NETWORK_FAILURE_FLAG


class TestShouldProceedToNextGraph:
    @pytest.fixture
    def mock_config(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
        generator_params:
          retry:
            max_attempts: 10
            failure_threshold: 3
        """)
        return str(config_file)

    def test_returns_false_below_threshold(self, mock_config):
        """Should return False if attempts are below threshold."""
        with patch('code.src.generators.retry_logic.load_retry_config', return_value={"failure_threshold": 3}):
            result = should_proceed_to_next_graph("run-1", "graph-1", 2, mock_config)
            assert result is False

    def test_returns_true_at_threshold(self, mock_config, tmp_path):
        """Should return True if attempts meet threshold and log failure."""
        log_dir = tmp_path / "data"
        log_dir.mkdir()
        log_file = log_dir / "run_log.json"

        # Mock Path to write to tmp_path
        with patch('code.src.generators.retry_logic.Path', return_value=log_file):
            with patch('code.src.generators.retry_logic.log_run._get_timestamp', return_value="2023-01-01T00:00:00"):
                with patch('code.src.generators.retry_logic.load_retry_config', return_value={"failure_threshold": 3}):
                    result = should_proceed_to_next_graph("run-1", "graph-1", 3, mock_config)
                    assert result is True

        # Verify log was written
        assert log_file.exists()
        with open(log_file, 'r') as f:
            data = json.load(f)
            assert data[0]["status"] == DISCONNECTED_NETWORK_FAILURE_FLAG

    def test_returns_true_above_threshold(self, mock_config, tmp_path):
        """Should return True if attempts exceed threshold."""
        log_dir = tmp_path / "data"
        log_dir.mkdir()
        log_file = log_dir / "run_log.json"

        with patch('code.src.generators.retry_logic.Path', return_value=log_file):
            with patch('code.src.generators.retry_logic.log_run._get_timestamp', return_value="2023-01-01T00:00:00"):
                with patch('code.src.generators.retry_logic.load_retry_config', return_value={"failure_threshold": 3}):
                    result = should_proceed_to_next_graph("run-1", "graph-1", 5, mock_config)
                    assert result is True


class TestGetRetryLimit:
    def test_get_retry_limit(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
        generator_params:
          retry:
            max_attempts: 15
        """)
        limit = get_retry_limit(str(config_file))
        assert limit == 15