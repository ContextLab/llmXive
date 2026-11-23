import pytest
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.cpu_profiler import (
    get_elapsed_time, cpu_timer, profile_function,
    get_timing_report, reset_timing_results
)

class TestCPUProfiler:
    def test_cpu_timer_basic(self):
        """Test basic timing functionality"""
        @cpu_timer("test_function")
        def dummy_func():
            time.sleep(0.1)
        
        dummy_func()
        
        report = get_timing_report()
        assert "test_function" in report
        assert report["test_function"]["count"] == 1
        assert report["test_function"]["total_time"] >= 0.09

    def test_reset_timing_results(self):
        """Test that timing results can be reset"""
        @cpu_timer("reset_test")
        def dummy():
            pass
        
        dummy()
        reset_timing_results()
        
        report = get_timing_report()
        assert len(report) == 0

    def test_profile_function_decorator(self):
        """Test the profile_function decorator"""
        def simple_func():
            return 42
        
        profiled_func = profile_function("profiled")(simple_func)
        result = profiled_func()
        
        assert result == 42
        
        report = get_timing_report()
        assert "profiled" in report

    def test_get_elapsed_time(self):
        """Test get_elapsed_time function"""
        start = time.perf_counter()
        time.sleep(0.05)
        elapsed = get_elapsed_time(start)
        
        assert elapsed >= 0.04
        assert isinstance(elapsed, float)

    def test_multiple_timers(self):
        """Test multiple timers running concurrently"""
        @cpu_timer("timer1")
        def func1():
            time.sleep(0.05)
        
        @cpu_timer("timer2")
        def func2():
            time.sleep(0.05)
        
        func1()
        func2()
        
        report = get_timing_report()
        assert "timer1" in report
        assert "timer2" in report
        assert report["timer1"]["count"] == 1
        assert report["timer2"]["count"] == 1

    def test_timing_accuracy(self):
        """Test that timing is reasonably accurate"""
        @cpu_timer("accuracy_test")
        def precise_func():
            time.sleep(0.1)
        
        precise_func()
        
        report = get_timing_report()
        elapsed = report["accuracy_test"]["total_time"]
        
        # Allow 20% tolerance
        assert 0.08 <= elapsed <= 0.15
