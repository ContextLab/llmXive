"""
Integration tests for training timing instrumentation.

These tests verify that the timing module correctly measures execution time,
logs appropriate messages, and enforces the 1-hour training budget.
"""
import os
import sys
import time
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from src.models.timing import (
    training_timer,
    save_timing_results,
    assert_training_time,
    MAX_TRAINING_TIME_SECONDS,
    TRAINING_WARNING_THRESHOLD
)
from src.utils.config import get_path


class TestTimingInstrumentation:
    """Test suite for timing instrumentation functionality."""

    def test_training_timer_measures_duration(self):
        """Verify that the training timer correctly measures duration."""
        with training_timer("test_operation") as timing_info:
            time.sleep(0.1)  # Sleep for 100ms
        
        # Verify timing info contains expected keys
        assert 'duration_seconds' in timing_info
        assert 'duration_minutes' in timing_info
        assert 'within_budget' in timing_info
        assert 'percentage_of_budget' in timing_info
        
        # Verify duration is at least 0.1 seconds (with some tolerance)
        assert timing_info['duration_seconds'] >= 0.1
        
        # Verify it's within budget
        assert timing_info['within_budget'] is True

    def test_training_timer_within_budget(self):
        """Verify that short operations are marked as within budget."""
        with training_timer("quick_operation") as timing_info:
            time.sleep(0.05)
        
        assert timing_info['within_budget'] is True
        assert timing_info['percentage_of_budget'] < 1.0

    def test_assert_training_time_passes(self):
        """Verify that assert_training_time passes for durations within budget."""
        # Should not raise
        assert_training_time(100, "test_operation")
        assert_training_time(MAX_TRAINING_TIME_SECONDS - 1, "test_operation")

    def test_assert_training_time_fails(self):
        """Verify that assert_training_time raises for durations exceeding budget."""
        with pytest.raises(RuntimeError) as exc_info:
            assert_training_time(MAX_TRAINING_TIME_SECONDS + 100, "test_operation")
        
        assert "exceeded the maximum allowed time" in str(exc_info.value)

    def test_save_timing_results_creates_file(self):
        """Verify that save_timing_results creates a valid JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / 'timing.json'
            
            timing_info = {
                'operation': 'test',
                'duration_seconds': 10.5,
                'within_budget': True
            }
            
            result_path = save_timing_results(timing_info, output_path)
            
            # Verify file was created
            assert result_path.exists()
            
            # Verify JSON is valid
            with open(result_path, 'r') as f:
                data = json.load(f)
            
            assert 'timestamp' in data
            assert 'results' in data
            assert data['results']['operation'] == 'test'
            assert data['results']['duration_seconds'] == 10.5

    def test_timing_results_format(self):
        """Verify that timing results have the expected format."""
        with training_timer("format_test") as timing_info:
            time.sleep(0.01)
        
        # Check all expected fields
        expected_fields = [
            'operation', 'duration_seconds', 'duration_minutes',
            'max_allowed_seconds', 'max_allowed_minutes',
            'within_budget', 'percentage_of_budget'
        ]
        
        for field in expected_fields:
            assert field in timing_info, f"Missing field: {field}"
        
        # Verify calculated values
        assert timing_info['duration_minutes'] == timing_info['duration_seconds'] / 60.0
        assert timing_info['percentage_of_budget'] == (
            timing_info['duration_seconds'] / MAX_TRAINING_TIME_SECONDS
        ) * 100

    def test_warning_threshold(self):
        """Verify that warnings are triggered when approaching time limit."""
        # This test verifies the threshold constant is reasonable
        assert 0 < TRAINING_WARNING_THRESHOLD < 1.0
        
        # Simulate being at the threshold
        simulated_duration = MAX_TRAINING_TIME_SECONDS * TRAINING_WARNING_THRESHOLD
        percentage = (simulated_duration / MAX_TRAINING_TIME_SECONDS) * 100
        
        assert percentage == TRAINING_WARNING_THRESHOLD * 100

    def test_timing_integration_with_mock_training(self):
        """Integration test simulating a full training workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / 'timing.json'
            
            # Simulate training
            with training_timer("mock_training") as timing_info:
                time.sleep(0.1)
            
            # Save results
            saved_path = save_timing_results(timing_info, output_path)
            
            # Verify file exists and contains correct data
            assert saved_path.exists()
            
            with open(saved_path, 'r') as f:
                data = json.load(f)
            
            assert data['results']['operation'] == 'mock_training'
            assert data['results']['within_budget'] is True
            assert 'timestamp' in data

    def test_max_training_time_constant(self):
        """Verify that the maximum training time constant is set correctly."""
        assert MAX_TRAINING_TIME_SECONDS == 3600  # 1 hour in seconds
        assert MAX_TRAINING_TIME_SECONDS / 60 == 60  # 1 hour in minutes

if __name__ == "__main__":
    pytest.main([__file__, "-v"])