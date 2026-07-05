import pytest
import math
import sys
import os

# Add the project root to the path so we can import code modules
# In a real execution environment, this might be handled by PYTHONPATH or setup.py
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.data.descriptors import calculate_tolerance_factor

def test_tolerance_factor_calculation_returns_correct_value_for_KCl3():
    """
    Test the tolerance factor calculation for KCl3 (hypothetical perovskite structure).
    
    Reference values (Shannon radii in Angstroms):
    K+ (CN=12) = 2.80
    Cl- (CN=6) = 1.81
    
    Formula: t = (r_A + r_X) / (sqrt(2) * (r_B + r_X))
    
    For KCl3:
    r_A = 2.80 (K+)
    r_B = 1.81 (Cl-, assuming Cl occupies B-site in this hypothetical case)
    r_X = 1.81 (Cl-)
    
    t = (2.80 + 1.81) / (sqrt(2) * (1.81 + 1.81))
    t = 4.61 / (1.4142 * 3.62)
    t = 4.61 / 5.119
    t ≈ 0.9005
    """
    # Using standard Shannon radii for K+ (CN=12) and Cl- (CN=6)
    r_A = 2.80  # K+
    r_B = 1.81  # Cl- (acting as B-site cation in this hypothetical)
    r_X = 1.81  # Cl-
    
    expected_t = (r_A + r_X) / (math.sqrt(2) * (r_B + r_X))
    
    # Calculate using our implementation
    actual_t = calculate_tolerance_factor(r_A, r_B, r_X)
    
    # Assert with tolerance for floating point arithmetic
    assert math.isclose(actual_t, expected_t, rel_tol=1e-5), \
        f"Expected tolerance factor {expected_t:.6f}, got {actual_t:.6f}"
