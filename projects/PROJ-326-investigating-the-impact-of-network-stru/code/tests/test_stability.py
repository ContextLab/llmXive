"""
Unit tests for numerical stability checks and divergence detection.

Tests verify that:
1. Normal energy values pass stability checks
2. Divergent energy values trigger immediate abort
3. Divergence is logged correctly
4. Result is flagged as [SIMULATION_DIVERGENCE]
5. No retry or recovery logic is present
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.simulation.stability import (
    check_numerical_stability,
    handle_divergence,
    validate_simulation_step,
    SimulationDivergenceError,
    DIVERGENCE_THRESHOLD,
    MAX_ENERGY_DENSITY
)
from code.src.utils.logging import log_metric, init_logging


class TestNumericalStabilityChecks:
    """Tests for numerical stability checking functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_run_id = "test_run_123"
        self.test_seed = 42
        self.test_step = 10
        
        # Ensure logging is initialized
        init_logging()
    
    def test_normal_energy_values_pass(self):
        """Test that normal energy values pass stability check."""
        energy_values = [1.0, 2.5, -1.5, 0.5, 3.2]
        
        is_stable, error_msg = check_numerical_stability(
            energy_values, self.test_step, self.test_run_id
        )
        
        assert is_stable is True
        assert error_msg is None
    
    def test_large_but_valid_energy_values_pass(self):
        """Test that large but valid energy values pass (below threshold)."""
        # Values below DIVERGENCE_THRESHOLD (1e6) should pass
        energy_values = [1e5, 2e5, -1e5, 5e4, 3e5]
        
        is_stable, error_msg = check_numerical_stability(
            energy_values, self.test_step, self.test_run_id
        )
        
        assert is_stable is True
        assert error_msg is None
    
    def test_divergent_energy_values_fail(self):
        """Test that energy values exceeding threshold trigger divergence."""
        # One value exceeds DIVERGENCE_THRESHOLD (1e6)
        energy_values = [1.0, 2.5, 1e7, 0.5, 3.2]
        
        is_stable, error_msg = check_numerical_stability(
            energy_values, self.test_step, self.test_run_id
        )
        
        assert is_stable is False
        assert error_msg is not None
        assert "Divergence detected" in error_msg
        assert "[SIMULATION_DIVERGENCE]" in error_msg
    
    def test_nan_values_trigger_divergence(self):
        """Test that NaN values trigger divergence detection."""
        import math
        energy_values = [1.0, float('nan'), 3.2]
        
        is_stable, error_msg = check_numerical_stability(
            energy_values, self.test_step, self.test_run_id
        )
        
        assert is_stable is False
        assert error_msg is not None
        assert "NaN" in error_msg
    
    def test_inf_values_trigger_divergence(self):
        """Test that infinite values trigger divergence detection."""
        energy_values = [1.0, float('inf'), 3.2]
        
        is_stable, error_msg = check_numerical_stability(
            energy_values, self.test_step, self.test_run_id
        )
        
        assert is_stable is False
        assert error_msg is not None
        assert "Infinite" in error_msg
    
    def test_high_energy_density_triggers_divergence(self):
        """Test that high average energy density triggers divergence."""
        # Create values with high average density (above MAX_ENERGY_DENSITY = 1e4)
        energy_values = [1e5] * 10  # Average = 1e5 > 1e4
        
        is_stable, error_msg = check_numerical_stability(
            energy_values, self.test_step, self.test_run_id
        )
        
        assert is_stable is False
        assert error_msg is not None
        assert "avg_energy_density" in error_msg
    
    def test_empty_energy_list_passes(self):
        """Test that empty energy list is considered stable."""
        energy_values = []
        
        is_stable, error_msg = check_numerical_stability(
            energy_values, self.test_step, self.test_run_id
        )
        
        assert is_stable is True
        assert error_msg is None


