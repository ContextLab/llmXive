"""
Unit tests for feature engineering module.
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
    parse_formula,
    get_valence_electrons,
    get_element_properties,
    compute_compositional_features,
    add_features_to_dataframe,
    DESCRIPTOR_COLUMNS
)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        'material_id': ['MP-1', 'MP-2', 'MP-3'],
        'formula': ['Cu', 'Al2O3', 'FeNi3'],
        'C11': [168, 100, 200],
        'C12': [120, 40, 120],
        'C44': [75, 30, 100],
        'A1': [3.125, 0.6, 1.25]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_file(sample_dataframe):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_dataframe.to_csv(f, index=False)
        return f.name

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

class TestParseFormula:
    def test_parse_simple_formula(self):
        """Test parsing a simple elemental formula."""
        result = parse_formula('Cu')
        assert result == {'Cu': 1}

    def test_parse_compound_formula(self):
        """Test parsing a compound formula with counts."""
        result = parse_formula('Al2O3')
        assert result == {'Al': 2, 'O': 3}

    def test_parse_alloy_formula(self):
        """Test parsing an alloy formula."""
        result = parse_formula('FeNi3')
        assert result == {'Fe': 1, 'Ni': 3}

    def test_parse_empty_formula_raises(self):
        """Test that empty formula raises ValueError."""
        with pytest.raises(ValueError):
            parse_formula('')

    def test_parse_none_formula_raises(self):
        """Test that None formula raises ValueError."""
        with pytest.raises(ValueError):
            parse_formula(None)

class TestGetValenceElectrons:
    def test_get_valence_copper(self):
        """Test valence electrons for copper (group 11)."""
        result = get_valence_electrons('Cu')
        assert result is not None
        assert result == 11  # Group 11

    def test_get_valence_aluminum(self):
        """Test valence electrons for aluminum (group 13)."""
        result = get_valence_electrons('Al')
        assert result is not None
        assert result == 3  # Group 13 - 10

    def test_get_valence_invalid_element(self):
        """Test handling of invalid element."""
        result = get_valence_electrons('Xx')
        assert result is None

class TestGetElementProperties:
    def test_get_properties_copper(self):
        """Test getting properties for copper."""
        result = get_element_properties('Cu')
        assert result is not None
        assert 'atomic_radius' in result
        assert 'electronegativity' in result
        assert result['atomic_radius'] > 0
        assert result['electronegativity'] > 0

    def test_get_properties_aluminum(self):
        """Test getting properties for aluminum."""
        result = get_element_properties('Al')
        assert result is not None
        assert result['atomic_radius'] > 0
        assert result['electronegativity'] > 0

    def test_get_properties_invalid_element(self):
        """Test handling of invalid element."""
        result = get_element_properties('Xx')
        assert result is None

class TestComputeCompositionalFeatures:
    def test_compute_features_simple(self):
        """Test feature computation for a simple element."""
        result = compute_compositional_features('Cu')
        assert result is not None
        assert 'atomic_radius_variance' in result
        assert 'electronegativity_std' in result
        assert 'valence_electron_concentration' in result
        # For a single element, variance and std should be 0
        assert result['atomic_radius_variance'] == 0.0
        assert result['electronegativity_std'] == 0.0

    def test_compute_features_compound(self):
        """Test feature computation for a compound."""
        result = compute_compositional_features('Al2O3')
        assert result is not None
        assert result['atomic_radius_variance'] > 0
        assert result['electronegativity_std'] > 0
        assert result['valence_electron_concentration'] > 0

    def test_compute_features_alloy(self):
        """Test feature computation for an alloy."""
        result = compute_compositional_features('FeNi3')
        assert result is not None
        assert result['atomic_radius_variance'] >= 0
        assert result['electronegativity_std'] >= 0
        assert result['valence_electron_concentration'] > 0

    def test_compute_features_invalid_formula(self):
        """Test handling of invalid formula."""
        result = compute_compositional_features('Xx2Yy3')
        assert result is None

class TestFeaturesIntegration:
    def test_add_features_to_dataframe(self, sample_dataframe):
        """Test adding features to a DataFrame."""
        df_with_features = add_features_to_dataframe(sample_dataframe, 'formula')
        
        # Check that new columns were added
        for col in DESCRIPTOR_COLUMNS:
            assert col in df_with_features.columns
        
        # Check that features were computed for valid formulas
        assert df_with_features['atomic_radius_variance'].notna().sum() == 3
        assert df_with_features['electronegativity_std'].notna().sum() == 3
        assert df_with_features['valence_electron_concentration'].notna().sum() == 3

    def test_add_features_handles_invalid(self):
        """Test that invalid formulas are handled gracefully."""
        data = {
            'material_id': ['MP-1', 'MP-2'],
            'formula': ['Cu', 'InvalidFormula'],
            'C11': [168, 200],
            'C12': [120, 120],
            'C44': [75, 100],
            'A1': [3.125, 1.25]
        }
        df = pd.DataFrame(data)
        
        df_with_features = add_features_to_dataframe(df, 'formula')
        
        # First row should have features, second should be NaN
        assert df_with_features.loc[0, 'atomic_radius_variance'] == 0.0
        assert pd.isna(df_with_features.loc[1, 'atomic_radius_variance'])

    def test_full_pipeline_integration(self, temp_csv_file, temp_output_dir):
        """Test full feature engineering pipeline."""
        output_path = os.path.join(temp_output_dir, 'output.csv')
        
        # Read input
        df = pd.read_csv(temp_csv_file)
        
        # Add features
        df_with_features = add_features_to_dataframe(df, 'formula')
        
        # Save output
        df_with_features.to_csv(output_path, index=False)
        
        # Verify output
        assert os.path.exists(output_path)
        output_df = pd.read_csv(output_path)
        
        assert len(output_df) == len(df)
        for col in DESCRIPTOR_COLUMNS:
            assert col in output_df.columns
            assert output_df[col].notna().sum() == 3  # All 3 should be valid

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame(columns=['formula', 'C11', 'C12', 'C44', 'A1'])
        df_with_features = add_features_to_dataframe(df, 'formula')
        
        for col in DESCRIPTOR_COLUMNS:
            assert col in df_with_features.columns
            assert len(df_with_features) == 0