"""
Integration tests for User Story 2: Null Model Generation and Comparison.

These tests verify that:
1. Product states have near-zero entanglement entropy
2. Haar-random states have maximal entanglement entropy
3. Statistical distinction (t-test) exists between null models and physical states
"""
import os
import sys
import tempfile
import numpy as np
import pytest
import h5py

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.null_models import (
    generate_random_product_state,
    generate_haar_random_state,
    generate_random_product_states_batch,
    generate_haar_random_states_batch,
    save_product_states_to_hdf5,
    save_haar_states_to_hdf5,
    NullModelError
)
from code.metrics import calculate_entanglement_entropy
from code.statistics import run_welch_t_test
from code.config import Config


class TestNullModelGeneration:
    """Tests for null model state generation."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_product_state_generation_small(self):
        """Test product state generation for small N."""
        n_sites = 4
        state = generate_random_product_state(n_sites, seed=42)
        
        # Check dimensions
        assert state.shape == (2 ** n_sites,)
        
        # Check normalization
        norm = np.linalg.norm(state)
        assert np.isclose(norm, 1.0, atol=1e-10)
        
        # Check no NaN/Inf
        assert not np.any(np.isnan(state))
        assert not np.any(np.isinf(state))

    def test_product_state_generation_medium(self):
        """Test product state generation for medium N."""
        n_sites = 10
        state = generate_random_product_state(n_sites, seed=42)
        
        assert state.shape == (2 ** n_sites,)
        assert np.isclose(np.linalg.norm(state), 1.0, atol=1e-10)
        assert not np.any(np.isnan(state))
        assert not np.any(np.isinf(state))

    def test_haar_state_generation_small(self):
        """Test Haar-random state generation for small N."""
        n_sites = 4
        state = generate_haar_random_state(n_sites, seed=42)
        
        assert state.shape == (2 ** n_sites,)
        assert np.isclose(np.linalg.norm(state), 1.0, atol=1e-10)
        assert not np.any(np.isnan(state))
        assert not np.any(np.isinf(state))

    def test_haar_state_generation_medium(self):
        """Test Haar-random state generation for medium N."""
        n_sites = 10
        state = generate_haar_random_state(n_sites, seed=42)
        
        assert state.shape == (2 ** n_sites,)
        assert np.isclose(np.linalg.norm(state), 1.0, atol=1e-10)
        assert not np.any(np.isnan(state))
        assert not np.any(np.isinf(state))

    def test_batch_product_states(self):
        """Test batch generation of product states."""
        n_sites = 6
        n_states = 5
        states = generate_random_product_states_batch(n_sites, n_states, seed=42)
        
        assert len(states) == n_states
        for i, state in enumerate(states):
            assert state.shape == (2 ** n_sites,)
            assert np.isclose(np.linalg.norm(state), 1.0, atol=1e-10)

    def test_batch_haar_states(self):
        """Test batch generation of Haar-random states."""
        n_sites = 6
        n_states = 5
        states = generate_haar_random_states_batch(n_sites, n_states, seed=42)
        
        assert len(states) == n_states
        for i, state in enumerate(states):
            assert state.shape == (2 ** n_sites,)
            assert np.isclose(np.linalg.norm(state), 1.0, atol=1e-10)

    def test_save_product_states_hdf5(self, temp_dir):
        """Test saving product states to HDF5."""
        n_sites = 6
        n_states = 3
        states = generate_random_product_states_batch(n_sites, n_states, seed=42)
        
        output_path = os.path.join(temp_dir, "test_product.h5")
        save_product_states_to_hdf5(states, n_sites, output_path, "product", seed=42)
        
        # Verify file exists and contains correct data
        assert os.path.exists(output_path)
        with h5py.File(output_path, 'r') as f:
            assert f.attrs['state_type'] == 'product'
            assert f.attrs['n_sites'] == n_sites
            assert f.attrs['n_states'] == n_states
            assert 'wavefunctions' in f
            assert f['wavefunctions'].shape == (n_states, 2 ** n_sites)

    def test_save_haar_states_hdf5(self, temp_dir):
        """Test saving Haar-random states to HDF5."""
        n_sites = 6
        n_states = 3
        states = generate_haar_random_states_batch(n_sites, n_states, seed=42)
        
        output_path = os.path.join(temp_dir, "test_haar.h5")
        save_haar_states_to_hdf5(states, n_sites, output_path, seed=42)
        
        assert os.path.exists(output_path)
        with h5py.File(output_path, 'r') as f:
            assert f.attrs['state_type'] == 'haar'
            assert f.attrs['n_sites'] == n_sites
            assert f.attrs['n_states'] == n_states

    def test_invalid_n_sites(self):
        """Test that invalid n_sites raises error."""
        with pytest.raises(NullModelError):
            generate_random_product_state(1, seed=42)

    def test_zero_norm_handling(self):
        """Test handling of zero-norm states (edge case)."""
        # This is hard to trigger with random generation, but we test the logic
        # by checking that the functions don't crash on normal inputs
        n_sites = 8
        for _ in range(10):
            state = generate_random_product_state(n_sites, seed=None)
            assert np.linalg.norm(state) > 1e-10


class TestNullModelMetrics:
    """Tests for metric calculation on null models."""

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_product_state_entanglement(self):
        """
        Test that product states have near-zero entanglement entropy.
        
        For a true product state, the entanglement entropy across any cut
        should be zero (or very close to zero due to numerical precision).
        """
        n_sites = 6
        n_states = 5
        states = generate_random_product_states_batch(n_sites, n_states, seed=42)
        
        entropies = []
        for state in states:
            # Calculate entanglement entropy across the middle cut
            cut = n_sites // 2
            entropy = calculate_entanglement_entropy(state, n_sites, cut)
            entropies.append(entropy)
        
        entropies = np.array(entropies)
        
        # Product states should have very low entanglement
        # Allow for small numerical errors
        assert np.all(entropies < 0.1), f"Product state entropies too high: {entropies}"
        assert np.mean(entropies) < 0.05, f"Mean product state entropy too high: {np.mean(entropies)}"

    def test_haar_state_entanglement(self):
        """
        Test that Haar-random states have high entanglement entropy.
        
        For Haar-random states, the entanglement entropy should be close
        to the Page value: S ~ ln(2^min(A,B)) - 1/2 for large systems.
        For N=6, cut=3: dim_A = dim_B = 8, Page value ~ ln(8) - 1/2 ~ 1.59
        """
        n_sites = 6
        n_states = 10
        states = generate_haar_random_states_batch(n_sites, n_states, seed=42)
        
        entropies = []
        for state in states:
            cut = n_sites // 2
            entropy = calculate_entanglement_entropy(state, n_sites, cut)
            entropies.append(entropy)
        
        entropies = np.array(entropies)
        
        # Haar-random states should have high entanglement
        # For N=6, cut=3, max entropy is ln(8) ~ 2.079
        # Page value is approximately ln(8) - 1/2 ~ 1.58
        assert np.all(entropies > 1.0), f"Some Haar state entropies too low: {entropies}"
        assert np.mean(entropies) > 1.3, f"Mean Haar state entropy too low: {np.mean(entropies)}"

    def test_statistical_distinction(self, temp_dir):
        """
        Test that product states and Haar states are statistically distinct.
        
        Use Welch's t-test to verify p < 0.05.
        """
        n_sites = 8
        n_states = 20
        
        # Generate states
        product_states = generate_random_product_states_batch(n_sites, n_states, seed=42)
        haar_states = generate_haar_random_states_batch(n_sites, n_states, seed=42 + 1000)
        
        # Calculate entanglement entropies
        cut = n_sites // 2
        product_entropies = []
        for state in product_states:
            entropy = calculate_entanglement_entropy(state, n_sites, cut)
            product_entropies.append(entropy)
        
        haar_entropies = []
        for state in haar_states:
            entropy = calculate_entanglement_entropy(state, n_sites, cut)
            haar_entropies.append(entropy)
        
        product_entropies = np.array(product_entropies)
        haar_entropies = np.array(haar_entropies)
        
        # Perform Welch's t-test
        t_stat, p_value = run_welch_t_test(product_entropies, haar_entropies)
        
        # Verify statistical distinction
        assert p_value < 0.05, f"Product and Haar states not statistically distinct (p={p_value})"
        assert t_stat > 0, "t-statistic should be positive (product < Haar)"
        
        # Verify means are in expected order
        assert np.mean(product_entropies) < np.mean(haar_entropies), \
            f"Product mean ({np.mean(product_entropies)}) should be < Haar mean ({np.mean(haar_entropies)})"


class TestNullModelIntegration:
    """Full integration tests for null model pipeline."""

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_full_null_model_pipeline(self, temp_dir):
        """
        Test the complete null model generation and analysis pipeline.
        
        This test:
        1. Generates product and Haar states
        2. Saves them to HDF5
        3. Loads them back
        4. Calculates metrics
        5. Performs statistical comparison
        """
        n_sites = 8
        n_states = 10
        
        # Generate states
        product_states = generate_random_product_states_batch(n_sites, n_states, seed=42)
        haar_states = generate_haar_random_states_batch(n_sites, n_states, seed=42 + 1000)
        
        # Save to HDF5
        product_path = os.path.join(temp_dir, "product_states.h5")
        haar_path = os.path.join(temp_dir, "haar_states.h5")
        
        save_product_states_to_hdf5(product_states, n_sites, product_path, "product", seed=42)
        save_haar_states_to_hdf5(haar_states, n_sites, haar_path, seed=42 + 1000)
        
        # Load and verify
        with h5py.File(product_path, 'r') as f:
            loaded_product = f['wavefunctions'][:]
            assert loaded_product.shape == (n_states, 2 ** n_sites)
        
        with h5py.File(haar_path, 'r') as f:
            loaded_haar = f['wavefunctions'][:]
            assert loaded_haar.shape == (n_states, 2 ** n_sites)
        
        # Calculate metrics
        cut = n_sites // 2
        product_entropies = [calculate_entanglement_entropy(state, n_sites, cut) 
                            for state in loaded_product]
        haar_entropies = [calculate_entanglement_entropy(state, n_sites, cut) 
                         for state in loaded_haar]
        
        # Statistical comparison
        t_stat, p_value = run_welch_t_test(np.array(product_entropies), np.array(haar_entropies))
        
        # Assertions
        assert p_value < 0.05, "Null models not statistically distinct"
        assert np.mean(product_entropies) < np.mean(haar_entropies)
        assert np.max(product_entropies) < 0.5, "Product states have too much entanglement"
        assert np.min(haar_entropies) > 1.0, "Haar states have too little entanglement"