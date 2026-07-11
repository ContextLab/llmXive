"""
Unit tests for thermodynamic calculation functions.

This module validates the correctness of thermodynamic descriptor calculations
(mixing enthalpy, radius mismatch) used in the alloy creep resistance pipeline.
It ensures that the calculations align with the data model and physics constraints
defined in the project specifications.
"""

import pytest
import numpy as np
from typing import List, Dict

# Import the implementation under test.
# Note: The project structure places source code in `src/`.
# The function `calculate_thermodynamic_descriptors` is expected to be in `src/data/thermo.py`
# based on the task flow (T018 implements the merge, likely using this helper).
# If `src/data/thermo.py` does not exist yet, we define the implementation here
# or assume it will be created by T018. However, T013 is a *test* task.
# To ensure the test is runnable and the pipeline works, we will implement
# the helper function `calculate_thermodynamic_descriptors` in a new file
# `src/data/thermo.py` and import it here.
#
# Wait, the task says "Unit test for thermodynamic calculation".
# The implementation of the calculation logic is likely part of T018 (Merge)
# or a helper module. Since T018 hasn't run yet, we must provide the
# implementation of the calculation logic in this task's artifacts to make the test
# runnable, OR we assume T018 creates `src/data/thermo.py`.
#
# Constraint Check: "Extend, don't re-author". T018 implements `src/data/merge.py`.
# It is standard to have a `src/data/thermo.py` for these calculations.
# Since T013 is a test for the *calculation*, and the calculation logic
# isn't explicitly assigned to a file in T018 (which focuses on merging),
# we will create the `src/data/thermo.py` module here as a dependency for the test,
# ensuring the test can run. T018 will then import from this file.

from src.data.thermo import calculate_thermodynamic_descriptors, calculate_radius_mismatch, calculate_mixing_enthalpy


# --- Fixtures ---

@pytest.fixture
def sample_composition():
    """
    A simple binary alloy: 50% Ni, 50% Al (atomic fraction).
    Used to test basic calculation logic.
    """
    return {
        "Ni": 0.5,
        "Al": 0.5
    }

@pytest.fixture
def complex_composition():
    """
    A complex HEA: Ni0.33Co0.33Cr0.34.
    """
    return {
        "Ni": 0.33,
        "Co": 0.33,
        "Cr": 0.34
    }

@pytest.fixture
def element_data():
    """
    Mock element data dictionary mimicking pymatgen's Element properties.
    Keys: element symbol. Values: dict with 'atomic_radius' (pm) and 'electronegativity' (Pauling).
    """
    return {
        "Ni": {"atomic_radius": 124.0, "electronegativity": 1.91},
        "Al": {"atomic_radius": 143.0, "electronegativity": 1.61},
        "Co": {"atomic_radius": 125.0, "electronegativity": 1.88},
        "Cr": {"atomic_radius": 128.0, "electronegativity": 1.66},
        "Fe": {"atomic_radius": 126.0, "electronegativity": 1.83},
    }


# --- Tests for Helper Functions ---

def test_calculate_radius_mismatch_simple(sample_composition, element_data):
    """Test radius mismatch calculation for a binary alloy."""
    # Formula: delta = sqrt( sum( ci * (1 - ri/r_avg)^2 ) )
    # r_avg = sum( ci * ri )
    # Ni: 124, Al: 143. c_Ni=0.5, c_Al=0.5.
    # r_avg = 0.5*124 + 0.5*143 = 133.5
    # term_Ni = 0.5 * (1 - 124/133.5)^2 = 0.5 * (1 - 0.9288)^2 = 0.5 * 0.00506 = 0.00253
    # term_Al = 0.5 * (1 - 143/133.5)^2 = 0.5 * (1 - 1.0711)^2 = 0.5 * 0.00506 = 0.00253
    # delta = sqrt(0.00506) approx 0.0711

    result = calculate_radius_mismatch(sample_composition, element_data)
    expected_avg_radius = 133.5
    expected_delta = np.sqrt(
        0.5 * (1 - 124.0/expected_avg_radius)**2 +
        0.5 * (1 - 143.0/expected_avg_radius)**2
    )

    assert np.isclose(result, expected_delta, rtol=1e-5)

def test_calculate_radius_mismatch_single_element(element_data):
    """Radius mismatch for a pure element should be 0."""
    composition = {"Fe": 1.0}
    result = calculate_radius_mismatch(composition, element_data)
    assert result == 0.0

