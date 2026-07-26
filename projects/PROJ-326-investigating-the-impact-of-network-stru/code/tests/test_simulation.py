"""
Unit tests for simulation stability and divergence detection (T052, T026a, T026b).
"""
import pytest
import time
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

from code.src.simulation.stability import (
    check_for_nan_inf,
    check_energy_conservation,
    detect_divergence,
    run_stability_check,
    enforce_runtime_limit,
    log_runtime_duration,
    SimulationDivergenceError,
    StabilityError
)
from code.src.utils.logging import get_run_log

class TestDivergenceDetection:
    """Tests for T052: explicit numerical stability assertions for energy divergence."""

    def test_detect_divergence_normal_case(self):
        """Test that normal energy values are not flagged as divergence."""
        initial = 100.0
        current = 150.0  # 1.5x amplification, below 1000x threshold
        assert detect_divergence(current, initial) is False

    def test_detect_divergence_threshold_exceeded(self):
        """Test that energy exceeding threshold is flagged as divergence."""
        initial = 100.0
        current = 1500.0  # 15x amplification, still below 1000x default
        assert detect_divergence(current, initial) is False
        
        # Now test with a lower threshold
        assert detect_divergence(current, initial, amplification_factor=10.0) is True

    def test_detect_divergence_severe_amplification(self):
        """Test severe amplification is detected with default threshold."""
        initial = 100.0
        current = 1500000.0  # 15000x amplification
        assert detect_divergence(current, initial) is True

    def test_detect_divergence_zero_initial_energy(self):
        """Test divergence detection when initial energy is zero."""
        # Zero initial, zero current -> no divergence
        assert detect_divergence(0.0, 0.0) is False
        
        # Zero initial, non-zero current -> divergence
        assert detect_divergence(1.0, 0.0) is True
        assert detect_divergence(-1.0, 0.0) is True

    def test_detect_divergence_negative_energy(self):
        """Test that negative energy values are handled correctly."""
        initial = -100.0
        current = -150000.0  # 1500x amplification in magnitude
        assert detect_divergence(current, initial) is True

    def test_run_stability_check_divergence_raises_error(self):
        """
        T052: Test that run_stability_check raises SimulationDivergenceError
        when energy divergence is detected, and logs [SIMULATION_DIVERGENCE].
        """
        run_id = "test_divergence_run"
        start_time = time.time()
        initial_energy = 100.0
        current_energy = 1500000.0  # Severe divergence
        
        config = {
            "divergence_threshold": 1000.0,
            "simulation_timeout_seconds": 3600.0
        }

        # Mock the log_run function to capture calls
        with patch('code.src.simulation.stability.log_run') as mock_log:
            with patch('code.src.simulation.stability.logging.getLogger') as mock_logger:
                mock_logger_instance = MagicMock()
                mock_logger.return_value = mock_logger_instance
                
                # This should raise SimulationDivergenceError
                with pytest.raises(SimulationDivergenceError) as exc_info:
                    run_stability_check(run_id, start_time, current_energy, initial_energy, config)
                
                # Verify the error message contains the divergence flag
                assert "[SIMULATION_DIVERGENCE]" in str(exc_info.value)
                
                # Verify logger.warning was called with the flag
                mock_logger_instance.warning.assert_called()
                warning_call_args = mock_logger_instance.warning.call_args[0][0]
                assert "[SIMULATION_DIVERGENCE]" in warning_call_args

    def test_run_stability_check_no_divergence(self):
        """Test that normal energy values pass the stability check."""
        run_id = "test_normal_run"
        start_time = time.time()
        initial_energy = 100.0
        current_energy = 150.0  # Normal variation
        
        config = {
            "divergence_threshold": 1000.0,
            "simulation_timeout_seconds": 3600.0
        }

        with patch('code.src.simulation.stability.log_run'):
            with patch('code.src.simulation.stability.logging.getLogger'):
                result = run_stability_check(run_id, start_time, current_energy, initial_energy, config)
                
                assert result["status"] == "OK"
                assert result["divergence_detected"] is False

    def test_run_stability_check_uses_config_threshold(self):
        """Test that run_stability_check uses the divergence threshold from config."""
        run_id = "test_config_threshold_run"
        start_time = time.time()
        initial_energy = 100.0
        current_energy = 500.0  # 5x amplification
        
        # Config with lower threshold (4x)
        config = {
            "divergence_threshold": 4.0,
            "simulation_timeout_seconds": 3600.0
        }

        with patch('code.src.simulation.stability.log_run'):
            with patch('code.src.simulation.stability.logging.getLogger') as mock_logger:
                mock_logger_instance = MagicMock()
                mock_logger.return_value = mock_logger_instance
                
                with pytest.raises(SimulationDivergenceError):
                    run_stability_check(run_id, start_time, current_energy, initial_energy, config)
                
                # Should have triggered divergence with 4.0 threshold
                mock_logger_instance.warning.assert_called()

