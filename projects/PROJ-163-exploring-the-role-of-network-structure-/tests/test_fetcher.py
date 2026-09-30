import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Mock the Qiskit imports for unit testing without API keys
import sys
from unittest.mock import MagicMock, patch

# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fetcher import process_historical_data

class TestProcessHistoricalData:
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.historical_dir = os.path.join(self.temp_dir, "historical")
        self.output_csv = os.path.join(self.temp_dir, "output.csv")
        os.makedirs(self.historical_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_process_historical_data_creates_csv(self):
        """Test that process_historical_data creates the output CSV with correct headers."""
        # Create a mock JSON file
        mock_data = {
            "device_id": "ibmq_manila",
            "timestamp": "2023-10-01T00:00:00Z",
            "t1_mean": 100.5,
            "t2_mean": 200.5,
            "cx_error_mean": 0.01,
            "readout_error_mean": 0.02,
            "chip_family": "Falcon"
        }
        mock_file = os.path.join(self.historical_dir, "ibmq_manila_20231001.json")
        with open(mock_file, 'w') as f:
            json.dump(mock_data, f)

        # Run the function
        process_historical_data(self.historical_dir, self.output_csv)

        # Verify output
        assert os.path.exists(self.output_csv)
        with open(self.output_csv, 'r') as f:
            content = f.read()
            assert "device_id" in content
            assert "ibmq_manila" in content
            assert "100.5" in content

    def test_process_historical_data_handles_multiple_files(self):
        """Test processing multiple historical snapshots."""
        # Create two mock JSON files
        data1 = {
            "device_id": "ibmq_manila",
            "timestamp": "2023-10-01T00:00:00Z",
            "t1_mean": 100.5,
            "t2_mean": 200.5,
            "cx_error_mean": 0.01,
            "readout_error_mean": 0.02,
            "chip_family": "Falcon"
        }
        data2 = {
            "device_id": "ibmq_quito",
            "timestamp": "2023-10-02T00:00:00Z",
            "t1_mean": 110.5,
            "t2_mean": 210.5,
            "cx_error_mean": 0.015,
            "readout_error_mean": 0.025,
            "chip_family": "Falcon"
        }

        with open(os.path.join(self.historical_dir, "ibmq_manila_20231001.json"), 'w') as f:
            json.dump(data1, f)
        with open(os.path.join(self.historical_dir, "ibmq_quito_20231002.json"), 'w') as f:
            json.dump(data2, f)

        process_historical_data(self.historical_dir, self.output_csv)

        with open(self.output_csv, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 3  # Header + 2 rows

    def test_process_historical_data_skips_invalid_json(self):
        """Test that invalid JSON files are skipped."""
        # Create an invalid JSON file
        invalid_file = os.path.join(self.historical_dir, "invalid_20231001.json")
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")

        # Create a valid one
        valid_data = {
            "device_id": "ibmq_manila",
            "timestamp": "2023-10-01T00:00:00Z",
            "t1_mean": 100.5,
            "t2_mean": 200.5,
            "cx_error_mean": 0.01,
            "readout_error_mean": 0.02,
            "chip_family": "Falcon"
        }
        with open(os.path.join(self.historical_dir, "ibmq_manila_20231001.json"), 'w') as f:
            json.dump(valid_data, f)

        process_historical_data(self.historical_dir, self.output_csv)

        with open(self.output_csv, 'r') as f:
            content = f.read()
            assert "ibmq_manila" in content
            assert "invalid" not in content

    def test_process_historical_data_skips_missing_metrics(self):
        """Test that files missing required metrics are skipped."""
        incomplete_data = {
            "device_id": "ibmq_manila",
            "timestamp": "2023-10-01T00:00:00Z",
            "t1_mean": 100.5
            # Missing t2_mean, cx_error_mean, readout_error_mean
        }
        with open(os.path.join(self.historical_dir, "ibmq_manila_20231001.json"), 'w') as f:
            json.dump(incomplete_data, f)

        process_historical_data(self.historical_dir, self.output_csv)

        with open(self.output_csv, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1  # Only header