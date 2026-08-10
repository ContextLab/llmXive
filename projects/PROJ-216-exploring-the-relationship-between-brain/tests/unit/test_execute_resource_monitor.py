"""
Unit tests for the execute_resource_monitor script logic.

These tests verify that the script correctly integrates with the ResourceMonitor
class and produces the expected output structure without necessarily running
the full heavy simulation in a unit test context.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import ResourceMonitor

class TestExecuteResourceMonitorLogic:
    """Tests for the execution logic of the resource monitor."""

    def test_monitor_start_stop_flow(self, tmp_path):
        """Verify that start/stop flow creates the file with valid schema."""
        output_file = tmp_path / "resource_profile.json"
        
        # Create a mock monitor that simulates the behavior without heavy allocation
        # We patch the internal tracking to ensure we get a result
        with patch('utils.ResourceMonitor._track') as mock_track:
            # Simulate a tracking loop that records some values
            mock_track.side_effect = lambda: None 
            
            monitor = ResourceMonitor(
                subject_id="test_sub",
                output_path=str(output_file)
            )
            
            # Manually set some internal state to simulate a run
            monitor.peak_ram_gb = 2.5
            monitor.start_time = 0
            monitor.end_time = 3600 # 1 hour
            
            monitor.stop()
            
            # Verify file creation
            assert output_file.exists(), "Output file should be created"
            
            # Verify content
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            assert "peak_ram_gb" in data
            assert "total_runtime_hours" in data
            assert data["peak_ram_gb"] == 2.5
            assert data["total_runtime_hours"] == 1.0

    def test_output_schema_validation(self, tmp_path):
        """Verify the output schema matches the requirement."""
        output_file = tmp_path / "resource_profile.json"
        
        monitor = ResourceMonitor(
            subject_id="test_sub",
            output_path=str(output_file)
        )
        
        # Simulate a run
        monitor.peak_ram_gb = 4.2
        monitor.start_time = 0
        monitor.end_time = 7200 # 2 hours
        monitor.stop()
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Check types
        assert isinstance(data["peak_ram_gb"], (int, float))
        assert isinstance(data["total_runtime_hours"], (int, float))
        
        # Check values are positive
        assert data["peak_ram_gb"] > 0
        assert data["total_runtime_hours"] >= 0

    def test_directory_creation(self, tmp_path):
        """Verify that the script creates the output directory if missing."""
        nested_dir = tmp_path / "deep" / "nested"
        output_file = nested_dir / "resource_profile.json"
        
        monitor = ResourceMonitor(
            subject_id="test_sub",
            output_path=str(output_file)
        )
        
        monitor.peak_ram_gb = 1.0
        monitor.start_time = 0
        monitor.end_time = 100
        monitor.stop()
        
        assert output_file.exists()
        assert nested_dir.exists()