"""
Tests for the Neural Baseline Proxy (T005).

These tests verify that the proxy:
1. Initializes correctly with valid configuration.
2. Produces metrics without NaN values.
3. Respects the CPU-only constraint (no GPU imports).
4. Generates output files when requested.
"""

import pytest
import numpy as np
import tempfile
import os
import sys
import json

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from src.sim.neural_baseline import NeuralBaselineProxy, run_neural_baseline_proxy
from src.data_models import SimulationRun

class TestNeuralBaselineProxy:
    """Unit tests for the NeuralBaselineProxy class."""

    def test_initialization_defaults(self):
        """Test that the proxy initializes with default values."""
        config = {}
        proxy = NeuralBaselineProxy(config)
        
        assert proxy.model_size_m == 512
        assert proxy.total_steps == 10000
        assert proxy.seed == 42
        assert proxy.state.shape == (512,)

    def test_initialization_custom(self):
        """Test initialization with custom configuration."""
        config = {
            "model_size_m": 256,
            "steps": 500,
            "seed": 123
        }
        proxy = NeuralBaselineProxy(config)
        
        assert proxy.model_size_m == 256
        assert proxy.total_steps == 500
        assert proxy.seed == 123
        assert proxy.state.shape == (256,)

    def test_state_stability(self):
        """Test that the state does not explode to infinity."""
        config = {
            "model_size_m": 128,
            "steps": 100,
            "seed": 42
        }
        proxy = NeuralBaselineProxy(config)
        
        # Run a few steps manually
        for t in range(10):
            coherence, diversity, latency = proxy._compute_throttled_step(t)
            
            # Check for NaN
            assert not np.isnan(coherence), f"Coherence is NaN at step {t}"
            assert not np.isnan(diversity), f"Diversity is NaN at step {t}"
            assert not np.isnan(latency), f"Latency is NaN at step {t}"
            
            # Check for explosion
            assert np.isfinite(coherence)
            assert np.isfinite(diversity)
            assert np.isfinite(latency)
            assert np.all(np.isfinite(proxy.state))

    def test_metrics_collection(self):
        """Test that metrics are collected correctly during a run."""
        config = {
            "model_size_m": 64,
            "steps": 10,
            "seed": 42
        }
        proxy = NeuralBaselineProxy(config)
        result = proxy.run()
        
        assert isinstance(result, SimulationRun)
        assert result.total_steps_completed == 10
        assert len(result.metrics) == 10
        
        # Check metric structure
        for metric in result.metrics:
            assert "coherence_score" in metric
            assert "diversity_score" in metric
            assert "step_latency_ms" in metric
            assert "step" in metric
            assert "run_id" in metric

class TestRunNeuralBaseline:
    """Integration tests for the run_neural_baseline_proxy function."""

    def test_run_and_save(self):
        """Test running the proxy and saving results to a file."""
        config = {
            "model_size_m": 32,
            "steps": 5,
            "seed": 99
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_results.json")
            result = run_neural_baseline_proxy(config, output_path)
            
            # Verify file exists
            assert os.path.exists(output_path)
            
            # Verify content
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data["run_id"] == result.run_id
            assert data["total_steps_completed"] == 5
            assert len(data["metrics"]) == 5

    def test_cpu_only_constraint(self):
        """Verify that no GPU-specific libraries are imported in the module."""
        # This is a static check of the module source
        import src.sim.neural_baseline as module
        import inspect
        
        source = inspect.getsource(module)
        
        # Check for common GPU imports that should NOT be present
        forbidden_imports = ["torch.cuda", "tensorflow", "jax"]
        for forbidden in forbidden_imports:
            assert forbidden not in source, f"Forbidden GPU import found: {forbidden}"

    def test_reproducibility(self):
        """Test that the same seed produces the same results."""
        config = {
            "model_size_m": 32,
            "steps": 5,
            "seed": 42
        }
        
        result1 = run_neural_baseline_proxy(config, None)
        result2 = run_neural_baseline_proxy(config, None)
        
        # Compare metrics
        for m1, m2 in zip(result1.metrics, result2.metrics):
            assert np.isclose(m1["coherence_score"], m2["coherence_score"])
            assert np.isclose(m1["diversity_score"], m2["diversity_score"])
            # Latency might vary slightly due to system load, but should be similar order of magnitude
            # We don't assert strict equality on latency