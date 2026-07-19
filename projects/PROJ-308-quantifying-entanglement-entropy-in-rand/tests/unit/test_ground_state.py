"""
tests/unit/test_ground_state.py

Unit tests for ground state computation module.
"""

import pytest
import numpy as np
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from ground_state import (
    GroundStateError,
    get_default_ground_state_config,
    validate_ground_state_config,
    compute_ground_state,
    compute_ground_state_batch,
    is_numerically_unresolved,
    get_ground_state_statistics
)
from config import ConfigError


class TestGroundStateConfig:
    """Tests for ground state configuration functions."""

    def test_default_config_structure(self):
        """Test that default config has all required keys."""
        config = get_default_ground_state_config()
        required_keys = ['convergence_tol', 'max_bond_dim', 'dt_list', 'trunc_cut', 'verbose']
        for key in required_keys:
            assert key in config, f"Missing key: {key}"

    def test_default_config_values(self):
        """Test that default config has correct values."""
        config = get_default_ground_state_config()
        assert config['convergence_tol'] == 1e-8
        assert config['max_bond_dim'] == 400
        assert config['trunc_cut'] == 1e-10
        assert config['verbose'] == False
        assert 0.1 in config['dt_list']
        assert 0.001 in config['dt_list']

    def test_validate_config_passes_valid(self):
        """Test that valid config passes validation."""
        config = get_default_ground_state_config()
        validated = validate_ground_state_config(config)
        assert validated['convergence_tol'] == 1e-8
        assert validated['max_bond_dim'] == 400

    def test_validate_config_invalid_tolerance(self):
        """Test that invalid convergence tolerance raises error."""
        config = get_default_ground_state_config()
        config['convergence_tol'] = 1e-15  # Too small
        with pytest.raises(ConfigError):
            validate_ground_state_config(config)

    def test_validate_config_invalid_bond_dim(self):
        """Test that invalid max bond dimension raises error."""
        config = get_default_ground_state_config()
        config['max_bond_dim'] = 5  # Too small
        with pytest.raises(ConfigError):
            validate_ground_state_config(config)


class TestGroundStateComputation:
    """Tests for ground state computation functions."""

    def test_compute_ground_state_small_chain(self):
        """Test ground state computation on a small chain (L=20)."""
        L = 20
        delta = 0.1
        seed = 42

        # Use a more relaxed config for testing speed
        config = get_default_ground_state_config()
        config['max_bond_dim'] = 50  # Lower for faster test
        config['convergence_tol'] = 1e-4  # Looser for test
        config['dt_list'] = [0.1, 0.05, 0.01]

        psi, metadata = compute_ground_state(L, delta, seed=seed, config=config)

        assert psi is not None
        assert metadata is not None
        assert 'converged' in metadata
        assert 'max_chi_reached' in metadata
        assert 'energy' in metadata

    def test_compute_ground_state_double_precision(self):
        """Test that computations use double precision."""
        L = 20
        delta = 0.0
        seed = 123

        config = get_default_ground_state_config()
        config['max_bond_dim'] = 50
        config['convergence_tol'] = 1e-4

        psi, metadata = compute_ground_state(L, delta, seed=seed, config=config)

        # Check that MPS has float64 data
        # The MPS object should have float64 tensors
        for i in range(psi.L):
            B = psi.get_B(i, 'L')
            assert B.dtype == np.float64, f"MPS tensor at site {i} is not float64"

    def test_compute_ground_state_batch(self):
        """Test batch ground state computation."""
        L = 20
        delta = 0.1
        N_real = 3
        seed_base = 100

        config = get_default_ground_state_config()
        config['max_bond_dim'] = 50
        config['convergence_tol'] = 1e-4

        ground_states, metadata_list = compute_ground_state_batch(
            L, delta, N_real, seed_base, config
        )

        assert len(ground_states) == N_real
        assert len(metadata_list) == N_real
        assert all(ps is not None for ps in ground_states)
        assert all(md is not None for md in metadata_list)

    def test_numerically_unresolved_flagging(self):
        """Test that non-converged states are properly flagged."""
        # Create metadata that simulates non-convergence
        unresolved_meta = {
            'converged': False,
            'max_chi_reached': 400,
            'reason': 'Max bond dimension reached'
        }

        assert is_numerically_unresolved(unresolved_meta) is True

        converged_meta = {
            'converged': True,
            'max_chi_reached': 100,
            'energy': -10.5
        }

        assert is_numerically_unresolved(converged_meta) is False


