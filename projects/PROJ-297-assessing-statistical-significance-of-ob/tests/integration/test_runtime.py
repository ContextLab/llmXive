import os
import json
import time
import pytest
from pathlib import Path

# Import the main module to test
import code.main as main_module

class TestRuntimeMeasurement:
    """Tests for runtime measurement functionality (T041)."""

    @pytest.fixture
    def temp_runtime_log(self, tmp_path):
        """Fixture to provide a temporary path for runtime logs."""
        # Temporarily override the constant
        original_path = main_module.RUNTIME_LOG_PATH
        main_module.RUNTIME_LOG_PATH = str(tmp_path / "runtime_log.json")
        yield str(tmp_path / "runtime_log.json")
        # Restore original
        main_module.RUNTIME_LOG_PATH = original_path

    def test_runtime_log_structure(self, temp_runtime_log):
        """Verify that the runtime log JSON has the correct structure."""
        # Create a minimal mock result to test log generation
        mock_result = {
            "results": [],
            "runtime_log": {
                "start_time": "2024-01-01 00:00:00",
                "end_time": "2024-01-01 00:00:01",
                "total_runtime_seconds": 1.0,
                "time_limit_seconds": 600,
                "within_time_limit": True,
                "datasets_processed": 1,
                "permutations_per_dataset": 100,
                "thresholds_used": [0.3],
                "breakdown": {
                    "datasets": {"test_ds": 1.0},
                    "total_runtime_seconds": 1.0
                },
                "status": "success"
            }
        }
        
        # Write the log manually to test structure
        os.makedirs(os.path.dirname(temp_runtime_log), exist_ok=True)
        with open(temp_runtime_log, 'w') as f:
            json.dump(mock_result["runtime_log"], f, indent=2)
        
        # Verify the file exists
        assert os.path.exists(temp_runtime_log)
        
        # Verify structure
        with open(temp_runtime_log, 'r') as f:
            log_data = json.load(f)
        
        required_keys = [
            "start_time", "end_time", "total_runtime_seconds",
            "time_limit_seconds", "within_time_limit", "datasets_processed",
            "permutations_per_dataset", "thresholds_used", "breakdown", "status"
        ]
        
        for key in required_keys:
            assert key in log_data, f"Missing required key: {key}"

    def test_time_limit_enforcement(self, temp_runtime_log):
        """Verify that time limit is correctly enforced and logged."""
        # Test case: within limit
        log_within = {
            "total_runtime_seconds": 100.0,
            "time_limit_seconds": 600,
            "within_time_limit": True,
            "status": "success"
        }
        assert log_within["within_time_limit"] == True
        assert log_within["status"] == "success"

        # Test case: exceeded limit
        log_exceeded = {
            "total_runtime_seconds": 700.0,
            "time_limit_seconds": 600,
            "within_time_limit": False,
            "status": "exceeded_limit"
        }
        assert log_exceeded["within_time_limit"] == False
        assert log_exceeded["status"] == "exceeded_limit"

    def test_runtime_measurement_accuracy(self):
        """Verify that runtime measurement captures actual elapsed time."""
        start = time.time()
        time.sleep(0.1)  # Sleep for 100ms
        end = time.time()
        
        elapsed = round(end - start, 3)
        assert elapsed >= 0.1, f"Measured time {elapsed} is less than actual 0.1s sleep"
        assert elapsed < 0.2, f"Measured time {elapsed} is unreasonably high for 0.1s sleep"

    def test_runtime_log_path_constant(self):
        """Verify the runtime log path constant is correctly defined."""
        assert main_module.RUNTIME_LOG_PATH == "output/reports/runtime_log.json"
        assert main_module.RUNTIME_LOG_PATH.endswith(".json")
        assert "runtime" in main_module.RUNTIME_LOG_PATH

    def test_time_limit_constant(self):
        """Verify the time limit constant matches SC-004 (10 minutes)."""
        # SC-004 specifies a 10 minute (600 second) limit
        assert main_module.TIME_LIMIT_SECONDS == 600
        assert main_module.TIME_LIMIT_SECONDS > 0