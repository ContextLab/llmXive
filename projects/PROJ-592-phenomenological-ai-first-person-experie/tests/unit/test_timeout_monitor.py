"""Unit tests for timeout handling and sample-size logging."""
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from generation.timeout_monitor import (
    GenerationTimeoutError,
    SampleCountError,
    SampleCounter,
    TimeoutContext,
    run_with_timeout,
    log_sample_status,
    save_summary,
    enforce_minimum_samples,
)
from utils.logging import get_logger, clear_warnings


class TestSampleCounter:
    def test_record_success(self):
        counter = SampleCounter("test_condition")
        counter.record_success()
        assert counter.successful == 1
        assert counter.total_attempts == 1

    def test_record_failure(self):
        counter = SampleCounter("test_condition")
        counter.record_failure()
        assert counter.failed == 1
        assert counter.total_attempts == 1

    def test_record_timeout_failure(self):
        counter = SampleCounter("test_condition")
        counter.record_failure(is_timeout=True)
        assert counter.failed == 1
        assert counter.timeout_count == 1

    def test_success_rate(self):
        counter = SampleCounter("test_condition")
        counter.record_success()
        counter.record_success()
        counter.record_failure()
        assert counter.success_rate == pytest.approx(2/3)

    def test_to_dict(self):
        counter = SampleCounter("test_condition")
        counter.record_success()
        counter.record_failure()
        data = counter.to_dict()
        assert data["condition"] == "test_condition"
        assert data["successful"] == 1
        assert data["failed"] == 1
        assert "success_rate" in data
        assert "elapsed_seconds" in data


class TestTimeoutContext:
    def test_timeout_raises_error(self):
        counter = SampleCounter("test")
        with pytest.raises(GenerationTimeoutError):
            with TimeoutContext(1, "test", counter):
                time.sleep(2)  # Should timeout

        assert counter.timeout_count == 1

    def test_no_timeout_on_fast_operation(self):
        counter = SampleCounter("test")
        with TimeoutContext(5, "test", counter):
            time.sleep(0.1)  # Should complete
        
        assert counter.timeout_count == 0


class TestRunWithTimeout:
    def test_successful_execution(self):
        counter = SampleCounter("test")
        
        def fast_func():
            return "result"
        
        result = run_with_timeout(fast_func, 5, "test", counter)
        assert result == "result"
        assert counter.successful == 0  # No tracking in this path, just execution

    def test_timeout_execution(self):
        counter = SampleCounter("test")
        
        def slow_func():
            time.sleep(2)
            return "result"
        
        with pytest.raises(GenerationTimeoutError):
            run_with_timeout(slow_func, 1, "test", counter)
        
        assert counter.timeout_count == 1


class TestSaveSummary:
    def test_save_creates_file(self, tmp_path):
        counters = {
            "cond1": SampleCounter("cond1"),
            "cond2": SampleCounter("cond2")
        }
        counters["cond1"].record_success()
        counters["cond1"].record_failure()
        
        output_path = str(tmp_path / "summary.json")
        save_summary(counters, output_path)
        
        assert Path(output_path).exists()
        
        with open(output_path) as f:
            data = json.load(f)
        
        assert "conditions" in data
        assert "total_successful" in data
        assert data["total_successful"] == 1


class TestEnforceMinimumSamples:
    def test_all_meet_minimum(self):
        counters = {
            "cond1": SampleCounter("cond1"),
            "cond2": SampleCounter("cond2")
        }
        counters["cond1"].successful = 100
        counters["cond2"].successful = 90
        
        result = enforce_minimum_samples(counters, minimum_per_condition=80)
        assert result is True

    def test_some_fail_minimum(self):
        counters = {
            "cond1": SampleCounter("cond1"),
            "cond2": SampleCounter("cond2")
        }
        counters["cond1"].successful = 100
        counters["cond2"].successful = 50
        
        result = enforce_minimum_samples(counters, minimum_per_condition=80)
        assert result is False
