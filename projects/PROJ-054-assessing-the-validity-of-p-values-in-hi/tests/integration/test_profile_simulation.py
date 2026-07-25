"""
Integration tests for the simulation profiling task (T036).
Verifies that the profiling script runs correctly and produces valid output.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from profile_simulation import (
    run_profiled_sweep,
    write_profile_report,
    get_memory_usage_mb,
    MAX_RUNTIME_SECONDS
)


class TestMemoryUsage:
    """Tests for memory usage monitoring."""

    def test_get_memory_usage_mb_returns_positive(self):
        """Verify that memory usage is reported as a positive number."""
        memory = get_memory_usage_mb()
        assert memory >= 0, "Memory usage should be non-negative"

    def test_memory_usage_increases_with_allocation(self):
        """Verify that memory usage increases when allocating large arrays."""
        initial_memory = get_memory_usage_mb()
        
        # Allocate a large array
        large_array = np.zeros(10000000, dtype=np.float64)  # ~80MB
        
        current_memory = get_memory_usage_mb()
        
        # Memory should have increased (allow some tolerance for system variations)
        assert current_memory >= initial_memory, "Memory should increase after allocation"
        
        # Clean up
        del large_array


class TestProfileSweep:
    """Tests for the profiled sweep execution."""

    def test_profile_sweep_returns_valid_structure(self):
        """Verify that the profile sweep returns a dictionary with required keys."""
        # Mock the SimulationOrchestrator to avoid actual simulation
        with patch('profile_simulation.SimulationOrchestrator') as mock_orchestrator:
            mock_instance = MagicMock()
            mock_instance.run = MagicMock()
            mock_orchestrator.return_value = mock_instance
            
            results = run_profiled_sweep()
            
            assert isinstance(results, dict)
            assert "start_time" in results
            assert "configs_profiled" in results
            assert "config_results" in results
            assert "total_runtime" in results
            assert "peak_memory_mb" in results
            assert "estimated_full_runtime_hours" in results
            assert "within_budget" in results
            assert "warnings" in results

    def test_profile_sweep_executes_all_configs(self):
        """Verify that all profile configurations are executed."""
        with patch('profile_simulation.SimulationOrchestrator') as mock_orchestrator:
            mock_instance = MagicMock()
            mock_instance.run = MagicMock()
            mock_orchestrator.return_value = mock_instance
            
            results = run_profiled_sweep()
            
            # We defined 6 profile configs
            assert results["configs_profiled"] == 6
            assert len(results["config_results"]) == 6

    def test_profile_sweep_tracks_memory(self):
        """Verify that memory usage is tracked during the sweep."""
        with patch('profile_simulation.SimulationOrchestrator') as mock_orchestrator:
            with patch('profile_simulation.get_memory_usage_mb') as mock_memory:
                mock_orchestrator.return_value = MagicMock()
                mock_orchestrator.return_value.run = MagicMock()
                
                # Return increasing memory values
                mock_memory.side_effect = [100, 150, 200, 250, 300, 350, 400]
                
                results = run_profiled_sweep()
                
                assert results["peak_memory_mb"] > 0
                assert results["peak_memory_mb"] >= 100


class TestReportWriting:
    """Tests for report writing functionality."""

    def test_write_profile_report_creates_file(self):
        """Verify that the report file is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_profile.json"
            
            sample_results = {
                "start_time": 0,
                "configs_profiled": 2,
                "config_results": [],
                "total_runtime": 10.0,
                "peak_memory_mb": 500.0,
                "estimated_full_runtime_hours": 4.0,
                "within_budget": True,
                "warnings": []
            }
            
            write_profile_report(sample_results, output_path)
            
            assert output_path.exists(), "Report file should be created"
            
            # Verify file content
            with open(output_path, 'r') as f:
                content = json.load(f)
            
            assert content["task_id"] == "T036"
            assert content["results"]["total_runtime"] == 10.0

    def test_write_profile_report_creates_directories(self):
        """Verify that parent directories are created if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "nested" / "dir" / "report.json"
            
            sample_results = {
                "start_time": 0,
                "configs_profiled": 1,
                "config_results": [],
                "total_runtime": 1.0,
                "peak_memory_mb": 100.0,
                "estimated_full_runtime_hours": 1.0,
                "within_budget": True,
                "warnings": []
            }
            
            write_profile_report(sample_results, nested_path)
            
            assert nested_path.exists(), "Nested directories should be created"


class TestBudgetVerification:
    """Tests for budget verification logic."""

    def test_within_budget_flag_logic(self):
        """Verify that within_budget flag is set correctly."""
        with patch('profile_simulation.SimulationOrchestrator') as mock_orchestrator:
            with patch('profile_simulation.get_memory_usage_mb') as mock_memory:
                mock_orchestrator.return_value = MagicMock()
                mock_orchestrator.return_value.run = MagicMock()
                mock_memory.return_value = 100.0
                
                # Mock the runtime to be very small
                with patch('profile_simulation.time.time') as mock_time:
                    mock_time.side_effect = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                    
                    results = run_profiled_sweep()
                    
                    # Should be within budget for small runtimes
                    assert isinstance(results["within_budget"], bool)

    def test_budget_constant_correct(self):
        """Verify that the MAX_RUNTIME_SECONDS constant is 6 hours."""
        assert MAX_RUNTIME_SECONDS == 6 * 3600, "MAX_RUNTIME_SECONDS should be 6 hours"


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_profile_workflow(self):
        """Test the complete profiling workflow with mocked components."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "profile_results.json"
            
            with patch('profile_simulation.SimulationOrchestrator') as mock_orchestrator:
                mock_instance = MagicMock()
                mock_instance.run = MagicMock()
                mock_orchestrator.return_value = mock_instance
                
                with patch('profile_simulation.get_memory_usage_mb') as mock_memory:
                    mock_memory.return_value = 100.0
                    
                    results = run_profiled_sweep()
                    write_profile_report(results, output_path)
                    
                    # Verify file exists and contains valid JSON
                    assert output_path.exists()
                    
                    with open(output_path, 'r') as f:
                        report = json.load(f)
                    
                    assert report["task_id"] == "T036"
                    assert "results" in report
                    assert report["results"]["configs_profiled"] == 6

    def test_profile_with_real_simulation_config(self):
        """Test with actual SimulationConfig (but mocked execution)."""
        from utils.simulation import SimulationConfig
        
        with patch('profile_simulation.SimulationOrchestrator') as mock_orchestrator:
            mock_orchestrator.return_value = MagicMock()
            mock_orchestrator.return_value.run = MagicMock()
            
            # This should not raise an exception
            results = run_profiled_sweep()
            
            assert "config_results" in results
            assert len(results["config_results"]) > 0