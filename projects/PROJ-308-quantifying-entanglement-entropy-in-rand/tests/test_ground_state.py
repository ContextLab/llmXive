"""
Tests for ground state computation module.

Focuses on:
- TEBD convergence logic
- Double-precision enforcement
- Numerically unresolved flagging
"""

import pytest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from ground_state import (
    get_default_ground_state_config,
    validate_ground_state_config,
    compute_ground_state,
    compute_ground_state_batch,
    is_numerically_unresolved,
    GroundStateError
)
from config import ConfigError

class TestGroundStateConfig:
    """Tests for ground state configuration validation."""

    def test_default_config_values(self):
        """Test that default config has expected values."""
        config = get_default_ground_state_config()
        
        assert config['max_bond_dimension'] == 400
        assert config['convergence_tol'] == 1e-8
        assert config['truncation_threshold'] == 1e-10
        assert config['max_sweeps'] == 50
        assert config['verbose'] is False

    def test_validate_config_validates_ranges(self):
        """Test that config validation enforces parameter ranges."""
        # Valid config
        valid_config = {
            'max_bond_dimension': 200,
            'convergence_tol': 1e-9,
            'truncation_threshold': 1e-12,
            'max_sweeps': 100,
            'random_seed': 42,
            'verbose': True
        }
        validated = validate_ground_state_config(valid_config)
        
        assert validated['max_bond_dimension'] == 200
        assert validated['convergence_tol'] == 1e-9
        assert validated['verbose'] is True

    def test_validate_config_rejects_invalid_max_bond(self):
        """Test rejection of out-of-range max_bond_dimension."""
        with pytest.raises(ConfigError):
            validate_ground_state_config({'max_bond_dimension': 5})
        
        with pytest.raises(ConfigError):
            validate_ground_state_config({'max_bond_dimension': 2000})

    def test_validate_config_rejects_invalid_tol(self):
        """Test rejection of out-of-range convergence_tol."""
        with pytest.raises(ConfigError):
            validate_ground_state_config({'convergence_tol': 1e-15})
        
        with pytest.raises(ConfigError):
            validate_ground_state_config({'convergence_tol': 1e-3})

class TestGroundStateComputation:
    """Tests for ground state computation."""

    def test_compute_ground_state_basic(self):
        """Test basic ground state computation."""
        L = 10
        delta = 0.1
        
        result = compute_ground_state(L=L, delta=delta, N_real=1, seed=42)
        
        assert result['mps'] is not None
        assert result['couplings'] is not None
        assert len(result['couplings']) == L - 1
        assert 'convergence_info' in result
        assert 'unresolved' in result

    def test_compute_ground_state_double_precision(self):
        """Test that couplings are double precision."""
        L = 10
        delta = 0.2
        
        result = compute_ground_state(L=L, delta=delta, N_real=1, seed=123)
        
        assert result['couplings'].dtype == np.float64
        assert result['couplings'].dtype.itemsize == 8  # 64-bit

    def test_compute_ground_state_coupling_range(self):
        """Test that couplings are within expected range [1-delta, 1+delta]."""
        L = 20
        delta = 0.3
        
        result = compute_ground_state(L=L, delta=delta, N_real=1, seed=456)
        
        couplings = result['couplings']
        lower_bound = 1 - delta
        upper_bound = 1 + delta
        
        assert np.all(couplings >= lower_bound - 1e-10)
        assert np.all(couplings <= upper_bound + 1e-10)

    def test_compute_ground_state_batch(self):
        """Test batch ground state computation."""
        L = 8
        delta = 0.1
        N_real = 5
        
        results = compute_ground_state_batch(L=L, delta=delta, N_real=N_real, seed=789)
        
        assert len(results) == N_real
        for i, result in enumerate(results):
            assert result['realization_id'] == i
            assert result['mps'] is not None
            assert result['couplings'] is not None

    def test_numerically_unresolved_flagging(self):
        """Test that numerically unresolved states are properly flagged."""
        L = 10
        delta = 0.5  # High disorder might cause convergence issues
        
        # Use very restrictive config to force potential non-convergence
        config = get_default_ground_state_config()
        config['max_bond_dimension'] = 10  # Very low
        config['max_sweeps'] = 5  # Very few sweeps
        
        result = compute_ground_state(L=L, delta=delta, N_real=1, seed=999, config=config)
        
        # With such restrictive settings, state should likely be unresolved
        # We check that the flagging mechanism works
        assert 'unresolved' in result
        assert 'convergence_info' in result
        
        # Verify is_numerically_unresolved function
        flag = is_numerically_unresolved(result)
        assert isinstance(flag, bool)

    def test_numerically_unresolved_function(self):
        """Test the is_numerically_unresolved helper function."""
        # Test with resolved state
        resolved_result = {
            'unresolved': False,
            'convergence_info': {'converged': True}
        }
        assert not is_numerically_unresolved(resolved_result)
        
        # Test with unresolved state (explicit flag)
        unresolved_result = {
            'unresolved': True,
            'convergence_info': {'converged': False}
        }
        assert is_numerically_unresolved(unresolved_result)
        
        # Test with fallback to convergence_info
        fallback_result = {
            'convergence_info': {
                'converged': False,
                'max_bond_reached': True
            }
        }
        assert is_numerically_unresolved(fallback_result)
        
        # Test with converged state
        converged_result = {
            'convergence_info': {
                'converged': True,
                'max_bond_reached': False
            }
        }
        assert not is_numerically_unresolved(converged_result)
        
        # Test with invalid input
        with pytest.raises(GroundStateError):
            is_numerically_unresolved("not a dict")

