"""
Unit tests for the descriptor calculator.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.features.descriptor_calculator import (
    calculate_average_electronegativity,
    calculate_valence_electron_concentration,
    calculate_atomic_radii_variance,
    calculate_average_d_electrons,
    calculate_atomic_size_mismatch,
    compute_descriptors_row,
    calculate_all_descriptors,
    load_elemental_properties
)


@pytest.fixture
def mock_properties():
    """Mock properties dictionary for testing."""
    return {
        'Co': {
            'electronegativity': 1.88,
            'atomic_radii': 125.0,
            'valence_electrons': 9,
            'd_electrons': 7
        },
        'Mn': {
            'electronegativity': 1.55,
            'atomic_radii': 127.0,
            'valence_electrons': 7,
            'd_electrons': 5
        },
        'Ga': {
            'electronegativity': 1.81,
            'atomic_radii': 135.0,
            'valence_electrons': 3,
            'd_electrons': 10
        },
        'Fe': {
            'electronegativity': 1.83,
            'atomic_radii': 126.0,
            'valence_electrons': 8,
            'd_electrons': 6
        },
        'Al': {
            'electronegativity': 1.61,
            'atomic_radii': 143.0,
            'valence_electrons': 3,
            'd_electrons': 0
        }
    }


def test_calculate_average_electronegativity(mock_properties):
    """Test average electronegativity calculation for Co2MnGa."""
    # Co2MnGa -> Co: 0.5, Mn: 0.25, Ga: 0.25
    composition = {'Co': 0.5, 'Mn': 0.25, 'Ga': 0.25}
    expected = (1.88 * 0.5) + (1.55 * 0.25) + (1.81 * 0.25)
    
    result = calculate_average_electronegativity(composition, mock_properties)
    assert np.isclose(result, expected, rtol=1e-5)


def test_calculate_valence_electron_concentration(mock_properties):
    """Test VEC calculation for Co2MnGa."""
    # Co: 9, Mn: 7, Ga: 3
    composition = {'Co': 0.5, 'Mn': 0.25, 'Ga': 0.25}
    expected = (9 * 0.5) + (7 * 0.25) + (3 * 0.25)
    
    result = calculate_valence_electron_concentration(composition, mock_properties)
    assert np.isclose(result, expected, rtol=1e-5)


def test_calculate_atomic_radii_variance(mock_properties):
    """Test atomic radii variance calculation."""
    # Co: 125, Mn: 127, Ga: 135
    composition = {'Co': 0.5, 'Mn': 0.25, 'Ga': 0.25}
    radii = np.array([125.0, 127.0, 135.0])
    weights = np.array([0.5, 0.25, 0.25])
    mean_r = np.average(radii, weights=weights)
    expected_var = np.average((radii - mean_r) ** 2, weights=weights)
    
    result = calculate_atomic_radii_variance(composition, mock_properties)
    assert np.isclose(result, expected_var, rtol=1e-5)


def test_calculate_average_d_electrons(mock_properties):
    """Test average d-electrons calculation."""
    # Co: 7, Mn: 5, Ga: 10
    composition = {'Co': 0.5, 'Mn': 0.25, 'Ga': 0.25}
    expected = (7 * 0.5) + (5 * 0.25) + (10 * 0.25)
    
    result = calculate_average_d_electrons(composition, mock_properties)
    assert np.isclose(result, expected, rtol=1e-5)


def test_calculate_atomic_size_mismatch(mock_properties):
    """Test atomic size mismatch (delta) calculation."""
    composition = {'Co': 0.5, 'Mn': 0.25, 'Ga': 0.25}
    
    # Manual calculation
    radii = np.array([125.0, 127.0, 135.0])
    weights = np.array([0.5, 0.25, 0.25])
    mean_r = np.average(radii, weights=weights)
    terms = weights * (1 - (radii / mean_r)) ** 2
    expected_delta = np.sqrt(np.sum(terms))
    
    result = calculate_atomic_size_mismatch(composition, mock_properties)
    assert np.isclose(result, expected_delta, rtol=1e-5)


def test_compute_descriptors_row(mock_properties):
    """Test full row descriptor computation."""
    row_data = {
        'composition_fractions': "{'Co': 0.5, 'Mn': 0.25, 'Ga': 0.25}",
        'coercivity': 10.0,
        'saturation_magnetization': 800.0
    }
    row = pd.Series(row_data)
    
    result = compute_descriptors_row(row, mock_properties)
    
    assert 'avg_electronegativity' in result
    assert 'vec' in result
    assert 'atomic_radii_variance' in result
    assert 'avg_d_electrons' in result
    assert 'atomic_size_mismatch' in result
    
    assert not np.isnan(result['vec'])
    assert result['vec'] > 0


def test_calculate_all_descriptors(mock_properties):
    """Test batch descriptor calculation."""
    df = pd.DataFrame([
        {'composition_fractions': "{'Co': 0.5, 'Mn': 0.25, 'Ga': 0.25}", 'coercivity': 10.0},
        {'composition_fractions': "{'Fe': 0.5, 'Co': 0.25, 'Ga': 0.25}", 'coercivity': 20.0}
    ])
    
    result = calculate_all_descriptors(df, mock_properties)
    
    assert 'vec' in result.columns
    assert len(result) == 2
    assert not result['vec'].isna().all()


def test_missing_element_handling(mock_properties):
    """Test behavior when an element is missing from properties."""
    composition = {'Co': 0.5, 'UnknownElement': 0.5}
    
    result = calculate_average_electronegativity(composition, mock_properties)
    assert np.isnan(result)


def test_empty_composition(mock_properties):
    """Test behavior with empty composition."""
    composition = {}
    
    result = calculate_average_electronegativity(composition, mock_properties)
    assert result == 0.0
    
    result = calculate_valence_electron_concentration(composition, mock_properties)
    assert result == 0.0
    
    result = calculate_atomic_radii_variance(composition, mock_properties)
    assert np.isnan(result)
    
    result = calculate_atomic_size_mismatch(composition, mock_properties)
    assert np.isnan(result)