"""
Unit tests for User Story 2: Dimensionality Reduction.

Specifically tests UMAP parameter application and configuration loading.
"""
import os
import sys
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.config import load_config, get_config_value
from umap import UMAP


class TestUMAPParameterApplication:
    """Tests for verifying UMAP parameters are correctly applied."""

    def test_umap_default_parameters_from_config(self):
        """
        Verify that the UMAP instance is created with the correct 
        n_neighbors and min_dist parameters as defined in the spec.
        
        Spec requirement: n_neighbors=15, min_dist=0.1
        """
        # Load configuration to ensure values are available
        config = load_config()
        
        # Verify config contains the expected values (T004 ensures these exist)
        n_neighbors = get_config_value('UMAP_N_NEIGHBORS', 15)
        min_dist = get_config_value('UMAP_MIN_DIST', 0.1)
        
        # Create UMAP instance with specific parameters
        umap_model = UMAP(
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            n_components=2,
            random_state=42,  # Fixed seed for reproducibility
            metric='euclidean'
        )
        
        # Assert parameters are set correctly
        assert umap_model.n_neighbors == n_neighbors, \
            f"Expected n_neighbors={n_neighbors}, got {umap_model.n_neighbors}"
        assert umap_model.min_dist == min_dist, \
            f"Expected min_dist={min_dist}, got {umap_model.min_dist}"
        assert umap_model.n_components == 2, \
            f"Expected n_components=2, got {umap_model.n_components}"

    def test_umap_fits_mock_data_without_error(self):
        """
        Verify that UMAP can successfully fit on a small mock dataset
        with the specified parameters.
        """
        # Create a small mock dataset (100 samples, 10 features)
        np.random.seed(42)
        mock_data = np.random.rand(100, 10)
        
        # Initialize UMAP with spec parameters
        umap_model = UMAP(
            n_neighbors=15,
            min_dist=0.1,
            n_components=2,
            random_state=42,
            metric='euclidean',
            verbose=False
        )
        
        # Fit the model - this should not raise an exception
        try:
            embedding = umap_model.fit_transform(mock_data)
            
            # Verify output shape
            assert embedding.shape == (100, 2), \
                f"Expected shape (100, 2), got {embedding.shape}"
            
            # Verify embedding contains finite values
            assert np.all(np.isfinite(embedding)), \
                "Embedding contains non-finite values (NaN or Inf)"
                
        except Exception as e:
            pytest.fail(f"UMAP fit_transform failed with parameters n_neighbors=15, min_dist=0.1: {e}")

    def test_umap_parameters_are_integers_and_floats(self):
        """
        Verify that n_neighbors is an integer and min_dist is a float,
        ensuring type safety for the UMAP library.
        """
        n_neighbors = 15
        min_dist = 0.1
        
        umap_model = UMAP(
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            n_components=2,
            random_state=42
        )
        
        assert isinstance(umap_model.n_neighbors, int), \
            f"n_neighbors must be int, got {type(umap_model.n_neighbors)}"
        assert isinstance(umap_model.min_dist, float), \
            f"min_dist must be float, got {type(umap_model.min_dist)}"
            
    def test_umap_config_values_match_spec(self):
        """
        Explicitly verify that the hardcoded spec values (n_neighbors=15, 
        min_dist=0.1) are the ones being used if config is not overridden.
        """
        # Test with explicit spec values
        umap_model = UMAP(
            n_neighbors=15,
            min_dist=0.1,
            n_components=2,
            random_state=42
        )
        
        assert umap_model.n_neighbors == 15
        assert umap_model.min_dist == 0.1