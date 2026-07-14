"""
Unit tests for descriptor computation in code/descriptors.py.
"""
import pytest
import pandas as pd
import numpy as np
from code.descriptors import (
    compute_descriptors,
    _parse_composition,
    _calculate_mean_atomic_radius,
    _calculate_electronegativity_std,
    _calculate_cation_size_variance,
    _calculate_valence_electron_concentration,
    _determine_primary_anion_cation_group
)

class TestCompositionParsing:
    """Tests for composition parsing functionality."""

    def test_parse_simple_oxide(self):
        """Test parsing of simple oxide Al2O3."""
        result = _parse_composition("Al2O3")
        assert result is not None
        # Al2O3: 2 Al, 3 O -> total 5 atoms
        # Al fraction: 2/5 = 0.4, O fraction: 3/5 = 0.6
        assert abs(result['Al'] - 0.4) < 1e-6
        assert abs(result['O'] - 0.6) < 1e-6

    def test_parse_complex_composition(self):
        """Test parsing of complex composition."""
        result = _parse_composition("BaTiO3")
        assert result is not None
        # BaTiO3: 1 Ba, 1 Ti, 3 O -> total 5 atoms
        assert abs(result['Ba'] - 0.2) < 1e-6
        assert abs(result['Ti'] - 0.2) < 1e-6
        assert abs(result['O'] - 0.6) < 1e-6

    def test_parse_invalid_composition(self):
        """Test that invalid compositions return None."""
        result = _parse_composition("InvalidFormulaXYZ")
        assert result is None

    def test_parse_empty_string(self):
        """Test that empty string returns None."""
        result = _parse_composition("")
        assert result is None

class TestMeanAtomicRadius:
    """Tests for mean atomic radius calculation."""

    def test_al2o3_radius(self):
        """Test mean atomic radius for Al2O3."""
        composition = {'Al': 0.4, 'O': 0.6}
        # Al radius: 1.43, O radius: 0.73
        # Expected: 0.4 * 1.43 + 0.6 * 0.73 = 0.572 + 0.438 = 1.01
        expected = 0.4 * 1.43 + 0.6 * 0.73
        result = _calculate_mean_atomic_radius(composition)
        assert abs(result - expected) < 1e-6

    def test_batio3_radius(self):
        """Test mean atomic radius for BaTiO3."""
        composition = {'Ba': 0.2, 'Ti': 0.2, 'O': 0.6}
        # Ba: 1.98, Ti: 1.36, O: 0.73
        # Expected: 0.2*1.98 + 0.2*1.36 + 0.6*0.73 = 0.396 + 0.272 + 0.438 = 1.106
        expected = 0.2 * 1.98 + 0.2 * 1.36 + 0.6 * 0.73
        result = _calculate_mean_atomic_radius(composition)
        assert abs(result - expected) < 1e-6

class TestElectronegativityStd:
    """Tests for electronegativity standard deviation calculation."""

    def test_al2o3_electronegativity(self):
        """Test electronegativity std for Al2O3."""
        composition = {'Al': 0.4, 'O': 0.6}
        # Al: 1.61, O: 3.44
        # Mean: 0.4*1.61 + 0.6*3.44 = 0.644 + 2.064 = 2.708
        # Variance: 0.4*(1.61-2.708)^2 + 0.6*(3.44-2.708)^2
        #         = 0.4*1.205604 + 0.6*0.535824 = 0.4822416 + 0.3214944 = 0.803736
        # Std: sqrt(0.803736) = 0.8965
        mean = 0.4 * 1.61 + 0.6 * 3.44
        variance = 0.4 * (1.61 - mean)**2 + 0.6 * (3.44 - mean)**2
        expected = variance ** 0.5
        result = _calculate_electronegativity_std(composition)
        assert abs(result - expected) < 1e-6

class TestCationSizeVariance:
    """Tests for cation size variance calculation."""

    def test_al2o3_cation_variance(self):
        """Test cation size variance for Al2O3 (only Al is cation)."""
        composition = {'Al': 0.4, 'O': 0.6}
        # Only Al is cation, so variance should be 0 (single element)
        result = _calculate_cation_size_variance(composition)
        assert abs(result) < 1e-6

    def test_batio3_cation_variance(self):
        """Test cation size variance for BaTiO3 (Ba and Ti are cations)."""
        composition = {'Ba': 0.2, 'Ti': 0.2, 'O': 0.6}
        # Cations: Ba (1.98) and Ti (1.36)
        # Normalized: Ba: 0.5, Ti: 0.5
        # Mean: 0.5*1.98 + 0.5*1.36 = 1.67
        # Variance: 0.5*(1.98-1.67)^2 + 0.5*(1.36-1.67)^2
        #         = 0.5*0.0961 + 0.5*0.0961 = 0.0961
        result = _calculate_cation_size_variance(composition)
        expected_variance = 0.5 * (1.98 - 1.67)**2 + 0.5 * (1.36 - 1.67)**2
        assert abs(result - expected_variance) < 1e-6

