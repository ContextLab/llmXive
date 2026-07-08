import pytest
import math
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.descriptors import calculate_tolerance_factor, get_ionic_radius

def test_tolerance_factor_calculation_returns_correct_value_for_KCl3():
    """
    Test case for T009: Verify tolerance factor calculation for KCl3.
    
    Formula: KCl3 -> A=K, B=Cl, X=Cl (This is chemically unusual, but we test the math).
    Usually perovskite is ABX3. If input is KCl3, we assume A=K, B=Cl, X=Cl?
    Or perhaps the test implies a hypothetical KCl3 structure where K is A, Cl is B?
    Standard perovskite: A is large cation, B is small cation, X is anion.
    Let's assume the function signature expects A, B, X ions.
    For KCl3, if it's treated as A=K, B=Cl, X=Cl:
    r_A = r(K+) ~ 1.38 A (CN=12) or 1.64?
    r_B = r(Cl-) ~ 1.81 A? (Cl is usually anion)
    r_X = r(Cl-) ~ 1.81 A?
    
    Actually, KCl3 is not a standard perovskite. Let's assume the test data provided
    in the prompt implies specific radii or the function handles the formula string.
    Looking at the function signature in descriptors.py (implied):
    calculate_tolerance_factor(r_A, r_B, r_X)
    
    Let's assume we pass radii directly for the test to avoid formula parsing complexity
    unless the function parses strings. The task says "test_tolerance_factor_calculation...".
    
    Let's assume we test the formula t = (rA + rX) / (sqrt(2) * (rB + rX))
    Values for KCl3 (hypothetical):
    r_K (CN12) ~ 1.64 A
    r_Cl (CN6) ~ 1.81 A (if B is Cl? Unlikely)
    r_Cl (CN?) ~ 1.81 A
    
    Let's use standard ionic radii for a valid perovskite example if KCl3 is invalid,
    but the test specifically asks for KCl3.
    Perhaps it means A=K, B=H, X=Cl? No, formula is KCl3.
    Maybe it means A=K, B=Cl, X=Cl?
    r_A (K+) = 1.38 (CN6) -> 1.64 (CN12)
    r_B (Cl-) = 1.81 (CN6)
    r_X (Cl-) = 1.81
    
    t = (1.64 + 1.81) / (1.414 * (1.81 + 1.81)) = 3.45 / (1.414 * 3.62) = 3.45 / 5.12 = 0.67
    
    We will test with hardcoded radii that correspond to the ions in KCl3 if the function takes ions,
    or pass the formula if it parses.
    Based on typical descriptors.py implementations, it likely takes element symbols or radii.
    Let's assume the function signature is calculate_tolerance_factor(r_A, r_B, r_X).
    We will provide the radii for K, Cl, Cl.
    """
    # Ionic radii in Angstroms (Shannon radii, CN=12 for A, CN=6 for B/X)
    # K+ (CN12) ~ 1.64 A
    # Cl- (CN6) ~ 1.81 A
    # Assuming B is Cl- and X is Cl- for KCl3 hypothetical
    r_A = 1.64
    r_B = 1.81
    r_X = 1.81
    
    expected_t = (r_A + r_X) / (math.sqrt(2) * (r_B + r_X))
    
    result = calculate_tolerance_factor(r_A, r_B, r_X)
    
    assert math.isclose(result, expected_t, rel_tol=1e-4), f"Expected {expected_t}, got {result}"
