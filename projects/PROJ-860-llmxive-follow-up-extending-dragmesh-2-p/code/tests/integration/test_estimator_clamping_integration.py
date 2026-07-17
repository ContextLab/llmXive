"""
Integration tests for FR-007 clamping logic in the full pipeline context.

Verifies that the clamping logic works correctly when integrated with
the training and evaluation loops, ensuring bounded k_est values
throughout the experiment.
"""
import pytest
import sys
import os
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from estimator import VirtualTactileEstimator
from seed_config import set_seeds


class TestFR007Integration:
    """Integration tests for FR-007 clamping in realistic scenarios."""

    def test_clamping_in_episode_simulation(self):
        """Verify clamping works correctly during a simulated episode."""
        set_seeds(42)
        
        estimator = VirtualTactileEstimator(
            window_size=5,
            min_k=0.1,
            max_k=10.0
        )
        
        # Simulate a realistic episode with varying torque/velocity
        episode_data = []
        for step in range(20):
            # Simulate varying conditions
            torque = np.random.uniform(-5.0, 5.0)
            velocity = np.random.uniform(-2.0, 2.0)
            
            k_est = estimator.update(torque, velocity)
            
            # Verify clamping at each step
            assert 0.1 <= k_est <= 10.0, \
                f"Step {step}: k_est {k_est} out of bounds [0.1, 10.0]"
            
            episode_data.append({
                'step': step,
                'torque': torque,
                'velocity': velocity,
                'k_est': k_est
            })
        
        # Verify final state
        final_k = estimator.get_current_estimate()
        assert 0.1 <= final_k <= 10.0, \
            f"Final k_est {final_k} out of bounds [0.1, 10.0]"

    def test_clamping_across_multiple_episodes(self):
        """Verify clamping consistency across multiple independent episodes."""
        set_seeds(123)
        
        k_estimates = []
        
        for episode_id in range(5):
            estimator = VirtualTactileEstimator(
                window_size=5,
                min_k=0.5,
                max_k=8.0
            )
            
            # Run episode
            for step in range(10):
                torque = np.random.uniform(-10.0, 10.0)
                velocity = np.random.uniform(-5.0, 5.0)
                k_est = estimator.update(torque, velocity)
                k_estimates.append(k_est)
        
        # Verify all estimates are within bounds
        for i, k in enumerate(k_estimates):
            assert 0.5 <= k <= 8.0, \
                f"Episode estimate {i}: k_est {k} out of bounds [0.5, 8.0]"
        
        # Verify we got estimates
        assert len(k_estimates) == 50, f"Expected 50 estimates, got {len(k_estimates)}"

    def test_clamping_with_edge_case_sequences(self):
        """Test clamping with sequences that stress the bounds."""
        estimator = VirtualTactileEstimator(
            window_size=3,
            min_k=1.0,
            max_k=5.0
        )
        
        # Sequence: low -> high -> low -> high
        test_cases = [
            (0.001, 1.0),    # Very low k
            (100.0, 0.001),  # Very high k
            (0.001, 1.0),    # Very low k
            (100.0, 0.001),  # Very high k
        ]
        
        results = []
        for torque, velocity in test_cases:
            k = estimator.update(torque, velocity)
            results.append(k)
            assert 1.0 <= k <= 5.0, f"Result {k} out of bounds"
        
        # Verify the moving average behavior
        # Buffer should contain [1.0, 5.0, 1.0] after 3 steps
        # Mean = 2.333...
        assert abs(results[2] - 2.333333) < 0.001, \
            f"Moving average result {results[2]} incorrect"

    def test_clamping_reproducibility(self):
        """Verify clamping produces consistent results with fixed seeds."""
        set_seeds(42)
        estimator1 = VirtualTactileEstimator(min_k=0.2, max_k=12.0)
        
        set_seeds(42)
        estimator2 = VirtualTactileEstimator(min_k=0.2, max_k=12.0)
        
        # Run same sequence
        for _ in range(10):
            torque = np.random.uniform(-5.0, 5.0)
            velocity = np.random.uniform(-2.0, 2.0)
            k1 = estimator1.update(torque, velocity)
            
            torque = np.random.uniform(-5.0, 5.0)
            velocity = np.random.uniform(-2.0, 2.0)
            k2 = estimator2.update(torque, velocity)
            
            assert abs(k1 - k2) < 1e-9, f"Non-reproducible: {k1} vs {k2}"

    def test_clamping_statistics_compliance(self):
        """Verify clamping maintains statistical properties."""
        estimator = VirtualTactileEstimator(
            window_size=10,
            min_k=0.0,
            max_k=20.0
        )
        
        # Generate a large sample
        all_k = []
        for _ in range(100):
            torque = np.random.uniform(-100.0, 100.0)
            velocity = np.random.uniform(-10.0, 10.0)
            k = estimator.update(torque, velocity)
            all_k.append(k)
        
        # Verify all within bounds
        assert min(all_k) >= 0.0
        assert max(all_k) <= 20.0
        
        # Verify no NaN or Inf
        assert all(np.isfinite(k) for k in all_k)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])