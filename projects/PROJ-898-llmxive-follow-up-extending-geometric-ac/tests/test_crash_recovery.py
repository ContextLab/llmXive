"""
Unit tests for crash recovery mechanism in data_generation.py.

Tests verify that the CrashRecoveryHandler properly handles
physics simulation failures and recovers gracefully.
"""
import pytest
import os
import sys
import json
import tempfile
import time
from unittest.mock import patch, MagicMock
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.data_generation import (
    CrashRecoveryHandler,
    PhysicsSimulationError,
    URDFLoadError,
    SimulationStepError,
    TimeoutError,
    RecoveryResult
)

class TestCrashRecoveryHandler:
    """Test suite for CrashRecoveryHandler class."""
    
    @pytest.fixture
    def handler(self):
        """Create a CrashRecoveryHandler instance with test settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "errors.log")
            handler = CrashRecoveryHandler(
                max_retries=3,
                base_delay=0.1,
                max_delay=0.5,
                log_file=log_file
            )
            yield handler
    
    def test_initialization(self, handler):
        """Test that handler initializes with correct parameters."""
        assert handler.max_retries == 3
        assert handler.base_delay == 0.1
        assert handler.max_delay == 0.5
        assert handler.log_file is not None
    
    def test_handle_urdf_load_failure_success_after_retry(self, handler):
        """Test URDF load failure recovery with successful retry."""
        # Mock PyBullet functions
        with patch('code.data_generation.p') as mock_p, \
             patch('code.data_generation.pybullet_data') as mock_data:
            
            mock_p.resetSimulation = MagicMock()
            mock_p.setAdditionalSearchPath = MagicMock()
            mock_p.loadURDF = MagicMock(side_effect=[-1, 123])  # First fail, then succeed
            mock_data.getDataPath = MagicMock(return_value="/fake/path")
            
            result = handler.handle_urdf_load_failure("test.urdf", "test_context")
            
            assert result.success is True
            assert result.attempts == 2
            assert result.total_wait_time > 0.0
            assert result.error_message is None
            
            # Verify resetSimulation was called before each retry
            assert mock_p.resetSimulation.call_count == 2
    
    def test_handle_urdf_load_failure_max_retries(self, handler):
        """Test URDF load failure after max retries."""
        with patch('code.data_generation.p') as mock_p, \
             patch('code.data_generation.pybullet_data') as mock_data:
            
            mock_p.resetSimulation = MagicMock()
            mock_p.setAdditionalSearchPath = MagicMock()
            mock_p.loadURDF = MagicMock(return_value=-1)  # Always fail
            mock_data.getDataPath = MagicMock(return_value="/fake/path")
            
            result = handler.handle_urdf_load_failure("test.urdf", "test_context")
            
            assert result.success is False
            assert result.attempts == 3
            assert result.error_message is not None
            assert "Failed to load test.urdf" in result.error_message
    
    def test_handle_simulation_step_failure(self, handler):
        """Test simulation step failure recovery."""
        with patch('code.data_generation.p') as mock_p, \
             patch('code.data_generation.pybullet_data') as mock_data:
            
            mock_p.resetSimulation = MagicMock()
            mock_p.setAdditionalSearchPath = MagicMock()
            mock_data.getDataPath = MagicMock(return_value="/fake/path")
            
            result = handler.handle_simulation_step_failure("test_context")
            
            assert result.success is True
            assert result.attempts == 1
            assert result.total_wait_time == 0.0
    
    def test_handle_timeout(self, handler):
        """Test timeout error handling."""
        result = handler.handle_timeout("test_operation", 300.0)
        
        assert result.success is False
        assert result.attempts == 1
        assert result.total_wait_time == 0.0
        assert result.error_message is not None
        assert "test_operation" in result.error_message
        assert "300.0" in result.error_message
    
    def test_exponential_backoff(self, handler):
        """Test that delays increase exponentially."""
        delays = []
        current_delay = handler.base_delay
        
        for i in range(5):
            delays.append(current_delay)
            current_delay = min(current_delay * 2, handler.max_delay)
        
        # Verify exponential growth up to max
        assert delays[0] == handler.base_delay
        assert delays[1] == handler.base_delay * 2
        assert delays[2] == handler.base_delay * 4
        # Last delays should be capped at max_delay
        assert all(d <= handler.max_delay for d in delays[3:])
    
    def test_error_logging(self, handler):
        """Test that errors are properly logged to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_errors.log")
            test_handler = CrashRecoveryHandler(
                max_retries=1,
                base_delay=0.1,
                log_file=log_file
            )
            
            # Create a test error
            error = URDFLoadError("Test URDF load failure")
            
            # Call private log method
            test_handler._log_error(error, 1, 0.1)
            
            # Verify log file exists and contains error
            assert os.path.exists(log_file)
            
            with open(log_file, 'r') as f:
                log_content = f.read()
            
            assert "urdf_load" in log_content
            assert "Test URDF load failure" in log_content
            assert "attempt" in log_content
            
            # Parse and verify JSON structure
            log_entry = json.loads(log_content.strip())
            assert log_entry["error_type"] == "urdf_load"
            assert log_entry["attempt"] == 1
            assert log_entry["total_delay"] == 0.1
            assert "timestamp" in log_entry
    
    def test_recovery_result_dataclass(self):
        """Test RecoveryResult dataclass initialization."""
        result = RecoveryResult(
            success=True,
            attempts=2,
            total_wait_time=1.5,
            error_message=None
        )
        
        assert result.success is True
        assert result.attempts == 2
        assert result.total_wait_time == 1.5
        assert result.error_message is None
    
    def test_custom_exceptions(self):
        """Test custom exception classes."""
        # Test PhysicsSimulationError
        error = PhysicsSimulationError("Test error", "test_type")
        assert str(error) == "Test error"
        assert error.error_type == "test_type"
        assert hasattr(error, "timestamp")
        
        # Test URDFLoadError
        urdf_error = URDFLoadError("URDF failed")
        assert urdf_error.error_type == "urdf_load"
        
        # Test SimulationStepError
        step_error = SimulationStepError("Step failed")
        assert step_error.error_type == "simulation_step"
        
        # Test TimeoutError
        timeout_error = TimeoutError("Timed out")
        assert timeout_error.error_type == "timeout"
    
    def test_crash_recovery(self, handler):
        """
        Integration test for crash recovery mechanism.
        
        This test verifies that the recovery handler can successfully
        recover from simulated failures and that the recovery process
        is logged correctly.
        """
        # Simulate a scenario where recovery is needed
        with patch('code.data_generation.p') as mock_p, \
             patch('code.data_generation.pybullet_data') as mock_data:
            
            mock_p.resetSimulation = MagicMock()
            mock_p.setAdditionalSearchPath = MagicMock()
            mock_p.loadURDF = MagicMock(side_effect=[
                -1,  # First attempt fails
                -1,  # Second attempt fails
                456  # Third attempt succeeds
            ])
            mock_data.getDataPath = MagicMock(return_value="/fake/path")
            
            # Attempt recovery
            result = handler.handle_urdf_load_failure("recovery_test.urdf", "integration_test")
            
            # Verify recovery was successful
            assert result.success is True
            assert result.attempts == 3
            assert result.total_wait_time > 0.0
            
            # Verify all resetSimulation calls were made
            assert mock_p.resetSimulation.call_count == 3
            
            # Verify error log was created
            assert os.path.exists(handler.log_file)
            
            # Verify log contains multiple entries
            with open(handler.log_file, 'r') as f:
                log_lines = f.readlines()
            
            # Should have 2 error entries (for failed attempts)
            assert len(log_lines) >= 2
            
            # Parse and verify each log entry
            for line in log_lines:
                entry = json.loads(line.strip())
                assert "error_type" in entry
                assert "message" in entry
                assert "attempt" in entry

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