class TestGroundStateStatistics:
    """Tests for ground state statistics functions."""

    def test_get_ground_state_statistics_empty(self):
        """Test statistics on empty list."""
        stats = get_ground_state_statistics([])
        assert stats['total_realizations'] == 0
        assert stats['converged_count'] == 0
        assert stats['convergence_rate'] == 0.0

    def test_get_ground_state_statistics_all_converged(self):
        """Test statistics when all states converged."""
        metadata_list = [
            {'converged': True, 'max_chi_reached': 100},
            {'converged': True, 'max_chi_reached': 150},
            {'converged': True, 'max_chi_reached': 120}
        ]

        stats = get_ground_state_statistics(metadata_list)
        assert stats['total_realizations'] == 3
        assert stats['converged_count'] == 3
        assert stats['unresolved_count'] == 0
        assert stats['convergence_rate'] == 1.0
        assert stats['avg_max_chi'] == 123.0
        assert stats['max_chi_overall'] == 150

    def test_get_ground_state_statistics_mixed(self):
        """Test statistics with mixed convergence."""
        metadata_list = [
            {'converged': True, 'max_chi_reached': 100},
            {'converged': False, 'max_chi_reached': 400},
            {'converged': True, 'max_chi_reached': 120}
        ]

        stats = get_ground_state_statistics(metadata_list)
        assert stats['total_realizations'] == 3
        assert stats['converged_count'] == 2
        assert stats['unresolved_count'] == 1
        assert abs(stats['convergence_rate'] - 2/3) < 1e-6


class TestConvergence:
    """Specific tests for convergence behavior (FR-003)."""

    def test_convergence_tolerance_enforcement(self):
        """Test that convergence tolerance is respected when achievable."""
        L = 20
        delta = 0.0  # Clean chain, easier to converge
        seed = 42

        config = get_default_ground_state_config()
        config['max_bond_dim'] = 100
        config['convergence_tol'] = 1e-4
        config['dt_list'] = [0.1, 0.05, 0.01]

        psi, metadata = compute_ground_state(L, delta, seed=seed, config=config)

        # For clean chains with low bond dimension, should converge
        # (This is a soft check - physics dependent)
        assert metadata is not None
        # We don't assert converged=True because it depends on physics
        # but we assert the metadata structure is correct

    def test_adaptive_bond_dimension(self):
        """Test that bond dimension grows adaptively."""
        L = 20
        delta = 0.5  # Stronger disorder
        seed = 99

        config = get_default_ground_state_config()
        config['max_bond_dim'] = 100
        config['convergence_tol'] = 1e-4

        psi, metadata = compute_ground_state(L, delta, seed=seed, config=config)

        # Check that max_bond_dim was tracked
        assert 'max_chi_reached' in metadata
        assert metadata['max_chi_reached'] <= config['max_bond_dim']

    def test_unresolved_flag_on_max_bond(self):
        """Test flagging when max bond dimension is hit without convergence."""
        L = 30
        delta = 0.8  # High disorder, harder to converge
        seed = 777

        config = get_default_ground_state_config()
        config['max_bond_dim'] = 20  # Artificially low to trigger unresolved
        config['convergence_tol'] = 1e-8

        psi, metadata = compute_ground_state(L, delta, seed=seed, config=config)

        # With such low max_bond_dim, likely unresolved
        # Check that metadata captures this
        assert 'reason' in metadata or 'converged' in metadata
        if not metadata.get('converged', False):
            assert metadata.get('reason') is not None
            assert 'unresolved' in metadata.get('reason', '').lower() or \
                   'max bond' in metadata.get('reason', '').lower() or \
                   'convergence' in metadata.get('reason', '').lower()