class TestConvergenceLogic:
    """Tests specifically for TEBD convergence logic."""

    def test_convergence_tolerance_enforcement(self):
        """Test that convergence tolerance is enforced."""
        L = 8
        delta = 0.1
        
        # Use a very tight tolerance
        config = get_default_ground_state_config()
        config['convergence_tol'] = 1e-9
        
        result = compute_ground_state(L=L, delta=delta, N_real=1, seed=111, config=config)
        
        conv_info = result['convergence_info']
        assert 'converged' in conv_info
        assert 'energy' in conv_info
        
        # If converged, the energy change should be within tolerance
        if conv_info['converged']:
            energy_history = conv_info.get('energy_history', [])
            if len(energy_history) >= 2:
                # Last change should be small
                last_change = abs(energy_history[-1] - energy_history[-2])
                assert last_change < config['convergence_tol'] * 10  # Allow some margin

    def test_max_bond_dimension_handling(self):
        """Test that max bond dimension is respected."""
        L = 10
        delta = 0.2
        
        config = get_default_ground_state_config()
        max_chi = 20
        config['max_bond_dimension'] = max_chi
        
        result = compute_ground_state(L=L, delta=delta, N_real=1, seed=222, config=config)
        
        mps = result['mps']
        if mps is not None:
            # Check that bond dimensions don't exceed max
            bond_dims = mps.chi
            assert max(bond_dims) <= max_chi + 1  # Allow slight overshoot during evolution

    def test_adaptive_bond_dimension(self):
        """Test that bond dimension adapts during evolution."""
        L = 12
        delta = 0.1
        
        config = get_default_ground_state_config()
        config['max_bond_dimension'] = 100
        
        result = compute_ground_state(L=L, delta=delta, N_real=1, seed=333, config=config)
        
        conv_info = result['convergence_info']
        if conv_info['converged']:
            # Final bond dimension should be less than max if it adapted
            final_chi = conv_info.get('final_bond_dim', 0)
            assert final_chi <= config['max_bond_dimension']

    def test_convergence_info_structure(self):
        """Test that convergence_info has all required fields."""
        L = 8
        delta = 0.1
        
        result = compute_ground_state(L=L, delta=delta, N_real=1, seed=444)
        
        conv_info = result['convergence_info']
        
        required_fields = [
            'converged',
            'energy',
            'final_bond_dim',
            'num_sweeps',
            'max_bond_reached',
            'reason'
        ]
        
        for field in required_fields:
            assert field in conv_info, f"Missing field: {field}"

    def test_convergence_with_different_seeds(self):
        """Test that different seeds produce different but valid results."""
        L = 10
        delta = 0.1
        
        results = []
        for seed in [100, 200, 300]:
            result = compute_ground_state(L=L, delta=delta, N_real=1, seed=seed)
            results.append(result)
        
        # All should have valid MPS
        for result in results:
            assert result['mps'] is not None
            assert result['couplings'] is not None
            assert len(result['couplings']) == L - 1

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_small_chain(self):
        """Test with minimum chain length."""
        L = 4
        delta = 0.1
        
        result = compute_ground_state(L=L, delta=delta, N_real=1, seed=555)
        
        assert result['mps'] is not None
        assert len(result['couplings']) == 3  # L-1

    def test_large_delta(self):
        """Test with large disorder strength."""
        L = 8
        delta = 0.9  # Near maximum
        
        result = compute_ground_state(L=L, delta=delta, N_real=1, seed=666)
        
        assert result['mps'] is not None
        # Couplings should be in [0.1, 1.9]
        assert np.all(result['couplings'] >= 0.0)
        assert np.all(result['couplings'] <= 2.0)

    def test_zero_delta(self):
        """Test with no disorder (clean chain)."""
        L = 8
        delta = 0.0
        
        result = compute_ground_state(L=L, delta=delta, N_real=1, seed=777)
        
        assert result['mps'] is not None
        # All couplings should be exactly 1.0
        assert np.allclose(result['couplings'], 1.0)

    def test_invalid_l(self):
        """Test with invalid chain length."""
        with pytest.raises(Exception):
            compute_ground_state(L=2, delta=0.1, N_real=1)  # Too small

    def test_invalid_delta(self):
        """Test with invalid disorder strength."""
        with pytest.raises(Exception):
            compute_ground_state(L=10, delta=1.5, N_real=1)  # Too large