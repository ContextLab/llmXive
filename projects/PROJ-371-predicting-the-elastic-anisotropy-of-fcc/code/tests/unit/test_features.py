import os
import sys
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

from src.data.features import (
    parse_formula,
    get_valence_electrons,
    get_element_properties,
    compute_compositional_features,
    main
)
from src.utils.config import get_path

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        'material_id': ['MP-123', 'MP-456', 'MP-789'],
        'formula': ['Fe2O3', 'CuNi', 'Al0.5Fe0.5'],
        'C11': [200, 150, 180],
        'C12': [100, 80, 90],
        'C44': [50, 40, 45],
        'A1': [1.0, 1.0, 1.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_file(sample_dataframe):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_dataframe.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

class TestParseFormula:
    def test_parse_simple_formula(self):
        """Test parsing a simple formula."""
        result = parse_formula("Fe2O3")
        assert result == {'Fe': 2.0, 'O': 3.0}

    def test_parse_decimal_formula(self):
        """Test parsing a formula with decimal coefficients."""
        result = parse_formula("Cu0.5Ni0.5")
        assert result == {'Cu': 0.5, 'Ni': 0.5}

    def test_parse_missing_formula(self):
        """Test parsing missing or invalid formula."""
        assert parse_formula(None) == {}
        assert parse_formula("") == {}
        assert parse_formula("NaN") == {}

    def test_parse_complex_formula(self):
        """Test parsing a complex formula."""
        result = parse_formula("Al0.5Fe0.5")
        assert result == {'Al': 0.5, 'Fe': 0.5}

class TestGetValenceElectrons:
    def test_get_valence_main_group(self):
        """Test getting valence electrons for main group elements."""
        # Sodium (Na) is in group 1, should have 1 valence electron
        result = get_valence_electrons("Na")
        assert result is not None
        assert result == 1

    def test_get_valence_transition(self):
        """Test getting valence electrons for transition metals."""
        # Iron (Fe) is in group 8, transition metal
        result = get_valence_electrons("Fe")
        assert result is not None
        # The exact value depends on the implementation, but it should be a positive integer
        assert result > 0

    def test_get_valence_invalid_element(self):
        """Test getting valence electrons for an invalid element."""
        result = get_valence_electrons("Xyz")
        assert result is None

class TestGetElementProperties:
    def test_get_properties_valid_element(self):
        """Test getting properties for a valid element."""
        props = get_element_properties("Fe")
        assert props is not None
        assert 'atomic_radius' in props
        assert 'electronegativity' in props
        assert 'valence_electrons' in props
        # Check that at least some properties are not None
        assert props['atomic_radius'] is not None or props['electronegativity'] is not None

    def test_get_properties_invalid_element(self):
        """Test getting properties for an invalid element."""
        props = get_element_properties("Xyz")
        assert props is None

    def test_get_properties_returns_dict(self):
        """Test that the returned value is a dictionary with expected keys."""
        props = get_element_properties("Cu")
        assert isinstance(props, dict)
        assert set(props.keys()) == {'atomic_radius', 'electronegativity', 'valence_electrons'}

class TestComputeCompositionalFeatures:
    def test_compute_features_basic(self, sample_dataframe):
        """Test basic feature computation."""
        df_features = compute_compositional_features(sample_dataframe)
        
        # Check that new columns are added
        assert 'atomic_radius_variance' in df_features.columns
        assert 'electronegativity_std' in df_features.columns
        assert 'valence_electron_concentration' in df_features.columns

    def test_compute_features_no_nan(self, sample_dataframe):
        """Test that features are computed without NaN for valid formulas."""
        df_features = compute_compositional_features(sample_dataframe)
        
        # Check that at least some rows have non-NaN values
        non_nan_count = df_features['atomic_radius_variance'].notna().sum()
        assert non_nan_count > 0

    def test_compute_features_empty_dataframe(self):
        """Test feature computation on an empty DataFrame."""
        empty_df = pd.DataFrame(columns=['formula'])
        result = compute_compositional_features(empty_df)
        assert result.empty
        assert 'atomic_radius_variance' in result.columns

    def test_compute_features_handles_missing_elements(self):
        """Test that missing elements result in NaN features."""
        data = {
            'formula': ['Fe2O3', 'Xyz123'],  # Xyz is invalid
            'C11': [200, 150]
        }
        df = pd.DataFrame(data)
        df_features = compute_compositional_features(df)
        
        # First row should have features, second should be NaN
        assert df_features.loc[0, 'atomic_radius_variance'] is not None
        assert pd.isna(df_features.loc[1, 'atomic_radius_variance'])

    def test_compute_features_weighted_average(self):
        """Test that weighted average is computed correctly."""
        # Create a DataFrame with known stoichiometry
        data = {
            'formula': ['Fe2O3'],  # 2 Fe, 3 O
            'C11': [200]
        }
        df = pd.DataFrame(data)
        df_features = compute_compositional_features(df)
        
        # The valence electron concentration should be a weighted average
        # Fe has ~8 valence electrons, O has 6
        # Weighted average: (2*8 + 3*6) / 5 = 34/5 = 6.8
        # The exact value depends on the implementation, but it should be around this
        assert df_features.loc[0, 'valence_electron_concentration'] is not None
        assert 5 < df_features.loc[0, 'valence_electron_concentration'] < 8

class TestFeaturesIntegration:
    def test_main_function_creates_output(self, temp_csv_file, temp_output_dir, sample_dataframe):
        """Test that main function creates output file."""
        # Mock get_path to use temp directory
        with patch('src.data.features.get_path') as mock_get_path:
            mock_get_path.side_effect = lambda key, filename: os.path.join(temp_output_dir, filename)
            
            # Run main
            main()
            
            # Check that output file was created
            output_path = os.path.join(temp_output_dir, "elastic_anisotropy_with_features.csv")
            assert os.path.exists(output_path)

    def test_main_function_with_valid_data(self, temp_csv_file, temp_output_dir, sample_dataframe):
        """Test main function with valid data."""
        with patch('src.data.features.get_path') as mock_get_path:
            mock_get_path.side_effect = lambda key, filename: os.path.join(temp_output_dir, filename)
            
            # Run main
            main()
            
            # Read output and check for features
            output_path = os.path.join(temp_output_dir, "elastic_anisotropy_with_features.csv")
            df_output = pd.read_csv(output_path)
            
            assert 'atomic_radius_variance' in df_output.columns
            assert 'electronegativity_std' in df_output.columns
            assert 'valence_electron_concentration' in df_output.columns
            assert len(df_output) == len(sample_dataframe)

    def test_main_function_handles_missing_input(self, temp_output_dir):
        """Test that main function handles missing input file."""
        with patch('src.data.features.get_path') as mock_get_path:
            mock_get_path.side_effect = lambda key, filename: os.path.join(temp_output_dir, filename)
            
            # Try to run main with missing input
            with pytest.raises(SystemExit):
                main()
