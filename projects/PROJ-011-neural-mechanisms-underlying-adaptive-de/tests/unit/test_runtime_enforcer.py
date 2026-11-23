"""
Unit tests for the runtime enforcer.
"""
import time
import pytest
from pathlib import Path
import json

from code.modeling.runtime_enforcer import (
    RuntimeEnforcer,
    RuntimeLimitExceeded,
    SampleSizeReductionRequired
)
from code.utils.config import set_config, reset_config


@pytest.fixture
def test_config():
    """Provide a test configuration."""
    config = {
        "modeling": {
            "max_runtime_seconds": 10,
            "target_sample_size": 10,
            "min_sample_size": 2
        }
    }
    set_config(config)
    yield config
    reset_config()


def test_runtime_enforcer_initialization(test_config):
    """Test that RuntimeEnforcer initializes correctly."""
    enforcer = RuntimeEnforcer(test_config)
    assert enforcer.max_runtime == 10
    assert enforcer.target_sample_size == 10
    assert enforcer.min_sample_size == 2
    assert enforcer.start_time is None
    assert enforcer.elapsed_time == 0.0


def test_check_runtime_before_start(test_config):
    """Test that check_runtime returns True before timer starts."""
    enforcer = RuntimeEnforcer(test_config)
    assert enforcer.check_runtime() is True


def test_check_runtime_within_limits(test_config):
    """Test that check_runtime returns True when within limits."""
    enforcer = RuntimeEnforcer(test_config)
    enforcer.start_timer()
    time.sleep(0.1)
    assert enforcer.check_runtime() is True
    assert enforcer.elapsed_time > 0


def test_calculate_adaptive_sample_size(test_config):
    """Test adaptive sample size calculation."""
    enforcer = RuntimeEnforcer(test_config)
    enforcer.start_timer()

    # Simulate a scenario where we need to reduce sample size
    estimated_time = 2.0  # 2 seconds per sample
    current_n = 10
    max_runtime = 10

    # We've used 0.1 seconds, so 9.9 seconds remain
    # 9.9 / 2.0 = 4.95 -> 4 samples max
    new_n = enforcer.calculate_adaptive_sample_size(estimated_time, current_n)

    assert new_n <= current_n
    assert new_n >= enforcer.min_sample_size


def test_sample_size_capped_at_target(test_config):
    """Test that sample size is capped at target if no time estimate provided."""
    enforcer = RuntimeEnforcer(test_config)
    enforcer.start_timer()

    # Request more than target
    new_n = enforcer.get_sample_size(20)
    assert new_n == enforcer.target_sample_size


def test_sample_size_within_target(test_config):
    """Test that sample size is returned as-is if within target."""
    enforcer = RuntimeEnforcer(test_config)
    enforcer.start_timer()

    # Request less than target
    new_n = enforcer.get_sample_size(5)
    assert new_n == 5


def test_finalization_writes_report(test_config, tmp_path):
    """Test that finalization writes the report."""
    # Override report path for testing
    report_path = tmp_path / "test_report.json"
    enforcer = RuntimeEnforcer(test_config)
    enforcer.REPORT_PATH = report_path
    enforcer.start_timer()
    time.sleep(0.1)

    enforcer.finalize()

    assert report_path.exists()
    with open(report_path, 'r') as f:
        report = json.load(f)

    assert "final_sample_size" in report
    assert "total_runtime_seconds" in report
    assert "completed" in report


def test_context_manager(test_config):
    """Test that context manager works correctly."""
    with RuntimeEnforcer(test_config) as enforcer:
        assert enforcer.start_time is not None

    # After context, report should be written (if we had a real path)
    # We can't easily test the file write here without mocking


def test_runtime_limit_exceeded_logic(test_config):
    """Test logic for when runtime limit is exceeded."""
    enforcer = RuntimeEnforcer(test_config)
    enforcer.start_time = time.time() - 15  # Simulate 15 seconds elapsed (limit is 10)

    assert enforcer.check_runtime() is False
    assert enforcer.report_data["runtime_limit_exceeded"] is True