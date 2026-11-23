import json
import os
import sys
import tempfile
import time
import logging
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.data_generation import (
    CrashRecoveryHandler, 
    URDFLoadError, 
    SimulationStepError, 
    RecoveryResult
)
from code.utils import setup_logging

class TestCrashRecoveryHandler:
    """
    Unit tests for T011: Error handling for physics simulation failures.
    """

    @pytest.fixture
    def handler(self, tmp_path):
        """Create a handler with a temporary error log path."""
        log_dir = tmp_path / "data" / "results"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = str(log_dir / "errors.log")
        
        logger = setup_logging()
        handler = CrashRecoveryHandler(logger, max_retries=2, base_delay=0.1)
        handler.error_log_path = log_path
        return handler, log_path

    def test_urdf_load_failure_recovery(self, handler):
        """Test that URDF load failure triggers retry and logs error."""
        handler_obj, log_path = handler

        # Mock p.loadURDF to always return -1 (failure)
        with patch('code.data_generation.p') as mock_p:
            mock_p.loadURDF.return_value = -1

            body_id, success = handler_obj.load_urdf_with_recovery(
                "fake.urdf", [0, 0, 0], [0, 0, 0, 1]
            )

            assert body_id == -1
            assert success is False
            assert mock_p.loadURDF.call_count == 2 # Initial + 1 retry

            # Verify log file exists and contains error
            assert os.path.exists(log_path)
            with open(log_path, 'r') as f:
                content = f.read()
            assert "PyBullet returned -1" in content
            assert "fake.urdf" in content

    def test_urdf_load_success_after_retry(self, handler):
        """Test that URDF load succeeds if it eventually returns a valid ID."""
        handler_obj, log_path = handler

        call_count = 0
        def mock_load(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return -1 # Fail first time
            return 123 # Succeed second time

        with patch('code.data_generation.p') as mock_p:
            mock_p.loadURDF.side_effect = mock_load

            body_id, success = handler_obj.load_urdf_with_recovery(
                "fake.urdf", [0, 0, 0], [0, 0, 0, 1]
            )

            assert body_id == 123
            assert success is True
            assert mock_p.loadURDF.call_count == 2

    def test_nan_detection_in_step(self, handler):
        """Test that NaN values in simulation state are detected."""
        handler_obj, _ = handler

        valid_state = {"pos": [1.0, 2.0, 3.0], "quat": [0.0, 0.0, 0.0, 1.0]}
        invalid_state = {"pos": [float('nan'), 2.0, 3.0], "quat": [0.0, 0.0, 0.0, 1.0]}
        
        assert handler_obj.validate_simulation_step(valid_state) is True
        assert handler_obj.validate_simulation_step(invalid_state) is False

    def test_infinity_detection_in_step(self, handler):
        """Test that Inf values in simulation state are detected."""
        handler_obj, _ = handler

        invalid_state = {"vel": [float('inf'), 0.0, 0.0]}
        assert handler_obj.validate_simulation_step(invalid_state) is False

    def test_recovery_from_step_error(self, handler):
        """Test that step error recovery returns correct RecoveryResult."""
        handler_obj, log_path = handler

        bad_state = {"pos": [float('nan'), 0.0, 0.0]}
        result = handler_obj.recover_from_step_error(bad_state)

        assert isinstance(result, RecoveryResult)
        assert result.success is False
        assert result.skipped_trial is True
        assert len(result.error_log) > 0
        
        # Verify logging
        with open(log_path, 'r') as f:
            content = f.read()
        assert "NaN/Inf detected" in content

    def test_crash_recovery_integration(self, handler):
        """
        Integration test simulating a full trial flow where:
        1. First load fails -> retries -> succeeds
        2. One step fails (NaN) -> recovery -> skips trial
        """
        handler_obj, log_path = handler

        # Track calls
        load_call_count = 0
        def mock_load_urdf(*args, **kwargs):
            nonlocal load_call_count
            load_call_count += 1
            return 100 if load_call_count > 1 else -1

        with patch('code.data_generation.p') as mock_p:
            mock_p.loadURDF.side_effect = mock_load_urdf
            
            # Simulate load
            body_id, success = handler_obj.load_urdf_with_recovery(
                "test.urdf", [0,0,0], [0,0,0,1]
            )
            assert success is True
            assert load_call_count == 2

            # Simulate step failure
            bad_step = {"pos": [float('nan'), 0, 0]}
            result = handler_obj.recover_from_step_error(bad_step)
            
            assert result.skipped_trial is True
            assert result.success is False

    def test_error_log_persistence(self, handler):
        """Verify that multiple errors are appended to the log file."""
        handler_obj, log_path = handler

        # Trigger two errors
        with patch('code.data_generation.p') as mock_p:
            mock_p.loadURDF.return_value = -1
            handler_obj.load_urdf_with_recovery("f1.urdf", [0,0,0], [0,0,0,1])
            handler_obj.load_urdf_with_recovery("f2.urdf", [0,0,0], [0,0,0,1])

        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        # Should have entries for both failures (and retries)
        assert len(lines) >= 2
        assert "f1.urdf" in lines[0]
        assert "f2.urdf" in lines[-1]
