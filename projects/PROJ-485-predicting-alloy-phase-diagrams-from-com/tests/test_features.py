import os
import csv
import tempfile
import pytest
from utils.error_codes import ErrorCode
from features.generate_descriptors import load_elemental_properties, calculate_mean_atomic_radius, calculate_electronegativity_variance, calculate_valence_electron_count, calculate_hume_rothery_concentration
from features.verify_elements import verify_element, verify_elemental_properties, load_csv_data

# Test data that exactly matches NIST reference (0% deviation)
VALID_CSV_CONTENT = """element,atomic_radius_angstrom,electronegativity_pauling,valence_electrons
Cu,1.28,1.90,1
Al,1.43,1.61,3
Zn,1.34,1.65,2
Fe,1.26,1.83,2
C,0.77,2.55,4
"""

# Test data with >1% deviation in atomic radius for Cu
INVALID_CSV_CONTENT = """element,atomic_radius_angstrom,electronegativity_pauling,valence_electrons
Cu,1.35,1.90,1
Al,1.43,1.61,3
Zn,1.34,1.65,2
Fe,1.26,1.83,2
C,0.77,2.55,4
"""

# Mock NIST reference data for testing deviation logic
MOCK_NIST_REFERENCE = {
    "Cu": {"atomic_radius_angstrom": 1.28, "electronegativity_pauling": 1.90, "valence_electrons": 1},
    "Al": {"atomic_radius_angstrom": 1.43, "electronegativity_pauling": 1.61, "valence_electrons": 3},
    "Zn": {"atomic_radius_angstrom": 1.34, "electronegativity_pauling": 1.65, "valence_electrons": 2},
    "Fe": {"atomic_radius_angstrom": 1.26, "electronegativity_pauling": 1.83, "valence_electrons": 2},
    "C": {"atomic_radius_angstrom": 0.77, "electronegativity_pauling": 2.55, "valence_electrons": 4},
}

def test_descriptor_deviation():
    """
    Assert derived values deviate <=1% from data/raw/elemental_properties.csv.
    This test verifies the verification logic itself by checking if the
    verify_elemental_properties function correctly identifies valid and invalid data.
    """
    # Test valid data (should pass)
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        f.write(VALID_CSV_CONTENT)
        temp_path = f.name

    try:
        # Verify the valid file passes
        result = verify_elemental_properties(temp_path)
        assert result is True, "Valid CSV should pass verification"
    finally:
        os.unlink(temp_path)

    # Test invalid data (should fail due to >1% deviation in Cu radius)
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        f.write(INVALID_CSV_CONTENT)
        temp_path = f.name

    try:
        # Verify the invalid file fails
        result = verify_elemental_properties(temp_path)
        assert result is False, "Invalid CSV (deviation > 1%) should fail verification"
    finally:
        os.unlink(temp_path)

def test_verify_element_function():
    """Test the helper function for deviation calculation."""
    # Exact match
    valid, dev = verify_element(1.28, 1.28)
    assert valid is True
    assert dev == 0.0

    # 0.5% deviation
    valid, dev = verify_element(1.2864, 1.28) # 0.5%
    assert valid is True
    assert 0.4 < dev < 0.6

    # 1.0% deviation (boundary - should pass)
    valid, dev = verify_element(1.2928, 1.28) # 1.0%
    assert valid is True
    
    # 1.1% deviation (failure)
    valid, dev = verify_element(1.2941, 1.28) # ~1.1%
    assert valid is False
    assert dev > 1.0

def test_missing_element():
    """Test that missing elements are caught."""
    content = """element,atomic_radius_angstrom,electronegativity_pauling,valence_electrons
    Cu,1.28,1.90,1
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        f.write(content)
        temp_path = f.name

    try:
        result = verify_elemental_properties(temp_path)
        assert result is False, "Missing elements should cause failure"
    finally:
        os.unlink(temp_path)

def test_calculate_mean_atomic_radius_accuracy():
    """Test that mean atomic radius calculation is accurate and within tolerance."""
    # Load the reference properties
    props = load_elemental_properties("data/raw/elemental_properties.csv")
    
    # Calculate mean for a known alloy: Cu50Al50
    # Expected mean = (1.28 + 1.43) / 2 = 1.355
    cu_al_mean = calculate_mean_atomic_radius(props, ["Cu", "Al"], [0.5, 0.5])
    expected_mean = 1.355
    
    # Check deviation is within 1%
    deviation = abs(cu_al_mean - expected_mean) / expected_mean * 100
    assert deviation <= 1.0, f"Mean atomic radius deviation {deviation}% exceeds 1% threshold"
    assert abs(cu_al_mean - expected_mean) < 0.014

def test_calculate_electronegativity_variance_accuracy():
    """Test that electronegativity variance calculation is accurate."""
    props = load_elemental_properties("data/raw/elemental_properties.csv")
    
    # Cu (1.90) and Al (1.61)
    # Mean = 1.755
    # Variance = ((1.90-1.755)^2 + (1.61-1.755)^2) / 2 = (0.021025 + 0.021025) / 2 = 0.021025
    cu_al_var = calculate_electronegativity_variance(props, ["Cu", "Al"], [0.5, 0.5])
    expected_var = 0.021025
    
    deviation = abs(cu_al_var - expected_var) / expected_var * 100 if expected_var > 0 else 0
    assert deviation <= 1.0, f"Electronegativity variance deviation {deviation}% exceeds 1% threshold"
    assert abs(cu_al_var - expected_var) < 0.0003

def test_calculate_valence_electron_count_accuracy():
    """Test that valence electron count calculation is accurate."""
    props = load_elemental_properties("data/raw/elemental_properties.csv")
    
    # Cu (1) and Al (3) with 50/50 mix
    # Expected = 0.5*1 + 0.5*3 = 2.0
    cu_al_vec = calculate_valence_electron_count(props, ["Cu", "Al"], [0.5, 0.5])
    expected_vec = 2.0
    
    deviation = abs(cu_al_vec - expected_vec) / expected_vec * 100 if expected_vec > 0 else 0
    assert deviation <= 1.0, f"Valence electron count deviation {deviation}% exceeds 1% threshold"
    assert abs(cu_al_vec - expected_vec) < 0.02

def test_calculate_hume_rothery_concentration_accuracy():
    """Test that Hume-Rothery concentration calculation is accurate."""
    props = load_elemental_properties("data/raw/elemental_properties.csv")
    
    # Cu (1) and Zn (2) with 50/50 mix
    # Expected = 0.5*1 + 0.5*2 = 1.5
    cu_zn_hr = calculate_hume_rothery_concentration(props, ["Cu", "Zn"], [0.5, 0.5])
    expected_hr = 1.5
    
    deviation = abs(cu_zn_hr - expected_hr) / expected_hr * 100 if expected_hr > 0 else 0
    assert deviation <= 1.0, f"Hume-Rothery concentration deviation {deviation}% exceeds 1% threshold"
    assert abs(cu_zn_hr - expected_hr) < 0.015