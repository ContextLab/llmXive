import os
import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils import ResourceMonitor

class TestResourceMonitorExecution:
    """
    Unit test to verify that the ResourceMonitor class correctly calculates
    and formats RAM values when executed, and that the final JSON artifact
    is generated with the correct schema.
    """

    def test_resource_monitor_schema_and_values(self, tmp_path):
        """
        Tests that the ResourceMonitor can be instantiated, started, stopped,
        and finalized to produce a valid JSON file with the required schema.
        """
        # Setup paths
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True, exist_ok=True)
        output_file = data_dir / "resource_profile.json"

        # Mock psutil to return predictable values for testing
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 1024 * 1024 * 1024  # 1 GB in bytes
        mock_process = MagicMock()
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.cpu_percent.return_value = 10.0

        with patch('utils.psutil.Process', return_value=mock_process):
            monitor = ResourceMonitor()
            monitor.start()
            
            # Simulate some time passing
            import time
            time.sleep(0.1)
            
            monitor.stop()
            
            # Override the output path for the test
            monitor.output_path = str(output_file)
            monitor.finalize()

        # Verify the file exists
        assert output_file.exists(), "resource_profile.json was not created"

        # Verify the content schema and values
        with open(output_file, 'r') as f:
            data = json.load(f)

        assert "peak_ram_gb" in data, "Missing key: peak_ram_gb"
        assert "total_runtime_hours" in data, "Missing key: total_runtime_hours"

        peak_ram = data["peak_ram_gb"]
        runtime = data["total_runtime_hours"]

        # Assertions based on mock data
        assert peak_ram > 0, f"peak_ram_gb must be > 0, got {peak_ram}"
        assert isinstance(peak_ram, float), f"peak_ram_gb must be float, got {type(peak_ram)}"
        
        assert runtime >= 0, f"total_runtime_hours must be >= 0, got {runtime}"
        assert isinstance(runtime, float), f"total_runtime_hours must be float, got {type(runtime)}"

        # Specific check for the mock: 1GB should result in peak_ram_gb approx 1.0
        # Allow some floating point tolerance
        assert abs(peak_ram - 1.0) < 0.01, f"Expected peak_ram_gb ~1.0, got {peak_ram}"

    def test_resource_monitor_with_no_data(self, tmp_path):
        """
        Tests that the monitor handles the case where start/stop are called
        but no actual data was recorded (edge case).
        """
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True, exist_ok=True)
        output_file = data_dir / "resource_profile.json"

        monitor = ResourceMonitor()
        monitor.output_path = str(output_file)
        
        # Directly call finalize without start/stop to test default behavior
        # The class should handle empty lists gracefully
        monitor.finalize()

        assert output_file.exists()
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Should have default 0 values if no data
        assert data["peak_ram_gb"] == 0.0
        assert data["total_runtime_hours"] == 0.0