class TestRuntimeLimit:
    """Tests for T026a: hard runtime abort mechanism."""

    def test_enforce_runtime_limit_within_limit(self):
        """Test that runtime within limit does not raise error."""
        run_id = "test_within_limit"
        start_time = time.time()
        max_seconds = 3600.0
        
        result = enforce_runtime_limit(run_id, start_time, max_seconds)
        assert result < max_seconds

    def test_enforce_runtime_limit_exceeded(self):
        """Test that runtime exceeding limit raises SimulationDivergenceError."""
        run_id = "test_exceeded"
        start_time = time.time() - 3700.0  # 3700 seconds ago
        max_seconds = 3600.0
        
        with pytest.raises(SimulationDivergenceError) as exc_info:
            enforce_runtime_limit(run_id, start_time, max_seconds)
        
        assert "Runtime exceeded limit" in str(exc_info.value)

class TestNaNInfCheck:
    """Tests for NaN and Inf detection."""

    def test_check_for_nan_inf_no_issues(self):
        """Test array with no NaN/Inf passes check."""
        arr = np.array([1.0, 2.0, 3.0])
        assert check_for_nan_inf(arr) is False

    def test_check_for_nan_inf_contains_nan(self):
        """Test array with NaN is detected."""
        arr = np.array([1.0, np.nan, 3.0])
        assert check_for_nan_inf(arr) is True

    def test_check_for_nan_inf_contains_inf(self):
        """Test array with Inf is detected."""
        arr = np.array([1.0, np.inf, 3.0])
        assert check_for_nan_inf(arr) is True

    def test_check_for_nan_inf_exceeds_threshold(self):
        """Test array with values exceeding threshold is detected."""
        arr = np.array([1.0, 2.0, 1e15])
        assert check_for_nan_inf(arr, threshold=1e10) is True

class TestEnergyConservation:
    """Tests for energy conservation checks."""

    def test_check_energy_conservation_within_tolerance(self):
        """Test that energy within tolerance is considered conserved."""
        initial = 100.0
        current = 100.0000001
        assert check_energy_conservation(initial, current, tolerance=1e-6) is True

    def test_check_energy_conservation_exceeds_tolerance(self):
        """Test that energy outside tolerance is not conserved."""
        initial = 100.0
        current = 101.0
        assert check_energy_conservation(initial, current, tolerance=1e-6) is False

class TestLogging:
    """Tests for runtime logging (T026b)."""

    def test_log_runtime_duration_creates_entry(self):
        """Test that log_runtime_duration creates a valid log entry."""
        run_id = "test_log_runtime"
        duration = 123.456
        
        with patch('code.src.simulation.stability.log_run') as mock_log:
            log_runtime_duration(run_id, duration)
            
            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs["event_type"] == "simulation_runtime"
            assert call_kwargs["run_id"] == run_id
            assert call_kwargs["duration_seconds"] == duration