class TestDivergenceHandling:
    """Tests for divergence handling and abort logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_run_id = "test_run_456"
        self.test_seed = 42
        self.test_step = 15
        self.test_energy = 1e7
        
        init_logging()
    
    def test_handle_divergence_raises_exception(self):
        """Test that handle_divergence always raises an exception."""
        with pytest.raises(SimulationDivergenceError) as exc_info:
            handle_divergence(
                self.test_run_id,
                self.test_step,
                self.test_energy,
                self.test_seed
            )
        
        assert exc_info.value.run_id == self.test_run_id
        assert exc_info.value.step == self.test_step
        assert exc_info.value.energy_value == self.test_energy
        assert exc_info.value.tag == "[SIMULATION_DIVERGENCE]"
    
    def test_handle_divergence_logs_event(self):
        """Test that handle_divergence logs the divergence event."""
        # Mock the log_metric function to verify it's called
        with patch('code.src.simulation.stability.log_metric') as mock_log:
            with pytest.raises(SimulationDivergenceError):
                handle_divergence(
                    self.test_run_id,
                    self.test_step,
                    self.test_energy,
                    self.test_seed
                )
            
            # Verify log_metric was called
            assert mock_log.called
            call_args = mock_log.call_args[0][0]
            
            assert call_args["event_type"] == "divergence_detected"
            assert call_args["run_id"] == self.test_run_id
            assert call_args["seed"] == self.test_seed
            assert call_args["status"] == "aborted"
    
    def test_validate_simulation_step_aborts_on_divergence(self):
        """Test that validate_simulation_step aborts when divergence is detected."""
        divergent_energies = [1.0, 2.5, 1e7, 0.5, 3.2]
        
        with pytest.raises(SimulationDivergenceError) as exc_info:
            validate_simulation_step(
                divergent_energies,
                self.test_step,
                self.test_run_id,
                self.test_seed
            )
        
        assert exc_info.value.tag == "[SIMULATION_DIVERGENCE]"
    
    def test_validate_simulation_step_returns_true_on_stability(self):
        """Test that validate_simulation_step returns True for stable values."""
        stable_energies = [1.0, 2.5, -1.5, 0.5, 3.2]
        
        result = validate_simulation_step(
            stable_energies,
            self.test_step,
            self.test_run_id,
            self.test_seed
        )
        
        assert result is True


class TestNoRetryLogic:
    """Tests to verify no retry or recovery logic exists."""
    
    def test_divergence_is_final(self):
        """Test that divergence cannot be recovered from (no retry)."""
        # The exception should propagate immediately
        with pytest.raises(SimulationDivergenceError):
            handle_divergence(
                "test_run", 10, 1e7, 42
            )
        
        # If we reach here, the exception was raised as expected
        # No retry logic should have been attempted
    
    def test_exception_contains_abort_tag(self):
        """Test that the exception contains the abort tag."""
        try:
            handle_divergence("test", 10, 1e7, 42)
        except SimulationDivergenceError as e:
            assert e.tag == "[SIMULATION_DIVERGENCE]"
            assert "aborted" in str(e).lower() or "abort" in str(e).lower()

class TestLoggingIntegration:
    """Tests for logging integration during divergence."""
    
    def test_divergence_logged_to_run_log(self):
        """Test that divergence events are logged to run_log.json."""
        import tempfile
        import json
        
        # Create a temporary log file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)
            temp_log_path = f.name
        
        try:
            # Patch the log file path
            with patch('code.src.utils.logging.RUN_LOG_PATH', temp_log_path):
                with pytest.raises(SimulationDivergenceError):
                    handle_divergence("test_run", 10, 1e7, 42)
                
                # Read the log file and verify entry
                with open(temp_log_path, 'r') as f:
                    log_data = json.load(f)
                
                # Find the divergence entry
                divergence_entries = [
                    entry for entry in log_data
                    if entry.get('event_type') == 'divergence_detected'
                ]
                
                assert len(divergence_entries) > 0
                entry = divergence_entries[0]
                assert entry['run_id'] == "test_run"
                assert entry['status'] == "aborted"
        finally:
            # Clean up
            if os.path.exists(temp_log_path):
                os.unlink(temp_log_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
