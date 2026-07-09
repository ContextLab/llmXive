"""
Tests for the memory monitoring module.
"""
import pytest
import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from memory_monitor import (
    get_current_rss_mb,
    check_memory_limit,
    MemoryTracker,
    save_memory_report,
    MAX_RSS_GB
)

class TestMemoryFunctions:
    """Test basic memory monitoring functions."""

    def test_get_current_rss_mb_returns_positive(self):
        """Test that get_current_rss_mb returns a positive value."""
        rss = get_current_rss_mb()
        assert rss > 0, "RSS should be positive"

    def test_check_memory_limit_returns_bool(self):
        """Test that check_memory_limit returns a boolean."""
        result = check_memory_limit()
        assert isinstance(result, bool), "Should return boolean"

    def test_check_memory_limit_within_limit(self):
        """Test that check_memory_limit returns True when within limit."""
        # Current memory should be well within 6.5 GB
        result = check_memory_limit()
        assert result is True, "Should be within limit for normal execution"

class TestMemoryTracker:
    """Test the MemoryTracker class."""

    def test_tracker_initialization(self):
        """Test that MemoryTracker initializes correctly."""
        tracker = MemoryTracker(subject_id="test_subj")
        assert tracker.subject_id == "test_subj"
        assert tracker.start_rss_mb is None
        assert tracker.peak_rss_mb == 0.0
        assert tracker.checkpoints == []

    def test_tracker_context_manager(self):
        """Test that MemoryTracker works as a context manager."""
        with MemoryTracker(subject_id="test_subj") as tracker:
            assert tracker.start_rss_mb is not None
            assert tracker.start_time is not None
        
        # After exit, peak should be at least the start value
        assert tracker.peak_rss_mb >= tracker.start_rss_mb

    def test_tracker_check_updates_peak(self):
        """Test that check() updates the peak RSS."""
        tracker = MemoryTracker(subject_id="test_subj")
        
        with patch("memory_monitor.get_current_rss_mb", return_value=100.0):
            with tracker:
                # First check should set peak to 100
                tracker.check()
                assert tracker.peak_rss_mb == 100.0
                
                # Second check with higher value should update peak
                with patch("memory_monitor.get_current_rss_mb", return_value=150.0):
                    tracker.check()
                    assert tracker.peak_rss_mb == 150.0

    def test_tracker_check_returns_boolean(self):
        """Test that check() returns a boolean."""
        tracker = MemoryTracker(subject_id="test_subj")
        
        with patch("memory_monitor.get_current_rss_mb", return_value=100.0):
            with tracker:
                result = tracker.check()
                assert isinstance(result, bool)

    def test_tracker_get_report(self):
        """Test that get_report() returns expected structure."""
        tracker = MemoryTracker(subject_id="test_subj")
        
        with patch("memory_monitor.get_current_rss_mb", return_value=100.0):
            with tracker:
                tracker.check()
                report = tracker.get_report()
                
                assert "subject_id" in report
                assert report["subject_id"] == "test_subj"
                assert "start_rss_mb" in report
                assert "peak_rss_mb" in report
                assert "peak_rss_gb" in report
                assert "max_allowed_gb" in report
                assert report["max_allowed_gb"] == MAX_RSS_GB
                assert "within_limit" in report
                assert "checkpoints" in report

    def test_tracker_exceeds_limit(self):
        """Test that tracker correctly detects when limit is exceeded."""
        tracker = MemoryTracker(subject_id="test_subj")
        
        # Mock a memory usage that exceeds the limit
        with patch("memory_monitor.get_current_rss_mb", return_value=MAX_RSS_GB * 1024 * 1.1):
            with tracker:
                result = tracker.check()
                assert result is False
                assert tracker.peak_rss_mb > MAX_RSS_GB * 1024

class TestSaveMemoryReport:
    """Test the save_memory_report function."""

    def test_save_report_creates_file(self, tmp_path):
        """Test that save_memory_report creates a JSON file."""
        # Mock the METRICS_DIR
        import memory_monitor
        original_dir = memory_monitor.METRICS_DIR
        memory_monitor.METRICS_DIR = tmp_path
        
        try:
            report = {
                "subject_id": "test_subj",
                "peak_rss_mb": 100.0,
                "peak_rss_gb": 0.1,
                "within_limit": True
            }
            
            save_memory_report("test_subj", report)
            
            expected_file = tmp_path / "memory_report_test_subj.json"
            assert expected_file.exists()
            
            with open(expected_file, "r") as f:
                saved_report = json.load(f)
                
            assert saved_report == report
        finally:
            memory_monitor.METRICS_DIR = original_dir

    def test_save_report_with_special_characters(self, tmp_path):
        """Test that save_memory_report handles special characters in subject ID."""
        import memory_monitor
        original_dir = memory_monitor.METRICS_DIR
        memory_monitor.METRICS_DIR = tmp_path
        
        try:
            report = {"subject_id": "sub-001", "peak_rss_mb": 100.0}
            save_memory_report("sub-001", report)
            
            expected_file = tmp_path / "memory_report_sub-001.json"
            assert expected_file.exists()
        finally:
            memory_monitor.METRICS_DIR = original_dir

if __name__ == "__main__":
    pytest.main([__file__, "-v"])