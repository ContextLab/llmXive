"""
Unit tests for neural baseline throttling logic.

Tests verify that the throttling mechanism correctly enforces
time limits and produces expected behavior under various conditions.
"""

import pytest
import time
from unittest.mock import patch, MagicMock
import numpy as np

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sim.neural_baseline import NeuralBaseline, ThrottleConfig, ThrottleState
from src.data_models import SimulationRun, MetricRecord
from src.config import DEFAULT_THROTTLE_FACTOR, SIMULATION_TIMEOUT_HOURS


class TestThrottleConfig:
    """Tests for ThrottleConfig dataclass."""
    
    def test_default_initialization(self):
        """Test default configuration values."""
        config = ThrottleConfig()
        
        assert config.max_runtime_hours == SIMULATION_TIMEOUT_HOURS
        assert config.throttle_factor == DEFAULT_THROTTLE_FACTOR
        assert config.check_interval_steps == 100
        assert config.warn_threshold_percent == 80.0
        
    def test_custom_initialization(self):
        """Test custom configuration values."""
        config = ThrottleConfig(
            max_runtime_hours=2.0,
            throttle_factor=0.5,
            check_interval_steps=50,
            warn_threshold_percent=90.0
        )
        
        assert config.max_runtime_hours == 2.0
        assert config.throttle_factor == 0.5
        assert config.check_interval_steps == 50
        assert config.warn_threshold_percent == 90.0


class TestThrottleState:
    """Tests for ThrottleState dataclass."""
    
    def test_initial_state(self):
        """Test initial state values."""
        state = ThrottleState()
        
        assert state.total_steps == 0
        assert state.elapsed_time == 0.0
        assert state.steps_since_last_check == 0
        assert state.is_throttled is False
        assert state.warning_issued is False
        
    def test_update_increment(self):
        """Test state update increments counters."""
        state = ThrottleState()
        state.start_time = time.time()
        
        state.update(steps=10)
        assert state.total_steps == 10
        assert state.steps_since_last_check == 10
        
        state.update(steps=5)
        assert state.total_steps == 15
        assert state.steps_since_last_check == 15
        
    def test_elapsed_time_calculation(self):
        """Test elapsed time calculation."""
        state = ThrottleState()
        start = time.time() - 5.0  # 5 seconds ago
        state.start_time = start
        
        time.sleep(0.1)  # Small delay to ensure measurable time
        state.update()
        
        assert state.elapsed_time >= 5.0
        assert state.elapsed_time < 6.0


