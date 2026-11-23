"""
tests/unit/test_descriptors.py

Unit tests for features/descriptors.py.
Verifies formula correctness for specific descriptors.
"""
import pytest
import numpy as np
import pandas as pd
from features.descriptors import (
    parse_composition,
    compute_atomic_radius,
    compute_electronegativity,
    compute_valence_electron_concentration,
    compute_atomic_size_mismatch,
    compute_electronegativity_difference,
    compute_mixing_enthalpy,
    compute_all_descriptors,
    apply_descriptors_to_dataframe,
    ELEMENT_PROPERTIES
)

# --- Test Data ---
# Simple binary alloy: Zr50Cu50
# Zr: R=160, chi=1.33, val=4
# Cu: R=128, chi=1.90, val=11
# Expected R_bar = 0.5*160 + 0.5*128 = 144
# Expected chi_bar = 0.5*1.33 + 0.5*1.90 = 1.615
# Expected e/a = 0.5*4 + 0.5*11 = 7.5

SIMPLE_BINARY = "Zr50Cu50"
SIMPLE_BINARY_DICT = {"Zr": 0.5, "Cu": 0.5}

# Ternary: Zr60Cu30Al10
# Zr: R=160, chi=1.33, val=4
# Cu: R=128, chi=1.90, val=11
# Al: R=143, chi=1.61, val=3
# R_bar = 0.6*160 + 0.3*128 + 0.1*143 = 96 + 38.4 + 14.3 = 148.7
# chi_bar = 0.6*1.33 + 0.3*1.90 + 0.1*1.61 = 0.798 + 0.57 + 0.161 = 1.529
# e/a = 0.6*4 + 0.3*11 + 0.1*3 = 2.4 + 3.3 + 0.3 = 6.0
TERNARY = "Zr60Cu30Al10"
TERNARY_DICT = {"Zr": 0.6, "Cu": 0.3, "Al": 0.1}

def test_parse_composition_simple():
    """Test parsing of simple binary composition."""
    result = parse_composition(SIMPLE_BINARY)
    assert abs(result["Zr"] - 0.5) < 1e-6
    assert abs(result["Cu"] - 0.5) < 1e-6
    assert len(result) == 2

def test_parse_composition_ternary():
    """Test parsing of ternary composition."""
    result = parse_composition(TERNARY)
    assert abs(result["Zr"] - 0.6) < 1e-6
    assert abs(result["Cu"] - 0.3) < 1e-6
    assert abs(result["Al"] - 0.1) < 1e-6

def test_parse_composition_invalid():
    """Test parsing of invalid composition."""
    with pytest.raises(ValueError):
        parse_composition("InvalidString")
    with pytest.raises(ValueError):
        parse_composition("Zr50Unknown50")

def test_compute_atomic_radius():
    """Test atomic radius calculation."""
    # Binary: 0.5*160 + 0.5*128 = 144
    r = compute_atomic_radius(SIMPLE_BINARY_DICT)
    assert abs(r - 144.0) < 1e-6

    # Ternary: 148.7
    r = compute_atomic_radius(TERNARY_DICT)
    assert abs(r - 148.7) < 1e-6

def test_compute_electronegativity():
    """Test electronegativity calculation."""
    # Binary: 1.615
    chi = compute_electronegativity(SIMPLE_BINARY_DICT)
    assert abs(chi - 1.615) < 1e-6

    # Ternary: 1.529
    chi = compute_electronegativity(TERNARY_DICT)
    assert abs(chi - 1.529) < 1e-6

def test_compute_valence_electron_concentration():
    """Test valence electron concentration calculation."""
    # Binary: 7.5
    v = compute_valence_electron_concentration(SIMPLE_BINARY_DICT)
    assert abs(v - 7.5) < 1e-6

    # Ternary: 6.0
    v = compute_valence_electron_concentration(TERNARY_DICT)
    assert abs(v - 6.0) < 1e-6

def test_compute_atomic_size_mismatch():
    """Test atomic size mismatch calculation."""
    # Binary:
    # R_bar = 144
    # Zr: (1 - 160/144)^2 = (1 - 1.111)^2 = (-0.111)^2 = 0.0123
    # Cu: (1 - 128/144)^2 = (1 - 0.888)^2 = (0.111)^2 = 0.0123
    # Sum = 0.5 * 0.0123 + 0.5 * 0.0123 = 0.0123
    # sqrt = 0.111
    # delta = 11.1%
    delta = compute_atomic_size_mismatch(SIMPLE_BINARY_DICT)
    assert delta > 0
    assert abs(delta - 11.11) < 0.5 # Approximate check

def test_compute_electronegativity_difference():
    """Test electronegativity difference calculation."""
    # Binary:
    # chi_bar = 1.615
    # Zr: (1.33 - 1.615)^2 = (-0.285)^2 = 0.0812
    # Cu: (1.90 - 1.615)^2 = (0.285)^2 = 0.0812
    # Sum = 0.5 * 0.0812 + 0.5 * 0.0812 = 0.0812
    # sqrt = 0.285
    delta_chi = compute_electronegativity_difference(SIMPLE_BINARY_DICT)
    assert abs(delta_chi - 0.285) < 1e-6

def test_compute_mixing_enthalpy():
    """Test mixing enthalpy calculation."""
    # Binary Zr-Cu:
    # Omega_Zr_Cu = -23.0 (from params)
    # H = Omega * c_Zr * c_Cu + Omega * c_Cu * c_Zr (since i!=j loop)
    # H = -23 * 0.5 * 0.5 + -23 * 0.5 * 0.5 = -5.75 + -5.75 = -11.5
    # Wait, the formula in code is sum_i sum_j (Omega_ij * c_i * c_j) for i != j
    # So it counts both (i,j) and (j,i).
    h = compute_mixing_enthalpy(SIMPLE_BINARY_DICT)
    assert h < 0
    # Expected: 2 * (-23.0 * 0.5 * 0.5) = -11.5
    assert abs(h - (-11.5)) < 1e-6

def test_compute_all_descriptors():
    """Test that all descriptors are computed correctly."""
    desc = compute_all_descriptors(SIMPLE_BINARY_DICT)
    assert "atomic_radius" in desc
    assert "electronegativity" in desc
    assert "valence_electron_concentration" in desc
    assert "atomic_size_mismatch" in desc
    assert "electronegativity_difference" in desc
    assert "mixing_enthalpy" in desc

    # Verify types
    for k, v in desc.items():
        assert isinstance(v, (int, float, np.floating))

def test_apply_descriptors_to_dataframe():
    """Test applying descriptors to a DataFrame."""
    data = {
        "composition": ["Zr50Cu50", "Zr60Cu30Al10", "Pd40Cu40P20"],
        "other_col": [1, 2, 3]
    }
    df = pd.DataFrame(data)
    result_df = apply_descriptors_to_dataframe(df, "composition")

    assert "atomic_radius" in result_df.columns
    assert "mixing_enthalpy" in result_df.columns
    assert len(result_df) == 3

def test_missing_element_raises_error():
    """Test that missing element data raises ValueError."""
    # Create a composition with an element not in our database (e.g., "X")
    # This should raise ValueError
    with pytest.raises(ValueError):
        parse_composition("X100")

def test_missing_property_raises_error():
    """Test that missing property (e.g., electronegativity) raises ValueError."""
    # He has None for electronegativity in our DB
    # This should raise ValueError when computing electronegativity
    with pytest.raises(ValueError):
        compute_electronegativity({"He": 1.0})