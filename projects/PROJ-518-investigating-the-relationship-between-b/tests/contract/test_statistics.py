"""
Contract test for SC-003: Verify that ΔR² is reported with precision of at least 4 decimal places.
This test validates the output of `format_delta_r2` implemented in T043.
"""
import pytest
from analysis.statistics import format_delta_r2


def test_format_delta_r2_precision():
    """
    Verify that format_delta_r2 returns a string with at least 4 decimal places.
    SC-003 Requirement: ΔR² is reported with precision of at least 4 decimal places.
    """
    # Test case 1: Small positive value
    result = format_delta_r2(0.0012345)
    assert isinstance(result, str), "Output must be a string"
    assert result == "0.0012", f"Expected '0.0012', got '{result}'"

    # Test case 2: Large value
    result = format_delta_r2(0.1234567)
    assert result == "0.1235", f"Expected '0.1235', got '{result}'"

    # Test case 3: Zero
    result = format_delta_r2(0.0)
    assert result == "0.0000", f"Expected '0.0000', got '{result}'"

    # Test case 4: Negative value (if applicable in regression comparison)
    result = format_delta_r2(-0.00005)
    assert result == "-0.0001", f"Expected '-0.0001', got '{result}'"

    # Verify the format always contains exactly 4 decimal places
    for val in [0.1, 0.12, 0.123, 0.1234, 0.12345]:
        formatted = format_delta_r2(val)
        # Check that there is a decimal point and exactly 4 digits after it
        if "." in formatted:
            decimal_part = formatted.split(".")[-1]
            assert len(decimal_part) == 4, f"Expected 4 decimal places, got {len(decimal_part)} in '{formatted}'"
