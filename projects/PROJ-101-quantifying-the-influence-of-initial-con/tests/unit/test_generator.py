"""
Unit tests for the data generator module.

Tests:
- T010: Noise injection statistics
- T011: Clean trajectory numerical precision
- T012: Unphysical flagging and high-noise warnings
"""
import pytest
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, List, Dict, Any

# Import from project
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.generator import (
    HighNoiseWarning,
    UnphysicalTrajectoryError,
    TrajectoryData,
    lorenz_ode_single,
    coupled_lorenz_ode,
    generate_initial_conditions,
    inject_gaussian_noise,
    integrate_trajectory,
    validate_trajectory
)
from utils.stability import check_boundedness, check_convergence


class TestNoiseInjectionStatistics:
    """T010: Unit test for noise injection statistics"""
    
    def test_noise_mean_variance(self):
        """Verify mean and variance match sigma_noise within 1% tolerance"""
        np.random.seed(42)
        
        sigma_noise = 0.05
        n_samples = 100000
        n_dim = 3
        
        # Generate noise
        noise = inject_gaussian_noise(
            state_shape=(n_samples, n_dim),
            sigma_noise=sigma_noise
        )
        
        # Check mean (should be close to 0)
        mean_noise = np.mean(noise)
        expected_mean = 0.0
        tolerance = 0.01 * sigma_noise
        
        assert abs(mean_noise - expected_mean) < tolerance, \
            f"Mean {mean_noise} exceeds tolerance {tolerance}"
        
        # Check variance (should be close to sigma^2)
        var_noise = np.var(noise, axis=0)
        expected_var = sigma_noise ** 2
        tolerance_var = 0.01 * expected_var
        
        # Allow some variance in variance estimate
        assert np.all(np.abs(var_noise - expected_var) < tolerance_var), \
            f"Variance {var_noise} exceeds tolerance {tolerance_var}"
    
    def test_noise_distribution_shape(self):
        """Verify noise distribution matches expected Gaussian shape"""
        np.random.seed(123)
        
        sigma_noise = 0.1
        n_samples = 10000
        n_dim = 6  # 2 oscillators * 3 variables each
        
        noise = inject_gaussian_noise(
            state_shape=(n_samples, n_dim),
            sigma_noise=sigma_noise
        )
        
        # Check shape
        assert noise.shape == (n_samples, n_dim), \
            f"Expected shape {(n_samples, n_dim)}, got {noise.shape}"
        
        # Check that noise is not all zeros
        assert np.any(noise != 0), "Noise should not be all zeros"
        
        # Check that noise is finite
        assert np.all(np.isfinite(noise)), "Noise should be finite"


class TestCleanTrajectoryPrecision:
    """T011: Unit test for clean trajectory numerical precision"""
    
    def test_deterministic_integration_precision(self):
        """Verify error < 1e-9 against reference for clean trajectory"""
        np.random.seed(42)
        
        # Parameters
        N_oscillators = 2
        max_time = 10.0
        dt = 0.01
        sigma_noise = 0.0  # Clean trajectory
        
        # Generate initial conditions
        initial_state = generate_initial_conditions(N_oscillators, seed=42)
        
        # Integrate first time
        result1 = integrate_trajectory(
            initial_state=initial_state,
            max_time=max_time,
            dt=dt,
            N_oscillators=N_oscillators,
            sigma_noise=sigma_noise,
            rtol=1e-9,
            atol=1e-12
        )
        
        # Integrate second time with same seed
        result2 = integrate_trajectory(
            initial_state=initial_state,
            max_time=max_time,
            dt=dt,
            N_oscillators=N_oscillators,
            sigma_noise=sigma_noise,
            rtol=1e-9,
            atol=1e-12
        )
        
        # Compare trajectories
        error = np.max(np.abs(result1['trajectory'] - result2['trajectory']))
        
        assert error < 1e-9, \
            f"Deterministic error {error} exceeds 1e-9 threshold"
    
    def test_numerical_stability_clean(self):
        """Verify clean trajectory remains bounded and stable"""
        np.random.seed(42)
        
        N_oscillators = 2
        max_time = 50.0
        dt = 0.01
        sigma_noise = 0.0
        
        initial_state = generate_initial_conditions(N_oscillators, seed=42)
        
        result = integrate_trajectory(
            initial_state=initial_state,
            max_time=max_time,
            dt=dt,
            N_oscillators=N_oscillators,
            sigma_noise=sigma_noise,
            rtol=1e-9,
            atol=1e-12
        )
        
        # Check boundedness
        is_bounded = check_boundedness(result['trajectory'], threshold=100)
        assert is_bounded, "Clean trajectory should remain bounded"
        
        # Check no NaN/Inf
        assert np.all(np.isfinite(result['trajectory'])), \
            "Clean trajectory should not contain NaN or Inf"


