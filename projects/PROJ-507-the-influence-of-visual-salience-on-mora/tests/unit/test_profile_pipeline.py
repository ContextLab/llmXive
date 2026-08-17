"""
Unit tests for the profile_pipeline module.

These tests verify that the timing decorator works correctly and that
the stage runners handle missing data gracefully (without crashing the profiler).
"""
import os
import sys
import time
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from profile_pipeline import timer_decorator, run_survey_stage, run_cleaning_stage

class TestTimerDecorator:
    def test_timer_decorator_returns_time(self):
        @timer_decorator
        def slow_func():
            time.sleep(0.1)
            return "done"
        
        result, elapsed = slow_func()
        assert result == "done"
        assert elapsed >= 0.1
        assert elapsed < 1.0  # Sanity check

    def test_timer_decorator_handles_exception(self):
        @timer_decorator
        def failing_func():
            raise ValueError("Intentional failure")
        
        with pytest.raises(ValueError):
            failing_func()

class TestSurveyStage:
    @patch('profile_pipeline.load_scenarios')
    @patch('profile_pipeline.load_stimulus_variants')
    def test_survey_stage_skips_on_missing_data(self, mock_variants, mock_scenarios):
        # Mock returning None/Empty to simulate missing data
        mock_scenarios.return_value = []
        mock_variants.return_value = []
        
        result, elapsed = run_survey_stage()
        assert result["status"] == "skipped"
        assert "no_data" in result.get("reason", "")

class TestCleaningStage:
    @patch('profile_pipeline.load_survey_data')
    @patch('profile_pipeline.detect_straight_lining')
    @patch('profile_pipeline.save_cleaned_data')
    def test_cleaning_stage_processes_data(self, mock_save, mock_detect, mock_load):
        # Mock data
        mock_data = [{"participant_id": 1, "rating": 5}, {"participant_id": 2, "rating": 5}]
        mock_load.return_value = mock_data
        mock_detect.return_value = (mock_data, [])
        
        # We need to mock the file existence check too
        with patch('pathlib.Path.exists', return_value=True):
            result, elapsed = run_cleaning_stage()
            assert result["status"] == "completed"
            assert result["total"] == 2
            mock_detect.assert_called_once()
            mock_save.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
