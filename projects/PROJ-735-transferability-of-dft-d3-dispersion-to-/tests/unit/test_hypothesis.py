"""
Unit tests for hypothesis testing (s=1.0) logic in derive_scaling.py.

This module tests the logic used to determine if the optimal scaling factor
significantly differs from 1.0 (the standard DFT-D3 value) based on bootstrap
confidence intervals.
"""

import pytest
import numpy as np
from typing import List, Tuple

# Import the function to be tested.
# Note: This function is expected to be implemented in code/derive_scaling.py
# as part of task T024. We import it here to test its logic independently.
# If the function is not yet implemented, this test will fail to import,
# which is the expected behavior for a "write tests first" approach.
try:
    from derive_scaling import test_hypothesis_s_equals_1
except ImportError:
    # Provide a mock or stub for the test to run if the implementation
    # is not yet available, or to ensure the test file itself is valid.
    # In a real "test first" scenario, the implementation would be missing.
    # For this task, we assume the implementation exists or will be added.
    # We define a stub here to allow the test file to be syntactically valid
    # and runnable if the import fails, but the test itself should fail
    # if the function is missing.
    def test_hypothesis_s_equals_1(
        s_opt: float,
        ci_lower: float,
        ci_upper: float,
        alpha: float = 0.05
    ) -> Tuple[bool, str]:
        """
        Stub for test_hypothesis_s_equals_1.

        Args:
            s_opt: The optimal scaling factor.
            ci_lower: Lower bound of the confidence interval.
            ci_upper: Upper bound of the confidence interval.
            alpha: Significance level.

        Returns:
            Tuple of (is_significant, message).
        """
        raise NotImplementedError("Implementation of test_hypothesis_s_equals_1 is pending in code/derive_scaling.py")

def test_hypothesis_rejects_null_when_ci_excludes_one():
    """
    Test that the hypothesis test correctly rejects the null hypothesis (s=1.0)
    when the confidence interval does not include 1.0.
    """
    # Case 1: CI is entirely above 1.0
    s_opt = 1.2
    ci_lower = 1.1
    ci_upper = 1.3
    is_significant, message = test_hypothesis_s_equals_1(s_opt, ci_lower, ci_upper)

    assert is_significant is True
    assert "1.0" in message or "1.00" in message
    assert "reject" in message.lower()

    # Case 2: CI is entirely below 1.0
    s_opt = 0.8
    ci_lower = 0.7
    ci_upper = 0.9
    is_significant, message = test_hypothesis_s_equals_1(s_opt, ci_lower, ci_upper)

    assert is_significant is True
    assert "1.0" in message or "1.00" in message
    assert "reject" in message.lower()

def test_hypothesis_fails_to_reject_null_when_ci_includes_one():
    """
    Test that the hypothesis test fails to reject the null hypothesis (s=1.0)
    when the confidence interval includes 1.0.
    """
    # Case 1: CI includes 1.0
    s_opt = 1.05
    ci_lower = 0.95
    ci_upper = 1.15
    is_significant, message = test_hypothesis_s_equals_1(s_opt, ci_lower, ci_upper)

    assert is_significant is False
    assert "fail to reject" in message.lower() or "do not reject" in message.lower()
    assert "1.0" in message or "1.00" in message

    # Case 2: CI includes 1.0 (s_opt exactly 1.0)
    s_opt = 1.0
    ci_lower = 0.9
    ci_upper = 1.1
    is_significant, message = test_hypothesis_s_equals_1(s_opt, ci_lower, ci_upper)

    assert is_significant is False

def test_hypothesis_edge_cases():
    """
    Test edge cases such as CI boundaries exactly at 1.0.
    """
    # Case 1: Lower bound is exactly 1.0
    s_opt = 1.1
    ci_lower = 1.0
    ci_upper = 1.2
    # Conventionally, if 1.0 is on the boundary, it is included in the CI,
    # so we fail to reject.
    is_significant, message = test_hypothesis_s_equals_1(s_opt, ci_lower, ci_upper)
    assert is_significant is False

    # Case 2: Upper bound is exactly 1.0
    s_opt = 0.9
    ci_lower = 0.8
    ci_upper = 1.0
    is_significant, message = test_hypothesis_s_equals_1(s_opt, ci_lower, ci_upper)
    assert is_significant is False

def test_hypothesis_message_format():
    """
    Test that the returned message is informative and contains key details.
    """
    s_opt = 1.5
    ci_lower = 1.4
    ci_upper = 1.6
    is_significant, message = test_hypothesis_s_equals_1(s_opt, ci_lower, ci_upper)

    assert isinstance(message, str)
    assert len(message) > 20
    assert str(s_opt) in message
    assert str(ci_lower) in message
    assert str(ci_upper) in message