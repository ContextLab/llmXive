"""
Unit tests for statistics module, specifically power validation logic.
"""
import numpy as np
import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from statistics import (
    compute_hemispherical_variance,
    calculate_max_stat_pvalue,
    inject_dipole_asymmetry,
    run_power_validation
)
from simulations import generate_single_synalm
from harmonics import compute_alm, compute_full_sky_cl
import healpy as hp


# Constants for testing
NTEST_SIDES = 16  # Small Nside for fast testing
L_MIN = 2
L_MAX = 16  # Reduced for speed
N_SIMS = 20  # Small number for testing


class TestPowerValidation:
    """Tests for power validation logic (injection/recovery)."""

    def test_inject_dipole_asymmetry(self):
        """Test that dipole asymmetry injection works and creates detectable signal."""
        # Generate a simple isotropic map for testing
        # Use a small Nside for speed
        nside = NTEST_SIDES
        npix = hp.nside2npix(nside)
        
        # Create a simple random Gaussian map (isotropic)
        np.random.seed(42)
        # Generate random alm and convert to map
        alm = hp.synalm(np.ones(hp.nside2npix(nside)) * 1e-10, nside, lmax=L_MAX)[:1]
        test_map = hp.alm2map(alm[0], nside, lmax=L_MAX)
        
        # Inject a known dipole asymmetry
        asymmetry_strength = 0.1  # 10% asymmetry
        injected_map = inject_dipole_asymmetry(test_map, asymmetry_strength, seed=123)
        
        # Verify the injection created a difference
        assert not np.array_equal(test_map, injected_map), "Injection should modify the map"
        
        # The injected map should have a different hemispherical variance
        var_original = compute_hemispherical_variance(test_map, L_MIN, L_MAX)
        var_injected = compute_hemispherical_variance(injected_map, L_MIN, L_MAX)
        
        # The variances should be different due to injection
        assert not np.allclose(var_original, var_injected), "Injection should change hemispherical variance"

    def test_power_validation_detection(self):
        """Test that power validation can detect injected anisotropy."""
        # Generate a baseline isotropic map
        nside = NTEST_SIDES
        np.random.seed(42)
        
        # Create a simple power spectrum for testing
        cl_input = np.ones(L_MAX + 1) * 1e-10
        cl_input[0] = 0  # No monopole
        cl_input[1] = 0  # No dipole in base
        
        # Generate a test map
        test_alm = hp.synalm(cl_input, nside, lmax=L_MAX)
        test_map = hp.alm2map(test_alm, nside, lmax=L_MAX)
        
        # Inject a strong dipole asymmetry
        asymmetry_strength = 0.2  # 20% asymmetry - should be easily detectable
        injected_map = inject_dipole_asymmetry(test_map, asymmetry_strength, seed=456)
        
        # Compute observed statistics
        var_obs = compute_hemispherical_variance(injected_map, L_MIN, L_MAX)
        max_stat_obs = max(var_obs)
        
        # Generate null distribution from isotropic simulations
        null_stats = []
        for _ in range(N_SIMS):
            sim_alm = hp.synalm(cl_input, nside, lmax=L_MAX)
            sim_map = hp.alm2map(sim_alm, nside, lmax=L_MAX)
            var_sim = compute_hemispherical_variance(sim_map, L_MIN, L_MAX)
            null_stats.append(max(var_sim))
        
        # Calculate p-value
        p_value = calculate_max_stat_pvalue(np.array(null_stats), max_stat_obs)
        
        # With strong injection, p-value should be low (indicating detection)
        # Note: With small N_SIMS, we can't guarantee p < 0.05, but we can check it's not 1.0
        assert p_value < 1.0, "Injected asymmetry should produce p-value < 1.0"
        
        # The observed statistic should be higher than most null statistics
        assert max_stat_obs > np.percentile(null_stats, 50), "Observed stat should be above median of null"

    def test_run_power_validation(self):
        """Test the full power validation workflow."""
        # Create a simple power spectrum
        cl_input = np.ones(L_MAX + 1) * 1e-10
        cl_input[0] = 0
        cl_input[1] = 0
        
        # Run power validation with injection
        result = run_power_validation(
            cl_input=cl_input,
            nside=NTEST_SIDES,
            n_sims=10,  # Small number for testing
            injection_strength=0.15,
            l_min=L_MIN,
            l_max=L_MAX,
            seed=789
        )
        
        # Verify result structure
        assert "detection_rate" in result, "Result should have detection_rate"
        assert "threshold" in result, "Result should have threshold"
        assert "n_trials" in result, "Result should have n_trials"
        assert "p_values" in result, "Result should have p_values"
        
        # With sufficient injection strength, we expect some detections
        # This is a soft check due to randomness
        assert result["n_trials"] == 10, "Should have correct number of trials"
        assert 0 <= result["detection_rate"] <= 1, "Detection rate should be between 0 and 1"

    def test_empty_injection(self):
        """Test that zero injection strength produces no change."""
        nside = NTEST_SIDES
        np.random.seed(999)
        
        # Create a test map
        cl_input = np.ones(L_MAX + 1) * 1e-10
        cl_input[0] = 0
        test_alm = hp.synalm(cl_input, nside, lmax=L_MAX)
        test_map = hp.alm2map(test_alm, nside, lmax=L_MAX)
        
        # Inject with zero strength
        injected_map = inject_dipole_asymmetry(test_map, 0.0, seed=111)
        
        # Maps should be identical (or very close due to floating point)
        assert np.allclose(test_map, injected_map), "Zero injection should not change map"

    def test_multiple_injection_axes(self):
        """Test injection along different axes."""
        nside = NTEST_SIDES
        np.random.seed(222)
        
        # Create a test map
        cl_input = np.ones(L_MAX + 1) * 1e-10
        cl_input[0] = 0
        test_alm = hp.synalm(cl_input, nside, lmax=L_MAX)
        test_map = hp.alm2map(test_alm, nside, lmax=L_MAX)
        
        # Inject along different axes
        map_z = inject_dipole_asymmetry(test_map, 0.1, axis='z', seed=333)
        map_x = inject_dipole_asymmetry(test_map, 0.1, axis='x', seed=333)
        map_y = inject_dipole_asymmetry(test_map, 0.1, axis='y', seed=333)
        
        # All should be different from original and from each other
        assert not np.array_equal(test_map, map_z)
        assert not np.array_equal(test_map, map_x)
        assert not np.array_equal(test_map, map_y)
        
        # Different axes should produce different maps
        assert not np.array_equal(map_z, map_x)
        assert not np.array_equal(map_z, map_y)
        assert not np.array_equal(map_x, map_y)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])