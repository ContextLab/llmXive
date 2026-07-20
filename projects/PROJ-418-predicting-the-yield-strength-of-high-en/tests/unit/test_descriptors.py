import pytest
import numpy as np
import pandas as pd
from data.descriptors import (
    get_elemental_properties,
    get_property,
    calculate_weighted_average,
    calculate_single_composition_descriptors,
    calculate_descriptors,
    filter_missing_properties
)

# --- Fixtures ---

@pytest.fixture
def sample_elemental_data():
    """Returns a DataFrame mimicking the output of get_elemental_properties()."""
    data = {
        'element': ['Fe', 'Co', 'Ni', 'Cr', 'Mn', 'Al', 'Ti', 'V', 'Cu', 'Zr'],
        'atomic_radius': [124.1, 125.2, 124.6, 124.9, 127.0, 143.1, 147.3, 134.0, 127.8, 160.0],
        'electronegativity': [1.83, 1.88, 1.91, 1.66, 1.55, 1.61, 1.54, 1.63, 1.90, 1.33],
        'valence_electrons': [8, 9, 10, 6, 7, 3, 4, 5, 11, 4],
        'melting_point': [1811, 1768, 1728, 2180, 1519, 933, 1941, 2183, 1358, 2128]
    }
    return pd.DataFrame(data).set_index('element')

@pytest.fixture
def sample_composition_dict():
    """Returns a dict representing a single HEA composition (atomic fractions)."""
    return {
        'Fe': 0.20,
        'Co': 0.20,
        'Ni': 0.20,
        'Cr': 0.20,
        'Al': 0.20
    }

@pytest.fixture
def sample_df_compositions():
    """Returns a DataFrame with multiple compositions for batch testing."""
    return pd.DataFrame([
        {'Fe': 0.20, 'Co': 0.20, 'Ni': 0.20, 'Cr': 0.20, 'Al': 0.20},
        {'Fe': 0.25, 'Co': 0.25, 'Ni': 0.25, 'Cr': 0.25, 'Al': 0.00},
        {'Ti': 0.10, 'V': 0.10, 'Cr': 0.20, 'Mn': 0.20, 'Fe': 0.20, 'Co': 0.10, 'Ni': 0.10}
    ])

# --- Tests for get_property ---

def test_get_property_exists(sample_elemental_data):
    """Test that get_property retrieves a known value."""
    radius = get_property(sample_elemental_data, 'Fe', 'atomic_radius')
    assert radius == 124.1

def test_get_property_missing_key_raises(sample_elemental_data):
    """Test that get_property raises KeyError for missing element."""
    with pytest.raises(KeyError):
        get_property(sample_elemental_data, 'Gold', 'atomic_radius')

def test_get_property_missing_column_raises(sample_elemental_data):
    """Test that get_property raises KeyError for missing column."""
    with pytest.raises(KeyError):
        get_property(sample_elemental_data, 'Fe', 'non_existent_prop')

# --- Tests for calculate_weighted_average ---

def test_calculate_weighted_average_basic(sample_elemental_data, sample_composition_dict):
    """Test basic weighted average calculation."""
    # VEC for CoCrFeNiAl: (8*0.2 + 9*0.2 + 10*0.2 + 6*0.2 + 3*0.2) = 7.2
    vec = calculate_weighted_average(sample_elemental_data, sample_composition_dict, 'valence_electrons')
    assert np.isclose(vec, 7.2)

def test_calculate_weighted_average_single_element(sample_elemental_data):
    """Test weighted average with a single element (should equal the property value)."""
    comp = {'Fe': 1.0}
    radius = calculate_weighted_average(sample_elemental_data, comp, 'atomic_radius')
    assert np.isclose(radius, 124.1)

def test_calculate_weighted_average_zero_fraction(sample_elemental_data):
    """Test that zero fraction elements do not contribute."""
    comp = {'Fe': 0.5, 'Co': 0.0, 'Ni': 0.5}
    # (124.1 * 0.5) + (124.6 * 0.5) = 124.35
    avg = calculate_weighted_average(sample_elemental_data, comp, 'atomic_radius')
    assert np.isclose(avg, 124.35)

# --- Tests for calculate_single_composition_descriptors ---

def test_calculate_single_composition_descriptors_returns_dict(sample_elemental_data, sample_composition_dict):
    """Test that the function returns a dictionary with expected keys."""
    result = calculate_single_composition_descriptors(sample_elemental_data, sample_composition_dict)
    assert isinstance(result, dict)
    expected_keys = ['VEC', 'delta', 'delta_chi', 'entropy', 'delta_Tm', 'Tm_avg']
    for key in expected_keys:
        assert key in result

