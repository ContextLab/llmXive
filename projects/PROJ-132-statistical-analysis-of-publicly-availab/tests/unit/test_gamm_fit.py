"""
Unit tests for the GAMM fitting module.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.gamm_fit import fit_unified_spatial_model, _compute_matern_kernel_distances


class TestGAMMFit:
    """Test suite for GAMM fitting functions."""

    @pytest.fixture
    def dummy_data(self):
        """Create dummy data for testing."""
        np.random.seed(42)
        n = 500
        df = pd.DataFrame({
            'species': np.random.choice(['A', 'B', 'C'], n),
            'temp': np.random.normal(15, 5, n),
            'precip': np.random.normal(100, 20, n),
            'effort': np.random.normal(10, 2, n),
            'lon': np.random.uniform(-100, -50, n),
            'lat': np.random.uniform(30, 50, n),
            'phenology_metric': np.random.normal(100, 10, n)
        })
        return df

    def test_matern_kernel_distances(self):
        """Test the Matérn kernel distance computation."""
        coords = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0]
        ])
        dists = _compute_matern_kernel_distances(coords)
        
        # Check shape
        assert dists.shape == (3, 3)
        
        # Check diagonal is zero
        assert np.allclose(np.diag(dists), 0)
        
        # Check symmetry
        assert np.allclose(dists, dists.T)
        
        # Check specific distance
        assert np.isclose(dists[0, 1], 1.0)

    def test_fit_unified_spatial_model_with_dummy_data(self, dummy_data):
        """Test fitting the unified spatial model with dummy data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "test_input.parquet")
            output_path = os.path.join(tmpdir, "test_output.json")
            
            dummy_data.to_parquet(input_path, index=False)
            
            result = fit_unified_spatial_model(input_path, output_path)
            
            assert result['success'] is True
            assert 'model_info' in result
            assert 'coefficients' in result
            assert 'diagnostics' in result
            assert 'moran_i' in result['diagnostics']
            assert os.path.exists(output_path)

    def test_fit_unified_spatial_model_empty_data(self):
        """Test fitting with empty data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "empty_input.parquet")
            output_path = os.path.join(tmpdir, "empty_output.json")
            
            # Create empty dataframe with correct columns
            df = pd.DataFrame(columns=['species', 'temp', 'precip', 'effort', 'lon', 'lat', 'phenology_metric'])
            df.to_parquet(input_path, index=False)
            
            result = fit_unified_spatial_model(input_path, output_path)
            
            assert result['success'] is False
            assert 'error' in result

    def test_fit_unified_spatial_model_species_filter(self, dummy_data):
        """Test fitting with species subset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "filtered_input.parquet")
            output_path = os.path.join(tmpdir, "filtered_output.json")
            
            dummy_data.to_parquet(input_path, index=False)
            
            result = fit_unified_spatial_model(
                input_path, 
                output_path, 
                species_subset=['A']
            )
            
            assert result['success'] is True
            assert 'A' in result['species_list']
            assert 'B' not in result['species_list']
            assert 'C' not in result['species_list']
