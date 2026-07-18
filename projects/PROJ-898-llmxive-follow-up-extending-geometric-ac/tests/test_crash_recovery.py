"""
Tests for crash recovery and error handling in physics simulations.

This module tests the CrashRecoveryHandler and error handling logic
in the data generation pipeline.
"""
import json
import os
import tempfile
import time
from unittest.mock import patch, MagicMock
import pytest

from code.data_generation import CrashRecoveryHandler, PhysicsSimulationError


class TestCrashRecoveryHandler:
    """Tests for the CrashRecoveryHandler class."""
    
    def test_initialization_creates_log_file(self):
        """Test that initialization creates the crash log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = CrashRecoveryHandler(log_dir=temp_dir)
            
            log_path = os.path.join(temp_dir, "crash_recovery_log.json")
            assert os.path.exists(log_path)
            
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            assert "crashes" in log_data
            assert "total_crashes" in log_data
            assert log_data["total_crashes"] == 0
    
    def test_record_state_adds_to_history(self):
        """Test that recording state adds to the history."""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = CrashRecoveryHandler(log_dir=temp_dir)
            
            test_state = {"key": "value", "step": 1}
            handler.record_state(1, test_state)
            
            assert len(handler.state_history) == 1
            assert handler.state_history[0]["step_id"] == 1
            assert handler.state_history[0]["state"] == test_state
    
    def test_record_state_limits_history_size(self):
        """Test that state history is limited to 100 entries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = CrashRecoveryHandler(log_dir=temp_dir)
            
            # Add 150 states
            for i in range(150):
                handler.record_state(i, {"step": i})
            
            assert len(handler.state_history) == 100
            # Should contain the last 100 states
            assert handler.state_history[0]["step_id"] == 50
            assert handler.state_history[-1]["step_id"] == 149
    
    def test_get_last_valid_state_returns_latest(self):
        """Test that getting last valid state returns the most recent."""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = CrashRecoveryHandler(log_dir=temp_dir)
            
            handler.record_state(1, {"step": 1})
            handler.record_state(2, {"step": 2})
            handler.record_state(3, {"step": 3})
            
            last_state = handler.get_last_valid_state()
            assert last_state["step_id"] == 3
            assert last_state["state"]["step"] == 3
    
    def test_get_last_valid_state_empty_history(self):
        """Test that getting last valid state returns None for empty history."""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = CrashRecoveryHandler(log_dir=temp_dir)
            
            last_state = handler.get_last_valid_state()
            assert last_state is None
    
    def test_handle_crash_updates_log(self):
        """Test that handling a crash updates the crash log."""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = CrashRecoveryHandler(log_dir=temp_dir)
            
            # Record a state first
            handler.record_state(10, {"test": "data"})
            
            # Handle a crash
            error = Exception("Test error")
            success = handler.handle_crash(
                error=error,
                step_id=10,
                trial_id="test_trial",
                topology_config={"test": "config"}
            )
            
            # Check log file
            log_path = os.path.join(temp_dir, "crash_recovery_log.json")
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            assert log_data["total_crashes"] == 1
            assert len(log_data["crashes"]) == 1
            
            crash_entry = log_data["crashes"][0]
            assert crash_entry["step_id"] == 10
            assert crash_entry["trial_id"] == "test_trial"
            assert crash_entry["error_type"] == "Exception"
            assert crash_entry["error_message"] == "Test error"
    
    def test_handle_crash_recovery_success(self):
        """Test successful recovery after a crash."""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = CrashRecoveryHandler(log_dir=temp_dir)
            
            # Record a state
            handler.record_state(5, {"step": 5})
            
            # Handle a crash - should succeed in recovery
            error = Exception("Test error")
            success = handler.handle_crash(
                error=error,
                step_id=5,
                trial_id="test_trial",
                topology_config={"test": "config"}
            )
            
            assert success is True
            
            # Check log
            log_path = os.path.join(temp_dir, "crash_recovery_log.json")
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            assert log_data["crashes"][0]["recovery_success"] is True
    
    def test_handle_crash_recovery_failure(self):
        """Test recovery failure when no state is available."""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = CrashRecoveryHandler(log_dir=temp_dir)
            
            # Don't record any state - recovery should fail
            error = Exception("Test error")
            success = handler.handle_crash(
                error=error,
                step_id=5,
                trial_id="test_trial",
                topology_config={"test": "config"}
            )
            
            # Recovery should fail because no state to restore
            assert success is False
            
            # Check log
            log_path = os.path.join(temp_dir, "crash_recovery_log.json")
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            assert log_data["crashes"][0]["recovery_success"] is False
    
    def test_max_retries_limit(self):
        """Test that recovery attempts are limited by max_retries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = CrashRecoveryHandler(log_dir=temp_dir, max_retries=2)
            
            # Record a state
            handler.record_state(5, {"step": 5})
            
            # Mock the get_last_valid_state to fail
            with patch.object(handler, 'get_last_valid_state', return_value=None):
                error = Exception("Test error")
                success = handler.handle_crash(
                    error=error,
                    step_id=5,
                    trial_id="test_trial",
                    topology_config={"test": "config"}
                )
            
            # Should have attempted recovery twice
            log_path = os.path.join(temp_dir, "crash_recovery_log.json")
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            assert log_data["crashes"][0]["recovery_attempts"] == 2
            assert success is False
    
    def test_crash_count_increment(self):
        """Test that crash count increments correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = CrashRecoveryHandler(log_dir=temp_dir)
            
            assert handler.crash_count == 0
            
            # Handle multiple crashes
            for i in range(3):
                handler.handle_crash(
                    error=Exception(f"Error {i}"),
                    step_id=i,
                    trial_id=f"trial_{i}",
                    topology_config={}
                )
            
            assert handler.crash_count == 3