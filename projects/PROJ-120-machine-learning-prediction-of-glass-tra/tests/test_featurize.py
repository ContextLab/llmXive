"""
Tests for compositional featurization logic in code/featurize.py.

This module verifies the calculation of network former/modifier ratios,
average electronegativity, and other compositional descriptors.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from featurize import (
    calculate_network_former_modifier_ratio,
    calculate_average_electronegativity,
    calculate_average_atomic_mass,
    calculate_valence_electron_count,
    get_atomic_fraction,
)
from pymatgen.core import Composition

# Define test compositions
# SiO2: Network Former (Si) only. Ratio should be high (infinite if no modifiers).
COMPOSITION_SIO2 = Composition("SiO2")

# Na2O: Network Modifier (Na) only. Ratio should be 0.
COMPOSITION_NA2O = Composition("Na2O")

# Soda-Lime-Silica (Simplified): 75% SiO2, 15% Na2O, 10% CaO
# Formers: Si. Modifiers: Na, Ca.
# Atomic fractions:
# Si: 0.75 (from SiO2) -> 0.75 * 1 = 0.75 moles Si per mole glass
# O: 0.75*2 + 0.15*1 + 0.10*1 = 1.5 + 0.15 + 0.10 = 1.75 moles O
# Na: 0.15 * 2 = 0.30 moles Na
# Ca: 0.10 * 1 = 0.10 moles Ca
# Total atoms: 0.75 (Si) + 1.75 (O) + 0.30 (Na) + 0.10 (Ca) = 2.9
# Atomic Fractions:
# Si: 0.75 / 2.9 ≈ 0.2586
# O: 1.75 / 2.9 ≈ 0.6034
# Na: 0.30 / 2.9 ≈ 0.1034
# Ca: 0.10 / 2.9 ≈ 0.0345
# Formers (Si): ~0.2586
# Modifiers (Na+Ca): ~0.1379
# Ratio: 0.2586 / 0.1379 ≈ 1.875
COMPOSITION_SODA_LIME = Composition("Si0.75Na0.30Ca0.10O1.75")

# Borosilicate: Si and B as formers, Na as modifier
# 80% SiO2, 10% B2O3, 10% Na2O
# Si: 0.80, B: 0.10*2=0.20, Na: 0.10*2=0.20, O: 0.80*2 + 0.10*3 + 0.10*1 = 1.6+0.3+0.1=2.0
# Total: 0.8+0.2+0.2+2.0 = 3.2
# Formers: Si (0.8), B (0.2) -> Sum = 1.0
# Modifiers: Na (0.2)
# Ratio: 1.0 / 0.2 = 5.0
COMPOSITION_BOROSILICATE = Composition("Si0.8B0.2Na0.2O2.0")

def test_get_atomic_fraction_si():
    """Verify atomic fraction calculation for SiO2."""
    comp = COMPOSITION_SIO2
    # SiO2 has 1 Si and 2 O. Total 3 atoms.
    # Fraction of Si should be 1/3.
    frac = get_atomic_fraction(comp, "Si")
    assert abs(frac - 1.0/3.0) < 1e-6, f"Expected ~0.333, got {frac}"

def test_get_atomic_fraction_modifier():
    """Verify atomic fraction calculation for Na in Na2O."""
    comp = COMPOSITION_NA2O
    # Na2O has 2 Na and 1 O. Total 3 atoms.
    # Fraction of Na should be 2/3.
    frac = get_atomic_fraction(comp, "Na")
    assert abs(frac - 2.0/3.0) < 1e-6, f"Expected ~0.666, got {frac}"

def test_network_former_modifier_ratio_sio2():
    """
    Test ratio for pure network former (SiO2).
    Since there are no modifiers, the denominator is 0.
    The function should handle this (return inf or a large number) or raise a specific error.
    Based on typical ML pipelines, we expect a large value or inf.
    """
    comp = COMPOSITION_SIO2
    ratio = calculate_network_former_modifier_ratio(comp)
    # Expected: Formers (Si) / Modifiers (0) -> Inf
    assert np.isinf(ratio), f"Expected inf for pure former, got {ratio}"

def test_network_former_modifier_ratio_na2o():
    """
    Test ratio for pure network modifier (Na2O).
    Formers = 0, Modifiers > 0. Ratio should be 0.
    """
    comp = COMPOSITION_NA2O
    ratio = calculate_network_former_modifier_ratio(comp)
    assert ratio == 0.0, f"Expected 0.0 for pure modifier, got {ratio}"

def test_network_former_modifier_ratio_soda_lime():
    """
    Test ratio for Soda-Lime-Silica.
    Expected ratio ~ 1.875 based on manual calculation.
    """
    comp = COMPOSITION_SODA_LIME
    ratio = calculate_network_former_modifier_ratio(comp)
    # Allow small tolerance for floating point
    expected = 1.875
    assert abs(ratio - expected) < 0.01, f"Expected ~{expected}, got {ratio}"

def test_network_former_modifier_ratio_borosilicate():
    """
    Test ratio for Borosilicate with multiple formers.
    Expected ratio = 5.0.
    """
    comp = COMPOSITION_BOROSILICATE
    ratio = calculate_network_former_modifier_ratio(comp)
    assert abs(ratio - 5.0) < 0.01, f"Expected 5.0, got {ratio}"

def test_average_electronegativity_sio2():
    """
    Test average electronegativity for SiO2.
    Si (1.90) * (1/3) + O (3.44) * (2/3)
    """
    comp = COMPOSITION_SIO2
    avg_en = calculate_average_electronegativity(comp)
    # Values from Pauling scale (approx): Si=1.90, O=3.44
    expected = (1.90 * (1/3)) + (3.44 * (2/3))
    assert abs(avg_en - expected) < 0.01, f"Expected ~{expected}, got {avg_en}"

def test_average_electronegativity_na2o():
    """
    Test average electronegativity for Na2O.
    Na (0.93) * (2/3) + O (3.44) * (1/3)
    """
    comp = COMPOSITION_NA2O
    avg_en = calculate_average_electronegativity(comp)
    # Values: Na=0.93, O=3.44
    expected = (0.93 * (2/3)) + (3.44 * (1/3))
    assert abs(avg_en - expected) < 0.01, f"Expected ~{expected}, got {avg_en}"

def test_average_atomic_mass_sio2():
    """
    Test average atomic mass for SiO2.
    Si (28.08) * (1/3) + O (16.00) * (2/3)
    """
    comp = COMPOSITION_SIO2
    avg_mass = calculate_average_atomic_mass(comp)
    # Values: Si=28.0855, O=15.999
    expected = (28.0855 * (1/3)) + (15.999 * (2/3))
    assert abs(avg_mass - expected) < 0.01, f"Expected ~{expected}, got {avg_mass}"

def test_valence_electron_count_sio2():
    """
    Test valence electron count for SiO2.
    Si (4) * (1/3) + O (6) * (2/3)
    """
    comp = COMPOSITION_SIO2
    valence = calculate_valence_electron_count(comp)
    # Values: Si=4, O=6
    expected = (4 * (1/3)) + (6 * (2/3))
    assert abs(valence - expected) < 0.01, f"Expected ~{expected}, got {valence}"

def test_valence_electron_count_complex():
    """
    Test valence electron count for a complex composition.
    Si (4), B (3), Na (1), O (6).
    """
    comp = COMPOSITION_BOROSILICATE
    valence = calculate_valence_electron_count(comp)
    # Si: 0.8, B: 0.2, Na: 0.2, O: 2.0. Total 3.0 atoms.
    # Fractions: Si=0.8/3, B=0.2/3, Na=0.2/3, O=2.0/3
    # Expected = 4*(0.8/3) + 3*(0.2/3) + 1*(0.2/3) + 6*(2.0/3)
    # = (3.2 + 0.6 + 0.2 + 12.0) / 3 = 16.0 / 3 = 5.333...
    expected = 16.0 / 3.0
    assert abs(valence - expected) < 0.01, f"Expected ~{expected}, got {valence}"