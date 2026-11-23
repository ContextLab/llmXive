"""
Unit tests for the instruction synthesizer module (T012).
"""

import unittest
import json
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock, Mock

# Ensure src is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from instruction_synthesizer import generate_natural_language_instruction


class MockMetadata:
    """Helper to create mock metadata dictionaries."""
    @staticmethod
    def create(velocity=None, duration=None):
        meta = {}
        if velocity is not None:
            meta["velocity_vector"] = velocity
        if duration is not None:
            meta["duration"] = duration
        return meta


class TestNaturalLanguageInstruction(unittest.TestCase):
    """Tests for generate_natural_language_instruction (T012)."""

    def test_move_right(self):
        """Test generation of 'move right' instruction."""
        meta = MockMetadata.create(velocity=[1.0, 0.0, 0.0], duration=2.0)
        result = generate_natural_language_instruction(meta)
        self.assertIn("move", result)
        self.assertIn("right", result)

    def test_move_left(self):
        """Test generation of 'move left' instruction."""
        meta = MockMetadata.create(velocity=[-1.0, 0.0, 0.0], duration=2.0)
        result = generate_natural_language_instruction(meta)
        self.assertIn("left", result)

    def test_move_up(self):
        """Test generation of 'move up' instruction."""
        meta = MockMetadata.create(velocity=[0.0, 1.0, 0.0], duration=2.0)
        result = generate_natural_language_instruction(meta)
        self.assertIn("up", result)

    def test_move_down(self):
        """Test generation of 'move down' instruction."""
        meta = MockMetadata.create(velocity=[0.0, -1.0, 0.0], duration=2.0)
        result = generate_natural_language_instruction(meta)
        self.assertIn("down", result)

    def test_move_forward(self):
        """Test generation of 'move forward' instruction."""
        meta = MockMetadata.create(velocity=[0.0, 0.0, 1.0], duration=2.0)
        result = generate_natural_language_instruction(meta)
        self.assertIn("forward", result)

    def test_move_backward(self):
        """Test generation of 'move backward' instruction."""
        meta = MockMetadata.create(velocity=[0.0, 0.0, -1.0], duration=2.0)
        result = generate_natural_language_instruction(meta)
        self.assertIn("backward", result)

    def test_stationary(self):
        """Test generation of 'remain stationary' instruction."""
        meta = MockMetadata.create(velocity=[0.0, 0.0, 0.0], duration=2.0)
        result = generate_natural_language_instruction(meta)
        self.assertEqual(result, "remain stationary")

    def test_missing_velocity_defaults_to_stationary(self):
        """Test that missing velocity defaults to stationary."""
        meta = MockMetadata.create(duration=2.0) # No velocity
        result = generate_natural_language_instruction(meta)
        self.assertEqual(result, "remain stationary")

    def test_invalid_velocity_defaults_to_stationary(self):
        """Test that invalid velocity format defaults to stationary."""
        meta = MockMetadata.create(velocity="invalid", duration=2.0)
        result = generate_natural_language_instruction(meta)
        self.assertEqual(result, "remain stationary")

    def test_duration_modifiers(self):
        """Test that duration adds 'quickly' or 'slowly' modifiers."""
        # Fast
        meta_fast = MockMetadata.create(velocity=[1.0, 0.0, 0.0], duration=0.5)
        result_fast = generate_natural_language_instruction(meta_fast)
        self.assertIn("quickly", result_fast)

        # Slow
        meta_slow = MockMetadata.create(velocity=[1.0, 0.0, 0.0], duration=5.0)
        result_slow = generate_natural_language_instruction(meta_slow)
        self.assertIn("slowly", result_slow)

        # Normal (no modifier)
        meta_normal = MockMetadata.create(velocity=[1.0, 0.0, 0.0], duration=2.0)
        result_normal = generate_natural_language_instruction(meta_normal)
        self.assertNotIn("quickly", result_normal)
        self.assertNotIn("slowly", result_normal)


if __name__ == '__main__':
    unittest.main()