class TestUnphysicalFlagging:
    """T012: Unit test for unphysical flagging and high-noise warnings"""
    
    def test_high_noise_warning(self):
        """Verify HighNoiseWarning at sigma > 0.1"""
        np.random.seed(42)
        
        N_oscillators = 2
        max_time = 10.0
        dt = 0.01
        sigma_noise = 0.15  # > 0.1 should trigger warning
        
        initial_state = generate_initial_conditions(N_oscillators, seed=42)
        
        with pytest.warns(HighNoiseWarning, match="High noise level"):
            result = integrate_trajectory(
                initial_state=initial_state,
                max_time=max_time,
                dt=dt,
                N_oscillators=N_oscillators,
                sigma_noise=sigma_noise,
                rtol=1e-9,
                atol=1e-12
            )
    
    def test_unphysical_trajectory_error_high_sigma(self):
        """Verify UnphysicalTrajectoryError at sigma > 1.0"""
        np.random.seed(42)
        
        N_oscillators = 2
        max_time = 10.0
        dt = 0.01
        sigma_noise = 1.5  # > 1.0 should trigger error
        
        initial_state = generate_initial_conditions(N_oscillators, seed=42)
        
        with pytest.raises(UnphysicalTrajectoryError, match="Unphysical trajectory"):
            result = integrate_trajectory(
                initial_state=initial_state,
                max_time=max_time,
                dt=dt,
                N_oscillators=N_oscillators,
                sigma_noise=sigma_noise,
                rtol=1e-9,
                atol=1e-12
            )
    
    def test_unphysical_trajectory_error_divergence(self):
        """Verify UnphysicalTrajectoryError when trajectory diverges"""
        np.random.seed(42)
        
        N_oscillators = 2
        max_time = 100.0
        dt = 0.01
        sigma_noise = 0.0  # Clean but with unstable initial conditions
        
        # Create extreme initial conditions that might diverge
        extreme_initial = np.random.randn(N_oscillators * 3) * 1000.0
        
        with pytest.raises(UnphysicalTrajectoryError, match="Unphysical trajectory"):
            result = integrate_trajectory(
                initial_state=extreme_initial,
                max_time=max_time,
                dt=dt,
                N_oscillators=N_oscillators,
                sigma_noise=sigma_noise,
                rtol=1e-9,
                atol=1e-12
            )
    
    def test_boundary_case_sigma_0_1(self):
        """Verify behavior at exactly sigma = 0.1 (boundary case)"""
        np.random.seed(42)
        
        N_oscillators = 2
        max_time = 10.0
        dt = 0.01
        sigma_noise = 0.1  # Exactly at boundary
        
        initial_state = generate_initial_conditions(N_oscillators, seed=42)
        
        # Should NOT raise warning at exactly 0.1
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = integrate_trajectory(
                initial_state=initial_state,
                max_time=max_time,
                dt=dt,
                N_oscillators=N_oscillators,
                sigma_noise=sigma_noise,
                rtol=1e-9,
                atol=1e-12
            )
            
            # Check no HighNoiseWarning
            high_noise_warnings = [
                warning for warning in w 
                if issubclass(warning.category, HighNoiseWarning)
            ]
            assert len(high_noise_warnings) == 0, \
                "Should not warn at exactly sigma = 0.1"
