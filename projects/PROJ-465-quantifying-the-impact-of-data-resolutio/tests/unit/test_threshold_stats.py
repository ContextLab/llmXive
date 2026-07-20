"""
Unit tests for T030: Threshold Statistics Calculation.
"""

import json
import tempfile
import os
from pathlib import Path
import pytest
import numpy as np

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from code.analysis.threshold_stats import calculate_threshold_for_event, calculate_threshold_std, MIN_EVENT_COUNT


class TestCalculateThresholdForEvent:
    def test_finding_lowest_threshold(self):
        """Test that the lowest rate where bias > CI is returned."""
        metrics = {
            "resolution_4096": {"bias_exceeded_ci": False},
            "resolution_2048": {"bias_exceeded_ci": False},
            "resolution_1024": {"bias_exceeded_ci": True},
            "resolution_512": {"bias_exceeded_ci": True}
        }
        # Failing rates: 1024, 512. Lowest is 512.
        result = calculate_threshold_for_event(metrics)
        assert result == 512.0

    def test_no_threshold_found(self):
        """Test handling when bias never exceeds CI."""
        metrics = {
            "resolution_4096": {"bias_exceeded_ci": False},
            "resolution_2048": {"bias_exceeded_ci": False},
            "resolution_1024": {"bias_exceeded_ci": False}
        }
        result = calculate_threshold_for_event(metrics)
        assert result is None

    def test_all_thresholds_exceeded(self):
        """Test when bias exceeds at all rates."""
        metrics = {
            "resolution_4096": {"bias_exceeded_ci": True},
            "resolution_2048": {"bias_exceeded_ci": True},
            "resolution_1024": {"bias_exceeded_ci": True}
        }
        # Failing rates: 4096, 2048, 1024. Lowest is 1024.
        result = calculate_threshold_for_event(metrics)
        assert result == 1024.0

    def test_empty_metrics(self):
        """Test handling of empty metrics."""
        result = calculate_threshold_for_event({})
        assert result is None


class TestCalculateThresholdStd:
    def test_std_calculation(self):
        """Test standard deviation calculation with sufficient events."""
        # Create a temporary aggregated results file
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "aggregated_results.json"
            output_path = Path(tmpdir) / "threshold_statistics.json"

            # Create mock data: 5 events with thresholds
            mock_data = [
                {"event_id": "E1", "metrics": {"resolution_1024": {"bias_exceeded_ci": True}, "resolution_2048": {"bias_exceeded_ci": False}}}, # Threshold 1024
                {"event_id": "E2", "metrics": {"resolution_512": {"bias_exceeded_ci": True}, "resolution_1024": {"bias_exceeded_ci": False}}},  # Threshold 512
                {"event_id": "E3", "metrics": {"resolution_1024": {"bias_exceeded_ci": True}, "resolution_2048": {"bias_exceeded_ci": False}}}, # Threshold 1024
                {"event_id": "E4", "metrics": {"resolution_256": {"bias_exceeded_ci": True}, "resolution_512": {"bias_exceeded_ci": False}}},   # Threshold 256
                {"event_id": "E5", "metrics": {"resolution_1024": {"bias_exceeded_ci": True}, "resolution_2048": {"bias_exceeded_ci": False}}}  # Threshold 1024
            ]

            with open(input_path, "w") as f:
                json.dump(mock_data, f)

            result = calculate_threshold_std(input_path, output_path)

            # Expected thresholds: [1024, 512, 1024, 256, 1024]
            expected_vals = np.array([1024, 512, 1024, 256, 1024])
            expected_std = float(np.std(expected_vals))
            expected_mean = float(np.mean(expected_vals))

            assert result["event_count"] == 5
            assert result["events_with_threshold"] == 5
            assert result["standard_deviation"] == pytest.approx(expected_std, rel=1e-5)
            assert result["mean_threshold"] == pytest.approx(expected_mean, rel=1e-5)
            assert result["events_excluded_no_threshold"] == 0
            assert Path(output_path).exists()

    def test_insufficient_events(self):
        """Test that SD is None if events_with_threshold < MIN_EVENT_COUNT."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "aggregated_results.json"
            output_path = Path(tmpdir) / "threshold_statistics.json"

            # Only 2 events (below default MIN_EVENT_COUNT of 3)
            mock_data = [
                {"event_id": "E1", "metrics": {"resolution_1024": {"bias_exceeded_ci": True}}},
                {"event_id": "E2", "metrics": {"resolution_512": {"bias_exceeded_ci": True}}}
            ]

            with open(input_path, "w") as f:
                json.dump(mock_data, f)

            result = calculate_threshold_std(input_path, output_path)

            assert result["standard_deviation"] is None
            assert result["mean_threshold"] is None
            assert result["events_with_threshold"] == 2
            assert "Insufficient events" in result.get("error", "") or result.get("standard_deviation") is None

    def test_mixed_thresholds_and_exclusions(self):
        """Test handling of events with and without thresholds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "aggregated_results.json"
            output_path = Path(tmpdir) / "threshold_statistics.json"

            mock_data = [
                {"event_id": "E1", "metrics": {"resolution_1024": {"bias_exceeded_ci": True}}}, # Has threshold
                {"event_id": "E2", "metrics": {"resolution_4096": {"bias_exceeded_ci": False}, "resolution_2048": {"bias_exceeded_ci": False}}}, # No threshold
                {"event_id": "E3", "metrics": {"resolution_512": {"bias_exceeded_ci": True}}}, # Has threshold
                {"event_id": "E4", "metrics": {"resolution_1024": {"bias_exceeded_ci": True}}}, # Has threshold
                {"event_id": "E5", "metrics": {"resolution_4096": {"bias_exceeded_ci": False}}} # No threshold
            ]

            with open(input_path, "w") as f:
                json.dump(mock_data, f)

            result = calculate_threshold_std(input_path, output_path)

            assert result["event_count"] == 5
            assert result["events_with_threshold"] == 3
            assert result["events_excluded_no_threshold"] == 2
            # 3 events is >= MIN_EVENT_COUNT (3), so SD should be calculated
            assert result["standard_deviation"] is not None

    def test_missing_file(self):
        """Test error handling when input file is missing."""
        with pytest.raises(FileNotFoundError):
            calculate_threshold_std(Path("/nonexistent/path.json"))
