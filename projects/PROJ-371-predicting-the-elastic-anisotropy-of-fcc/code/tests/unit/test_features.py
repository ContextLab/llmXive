"""
Unit tests for src/data/features.py
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.features import (
    get_element_properties,
    parse_formula,
    compute_compositional_features,
    get_valence_electrons
)

logger = logging.getLogger(__name__)

class TestGetElementProperties:
    def test_returns_valid_properties(self):
        """Test that valid elements return correct properties."""
        props = get_element_properties('Fe')
        assert props is not None
        assert 'radius' in props
        assert 'electronegativity' in props
        assert 'valence' in props
        assert props['radius'] > 0
        assert props['electronegativity'] > 0

    def test_returns_none_for_invalid_element(self):
        """Test that invalid element symbols return None."""
        props = get_element_properties('XYZ')
        assert props is None

    def test_valence_calculation(self):
        """Test valence electron calculation for various groups."""
        # Group 1
        assert get_valence_electrons('Na') == 1
        # Group 2
        assert get_valence_electrons('Mg') == 2
        # Group 11 (Cu)
        assert get_valence_electrons('Cu') == 11
        # Group 13 (Al)
        assert get_valence_electrons('Al') == 3

class TestComputeCompositionalFeatures:
    @pytest.fixture
    def sample_df(self):
        """Create a sample dataframe for testing."""
        data = {
            'material_id': ['MP-1', 'MP-2'],
            'formula': ['Fe', 'Al0.5Co0.5'],
            'C11': [200, 100],
            'C12': [100, 80],
            'C44': [50, 40],
            'A1': [1.0, 1.33]
        }
        return pd.DataFrame(data)

    def test_compute_features_single_element(self, sample_df):
        """Test feature computation for a single element."""
        df = sample_df[sample_df['material_id'] == 'MP-1'].copy()
        result = compute_compositional_features(df)
        
        assert 'atomic_radius_variance' in result.columns
        assert 'electronegativity_std' in result.columns
        assert 'valence_electron_concentration' in result.columns
        
        # For a single element, variance and std should be 0
        assert result['atomic_radius_variance'].iloc[0] == 0.0
        assert result['electronegativity_std'].iloc[0] == 0.0
        # VEC should match the element's valence
        assert result['valence_electron_concentration'].iloc[0] == 8 # Fe is group 8

    def test_compute_features_alloy(self, sample_df):
        """Test feature computation for an alloy."""
        df = sample_df[sample_df['material_id'] == 'MP-2'].copy()
        result = compute_compositional_features(df)
        
        assert 'atomic_radius_variance' in result.columns
        assert 'electronegativity_std' in result.columns
        
        # For an alloy, variance and std should be > 0
        assert result['atomic_radius_variance'].iloc[0] > 0
        assert result['electronegativity_std'].iloc[0] > 0

    def test_handles_missing_formula(self):
        """Test handling of missing formula."""
        df = pd.DataFrame({'formula': [None, 'Fe']})
        result = compute_compositional_features(df)
        
        assert pd.isna(result['atomic_radius_variance'].iloc[0])
        assert not pd.isna(result['atomic_radius_variance'].iloc[1])

    def test_handles_unknown_element(self):
        """Test handling of unknown elements in formula."""
        df = pd.DataFrame({'formula': ['XYZ', 'Fe']})
        result = compute_compositional_features(df)
        
        assert pd.isna(result['atomic_radius_variance'].iloc[0])
        assert not pd.isna(result['atomic_radius_variance'].iloc[1])

class TestValenceElectrons:
    def test_transition_metals(self):
        """Test valence for transition metals."""
        # Sc (Group 3)
        assert get_valence_electrons('Sc') == 3
        # Ti (Group 4)
        assert get_valence_electrons('Ti') == 4
        # Fe (Group 8)
        assert get_valence_electrons('Fe') == 8
        # Ni (Group 10)
        assert get_valence_electrons('Ni') == 10

    def test_main_group_metals(self):
        """Test valence for main group metals."""
        # Al (Group 13) -> 3
        assert get_valence_electrons('Al') == 3
        # Mg (Group 2) -> 2
        assert get_valence_electrons('Mg') == 2

class TestFeaturesIntegration:
    def test_full_pipeline_with_mock_data(self):
        """Test the full pipeline with mock data."""
        data = {
            'id': [1, 2, 3],
            'formula': ['Fe', 'Cu', 'Al0.5Fe0.5'],
            'target': [1.0, 1.1, 1.05]
        }
        df = pd.DataFrame(data)
        
        result = compute_compositional_features(df)
        
        assert len(result) == 3
        assert 'atomic_radius_variance' in result.columns
        assert 'electronegativity_std' in result.columns
        assert 'valence_electron_concentration' in result.columns
        
        # Check that pure elements have 0 variance/std
        assert result.loc[0, 'atomic_radius_variance'] == 0.0
        assert result.loc[1, 'electronegativity_std'] == 0.0
        
        # Check that alloy has non-zero variance/std
        assert result.loc[2, 'atomic_radius_variance'] > 0
        assert result.loc[2, 'electronegativity_std'] > 0