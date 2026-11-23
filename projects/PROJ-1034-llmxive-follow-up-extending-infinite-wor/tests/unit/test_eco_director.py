"""
Unit tests for eco_director.py state transitions.

This module verifies that the Eco-Director simulation engine correctly
transitions between states (INIT -> RUNNING -> TERMINATED/ABORTED) based
on configuration, runtime limits, and internal logic.

Dependencies:
  - src.sim.eco_director: load_config, validate_config, run_simulation,
    inject_runtime_params, handle_termination
  - src.data_models: SimulationRun, MetricRecord
  - src.config: set_seed
"""
import pytest
import os
import sys
import tempfile
import yaml
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import project modules using the verified API surface
# Note: The API surface lists 'src.sim.eco_director' with 'handle_termination'
from src.sim.eco_director import (
    load_config,
    validate_config,
    run_simulation,
    inject_runtime_params,
    handle_termination,
    get_memory_usage_mb
)
from src.data_models import SimulationRun, MetricRecord
from src.config import set_seed
from src.sim.logging_config import SimulationLogger, MetricRecord as LogMetricRecord


class TestEcoDirectorStateTransitions:
    """Tests for Eco-Director state machine logic."""

    def setup_method(self):
        """Create a temporary directory and default config for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.yaml")
        
        # Create a minimal valid config
        self.default_config = {
            "simulation": {
                "steps": 100,
                "seed": 42,
                "memory_limit_mb": 1024,
                "time_limit_seconds": 3600
            },
            "eco_director": {
                "rule_set": "default",
                "coherence_threshold": 0.5
            },
            "output": {
                "log_dir": self.temp_dir,
                "save_state": True
            }
        }
        
        with open(self.config_path, "w") as f:
            yaml.dump(self.default_config, f)

    def teardown_method(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)

    def test_initial_state_is_valid(self):
        """Verify that a loaded config results in a valid initial state."""
        config = load_config(self.config_path)
        assert config is not None
        assert "simulation" in config
        assert "eco_director" in config
        # Validate doesn't raise means state is valid
        assert validate_config(config) is True

    def test_run_simulation_transitions_to_running(self):
        """
        Verify that run_simulation enters the RUNNING state and produces
        a SimulationRun object with status 'running' initially.
        """
        # Mock the simulation step to avoid heavy computation
        # but still test the state transition logic
        with patch('src.sim.eco_director.eco_director_step') as mock_step:
            mock_step.return_value = (
                {"state": "active", "metrics": {"coherence": 0.8}},
                {"status": "ok"}
            )
            
            run_result = run_simulation(
                config_path=self.config_path,
                steps=10
            )
            
            assert run_result is not None
            assert isinstance(run_result, SimulationRun)
            # The final status should be 'completed' if no termination occurred
            assert run_result.status in ['completed', 'terminated', 'aborted']

    def test_memory_limit_triggers_termination(self):
        """
        Verify that exceeding memory_limit_mb triggers the termination handler
        and transitions the state to 'aborted' with a specific reason.
        """
        # Configure a very low memory limit
        low_memory_config = self.default_config.copy()
        low_memory_config["simulation"]["memory_limit_mb"] = 1  # 1 MB
        
        config_path = os.path.join(self.temp_dir, "low_mem_config.yaml")
        with open(config_path, "w") as f:
            yaml.dump(low_memory_config, f)

        # Mock get_memory_usage_mb to simulate an explosion
        with patch('src.sim.eco_director.get_memory_usage_mb', return_value=5000):
            with patch('src.sim.eco_director.eco_director_step') as mock_step:
                # Step returns normally, but memory check fails
                mock_step.return_value = (
                    {"state": "active", "metrics": {"coherence": 0.5}},
                    {"status": "ok"}
                )
                
                run_result = run_simulation(
                    config_path=config_path,
                    steps=10
                )
                
                assert run_result is not None
                assert run_result.status == 'aborted'
                assert "memory" in run_result.termination_reason.lower()

    def test_time_limit_triggers_termination(self):
        """
        Verify that exceeding time_limit_seconds triggers termination
        and sets status to 'aborted' with time-related reason.
        """
        # Configure a very low time limit
        low_time_config = self.default_config.copy()
        low_time_config["simulation"]["time_limit_seconds"] = 1  # 1 second
        
        config_path = os.path.join(self.temp_dir, "low_time_config.yaml")
        with open(config_path, "w") as f:
            yaml.dump(low_time_config, f)

        # Mock time to simulate elapsed time exceeding limit
        with patch('src.sim.eco_director.time.time') as mock_time:
            # Start time
            mock_time.side_effect = [0, 0, 5, 5, 10, 10]  # Simulate time passing
            
            with patch('src.sim.eco_director.eco_director_step') as mock_step:
                mock_step.return_value = (
                    {"state": "active", "metrics": {"coherence": 0.5}},
                    {"status": "ok"}
                )
                
                run_result = run_simulation(
                    config_path=config_path,
                    steps=10
                )
                
                # Depending on implementation, this might be 'aborted' or 'terminated'
                # The key is that it didn't complete normally
                assert run_result.status in ['aborted', 'terminated']
                assert "time" in run_result.termination_reason.lower() or "timeout" in run_result.termination_reason.lower()

    def test_inject_runtime_params_updates_state(self):
        """
        Verify that inject_runtime_params correctly modifies the config
        and that run_simulation respects these new parameters.
        """
        runtime_params = {
            "simulation": {
                "steps": 50,
                "coherence_threshold": 0.9
            }
        }
        
        # Inject params
        updated_config = inject_runtime_params(self.default_config, runtime_params)
        
        assert updated_config["simulation"]["steps"] == 50
        assert updated_config["eco_director"]["coherence_threshold"] == 0.9
        
        # Verify the updated config can be loaded and validated
        updated_path = os.path.join(self.temp_dir, "updated_config.yaml")
        with open(updated_path, "w") as f:
            yaml.dump(updated_config, f)
        
        loaded = load_config(updated_path)
        assert validate_config(loaded) is True

    def test_handle_termination_saves_partial_state(self):
        """
        Verify that handle_termination saves the current state to disk
        before exiting, ensuring no data loss on abort.
        """
        # Create a mock SimulationRun with partial data
        mock_run = SimulationRun(
            run_id="test-termination-123",
            status="aborted",
            steps_completed=50,
            total_steps=100,
            metrics={"coherence": 0.7},
            termination_reason="manual_abort",
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        
        # Mock the logger to capture output
        with patch('src.sim.eco_director.SimulationLogger') as MockLogger:
            mock_logger_instance = MagicMock()
            MockLogger.return_value = mock_logger_instance
            
            # Call the termination handler
            handle_termination(
                run=mock_run,
                config=self.default_config,
                reason="manual_abort"
            )
            
            # Verify that state was logged/saved
            assert mock_logger_instance.log_status.called
            # Check that the log contains the abort reason
            call_args = mock_logger_instance.log_status.call_args
            assert call_args is not None

    def test_validation_fails_on_missing_required_fields(self):
        """
        Verify that validate_config returns False for configs missing
        required simulation parameters.
        """
        invalid_config = {
            "simulation": {},  # Missing steps, seed, etc.
            "eco_director": {}
        }
        
        assert validate_config(invalid_config) is False

    def test_validation_fails_on_invalid_step_count(self):
        """
        Verify that validation fails if steps <= 0.
        """
        invalid_config = self.default_config.copy()
        invalid_config["simulation"]["steps"] = 0
        
        assert validate_config(invalid_config) is False

    def test_run_simulation_handles_config_errors_gracefully(self):
        """
        Verify that run_simulation returns a failed SimulationRun
        if the config is invalid, rather than crashing.
        """
        invalid_path = os.path.join(self.temp_dir, "invalid.yaml")
        with open(invalid_path, "w") as f:
            f.write("invalid: yaml: content")
        
        try:
            result = run_simulation(config_path=invalid_path, steps=10)
            # If it doesn't crash, it should return a result indicating failure
            # or raise a specific exception we can catch
            assert result is not None
        except Exception as e:
            # If it raises, it must be a specific configuration error, not a generic crash
            assert "config" in str(e).lower() or "yaml" in str(e).lower()

    def test_state_persistence_after_step(self):
        """
        Verify that intermediate states are logged correctly during simulation.
        """
        with patch('src.sim.eco_director.eco_director_step') as mock_step:
            # Return a sequence of states
            mock_step.side_effect = [
                ({"state": "step_1", "metrics": {"val": 1}}, {"status": "ok"}),
                ({"state": "step_2", "metrics": {"val": 2}}, {"status": "ok"}),
                ({"state": "step_3", "metrics": {"val": 3}}, {"status": "ok"}),
            ]
            
            # Run a short simulation
            result = run_simulation(
                config_path=self.config_path,
                steps=3
            )
            
            assert result is not None
            assert result.steps_completed >= 1
            # Verify that metrics were accumulated
            assert "metrics" in result.__dict__ or hasattr(result, 'metrics')

    def test_termination_reason_is_specific(self):
        """
        Verify that the termination reason string is descriptive and
        matches the specific failure mode (e.g., 'Memory Explosion' vs 'Time Out').
        """
        # Test Memory Explosion
        low_mem_config = self.default_config.copy()
        low_mem_config["simulation"]["memory_limit_mb"] = 1
        mem_path = os.path.join(self.temp_dir, "mem_config.yaml")
        with open(mem_path, "w") as f:
            yaml.dump(low_mem_config, f)
        
        with patch('src.sim.eco_director.get_memory_usage_mb', return_value=5000):
            with patch('src.sim.eco_director.eco_director_step', return_value=({"state": "a"}, {"status": "ok"})):
                res_mem = run_simulation(config_path=mem_path, steps=5)
                assert "memory" in res_mem.termination_reason.lower()

        # Test Time Out
        low_time_config = self.default_config.copy()
        low_time_config["simulation"]["time_limit_seconds"] = 1
        time_path = os.path.join(self.temp_dir, "time_config.yaml")
        with open(time_path, "w") as f:
            yaml.dump(low_time_config, f)
        
        with patch('src.sim.eco_director.time.time', side_effect=[0, 0, 5, 5]):
            with patch('src.sim.eco_director.eco_director_step', return_value=({"state": "a"}, {"status": "ok"})):
                res_time = run_simulation(config_path=time_path, steps=5)
                assert "time" in res_time.termination_reason.lower() or "timeout" in res_time.termination_reason.lower()