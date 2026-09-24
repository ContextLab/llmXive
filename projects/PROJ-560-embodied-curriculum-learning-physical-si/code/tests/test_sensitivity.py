import pytest
import numpy as np
import os
import sys
import json
import tempfile
from pathlib import Path

# Import the function under test and the model
# Assuming the project root is in sys.path or we adjust accordingly
# The API surface says: from tests.test_sensitivity import TestRobustnessWarning
# So we import the function directly from src.sensitivity
from src.sensitivity import check_robustness_warning
from src.models import SensitivitySweep


class TestRobustnessWarning:
    """
    Tests for the check_robustness_warning function (Task T030).
    SC-003: Flag robustness_warning: true if effect size drops below negligible threshold
    while remaining statistically significant.
    """

    def test_no_warning_when_effect_size_large_and_significant(self):
        """
        Scenario: Large effect size (|d| >= 0.2) and significant.
        Expected: No warning (False).
        """
        # Effect size 0.8 (large), significant at p < 0.05
        sweep_results = [
            SensitivitySweep(threshold=0.05, effect_size=0.8, significant=True),
            SensitivitySweep(threshold=0.01, effect_size=0.8, significant=False),
        ]
        result = check_robustness_warning(sweep_results)
        assert result is False, "Should not warn if effect size is large."

    def test_no_warning_when_effect_size_negligible_but_not_significant(self):
        """
        Scenario: Negligible effect size (|d| < 0.2) but NOT significant.
        Expected: No warning (False).
        """
        # Effect size 0.1 (negligible), not significant
        sweep_results = [
            SensitivitySweep(threshold=0.05, effect_size=0.1, significant=False),
            SensitivitySweep(threshold=0.10, effect_size=0.1, significant=False),
        ]
        result = check_robustness_warning(sweep_results)
        assert result is False, "Should not warn if result is not significant."

    def test_warning_triggered_when_effect_size_negligible_and_significant(self):
        """
        Scenario: Negligible effect size (|d| < 0.2) AND significant.
        Expected: Warning triggered (True).
        """
        # Effect size 0.15 (negligible), significant at p < 0.05
        sweep_results = [
            SensitivitySweep(threshold=0.05, effect_size=0.15, significant=True),
            SensitivitySweep(threshold=0.01, effect_size=0.15, significant=False),
        ]
        result = check_robustness_warning(sweep_results)
        assert result is True, "Should warn if effect size is negligible but significant."

    def test_warning_triggered_on_negative_effect_size_negligible_and_significant(self):
        """
        Scenario: Negative negligible effect size (|d| < 0.2) AND significant.
        Expected: Warning triggered (True).
        """
        # Effect size -0.15 (negligible magnitude), significant
        sweep_results = [
            SensitivitySweep(threshold=0.05, effect_size=-0.15, significant=True),
        ]
        result = check_robustness_warning(sweep_results)
        assert result is True, "Should warn if negative effect size is negligible but significant."

    def test_warning_triggered_if_any_sweep_point_meets_criteria(self):
        """
        Scenario: Multiple sweep points, one is negligible+significant, others are not.
        Expected: Warning triggered (True).
        """
        sweep_results = [
            SensitivitySweep(threshold=0.01, effect_size=0.5, significant=True), # Large, sig -> OK
            SensitivitySweep(threshold=0.05, effect_size=0.1, significant=True), # Negligible, sig -> WARN
            SensitivitySweep(threshold=0.10, effect_size=0.5, significant=True), # Large, sig -> OK
        ]
        result = check_robustness_warning(sweep_results)
        assert result is True, "Should warn if ANY point is negligible and significant."

    def test_empty_list_returns_false(self):
        """
        Scenario: Empty list of sweep results.
        Expected: No warning (False).
        """
        result = check_robustness_warning([])
        assert result is False, "Empty list should not trigger warning."

    def test_boundary_effect_size_exactly_0_2(self):
        """
        Scenario: Effect size exactly 0.2 (threshold boundary).
        Expected: No warning (since condition is < 0.2).
        """
        sweep_results = [
            SensitivitySweep(threshold=0.05, effect_size=0.2, significant=True),
        ]
        result = check_robustness_warning(sweep_results)
        assert result is False, "Effect size exactly 0.2 should not trigger warning (condition is < 0.2)."