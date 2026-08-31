import pytest
import sys
import os
import tempfile
import yaml
from unittest.mock import patch, MagicMock
import numpy as np

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sim.eco_director import (
    run_simulation, 
    handle_termination, 
    get_memory_usage_mb,
    load_config,
    validate_config
)
from src.data_models import SimulationRun
from src.sim.logging_config import create_logger

class TestT006bTermination:
    """
    Tests for T006b: Internal memory/time limit detection and signal emission.
    """

    def test_handle_termination_calls_exit(self):
        """Test that handle_termination exits cleanly."""
        run = SimulationRun(run_id="test", config={}, start_time=0, current_step=0)
        
        # Mock sys.exit to prevent actual exit during test
        with patch('sys.exit') as mock_exit:
            handle_termination("Test Reason", run)
            mock_exit.assert_called_once_with(1)

    def test_handle_termination_logs_reason(self):
        """Test that handle_termination logs the specific reason."""
        run = SimulationRun(run_id="test", config={}, start_time=0, current_step=0)
        
        with patch('sys.exit'), patch('builtins.print') as mock_print:
            handle_termination("Memory Explosion", run)
            # Check that print was called with the reason
            mock_print.assert_called()
            # Verify the reason is in the output
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Memory Explosion" in c for c in calls)

    def test_run_simulation_detects_memory_limit(self):
        """Test that run_simulation calls handle_termination when memory limit is exceeded."""
        config = {
            'grid_size': 10,
            'steps': 100,
            'memory_limit_mb': 1.0  # Very low limit to trigger immediate failure
        }
        
        # Mock get_memory_usage_mb to return a value exceeding the limit
        with patch('src.sim.eco_director.get_memory_usage_mb', return_value=1000.0):
            with patch('src.sim.eco_director.handle_termination') as mock_handler:
                with patch('sys.exit'): # Prevent actual exit
                    # We expect the simulation to call handle_termination immediately
                    # Since we mock get_memory_usage_mb to always return high value,
                    # the first check inside the loop should trigger it.
                    try:
                        run_simulation(config, seed=42)
                    except SystemExit:
                        pass # Expected if not mocked properly, but we patched exit
                    
                    # Verify handle_termination was called
                    assert mock_handler.called
                    # Verify it was called with a reason containing "Memory"
                    call_args = mock_handler.call_args
                    assert "Memory" in call_args[0][0]

    def test_run_simulation_detects_time_limit(self):
        """Test that run_simulation calls handle_termination when time limit is exceeded."""
        config = {
            'grid_size': 10,
            'steps': 100,
            'memory_limit_mb': 10000.0,
            'time_limit_seconds': 0.0001  # Very short time limit
        }
        
        with patch('src.sim.eco_director.handle_termination') as mock_handler:
            with patch('sys.exit'):
                try:
                    run_simulation(config, seed=42)
                except SystemExit:
                    pass
                
                assert mock_handler.called
                call_args = mock_handler.call_args
                assert "Time Limit" in call_args[0][0]

    def test_handle_termination_with_logger(self):
        """Test that handle_termination logs to the logger if provided."""
        run = SimulationRun(run_id="test", config={}, start_time=0, current_step=0)
        mock_logger = MagicMock()
        
        with patch('sys.exit'):
            handle_termination("Test Reason", run, mock_logger)
            mock_logger.log.assert_called_once()
            log_data = mock_logger.log.call_args[0][0]
            assert log_data['event'] == 'termination'
            assert log_data['reason'] == 'Test Reason'