class TestValenceElectronConcentration:
    """Tests for VEC calculation."""

    def test_al2o3_vec(self):
        """Test VEC for Al2O3."""
        composition = {'Al': 0.4, 'O': 0.6}
        # Al: 3 valence electrons, O: 6 valence electrons
        # VEC = 0.4*3 + 0.6*6 = 1.2 + 3.6 = 4.8
        expected = 0.4 * 3 + 0.6 * 6
        result = _calculate_valence_electron_concentration(composition)
        assert abs(result - expected) < 1e-6

    def test_batio3_vec(self):
        """Test VEC for BaTiO3."""
        composition = {'Ba': 0.2, 'Ti': 0.2, 'O': 0.6}
        # Ba: 2, Ti: 4, O: 6
        # VEC = 0.2*2 + 0.2*4 + 0.6*6 = 0.4 + 0.8 + 3.6 = 4.8
        expected = 0.2 * 2 + 0.2 * 4 + 0.6 * 6
        result = _calculate_valence_electron_concentration(composition)
        assert abs(result - expected) < 1e-6

class TestPrimaryAnionCationGroup:
    """Tests for primary anion-cation group determination."""

    def test_al2o3_group(self):
        """Test group for Al2O3."""
        composition = {'Al': 0.4, 'O': 0.6}
        result = _determine_primary_anion_cation_group(composition)
        assert result == "Al-O"

    def test_batio3_group(self):
        """Test group for BaTiO3."""
        composition = {'Ba': 0.2, 'Ti': 0.2, 'O': 0.6}
        result = _determine_primary_anion_cation_group(composition)
        # Ba and Ti are both cations, O is anion
        # Ti has higher fraction among cations? Actually Ba=0.2, Ti=0.2, so tie
        # The function picks the first one encountered with max fraction
        # Since we iterate through dict, order matters. But both are 0.2.
        # In practice, it should be either Ba-O or Ti-O.
        assert result.endswith("-O")

class TestComputeDescriptorsIntegration:
    """Integration tests for the full compute_descriptors function."""

    def test_compute_descriptors_basic(self):
        """Test compute_descriptors with a simple DataFrame."""
        df = pd.DataFrame({
            'composition': ['Al2O3', 'BaTiO3', 'SiO2']
        })
        
        result = compute_descriptors(df)
        
        # Check that new columns are added
        assert 'mean_atomic_radius' in result.columns
        assert 'electronegativity_std' in result.columns
        assert 'cation_size_variance' in result.columns
        assert 'valence_electron_concentration' in result.columns
        assert 'primary_anion_cation_group' in result.columns
        
        # Check that values are non-zero for valid compositions
        assert result['mean_atomic_radius'].iloc[0] > 0
        assert result['electronegativity_std'].iloc[0] > 0

    def test_compute_descriptors_with_invalid(self):
        """Test compute_descriptors with invalid compositions."""
        df = pd.DataFrame({
            'composition': ['Al2O3', 'Invalid', 'BaTiO3']
        })
        
        result = compute_descriptors(df)
        
        # First row should have valid descriptors
        assert result['mean_atomic_radius'].iloc[0] > 0
        
        # Second row (invalid) should have default values (0.0 or 'unknown-unknown')
        assert result['mean_atomic_radius'].iloc[1] == 0.0
        assert result['primary_anion_cation_group'].iloc[1] == 'unknown-unknown'
        
        # Third row should have valid descriptors
        assert result['mean_atomic_radius'].iloc[2] > 0

    def test_compute_descriptors_empty_composition(self):
        """Test compute_descriptors with empty composition strings."""
        df = pd.DataFrame({
            'composition': ['Al2O3', '', 'BaTiO3']
        })
        
        result = compute_descriptors(df)
        
        # First and third rows should have valid descriptors
        assert result['mean_atomic_radius'].iloc[0] > 0
        assert result['mean_atomic_radius'].iloc[2] > 0
        
        # Second row (empty) should have default values
        assert result['mean_atomic_radius'].iloc[1] == 0.0