"""Unit tests for timeout monitoring and sample counting utilities."""
import json
import os
import tempfile
import time
from pathlib import Path

import pytest

from generation.timeout_monitor import (
    GenerationTimeoutError,
    SampleCounter,
    TimeoutContext,
    enforce_minimum_samples,
    log_sample_status,
)


class TestSampleCounter:
    def test_increment(self, tmp_path):
        counter = SampleCounter(log_path=tmp_path / "counts.json")
        assert counter.increment("cond_a") == 1
        assert counter.increment("cond_a") == 2
        assert counter.increment("cond_b") == 1

    def test_get_missing(self, tmp_path):
        counter = SampleCounter(log_path=tmp_path / "counts.json")
        assert counter.get("nonexistent") == 0

    def test_check_minimum(self, tmp_path):
        counter = SampleCounter(log_path=tmp_path / "counts.json")
        assert not counter.check_minimum("cond", 80)
        for _ in range(80):
            counter.increment("cond")
        assert counter.check_minimum("cond", 80)

    def test_save_and_load(self, tmp_path):
        log_file = tmp_path / "counts.json"
        counter1 = SampleCounter(log_path=log_file)
        counter1.increment("cond")
        
        counter2 = SampleCounter(log_path=log_file)
        counter2.load()
        
        assert counter2.get("cond") == 1


class TestTimeoutContext:
    def test_timeout_raised(self):
        with pytest.raises(GenerationTimeoutError):
            with TimeoutContext(1):
                time.sleep(2)

    def test_no_timeout_when_fast(self):
        # Should complete without error
        with TimeoutContext(5):
            time.sleep(0.1)

class TestEnforceMinimum:
    def test_all_satisfied(self, tmp_path):
        counter = SampleCounter(log_path=tmp_path / "counts.json")
        counter.increment("cond")
        counter.increment("cond")
        satisfied, counts = enforce_minimum_samples(counter, minimum=2)
        assert satisfied is True
        assert counts["cond"] == 2

    def test_not_satisfied(self, tmp_path):
        counter = SampleCounter(log_path=tmp_path / "counts.json")
        counter.increment("cond")
        satisfied, _ = enforce_minimum_samples(counter, minimum=5)
        assert satisfied is False

class TestLogSampleStatus:
    def test_log_success(self, tmp_path):
        # Mock logger to avoid actual logging side effects in tests
        class MockLogger:
            def __init__(self):
                self.calls = []
            def log(self, *args, **kwargs):
                self.calls.append((args, kwargs))
        
        logger = MockLogger()
        counter = SampleCounter(log_path=tmp_path / "counts.json")
        
        log_sample_status("cond_a", True, "sample_1", counter, logger)
        
        # Verify counter updated
        assert counter.get("cond_a") == 1
        # Verify log was called
        assert len(logger.calls) > 0
        
        # Verify failure path
        log_sample_status("cond_a", False, "sample_2", counter, logger)
        assert counter.get("cond_a") == 1  # Should not increment on failure