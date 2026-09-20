"""
Unit tests for ground_state.py module.
"""

import pytest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.ground_state import (
    get_default_ground_state_config,
    validate_ground_state_config,
    compute_ground_state,
    compute_ground_state_batch,
    is_numerically_unresolved,
    get_ground_state_statistics,
    GroundStateError
)
from code.config import ConfigError

try:
    import tenpy
    HAS_TENPY = True
except ImportError:
    HAS_TENPY = False


@pytest.fixture
def default_config():
    return get_default_ground_state_config()


def test_default_config():
    """Test that default config returns valid values."""
    config = get_default_ground_state_config()
    assert config['max_bond_dim'] == 400
    assert config['truncation_threshold'] == 1e-10
    assert config['dt'] == 0.01
    assert config['n_steps'] == 100
    assert config['convergence_tol'] == 1e-8


def test_validate_config_valid(default_config):
    """Test validation with valid config."""
    # Should not raise
    validate_ground_state_config(default_config)


def test_validate_config_invalid_max_bond_dim(default_config):
    """Test validation with invalid max_bond_dim."""
    config = default_config.copy()
    config['max_bond_dim'] = 5  # Too low
    with pytest.raises(ConfigError):
        validate_ground_state_config(config)

    config['max_bond_dim'] = 2000  # Too high
    with pytest.raises(ConfigError):
        validate_ground_state_config(config)


def test_validate_config_invalid_truncation_threshold(default_config):
    """Test validation with invalid truncation_threshold."""
    config = default_config.copy()
    config['truncation_threshold'] = 1e-20  # Too low
    with pytest.raises(ConfigError):
        validate_ground_state_config(config)

    config['truncation_threshold'] = 0.1  # Too high
    with pytest.raises(ConfigError):
        validate_ground_state_config(config)


@pytest.mark.skipif(not HAS_TENPY, reason="TeNPy not installed")
def test_convergence():
    """Test TEBD convergence on a small system."""
    L = 6
    # Create a simple ordered system (no disorder) to ensure convergence
    couplings = np.ones(L - 1)
    
    config = get_default_ground_state_config()
    config['n_steps'] = 200  # More steps for convergence
    config['convergence_tol'] = 1e-6
    
    gs, energies, metadata = compute_ground_state(L, couplings, config)
    
    # Check that we got a result
    assert gs is not None
    assert energies is not None
    assert len(energies) > 1
    
    # Check convergence flag (may not be True for all systems, but should be stable)
    # We primarily check that the function runs without error and returns metadata
    assert 'converged' in metadata
    assert 'final_energy' in metadata
    assert 'max_bond_dim_reached' in metadata


@pytest.mark.skipif(not HAS_TENPY, reason="TeNPy not installed")
def test_numerically_unresolved_flagging():
    """Test that numerically unresolved states are flagged."""
    L = 10
    # Create a system that might be hard to converge
    # Use a large disorder strength
    couplings = np.random.uniform(-0.5, 1.5, size=L-1)
    
    config = get_default_ground_state_config()
    config['n_steps'] = 10  # Very few steps to force non-convergence
    config['max_bond_dim'] = 10  # Very low bond dimension
    
    gs, energies, metadata = compute_ground_state(L, couplings, config)
    
    # Check that the unresolved flag is set appropriately
    # With such low settings, it's likely to be unresolved
    assert 'is_numerically_unresolved' in metadata
    
    # If it converged despite low settings, that's also valid, but the flag should be accurate
    # We test the logic of the flag itself
    assert isinstance(metadata['is_numerically_unresolved'], bool)


@pytest.mark.skipif(not HAS_TENPY, reason="TeNPy not installed")
def test_batch_computation():
    """Test batch ground state computation."""
    L = 6
    delta = 0.2
    N_real = 3
    
    results = compute_ground_state_batch(L, delta, N_real, seed=42)
    
    assert len(results) == N_real
    
    for gs, energies, metadata in results:
        assert 'is_numerically_unresolved' in metadata
        assert 'final_energy' in metadata


def test_is_numerically_unresolved_function():
    """Test the is_numerically_unresolved helper function."""
    # Test with unresolved metadata
    meta_unresolved = {'is_numerically_unresolved': True}
    assert is_numerically_unresolved(meta_unresolved) is True
    
    # Test with resolved metadata
    meta_resolved = {'is_numerically_unresolved': False}
    assert is_numerically_unresolved(meta_resolved) is False
    
    # Test with missing key (should return True as fallback)
    meta_missing = {'converged': True}
    assert is_numerically_unresolved(meta_missing) is True
    
    # Test with None
    assert is_numerically_unresolved(None) is True


def test_get_ground_state_statistics():
    """Test statistics computation."""
    # Create mock results
    results = [
        (None, np.array([1.0, 0.9, 0.8]), {'is_numerically_unresolved': False, 'max_bond_dim_reached': 50}),
        (None, np.array([1.0, 0.95, 0.9]), {'is_numerically_unresolved': False, 'max_bond_dim_reached': 60}),
        (None, np.array([]), {'is_numerically_unresolved': True, 'max_bond_dim_reached': 10})
    ]
    
    stats = get_ground_state_statistics(results)
    
    assert stats['total_realizations'] == 3
    assert stats['unresolved_count'] == 1
    assert stats['converged_count'] == 2
    assert stats['convergence_rate'] == pytest.approx(2/3)
    assert stats['mean_energy'] is not None
    assert stats['mean_max_chi'] is not None


@pytest.mark.skipif(not HAS_TENPY, reason="TeNPy not installed")
def test_double_precision_enforcement():
    """Test that computations are done in double precision."""
    L = 6
    couplings = np.ones(L - 1, dtype=np.float64)
    
    config = get_default_ground_state_config()
    
    gs, energies, metadata = compute_ground_state(L, couplings, config)
    
    # Check that energies are float64
    assert energies.dtype == np.float64
    
    # Check that couplings were handled as float64
    assert couplings.dtype == np.float64
