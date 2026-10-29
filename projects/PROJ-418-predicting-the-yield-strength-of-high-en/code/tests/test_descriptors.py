"""
Unit tests for the descriptor calculation module.
"""

import pytest
import pandas as pd
import numpy as np

# Import the functions under test
from data.descriptors import (
    calculate_descriptors,
    calculate_single_composition_descriptors,
    get_elemental_properties,
)

@pytest.fixture
def sample_dataframe():
    """Create a minimal DataFrame with a single known composition."""
    return pd.DataFrame({
        "alloy_id": ["test1"],
        "composition": ["CoCrFeMnNi"]
    })

def test_get_elemental_properties_uses_csv():
    """The CSV file should be loaded and contain the expected keys."""
    props = get_elemental_properties()
    # The CSV we provided contains these elements
    for elem in ["Co", "Cr", "Fe", "Mn", "Ni"]:
        assert elem in props
        assert "radius" in props[elem]
        assert "electronegativity" in props[elem]
        assert "valence" in props[elem]

def test_calculate_single_composition_descriptors_known_values():
    """Check that descriptor values for CoCrFeMnNi are within expected tolerances."""
    # Build a single-row DataFrame
    df = pd.DataFrame({
        "alloy_id": ["test1"],
        "composition": ["CoCrFeMnNi"]
    })
    # Use the public function that processes a whole DataFrame
    result_df = calculate_descriptors(df)
    row = result_df.iloc[0]

    # Expected values (computed from the data in elemental_properties.csv)
    # These are reference values; we allow a small tolerance because of floating‑point rounding.
    # Mixing entropy: -R * Σ c_i ln(c_i) with c_i = 0.2 for each of 5 elements
    R = 8.314
    expected_entropy = -R * 5 * 0.2 * np.log(0.2)
    assert np.isclose(row["mixing_entropy"], expected_entropy, rtol=1e-6)

    # Atomic size mismatch (δ)
    radii = np.array([125, 128, 126, 127, 124])  # Co, Cr, Fe, Mn, Ni
    fractions = np.full(5, 0.2)
    r_bar = np.sum(radii * fractions)
    delta_sq = np.sum(fractions * (1 - radii / r_bar) ** 2)
    expected_delta = 100.0 * np.sqrt(delta_sq)
    assert np.isclose(row["atomic_size_mismatch"], expected_delta, rtol=1e-6)

    # Electronegativity variance (Δχ)
    chis = np.array([1.88, 1.66, 1.83, 1.55, 1.91])
    chi_bar = np.sum(chis * fractions)
    expected_delta_chi = np.sqrt(np.sum(fractions * (chis - chi_bar) ** 2))
    assert np.isclose(row["electronegativity_variance"], expected_delta_chi, rtol=1e-6)

    # Valence electron concentration (VEC)
    vals = np.array([9, 6, 8, 7, 10])
    expected_vec = np.sum(vals * fractions)
    assert np.isclose(row["vec"], expected_vec, rtol=1e-6)

    # Melting‑point variance (tm_variance)
    # All five elements have melting points in the CSV
    tms = np.array([1768, 1907, 1811, 1246, 1728])
    tm_bar = np.sum(tms * fractions)
    expected_tm_var = np.sqrt(np.sum(fractions * (tms - tm_bar) ** 2))
    assert np.isclose(row["tm_variance"], expected_tm_var, rtol=1e-6)

def test_missing_element_raises_key_error():
    """A composition containing an unknown element should raise KeyError."""
    df = pd.DataFrame({
        "alloy_id": ["bad1"],
        "composition": ["XyZ"]
    })
    with pytest.raises(KeyError):
        # The function iterates over rows and will raise when the element is unknown
        calculate_descriptors(df)

def test_descriptor_columns_present():
    """All descriptor columns defined in the schema must be present."""
    df = pd.DataFrame({
        "alloy_id": ["test1"],
        "composition": ["CoCrFeMnNi"]
    })
    result_df = calculate_descriptors(df)
    for col in [
        "mixing_entropy",
        "atomic_size_mismatch",
        "electronegativity_variance",
        "vec",
        "tm_variance",
    ]:
        assert col in result_df.columns
