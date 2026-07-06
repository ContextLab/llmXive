import pytest
import numpy as np
import sys
import os
from utils.stoichiometry_parser import parse_formula, normalize_formula
from utils.periodic_data import get_atomic_radius, get_electronegativity, get_valence_electrons

def calculate_mean_atomic_radius(formula: str) -> float:
    """Calculate weighted mean atomic radius for a given formula."""
    parsed = parse_formula(formula)
    if not parsed:
        return np.nan
    
    total_atoms = sum(parsed.values())
    if total_atoms == 0:
        return np.nan
    
    weighted_sum = 0.0
    for element, count in parsed.items():
        radius = get_atomic_radius(element)
        if radius is None:
            return np.nan
        weighted_sum += radius * count
    
    return weighted_sum / total_atoms

def calculate_electronegativity_variance(formula: str) -> float:
    """Calculate variance of electronegativity for a given formula."""
    parsed = parse_formula(formula)
    if not parsed:
        return np.nan
    
    total_atoms = sum(parsed.values())
    if total_atoms == 0:
        return np.nan
    
    electronegativities = []
    for element, count in parsed.items():
        en = get_electronegativity(element)
        if en is None:
            return np.nan
        electronegativities.extend([en] * count)
    
    return float(np.var(electronegativities))

def calculate_vec(formula: str) -> float:
    """Calculate Valence Electron Concentration (weighted average) for a given formula."""
    parsed = parse_formula(formula)
    if not parsed:
        return np.nan
    
    total_atoms = sum(parsed.values())
    if total_atoms == 0:
        return np.nan
    
    weighted_sum = 0.0
    for element, count in parsed.items():
        vec = get_valence_electrons(element)
        if vec is None:
            return np.nan
        weighted_sum += vec * count
    
    return weighted_sum / total_atoms

class TestMeanAtomicRadius:
    def test_valid_formula(self):
        # Bi2Te3: Bi radius ~ 1.60, Te radius ~ 1.40 (approximate)
        # Mean = (2*1.60 + 3*1.40) / 5 = 1.48
        result = calculate_mean_atomic_radius("Bi2Te3")
        assert result is not None and not np.isnan(result)
        assert result > 0

    def test_empty_formula(self):
        with pytest.raises((ValueError, TypeError)):
            calculate_mean_atomic_radius("")

    def test_single_element(self):
        # Pure Bi should return Bi's radius
        result = calculate_mean_atomic_radius("Bi")
        assert result is not None and not np.isnan(result)
        assert result > 0

class TestElectronegativityVariance:
    def test_valid_formula(self):
        result = calculate_electronegativity_variance("Bi2Te3")
        assert result is not None and not np.isnan(result)
        assert result >= 0

    def test_uniform_composition(self):
        # Pure element should have 0 variance
        result = calculate_electronegativity_variance("Bi")
        assert result == 0.0

    def test_missing_element(self):
        # Non-existent element should return NaN or raise error
        result = calculate_electronegativity_variance("X1")
        assert result is None or np.isnan(result)

class TestVecCalculation:
    def test_valid_formula(self):
        # Bi (Group 15) has 5 valence electrons, Te (Group 16) has 6
        # Bi2Te3: (2*5 + 3*6) / 5 = (10 + 18) / 5 = 28/5 = 5.6
        result = calculate_vec("Bi2Te3")
        assert result is not None and not np.isnan(result)
        assert abs(result - 5.6) < 0.1  # Allow for small floating point variations

    def test_known_vec_value(self):
        # Test with a known value: Pb (Group 14, 4 valence), Te (Group 16, 6 valence)
        # PbTe: (1*4 + 1*6) / 2 = 5.0
        result = calculate_vec("PbTe")
        assert result is not None and not np.isnan(result)
        assert abs(result - 5.0) < 0.1

    def test_empty_formula(self):
        with pytest.raises((ValueError, TypeError)):
            calculate_vec("")

    def test_single_element(self):
        # Pure Bi should return Bi's valence electron count (5)
        result = calculate_vec("Bi")
        assert result is not None and not np.isnan(result)
        assert result == 5.0