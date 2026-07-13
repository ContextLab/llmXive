"""
Unit tests for generate_trajectories.py
"""

import json
import math
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.generate_trajectories import (
    clamp_density,
    validate_density_computation,
    generate_trajectory,
    DENSITY_TARGETS
)
from code.utils.heuristics import calculate_composite_density


class TestClampDensity(unittest.TestCase):
    """Test clamping logic for zero density values (Edge Case)."""

    def test_positive_density_unchanged(self):
        self.assertEqual(clamp_density(3.5), 3.5)

    def test_zero_density_clamped(self):
        self.assertEqual(clamp_density(0.0), 0.001)

    def test_negative_density_clamped(self):
        self.assertEqual(clamp_density(-1.0), 0.001)

    def test_very_small_positive(self):
        self.assertEqual(clamp_density(0.0001), 0.0001)


class TestValidateDensityComputation(unittest.TestCase):
    """Test density validation logic (FR-007)."""

    def test_valid_density(self):
        text = "This is a test sentence with some technical tokens like def and class."
        density = calculate_composite_density(text)
        self.assertTrue(validate_density_computation(text, density))

    def test_invalid_density_detection(self):
        text = "This is a test."
        density = calculate_composite_density(text)
        # Pass a significantly wrong density value
        self.assertFalse(validate_density_computation(text, density + 10.0))


class TestGenerateTrajectory(unittest.TestCase):
    """Test trajectory generation logic."""

    def test_trajectory_structure(self):
        traj = generate_trajectory("low", 1.5, 0)

        self.assertIn("id", traj)
        self.assertIn("density_label", traj)
        self.assertIn("target_density", traj)
        self.assertIn("actual_density", traj)
        self.assertIn("text", traj)
        self.assertIn("evidence_turn_index", traj)
        self.assertIn("length_tokens", traj)
        self.assertIn("density_validated", traj)

        self.assertEqual(traj["density_label"], "low")
        self.assertEqual(traj["target_density"], 1.5)
        self.assertEqual(traj["id"], 0)
        self.assertGreater(traj["length_tokens"], 0)
        self.assertTrue(0 <= traj["evidence_turn_index"] <= 9)

    def test_density_clamping_in_trajectory(self):
        """Ensure generated trajectories have clamped densities."""
        traj = generate_trajectory("low", 0.0, 0)
        self.assertGreater(traj["actual_density"], 0)


class TestDensityTargets(unittest.TestCase):
    """Test that density targets are reasonable."""

    def test_targets_exist(self):
        self.assertIn("low", DENSITY_TARGETS)
        self.assertIn("medium", DENSITY_TARGETS)
        self.assertIn("high", DENSITY_TARGETS)

    def test_targets_increasing(self):
        self.assertLess(DENSITY_TARGETS["low"], DENSITY_TARGETS["medium"])
        self.assertLess(DENSITY_TARGETS["medium"], DENSITY_TARGETS["high"])


if __name__ == "__main__":
    unittest.main()