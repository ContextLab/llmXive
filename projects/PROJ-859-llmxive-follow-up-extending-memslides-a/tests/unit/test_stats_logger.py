"""
Unit tests for the Generation Stats Logger (T017).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from config import Config
from generators.stats_logger import GenerationStatsLogger, log_generation_stats


@pytest.fixture
def temp_config():
    """Create a temporary config with a temp data directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create necessary subdirectories
        data_dir = Path(tmpdir) / "data" / "raw"
        data_dir.mkdir(parents=True)
        
        # Create a minimal config file
        config_path = Path(tmpdir) / "config.yaml"
        config_content = {
            "data_dir": str(data_dir),
            "seed": 42,
            "output_dir": str(Path(tmpdir) / "output")
        }
        with open(config_path, 'w') as f:
            import yaml
            yaml.dump(config_content, f)
        
        # Create a custom Config class for testing that uses our temp dir
        class TestConfig(Config):
            def __init__(self, base_path=Path(tmpdir)):
                self.base_path = base_path
                self.data_dir = str(data_dir)
                self.seed = 42
        
        return TestConfig()


@pytest.fixture
def logger(temp_config):
    """Create a logger instance."""
    return GenerationStatsLogger(temp_config)


@pytest.fixture
def sample_session_file(temp_config):
    """Create a sample session file for testing."""
    session_id = "test-session-123"
    file_path = Path(temp_config.data_dir) / f"session_{session_id}.json"
    session_data = {
        "session_id": session_id,
        "exact_tool_sequence": ["create_slide", "add_text"],
        "metadata": {"tool_call_count": 2}
    }
    with open(file_path, 'w') as f:
        json.dump(session_data, f)
    return file_path


def test_compute_checksum(logger, sample_session_file):
    """Test that checksum is computed correctly."""
    checksum = logger.compute_checksum(sample_session_file)
    assert len(checksum) == 64  # SHA256 hex length
    assert all(c in '0123456789abcdef' for c in checksum)


def test_log_session_updates_state(logger, sample_session_file):
    """Test that logging a session updates the state file."""
    stats = {"tool_call_count": 2, "arg_variance": 0.5, "entropy": 1.0}
    
    logger.log_session(
        session_id="test-session-123",
        file_path=sample_session_file,
        stats=stats
    )
    
    state = logger._read_state()
    assert state["total_sessions_generated"] == 1
    assert len(state["files"]) == 1
    assert state["files"][0]["session_id"] == "test-session-123"
    assert state["files"][0]["checksum"] is not None


def test_log_session_aggregates_stats(logger, sample_session_file):
    """Test that stats are aggregated correctly across multiple logs."""
    stats1 = {"tool_call_count": 2, "arg_variance": 0.5}
    stats2 = {"tool_call_count": 3, "arg_variance": 1.0}
    
    # Log first session
    logger.log_session("s1", sample_session_file, stats1)
    
    # Log second session (reusing file for simplicity in unit test)
    # In real usage, this would be a different file, but we test aggregation logic
    logger.log_session("s2", sample_session_file, stats2)
    
    state = logger._read_state()
    assert state["total_sessions_generated"] == 2
    assert state["total_tool_calls"] == 5  # 2 + 3
    assert state["total_arg_variance_sum"] == 1.5  # 0.5 + 1.0


def test_get_summary(logger, sample_session_file):
    """Test that summary is calculated correctly."""
    stats = {"tool_call_count": 4, "arg_variance": 2.0}
    logger.log_session("s1", sample_session_file, stats)
    
    summary = logger.get_summary()
    assert summary["total_sessions"] == 1
    assert summary["average_tool_calls_per_session"] == 4.0
    assert summary["average_arg_variance"] == 2.0
    assert summary["file_count"] == 1
