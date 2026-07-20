"""
Unit tests for crash recovery and error handling in data generation.
Verifies that the system handles physics simulation failures gracefully.
"""

import json
import os
import sys
import tempfile
import time
from unittest.mock import patch, MagicMock
import pytest
import numpy as np

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data_generation import (
    CrashRecoveryHandler,
    PhysicsSimulationError,
    URDFLoadError,
    SimulationStepError,
    TimeoutError,
    RecoveryResult
)
from utils import setup_logging

class TestCrashRecoveryHandler:
    """Tests for the CrashRecoveryHandler class."""

    @pytest.fixture
    def handler(self, tmp_path):
        """Create a handler with a temporary log directory."""
        log_dir = tmp_path / "data" / "results"
        log_dir.mkdir(parents=True)
        
        # Mock the error log path
        with patch('data_generation.CrashRecoveryHandler.error_log_path', str(log_dir / "errors.log")):
            logger = setup_logging("test")
            return CrashRecoveryHandler(logger)

    def test_successful_operation(self, handler):
        """Test that a successful operation returns immediately."""
        def success_op():
            return "success"
        
        success, result = handler.retry_with_backoff(success_op, "test_op")
        assert success is True
        assert result == "success"

    def test_retry_on_transient_failure(self, handler):
        """Test that transient failures trigger retries with backoff."""
        attempts = [0]
        
        def flaky_op():
            attempts[0] += 1
            if attempts[0] < 3:
                raise SimulationStepError("Transient failure")
            return "success"
        
        success, result = handler.retry_with_backoff(flaky_op, "flaky_op")
        assert success is True
        assert result == "success"
        assert attempts[0] == 3  # Failed twice, succeeded on third

    def test_max_retries_exceeded(self, handler):
        """Test that max retries are respected and failure is returned."""
        def always_fail():
            raise URDFLoadError("Always fails")
        
        success, result = handler.retry_with_backoff(always_fail, "fail_op")
        assert success is False
        assert result is None

    def test_unexpected_error_raises(self, handler):
        """Test that unexpected errors are not caught and re-raised."""
        def unexpected_error():
            raise ValueError("Unexpected error")
        
        with pytest.raises(ValueError, match="Unexpected error"):
            handler.retry_with_backoff(unexpected_error, "unexpected_op")

    def test_log_error_creation(self, handler, tmp_path):
        """Test that error logs are created when errors occur."""
        log_file = tmp_path / "data" / "results" / "errors.log"
        
        # Create directory structure
        log_file.parent.mkdir(parents=True)
        
        # Mock the log file path
        handler.error_log_path = str(log_file)
        
        def fail_op():
            raise SimulationStepError("Test error")
        
        handler.retry_with_backoff(fail_op, "fail_op")
        
        assert log_file.exists()
        with open(log_file, "r") as f:
            content = f.read()
            assert "SimulationStepError" in content
            assert "Test error" in content

    def test_handle_urdf_load_success(self, handler):
        """Test successful URDF loading."""
        # Create a temporary URDF file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', delete=False) as f:
            f.write('''<?xml version="1.0"?>
            <robot name="test">
                <link name="base">
                    <inertial><mass value="1.0"/></inertial>
                    <visual><geometry><box size="0.1 0.1 0.1"/></geometry></visual>
                </link>
            </robot>''')
            urdf_path = f.name

        try:
            with patch('data_generation.p') as mock_p:
                mock_p.loadURDF.return_value = 1  # Valid body ID
                mock_p.getNumBodies.return_value = 0
                
                success, body_id = handler.handle_urdf_load(urdf_path, "test_trial")
                
                assert success is True
                assert body_id == 1
        finally:
            os.unlink(urdf_path)

    def test_handle_urdf_load_not_found(self, handler):
        """Test URDF loading with non-existent file."""
        success, body_id = handler.handle_urdf_load("/nonexistent/path.urdf", "test_trial")
        assert success is False
        assert body_id is None

    def test_handle_urdf_load_invalid_id(self, handler):
        """Test URDF loading that returns error ID."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', delete=False) as f:
            f.write('<?xml version="1.0"?><robot><link name="base"/></robot>')
            urdf_path = f.name

        try:
            with patch('data_generation.p') as mock_p:
                mock_p.loadURDF.return_value = -1  # Error ID
                
                success, body_id = handler.handle_urdf_load(urdf_path, "test_trial")
                
                assert success is False
                assert body_id is None
        finally:
            os.unlink(urdf_path)

    def test_handle_simulation_step_success(self, handler):
        """Test successful simulation step."""
        with patch('data_generation.p') as mock_p:
            mock_p.getNumBodies.return_value = 0
            mock_p.getBasePositionAndOrientation.return_value = ([0, 0, 0], [0, 0, 0, 1], [], [], [], [])
            mock_p.getBaseVelocity.return_value = ([0, 0, 0], [0, 0, 0])
            mock_p.getJointStates.return_value = []
            
            success, state = handler.handle_simulation_step("test_trial")
            
            assert success is True
            assert isinstance(state, dict)

    def test_handle_simulation_step_nan_detection(self, handler):
        """Test that NaN values in simulation state are detected."""
        with patch('data_generation.p') as mock_p:
            mock_p.getNumBodies.return_value = 1
            mock_p.getBasePositionAndOrientation.return_value = (
                [np.nan, 0, 0], [0, 0, 0, 1], [], [], [], []
            )
            mock_p.getBaseVelocity.return_value = ([0, 0, 0], [0, 0, 0])
            mock_p.getJointStates.return_value = []
            
            success, state = handler.handle_simulation_step("test_trial")
            
            assert success is False
            assert state is None

    def test_exponential_backoff_timing(self, handler):
        """Test that backoff time increases exponentially."""
        start_time = time.time()
        
        def always_fail():
            raise SimulationStepError("Fail")
        
        handler.retry_with_backoff(always_fail, "fail_op")
        elapsed = time.time() - start_time
        
        # Should have waited at least: 0.1 + 0.2 + 0.4 + 0.8 + 1.6 = 3.1 seconds
        # But capped at MAX_BACKOFF (5.0) for each step after the first few
        # With MAX_RETRIES=5, we expect 4 waits: 0.1, 0.2, 0.4, 0.8
        assert elapsed >= 1.0  # Minimum expected backoff time

class TestExceptions:
    """Tests for custom exception classes."""

    def test_physics_simulation_error(self):
        """Test base exception."""
        exc = PhysicsSimulationError("Test message")
        assert str(exc) == "Test message"

    def test_urdf_load_error(self):
        """Test URDF load exception."""
        exc = URDFLoadError("URDF failed")
        assert isinstance(exc, PhysicsSimulationError)
        assert str(exc) == "URDF failed"

    def test_simulation_step_error(self):
        """Test simulation step exception."""
        exc = SimulationStepError("Step failed")
        assert isinstance(exc, PhysicsSimulationError)
        assert str(exc) == "Step failed"

    def test_timeout_error(self):
        """Test timeout exception."""
        exc = TimeoutError("Timed out")
        assert isinstance(exc, PhysicsSimulationError)
        assert str(exc) == "Timed out"

class TestRecoveryResult:
    """Tests for RecoveryResult class."""

    def test_success_result(self):
        """Test successful recovery result."""
        result = RecoveryResult(success=True, retries=0)
        assert result.success is True
        assert result.retries == 0
        assert result.last_error is None

    def test_failure_result(self):
        """Test failed recovery result."""
        result = RecoveryResult(success=False, retries=3, last_error="Error message")
        assert result.success is False
        assert result.retries == 3
        assert result.last_error == "Error message"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
