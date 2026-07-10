"""
Integration test for environmental logging (T012).

This test verifies that the system correctly logs temperature, humidity, and
barometric pressure per run, and that these values are persisted to the
environment logs file in the correct format.

Dependencies:
- T014: code/analysis/environment.py (must be implemented)
- T005: code/utils/logging.py (already implemented)
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import setup_logging, log_environmental_params
from config import get_processed_data_path
from analysis.environment import record_run_environment


def test_environmental_logging_integration():
    """
    Integration test: Verify that environmental parameters are logged correctly
    and persisted to the environment logs file.

    Steps:
    1. Create a temporary directory for test outputs
    2. Setup logging to write to a temp file
    3. Call record_run_environment with known parameters
    4. Verify the log file contains the expected data
    5. Verify the data can be parsed and matches expected values
    """
    # Create a temporary directory for this test run
    temp_dir = tempfile.mkdtemp(prefix="env_logging_test_")
    original_processed_path = os.environ.get("PROJ_PROCESSED_PATH")

    try:
        # Override processed path to use temp directory
        os.environ["PROJ_PROCESSED_PATH"] = temp_dir

        # Setup logging
        log_file = Path(temp_dir) / "test_environment_logs.json"
        setup_logging(log_file=log_file, level="INFO")

        # Define test parameters (within specified tolerances)
        test_temp = 25.0  # °C (target: 25 ± 0.5°C)
        test_humidity = 45.0  # % RH (target: ±2% RH)
        test_pressure = 1013.25  # hPa (standard atmospheric pressure)
        run_id = "TEST_RUN_001"

        # Record the environment
        record_run_environment(
            temperature_c=test_temp,
            relative_humidity_pct=test_humidity,
            barometric_pressure_hpa=test_pressure,
            run_id=run_id
        )

        # Verify the log file exists
        assert log_file.exists(), f"Log file {log_file} was not created"

        # Read and parse the log file
        with open(log_file, 'r') as f:
            log_content = f.read()

        # The log file should contain JSON lines or a JSON array
        # Parse the content
        try:
            # Try parsing as JSON array first
            logs = json.loads(log_content)
        except json.JSONDecodeError:
            # If it's JSON lines, parse line by line
            logs = []
            for line in log_content.strip().split('\n'):
                if line.strip():
                    logs.append(json.loads(line))

        # Verify we have at least one log entry
        assert len(logs) > 0, "No log entries found in the log file"

        # Find the entry for our test run
        test_entry = None
        for entry in logs:
            if entry.get('run_id') == run_id:
                test_entry = entry
                break

        assert test_entry is not None, f"No log entry found for run_id {run_id}"

        # Verify the logged values match the input values
        assert abs(test_entry['temperature_c'] - test_temp) < 0.01, \
            f"Temperature mismatch: expected {test_temp}, got {test_entry['temperature_c']}"
        assert abs(test_entry['relative_humidity_pct'] - test_humidity) < 0.01, \
            f"Humidity mismatch: expected {test_humidity}, got {test_entry['relative_humidity_pct']}"
        assert abs(test_entry['barometric_pressure_hpa'] - test_pressure) < 0.01, \
            f"Pressure mismatch: expected {test_pressure}, got {test_entry['barometric_pressure_hpa']}"

        # Verify the run_id matches
        assert test_entry['run_id'] == run_id, \
            f"Run ID mismatch: expected {run_id}, got {test_entry['run_id']}"

        # Verify timestamp is present and valid
        assert 'timestamp' in test_entry, "Timestamp missing from log entry"
        timestamp = datetime.fromisoformat(test_entry['timestamp'].replace('Z', '+00:00'))
        assert timestamp <= datetime.now(timestamp.tzinfo), \
            "Log timestamp is in the future"

        # Verify tolerances are within spec
        assert abs(test_entry['temperature_c'] - 25.0) <= 0.5, \
            f"Temperature out of tolerance: {test_entry['temperature_c']}°C (target: 25 ± 0.5°C)"
        assert abs(test_entry['relative_humidity_pct'] - 45.0) <= 2.0, \
            f"Humidity out of tolerance: {test_entry['relative_humidity_pct']}% (target: ±2%)"

        print("✓ Environmental logging integration test passed")
        print(f"  - Log file: {log_file}")
        print(f"  - Run ID: {run_id}")
        print(f"  - Temperature: {test_entry['temperature_c']}°C")
        print(f"  - Humidity: {test_entry['relative_humidity_pct']}%")
        print(f"  - Pressure: {test_entry['barometric_pressure_hpa']} hPa")

    finally:
        # Restore original environment
        if original_processed_path:
            os.environ["PROJ_PROCESSED_PATH"] = original_processed_path
        elif "PROJ_PROCESSED_PATH" in os.environ:
            del os.environ["PROJ_PROCESSED_PATH"]

        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_environmental_logging_integration()
    print("\n✓ All integration tests for environmental logging passed.")