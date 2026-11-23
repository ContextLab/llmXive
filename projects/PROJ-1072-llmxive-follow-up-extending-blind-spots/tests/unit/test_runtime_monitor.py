"""
Unit tests for the Global Runtime Monitor (T023a).
"""
import pytest
import time
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from utils.runtime_monitor import RuntimeMonitor, create_monitor, GLOBAL_RUNTIME_LIMIT_SECONDS

@pytest.fixture
def monitor():
    return create_monitor()

def test_monitor_start(monitor):
    """Test that monitor starts correctly."""
    monitor.start()
    assert monitor.start_time is not None
    status = monitor.get_status()
    assert status['elapsed_time'] >= 0
    assert status['limit_reached'] is False

def test_check_before_task_sufficient_time(monitor):
    """Test check_before_task returns True when sufficient time remains."""
    monitor.start()
    # Simulate very little time elapsed
    with patch('time.time', return_value=monitor.start_time + 10):
        can_start = monitor.check_before_task(per_task_timeout=600)
        assert can_start is True

def test_check_before_task_insufficient_time(monitor):
    """Test check_before_task returns False when insufficient time remains."""
    monitor.start()
    # Simulate time elapsed close to limit
    simulated_time = monitor.start_time + (GLOBAL_RUNTIME_LIMIT_SECONDS - 100)
    with patch('time.time', return_value=simulated_time):
        can_start = monitor.check_before_task(per_task_timeout=600)
        assert can_start is False

def test_record_task_completion(monitor):
    """Test recording task completion."""
    monitor.start()
    monitor.record_task_completion(success=True)
    assert monitor.tasks_processed == 1
    assert monitor.tasks_skipped == 0

    monitor.record_task_completion(success=False)
    assert monitor.tasks_processed == 1
    assert monitor.tasks_skipped == 1

def test_halt_and_report(monitor, tmp_path):
    """Test halt_and_report generates correct report."""
    monitor.start()
    monitor.record_task_completion(success=True)
    monitor.record_task_completion(success=False)

    # Simulate time elapsed
    with patch('time.time', return_value=monitor.start_time + (GLOBAL_RUNTIME_LIMIT_SECONDS + 100)):
        report_path = tmp_path / 'runtime_limit_reached.json'
        report = monitor.halt_and_report(str(report_path))

        assert report_path.exists()
        assert report['reason'] == 'Runtime limit exceeded'
        assert report['effective_sample_size'] == 1
        assert report['tasks_skipped'] == 1
        assert 'timestamp' in report

        # Verify file content
        with open(report_path, 'r') as f:
            file_content = json.load(f)
            assert file_content['reason'] == 'Runtime limit exceeded'

def test_monitor_without_start(monitor):
    """Test behavior when check_before_task is called without start."""
    can_start = monitor.check_before_task(per_task_timeout=600)
    assert can_start is True  # Should allow first task even if not started
    assert monitor.start_time is not None