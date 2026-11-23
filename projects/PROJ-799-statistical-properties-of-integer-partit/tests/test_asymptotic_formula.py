"""
Contract tests for the asymptotic formula implementation.
Verifies that the formula matches the derivation in docs/verified_formula.md.
"""
import math
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.utils.asymptotic_baseline import calculate_asymptotic_baseline, C_CONSTANT

def test_constant_value():
    """Test that the constant C is correctly set to sqrt(24/pi^2)."""
    expected_c = math.sqrt(24.0 / (math.pi ** 2))
    assert math.isclose(C_CONSTANT, expected_c, rel_tol=1e-9), \
        f"Constant C mismatch: expected {expected_c}, got {C_CONSTANT}"

def test_formula_structure():
    """Test that the formula structure is correct: exp(C * sqrt(n/ln n))."""
    # Test with a known value
    # n = 100
    # ln(100) = 4.605
    # sqrt(100/4.605) = sqrt(21.71) = 4.66
    # C * 4.66 = 1.555 * 4.66 = 7.24
    # exp(7.24) = 1393
    
    n = 100
    result = calculate_asymptotic_baseline(n)
    
    # Manual calculation for verification
    manual_exponent = C_CONSTANT * math.sqrt(n / math.log(n))
    manual_result = math.exp(manual_exponent)
    
    assert math.isclose(result, manual_result, rel_tol=1e-10), \
        f"Formula structure mismatch: {result} vs {manual_result}"

def test_edge_cases():
    """Test edge cases like n=1, n=2."""
    # n=1 should raise error
    try:
        calculate_asymptotic_baseline(1)
        assert False, "Should have raised ValueError for n=1"
    except ValueError:
        pass

    # n=2 should work
    result_2 = calculate_asymptotic_baseline(2)
    assert result_2 > 0, "Result for n=2 should be positive"

def test_monotonicity():
    """Test that Q_as(n) is monotonically increasing for n > 1."""
    prev_val = 0
    for n in range(2, 1000):
        val = calculate_asymptotic_baseline(n)
        assert val > prev_val, f"Q_as(n) should be increasing: {val} <= {prev_val} at n={n}"
        prev_val = val

if __name__ == "__main__":
    test_constant_value()
    print("test_constant_value passed")
    
    test_formula_structure()
    print("test_formula_structure passed")
    
    test_edge_cases()
    print("test_edge_cases passed")
    
    test_monotonicity()
    print("test_monotonicity passed")
    
    print("All tests passed.")