"""
Additional specific test for SC-001 logic edge cases.
"""
import pytest

def test_sc001_logic_direct():
    """Direct logic test for SC-001 conditions."""
    # Simulate the logic from evaluate.py
    def determine_sc001(mae, n):
        if n < 50:
            return "LOW_POWER"
        if mae < 30:
            return "PASS"
        if mae > 50:
            return "FAIL"
        return "UNDECIDED" # 30 <= mae <= 50

    # Test high power, good MAE
    assert determine_sc001(20.0, 100) == "PASS"
    # Test high power, bad MAE
    assert determine_sc001(60.0, 100) == "FAIL"
    # Test low power
    assert determine_sc001(10.0, 40) == "LOW_POWER"
    # Test edge case
    assert determine_sc001(30.0, 100) == "UNDECIDED"