class TestNeuralBaseline:
    """Tests for NeuralBaseline class."""
    
    def test_initialization_with_defaults(self):
        """Test initialization with default parameters."""
        baseline = NeuralBaseline()
        
        assert baseline.params['simulation_steps'] == 10000
        assert baseline.params['population_size'] == 100
        assert baseline.config.throttle_factor == DEFAULT_THROTTLE_FACTOR
        
    def test_initialization_with_custom_params(self):
        """Test initialization with custom parameters."""
        params = {
            'simulation_steps': 5000,
            'population_size': 200
        }
        baseline = NeuralBaseline(params=params)
        
        assert baseline.params['simulation_steps'] == 5000
        assert baseline.params['population_size'] == 200
        
    def test_throttle_delay_calculation(self):
        """Test throttle delay calculation."""
        baseline = NeuralBaseline()
        baseline.config.throttle_factor = 2.0
        
        delay = baseline._calculate_throttle_delay()
        assert delay == 0.002  # 0.001 * 2.0
        
    def test_time_limit_check_not_exceeded(self):
        """Test time limit check when not exceeded."""
        baseline = NeuralBaseline()
        baseline.state.start_time = time.time() - 100  # 100 seconds ago
        baseline.state.elapsed_time = 100
        
        # 6 hour limit = 21600 seconds, 100 is well under
        assert baseline._check_time_limit() is False
        
    def test_time_limit_check_exceeded(self):
        """Test time limit check when exceeded."""
        baseline = NeuralBaseline()
        baseline.config.max_runtime_hours = 0.001  # Very short limit
        baseline.state.start_time = time.time() - 100  # 100 seconds ago
        baseline.state.elapsed_time = 100
        
        assert baseline._check_time_limit() is True
        
    def test_warning_threshold(self):
        """Test warning threshold behavior."""
        baseline = NeuralBaseline()
        baseline.config.warn_threshold_percent = 50.0
        baseline.config.max_runtime_hours = 0.001  # Very short limit
        
        baseline.state.start_time = time.time() - 50  # 50 seconds ago
        baseline.state.elapsed_time = 50
        
        # Should trigger warning at 50%
        result = baseline._check_time_limit()
        assert baseline.state.warning_issued is True
        
    def test_run_execution(self):
        """Test basic run execution."""
        params = {
            'simulation_steps': 100,
            'population_size': 10
        }
        config = ThrottleConfig(throttle_factor=0.001)  # Very fast for testing
        baseline = NeuralBaseline(params=params, throttle_config=config)
        
        result = baseline.run()
        
        assert isinstance(result, SimulationRun)
        assert result.simulation_type == 'neural_baseline'
        assert result.total_steps_executed <= 100
        assert len(result.metrics) > 0
        
    def test_run_respects_time_limit(self):
        """Test that run respects time limits."""
        params = {
            'simulation_steps': 10000,  # Would take a long time normally
            'population_size': 10
        }
        config = ThrottleConfig(
            max_runtime_hours=0.0001,  # Very short limit
            throttle_factor=0.001
        )
        baseline = NeuralBaseline(params=params, throttle_config=config)
        
        result = baseline.run()
        
        # Should stop before completing all steps due to time limit
        assert result.total_steps_executed < 10000
        assert result.is_power_limited is True
        
    def test_metric_recording(self):
        """Test that metrics are recorded correctly."""
        params = {
            'simulation_steps': 200,
            'population_size': 10
        }
        config = ThrottleConfig(
            throttle_factor=0.001,
            check_interval_steps=50
        )
        baseline = NeuralBaseline(params=params, throttle_config=config)
        
        result = baseline.run()
        
        # Should have metrics at steps 50, 100, 150, 200
        expected_steps = [50, 100, 150, 200]
        recorded_steps = [m.step for m in result.metrics]
        
        assert recorded_steps == expected_steps
        
    def test_metric_values_valid(self):
        """Test that recorded metric values are in valid ranges."""
        params = {
            'simulation_steps': 100,
            'population_size': 10
        }
        config = ThrottleConfig(throttle_factor=0.001)
        baseline = NeuralBaseline(params=params, throttle_config=config)
        
        result = baseline.run()
        
        for metric in result.metrics:
            assert 0.0 <= metric.coherence_score <= 1.0
            assert 0.0 <= metric.diversity_score <= 1.0
            assert metric.step_latency >= 0.0
            
    def test_status_method(self):
        """Test get_status method."""
        baseline = NeuralBaseline()
        
        status = baseline.get_status()
        
        assert 'running' in status
        assert 'total_steps' in status
        assert 'elapsed_time' in status
        assert 'is_throttled' in status
        assert 'metrics_count' in status
        
        assert status['running'] is False
        assert status['total_steps'] == 0
        assert status['metrics_count'] == 0
        
    def test_interrupted_run(self):
        """Test behavior when run is interrupted."""
        params = {
            'simulation_steps': 1000,
            'population_size': 10
        }
        config = ThrottleConfig(throttle_factor=0.001)
        baseline = NeuralBaseline(params=params, throttle_config=config)
        
        # Mock time.time to simulate interruption
        with patch('time.time', side_effect=[time.time()] * 1000000):
            # Simulate keyboard interrupt
            try:
                with patch.object(baseline, '_check_time_limit', side_effect=KeyboardInterrupt):
                    result = baseline.run()
            except:
                pass
                
        # Status should be updated
        status = baseline.get_status()
        assert status['running'] is False


class TestRunNeuralBaselineFunction:
    """Tests for the convenience function run_neural_baseline."""
    
    def test_basic_execution(self):
        """Test basic function execution."""
        with patch('src.sim.neural_baseline.NeuralBaseline.run') as mock_run:
            mock_run.return_value = SimulationRun(
                simulation_type='neural_baseline',
                total_steps_executed=100,
                metrics=[]
            )
            
            from src.sim.neural_baseline import run_neural_baseline
            
            result = run_neural_baseline({'simulation_steps': 100})
            
            assert result.simulation_type == 'neural_baseline'
            assert result.total_steps_executed == 100