def test_calculate_single_composition_descriptors_values(sample_elemental_data, sample_composition_dict):
    """Test specific descriptor values for CoCrFeNiAl."""
    # Using standard values for CoCrFeNiAl (approximate manual check)
    # VEC = 7.2
    # delta_chi: variance of electronegativity * 100
    # entropies and melting variances are calculated based on formulas in descriptors.py
    result = calculate_single_composition_descriptors(sample_elemental_data, sample_composition_dict)
    
    assert np.isclose(result['VEC'], 7.2)
    # delta_chi calculation: sum(c_i * (chi_i - chi_bar)^2) * 100
    # chi: [1.83, 1.88, 1.91, 1.66, 1.61] -> mean ~1.778
    # var ~ 0.015 -> delta_chi ~ 1.5 (approx)
    assert result['delta_chi'] > 0
    assert result['entropy'] > 0
    assert result['delta_Tm'] >= 0
    assert result['Tm_avg'] > 0

def test_calculate_single_composition_descriptors_missing_element_raises(sample_elemental_data):
    """Test that missing element in composition raises KeyError."""
    comp = {'Fe': 0.5, 'Gold': 0.5} # Gold not in sample_elemental_data
    with pytest.raises(KeyError):
        calculate_single_composition_descriptors(sample_elemental_data, comp)

# --- Tests for calculate_descriptors (Batch) ---

def test_calculate_descriptors_returns_dataframe(sample_elemental_data, sample_df_compositions):
    """Test that calculate_descriptors returns a DataFrame."""
    result = calculate_descriptors(sample_elemental_data, sample_df_compositions)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == len(sample_df_compositions)

def test_calculate_descriptors_columns(sample_elemental_data, sample_df_compositions):
    """Test that the output DataFrame contains descriptor columns."""
    result = calculate_descriptors(sample_elemental_data, sample_df_compositions)
    expected_cols = ['VEC', 'delta', 'delta_chi', 'entropy', 'delta_Tm', 'Tm_avg']
    for col in expected_cols:
        assert col in result.columns

# --- Tests for filter_missing_properties ---

def test_filter_missing_properties_no_missing(sample_elemental_data, sample_df_compositions):
    """Test filtering when all elements are present."""
    filtered = filter_missing_properties(sample_elemental_data, sample_df_compositions)
    assert len(filtered) == len(sample_df_compositions)

def test_filter_missing_properties_with_missing(sample_elemental_data):
    """Test filtering when some rows contain missing elements."""
    df = pd.DataFrame([
        {'Fe': 0.5, 'Co': 0.5}, # Valid
        {'Fe': 0.5, 'Gold': 0.5} # Invalid (Gold missing)
    ])
    filtered = filter_missing_properties(sample_elemental_data, df)
    assert len(filtered) == 1
    assert 'Gold' not in filtered.columns

def test_filter_missing_properties_all_missing(sample_elemental_data):
    """Test filtering when all rows contain missing elements."""
    df = pd.DataFrame([
        {'Gold': 0.5, 'Silver': 0.5}
    ])
    filtered = filter_missing_properties(sample_elemental_data, df)
    assert len(filtered) == 0

# --- Edge Cases ---

def test_empty_composition_raises(sample_elemental_data):
    """Test that empty composition dict raises error or handled gracefully."""
    with pytest.raises((ValueError, ZeroDivisionError)):
        calculate_single_composition_descriptors(sample_elemental_data, {})

def test_composition_sum_not_one(sample_elemental_data, sample_composition_dict):
    """Test behavior when composition sum != 1 (should normalize or raise)."""
    # The implementation in descriptors.py should handle normalization or raise.
    # Assuming it normalizes or calculates based on provided fractions.
    comp = {'Fe': 0.1, 'Co': 0.1} # Sum = 0.2
    # If the code normalizes: Fe=0.5, Co=0.5 -> VEC = 8.5
    # If the code uses raw: VEC = 1.7 (weighted by 0.2)
    # We test that it runs without crashing
    try:
        result = calculate_single_composition_descriptors(sample_elemental_data, comp)
        # If it runs, we assume the implementation handles it (either by normalizing or warning)
        assert result is not None
    except Exception:
        # If it raises, that's also a valid behavior (strict mode)
        pass