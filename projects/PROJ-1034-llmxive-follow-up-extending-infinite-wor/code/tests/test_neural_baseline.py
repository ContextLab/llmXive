"""
Unit tests for the Neural Baseline Proxy implementation.

These tests verify that the neural baseline:
1. Initializes correctly with valid config
2. Produces output of the correct shape
3. Handles state size mismatches gracefully
4. Respects throttling parameters
5. Fails loudly on invalid inputs
"""

import pytest
import numpy as np
import tempfile
import os
import yaml
import sys

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sim.neural_baseline import NeuralBaselineProxy, run_neural_baseline

class TestNeuralBaselineProxy:
    """Tests for the NeuralBaselineProxy class."""
    
    def test_init_with_valid_config(self):
        """Test that the proxy initializes correctly with a valid config."""
        config = {
            'state_size': 100,
            'num_steps': 10,
            'throttle_factor': 1.0
        }
        proxy = NeuralBaselineProxy(config, seed=42)
        
        assert proxy.state_size == 100
        assert proxy.num_steps == 10
        assert proxy.throttle_factor == 1.0
        assert proxy.weights.shape == (100, 100)
        assert proxy.bias.shape == (100,)
    
    def test_step_returns_correct_shape(self):
        """Test that step() returns a state of the correct shape."""
        config = {
            'state_size': 50,
            'num_steps': 5,
            'throttle_factor': 0.0  # Disable throttling for speed
        }
        proxy = NeuralBaselineProxy(config, seed=42)
        
        initial_state = np.random.randn(50)
        new_state, metrics = proxy.step(initial_state)
        
        assert new_state.shape == (50,)
        assert isinstance(metrics, dict)
        assert 'step_latency' in metrics
        assert 'memory_mb' in metrics
        assert 'state_norm' in metrics
    
    def test_step_handles_state_size_mismatch(self):
        """Test that step() handles state size mismatches by resizing."""
        config = {
            'state_size': 50,
            'num_steps': 5,
            'throttle_factor': 0.0
        }
        proxy = NeuralBaselineProxy(config, seed=42)
        
        # Input state smaller than expected
        small_state = np.random.randn(30)
        new_state, _ = proxy.step(small_state)
        assert new_state.shape == (50,)
        
        # Input state larger than expected
        large_state = np.random.randn(70)
        new_state, _ = proxy.step(large_state)
        assert new_state.shape == (50,)
    
    def test_step_throttling(self):
        """Test that throttling adds delay proportional to state size."""
        config = {
            'state_size': 100,
            'num_steps': 5,
            'throttle_factor': 100.0  # High throttle factor for testing
        }
        proxy = NeuralBaselineProxy(config, seed=42)
        
        initial_state = np.random.randn(100)
        import time
        start = time.time()
        _, metrics = proxy.step(initial_state)
        elapsed = time.time() - start
        
        # With high throttle, we expect some delay
        assert elapsed > 0.001  # At least 1ms delay
        assert metrics['step_latency'] > 0.001
    
    def test_step_non_deterministic_without_seed(self):
        """Test that step produces different results without a fixed seed."""
        config = {
            'state_size': 50,
            'num_steps': 5,
            'throttle_factor': 0.0
        }
        
        proxy1 = NeuralBaselineProxy(config)
        proxy2 = NeuralBaselineProxy(config)
        
        state = np.random.randn(50)
        out1, _ = proxy1.step(state)
        out2, _ = proxy2.step(state)
        
        # Without seed, results should likely differ (high probability)
        # We check that they are not identical to ensure randomness is used
        assert not np.array_equal(out1, out2)
    
    def test_step_deterministic_with_seed(self):
        """Test that step produces identical results with the same seed."""
        config = {
            'state_size': 50,
            'num_steps': 5,
            'throttle_factor': 0.0
        }
        
        proxy1 = NeuralBaselineProxy(config, seed=123)
        proxy2 = NeuralBaselineProxy(config, seed=123)
        
        state = np.random.randn(50)
        out1, _ = proxy1.step(state)
        out2, _ = proxy2.step(state)
        
        assert np.array_equal(out1, out2)

class TestRunNeuralBaseline:
    """Tests for the run_neural_baseline function."""
    
    def test_run_with_temp_config(self):
        """Test running the baseline with a temporary config file."""
        config = {
            'state_size': 20,
            'num_steps': 5,
            'throttle_factor': 0.0
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = f.name
        
        try:
            result = run_neural_baseline(temp_path, steps=5, seed=42)
            
            assert result['status'] == 'success'
            assert result['final_state'].shape == (20,)
            assert len(result['metrics']) == 5
            assert result['total_latency'] > 0
        finally:
            os.unlink(temp_path)
    
    def test_run_with_invalid_config_path(self):
        """Test that run_neural_baseline raises FileNotFoundError for missing config."""
        with pytest.raises(FileNotFoundError):
            run_neural_baseline("/nonexistent/path/config.yaml")
    
    def test_run_step_override(self):
        """Test that the steps argument overrides config num_steps."""
        config = {
            'state_size': 20,
            'num_steps': 100,  # Config says 100
            'throttle_factor': 0.0
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = f.name
        
        try:
            # Override to run only 3 steps
            result = run_neural_baseline(temp_path, steps=3, seed=42)
            
            assert result['status'] == 'success'
            assert len(result['metrics']) == 3
        finally:
            os.unlink(temp_path)
    
    def test_run_initial_state_override(self):
        """Test that initial_state argument is used if provided."""
        config = {
            'state_size': 10,
            'num_steps': 2,
            'throttle_factor': 0.0
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = f.name
        
        try:
            custom_state = np.ones(10) * 5.0
            result = run_neural_baseline(temp_path, initial_state=custom_state, seed=42)
            
            # The first step should start from the custom state
            # We verify by checking the first metric's state_norm
            # (Custom state norm is 5 * sqrt(10) ≈ 15.81)
            initial_norm = np.linalg.norm(custom_state)
            assert abs(result['metrics'][0]['state_norm'] - initial_norm) < 0.01
        finally:
            os.unlink(temp_path)