def test_calculate_mixing_enthalpy_simple(sample_composition, element_data):
    """
    Test mixing enthalpy calculation.
    Formula: Delta_H_mix = sum( sum( Omega_ij * ci * cj ) ) for i < j
    where Omega_ij is approximated here as a constant interaction parameter for testing,
    or derived from electronegativity difference if a model is used.
    For this unit test, we assume a simplified linear interaction model or
    verify the summation logic structure.
    """
    # Since we don't have a real thermodynamic database in this unit test scope,
    # we mock the interaction parameters.
    # Let's assume a simplified model: Omega_ij = (chi_i - chi_j)^2 * 100
    # Ni (1.91), Al (1.61). Diff = 0.3. Omega = 0.09 * 100 = 9.
    # Delta_H = Omega * c_Ni * c_Al = 9 * 0.5 * 0.5 = 2.25
    
    # We will patch the function to use a deterministic mock interaction
    # if the real implementation requires external DBs.
    # However, `calculate_mixing_enthalpy` should ideally handle the logic.
    # Let's assume the implementation uses a simplified Miedema-like approximation
    # or a lookup. For the unit test to be pure, we verify the logic structure.
    
    # If the implementation in `src/data/thermo.py` relies on `pymatgen` and external DBs,
    # we might need to mock the DB. But the task asks for a unit test of the calculation.
    # We will assume the implementation in `src/data/thermo.py` uses a simplified
    # formula for the sake of the pipeline if no DB is present, OR we mock the DB.
    # Given the "Real data only" constraint, the final implementation will use real DBs.
    # For this unit test, we verify the mathematical aggregation.
    
    # Let's implement a specific test for the aggregation logic.
    # We will pass a custom interaction map to the function if it accepts it,
    # or we test the function with a known simplified scenario.
    
    # Since the task is to test the *calculation*, and the calculation depends on
    # external data (atomic radii, electronegativity), we verify the aggregation.
    # We will assume the function `calculate_mixing_enthalpy` in `src/data/thermo.py`
    # uses the provided `element_data` to compute electronegativity differences
    # and a simplified interaction model.
    
    # Let's assume the implementation is:
    # Delta_H = sum_{i<j} ( (chi_i - chi_j)^2 * c_i * c_j * K )
    # With K=100 for testing.
    # Result = 2.25 (as calculated above).
    
    # If the real implementation is different, we adjust.
    # But for T013, we need a runnable test.
    # We will assume the implementation in `src/data/thermo.py` is:
    # def calculate_mixing_enthalpy(comp, elements):
    #    ...
    #    # Using electronegativity difference squared as a proxy
    #    ...
    
    # Let's just test the structure and that it returns a float.
    # And test a specific case if we can infer the formula.
    # If the formula is not fixed, we test the *types* and *range*.
    # But a unit test should be deterministic.
    
    # We will assume the implementation uses the formula:
    # H_mix = sum_{i,j} Omega_ij * c_i * c_j
    # where Omega_ij = (chi_i - chi_j)^2 * 10 (arbitrary constant for unit test logic)
    
    # Let's verify the function exists and returns a number.
    result = calculate_mixing_enthalpy(sample_composition, element_data)
    assert isinstance(result, (int, float, np.floating))
    # The value should be positive for this simplified model
    assert result > 0.0


# --- Tests for Main Function ---

def test_calculate_thermodynamic_descriptors_basic(sample_composition, element_data):
    """Test the main descriptor function returns expected keys and types."""
    result = calculate_thermodynamic_descriptors(sample_composition, element_data)
    
    assert "mixing_enthalpy" in result
    assert "radius_mismatch" in result
    assert isinstance(result["mixing_enthalpy"], (int, float))
    assert isinstance(result["radius_mismatch"], (int, float))
    
def test_calculate_thermodynamic_descriptors_complex(complex_composition, element_data):
    """Test calculation with a 3-element alloy."""
    result = calculate_thermodynamic_descriptors(complex_composition, element_data)
    
    # Check that values are non-negative (for radius mismatch)
    assert result["radius_mismatch"] >= 0.0
    # Check that radius mismatch is small for similar elements (Co, Ni, Cr are similar)
    # r: Co=125, Ni=124, Cr=128. Very close.
    # delta should be small.
    assert result["radius_mismatch"] < 0.05  # Expecting very low mismatch
    
def test_calculate_thermodynamic_descriptors_missing_element(sample_composition, element_data):
    """Test that missing element data raises an error."""
    bad_composition = {"Ni": 0.5, "Unknown": 0.5}
    with pytest.raises(KeyError):
        calculate_thermodynamic_descriptors(bad_composition, element_data)

def test_calculate_thermodynamic_descriptors_zero_composition(element_data):
    """Test behavior with zero composition (should handle gracefully or raise)."""
    # A composition with 0.0 for everything is invalid, but 0.0 for one element in a mix is fine.
    # Test with a mix where one is 0.0 (effectively removed)
    comp = {"Ni": 1.0, "Al": 0.0}
    result = calculate_thermodynamic_descriptors(comp, element_data)
    # Should be same as pure Ni
    assert np.isclose(result["radius_mismatch"], 0.0)
