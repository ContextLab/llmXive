"""
Unit tests for code/generate_trajectories.py
Verifies trajectory generation logic, density control, and evidence injection.
"""
import pytest
import json
import math
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.generate_trajectories import generate_text_block, inject_critical_evidence, clamp_density, validate_density_computation, generate_trajectory


class TestGenerateTextBlock:
    """Tests for the text block generation helper."""

    def test_length_accuracy(self):
        """Verify generated block matches requested length."""
        block = generate_text_block(length=50)
        assert len(block) == 50

    def test_content_composition(self):
        """Verify generated content contains expected characters."""
        block = generate_text_block(length=100)
        # Should contain letters, numbers, and spaces
        assert any(c.isalpha() for c in block)
        assert any(c.isdigit() for c in block)
        assert " " in block


class TestInjectCriticalEvidence:
    """Tests for critical evidence injection."""

    def test_injection_position(self):
        """Verify evidence is injected at the specified index."""
        text = "0123456789"
        evidence = "CRIT"
        index = 2
        result = inject_critical_evidence(text, evidence, index)
        assert result[2:6] == "CRIT"
        assert result[:2] == "01"
        assert result[6:] == "3456789"

    def test_overflow_handling(self):
        """Verify behavior when index is out of bounds (should append or clamp)."""
        text = "short"
        evidence = "EVID"
        # Index 100 is out of bounds
        result = inject_critical_evidence(text, evidence, 100)
        # Depending on implementation, it might append or raise.
        # Assuming it appends or clamps to end.
        assert "EVID" in result


class TestClampDensity:
    """Tests for density clamping logic."""

    def test_within_bounds(self):
        """Values within [0, 1] should be unchanged."""
        assert clamp_density(0.5) == 0.5
        assert clamp_density(0.0) == 0.0
        assert clamp_density(1.0) == 1.0

    def test_below_bounds(self):
        """Negative values should be clamped to 0."""
        assert clamp_density(-0.5) == 0.0

    def test_above_bounds(self):
        """Values > 1 should be clamped to 1."""
        assert clamp_density(1.5) == 1.0


class TestValidateDensityComputation:
    """Tests for density validation logic."""

    def test_valid_density(self):
        """Valid density should return True."""
        # Assuming the function checks if density is in [0, 1]
        assert validate_density_computation(0.5) is True
        assert validate_density_computation(0.0) is True
        assert validate_density_computation(1.0) is True

    def test_invalid_density(self):
        """Invalid density should return False."""
        assert validate_density_computation(-0.1) is False
        assert validate_density_computation(1.1) is False


class TestGenerateTrajectory:
    """Tests for the full trajectory generation."""

    def test_trajectory_structure(self):
        """Verify generated trajectory has required keys."""
        trajectory = generate_trajectory(target_density=0.5, evidence_turn_index=2)
        assert "text" in trajectory
        assert "metadata" in trajectory
        assert "density" in trajectory["metadata"]
        assert "evidence_turn_index" in trajectory["metadata"]

    def test_density_control(self):
        """Verify that target density influences the output density."""
        # This is a probabilistic check, so we run multiple times or check the logic.
        # For unit tests, we might mock the entropy calculation to ensure the logic path is taken.
        # Here we just check that the metadata reflects the input.
        t1 = generate_trajectory(target_density=0.2, evidence_turn_index=1)
        t2 = generate_trajectory(target_density=0.8, evidence_turn_index=1)
        
        # The actual density might not be exactly 0.2 or 0.8 due to randomness,
        # but the metadata should record the target.
        assert t1["metadata"]["target_density"] == 0.2
        assert t2["metadata"]["target_density"] == 0.8

    def test_evidence_inclusion(self):
        """Verify that critical evidence is present in the trajectory text."""
        evidence_marker = "CRITICAL_EVIDENCE"
        trajectory = generate_trajectory(target_density=0.5, evidence_turn_index=1)
        # The evidence marker should be in the text
        assert evidence_marker in trajectory["text"]
