"""
Unit tests for code/generation/timeout_monitor.py.
"""
import json
import os
import time
import tempfile
from pathlib import Path
import pytest

from generation.timeout_monitor import (
    SampleCounter,
    TimeoutContext,
    GenerationTimeoutError,
    run_with_timeout,
    log_sample_status,
    save_summary,
    enforce_minimum_samples
)


class TestSampleCounter:
    def test_record_success(self):
        counter = SampleCounter()
        counter.record_success("id_1", 0.5)
        assert counter.total == 1
        assert counter.success == 1
        assert counter.fail == 0
        assert len(counter.details) == 1
        assert counter.details[0]["status"] == "success"

    def test_record_fail(self):
        counter = SampleCounter()
        counter.record_fail("id_1", "Error message", 1.2)
        assert counter.total == 1
        assert counter.success == 0
        assert counter.fail == 1
        assert counter.details[0]["reason"] == "Error message"

    def test_record_timeout(self):
        counter = SampleCounter()
        counter.record_timeout("id_1", 2.5)
        assert counter.total == 1
        assert counter.fail == 1
        assert counter.timeouts == 1
        assert counter.details[0]["status"] == "timeout"

    def test_to_dict(self):
        counter = SampleCounter()
        counter.record_success("id_1", 0.1)
        d = counter.to_dict()
        assert "total" in d
        assert "success" in d
        assert "fail" in d
        assert "details" in d


class TestTimeoutContext:
    def test_no_timeout(self):
        # Should complete successfully within time
        with TimeoutContext(1.0):
            time.sleep(0.1)
        # No exception raised

    def test_timeout_raises(self):
        with pytest.raises(GenerationTimeoutError):
            with TimeoutContext(0.1):
                time.sleep(0.5)  # Sleep longer than timeout


class TestRunWithTimeout:
    def test_success(self):
        def fast_func():
            return 42

        result, duration = run_with_timeout(fast_func, timeout_seconds=1.0)
        assert result == 42
        assert duration < 1.0

    def test_timeout_raises(self):
        def slow_func():
            time.sleep(1.0)
            return 42

        with pytest.raises(GenerationTimeoutError):
            run_with_timeout(slow_func, timeout_seconds=0.1)


class TestLogSampleStatus:
    def test_log_success(self):
        counter = SampleCounter()
        log_sample_status(counter, "s1", "success", duration=0.1)
        assert counter.success == 1

    def test_log_fail(self):
        counter = SampleCounter()
        log_sample_status(counter, "s1", "fail", reason="Test", duration=0.1)
        assert counter.fail == 1

    def test_log_timeout(self):
        counter = SampleCounter()
        log_sample_status(counter, "s1", "fail", is_timeout=True, duration=0.1)
        assert counter.timeouts == 1


class TestSaveSummary:
    def test_save_to_file(self):
        counter = SampleCounter()
        counter.record_success("s1", 0.1)
        counter.record_fail("s2", "Error", 0.2)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_log.json"
            save_summary(counter, output_path)

            assert output_path.exists()
            with open(output_path, "r") as f:
                data = json.load(f)
            assert data["total"] == 2
            assert data["success"] == 1
            assert data["fail"] == 1


class TestEnforceMinimumSamples:
    def test_passes(self):
        counter = SampleCounter()
        counter.record_success("s1", 0.1)
        counter.record_success("s2", 0.1)
        # Should not raise
        enforce_minimum_samples(counter, min_samples=2, strategy="test", prompt_id="p1")

    def test_fails(self):
        counter = SampleCounter()
        counter.record_success("s1", 0.1)
        with pytest.raises(ValueError):
            enforce_minimum_samples(counter, min_samples=2, strategy="test", prompt_id="p1")