"""
Unit tests for the simulation profiling functionality (Task T036).

These tests verify that the profiling module correctly measures runtime and memory,
enforces the 6-hour time limit, and generates valid profile reports.
"""
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.profile_simulation import (
    get_memory_usage_mb,
    run_profiled_sweep,
    write_profile_report,
    MAX_RUNTIME_SECONDS,
    MAX_MEMORY_MB
)
from code.utils.simulation import SimulationConfig

class TestGetMemoryUsageMb:
    """Tests for memory usage measurement function."""
    
    def test_memory_usage_returns_positive_value(self):
        """Memory usage should always be a positive number."""
        memory = get_memory_usage_mb()
        assert memory > 0, "Memory usage should be positive"
        
    def test_memory_usage_returns_float(self):
        """Memory usage should be returned as a float."""
        memory = get_memory_usage_mb()
        assert isinstance(memory, float), "Memory should be returned as float"

class TestRunProfiledSweep:
    """Tests for the profiled sweep execution."""
    
    @patch('code.profile_simulation.SimulationOrchestrator')
    def test_sweep_respects_time_limit(self, mock_orchestrator_class):
        """Sweep should stop when time limit is reached."""
        # Create a mock orchestrator that simulates slow iterations
        mock_orchestrator = Mock()
        mock_orchestrator.run_single_iteration.side_effect = [
            {'success': True} for _ in range(100)
        ]
        mock_orchestrator_class.return_value = mock_orchestrator
        
        config = SimulationConfig(
            n_values=[100],
            p_values=[50],
            rho_values=[0.0],
            distribution_types=['normal'],
            n_iterations=100,
            seed=42
        )
        
        # Mock time to simulate long-running iterations
        with patch('code.profile_simulation.time') as mock_time:
            mock_time.time.side_effect = [0, 1000, 2000, 3000, 4000, 5000, 6000]  # Simulate time passing
            
            result = run_profiled_sweep(config, max_iterations=100)
            
            # Should have stopped before completing all iterations due to time limit
            assert result['timing']['iterations_completed'] < 100
            
    @patch('code.profile_simulation.SimulationOrchestrator')
    def test_sweep_collects_iteration_results(self, mock_orchestrator_class):
        """Sweep should collect results for each completed iteration."""
        mock_orchestrator = Mock()
        mock_orchestrator.run_single_iteration.return_value = {'success': True}
        mock_orchestrator_class.return_value = mock_orchestrator
        
        config = SimulationConfig(
            n_values=[100],
            p_values=[50],
            rho_values=[0.0],
            distribution_types=['normal'],
            n_iterations=5,
            seed=42
        )
        
        with patch('code.profile_simulation.time.time', side_effect=[0, 0.1, 0.2, 0.3, 0.4, 0.5]):
            result = run_profiled_sweep(config, max_iterations=5)
            
            assert len(result['iterations']) > 0
            assert result['timing']['iterations_completed'] > 0

class TestWriteProfileReport:
    """Tests for profile report writing."""
    
    def test_report_writes_valid_json(self, tmp_path):
        """Profile report should be written as valid JSON."""
        output_path = tmp_path / "test_report.json"
        
        test_data = {
            'timing': {'total_seconds': 100},
            'memory': {'peak_mb': 500},
            'constraints': {'satisfied': True}
        }
        
        write_profile_report(test_data, output_path)
        
        assert output_path.exists(), "Report file should be created"
        
        with open(output_path) as f:
            loaded = json.load(f)
            
        assert loaded == test_data, "Report content should match input"
        
    def test_report_creates_parent_directories(self, tmp_path):
        """Profile report should create parent directories if they don't exist."""
        output_path = tmp_path / "nested" / "dir" / "report.json"
        
        test_data = {'test': 'data'}
        
        write_profile_report(test_data, output_path)
        
        assert output_path.exists(), "Report file should be created with parent dirs"

class TestConstraints:
    """Tests for constraint validation."""
    
    def test_6h_limit_constant(self):
        """6-hour limit should be correctly defined in seconds."""
        assert MAX_RUNTIME_SECONDS == 6 * 3600, "6-hour limit should be 21600 seconds"
        
    def test_memory_limit_constant(self):
        """Memory limit should be correctly defined."""
        assert MAX_MEMORY_MB == 8 * 1024, "Memory limit should be 8GB in MB"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])