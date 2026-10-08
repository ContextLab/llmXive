"""
Unit tests for physics logic in physics_engine.py.
Tests verify that the simulation engine correctly detects logical contradictions
such as cycles, direct conflicts (A on B AND B on A), and impossible configurations.
"""
import unittest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from simulation.physics_engine import simulate_physics, parse_scene_description

class TestPhysicsLogic(unittest.TestCase):

    def test_direct_on_contradiction(self):
        """Test detection of direct 'on' contradiction (A on B AND B on A)"""
        objects = [
            {"id": "A", "name": "A", "type": "object"},
            {"id": "B", "name": "B", "type": "object"}
        ]
        constraints = [
            {"type": "on", "object_a": "A", "object_b": "B"},
            {"type": "on", "object_a": "B", "object_b": "A"}
        ]
        is_valid, contradictions = simulate_physics(objects, constraints, "test_1")
        self.assertFalse(is_valid)
        self.assertTrue(any("Direct On Contradiction" in c for c in contradictions))

    def test_direct_above_contradiction(self):
        """Test detection of direct 'above' contradiction (A above B AND B above A)"""
        objects = [
            {"id": "A", "name": "A", "type": "object"},
            {"id": "B", "name": "B", "type": "object"}
        ]
        constraints = [
            {"type": "above", "object_a": "A", "object_b": "B"},
            {"type": "above", "object_a": "B", "object_b": "A"}
        ]
        is_valid, contradictions = simulate_physics(objects, constraints, "test_2")
        self.assertFalse(is_valid)
        self.assertTrue(any("Direct Above Contradiction" in c for c in contradictions))

    def test_impossible_on_above(self):
        """Test detection of impossible configuration (A on B AND B above A)"""
        objects = [
            {"id": "A", "name": "A", "type": "object"},
            {"id": "B", "name": "B", "type": "object"}
        ]
        constraints = [
            {"type": "on", "object_a": "A", "object_b": "B"},
            {"type": "above", "object_a": "B", "object_b": "A"}
        ]
        is_valid, contradictions = simulate_physics(objects, constraints, "test_3")
        self.assertFalse(is_valid)
        self.assertTrue(any("Impossible Configuration" in c for c in contradictions))

    def test_valid_configuration(self):
        """Test a valid configuration with no contradictions"""
        objects = [
            {"id": "A", "name": "A", "type": "object"},
            {"id": "B", "name": "B", "type": "object"},
            {"id": "C", "name": "C", "type": "object"}
        ]
        constraints = [
            {"type": "on", "object_a": "A", "object_b": "B"},
            {"type": "on", "object_a": "B", "object_b": "C"}
        ]
        is_valid, contradictions = simulate_physics(objects, constraints, "test_4")
        self.assertTrue(is_valid)
        self.assertEqual(len(contradictions), 0)

    def test_cycle_detection(self):
        """Test detection of cycles in 'on' relationships"""
        objects = [
            {"id": "A", "name": "A", "type": "object"},
            {"id": "B", "name": "B", "type": "object"},
            {"id": "C", "name": "C", "type": "object"}
        ]
        constraints = [
            {"type": "on", "object_a": "A", "object_b": "B"},
            {"type": "on", "object_a": "B", "object_b": "C"},
            {"type": "on", "object_a": "C", "object_b": "A"}
        ]
        is_valid, contradictions = simulate_physics(objects, constraints, "test_5")
        self.assertFalse(is_valid)
        self.assertTrue(any("Cycle detected" in c for c in contradictions))

    def test_parse_scene_description_basic(self):
        """Test basic parsing of scene description"""
        description = "A is on B. C is next to D."
        _, objects, constraints = parse_scene_description(description)
        self.assertEqual(len(objects), 4)
        self.assertEqual(len(constraints), 2)
        # Check constraint types
        constraint_types = [c["type"] for c in constraints]
        self.assertIn("on", constraint_types)
        self.assertIn("next_to", constraint_types)

    def test_parse_scene_description_above_below(self):
        """Test parsing of 'above' and 'below' relationships"""
        description = "A is above B. C is below D."
        _, objects, constraints = parse_scene_description(description)
        self.assertEqual(len(objects), 4)
        self.assertEqual(len(constraints), 2)
        constraint_types = [c["type"] for c in constraints]
        self.assertIn("above", constraint_types)
        self.assertIn("below", constraint_types)

    def test_parse_scene_description_complex(self):
        """Test parsing of a more complex scene description"""
        description = "A is on B. B is on C. A is next to D."
        _, objects, constraints = parse_scene_description(description)
        self.assertEqual(len(objects), 4)
        self.assertEqual(len(constraints), 3)
        constraint_types = [c["type"] for c in constraints]
        self.assertEqual(constraint_types.count("on"), 2)
        self.assertEqual(constraint_types.count("next_to"), 1)

    def test_parse_scene_description_empty(self):
        """Test parsing of an empty scene description"""
        description = ""
        _, objects, constraints = parse_scene_description(description)
        self.assertEqual(len(objects), 0)
        self.assertEqual(len(constraints), 0)

    def test_parse_scene_description_single_object(self):
        """Test parsing of a scene with a single object"""
        description = "A is alone."
        _, objects, constraints = parse_scene_description(description)
        self.assertEqual(len(objects), 1)
        self.assertEqual(len(constraints), 0)

    def test_parse_scene_description_unsupported_relation(self):
        """Test parsing of a scene with an unsupported relation"""
        description = "A is inside B. C is on D."
        _, objects, constraints = parse_scene_description(description)
        self.assertEqual(len(objects), 4)
        # 'inside' is not supported, so only 'on' should be parsed
        self.assertEqual(len(constraints), 1)
        self.assertEqual(constraints[0]["type"], "on")

    def test_simulate_physics_with_unsupported_relation(self):
        """Test simulation with unsupported relations (should be ignored)"""
        objects = [
            {"id": "A", "name": "A", "type": "object"},
            {"id": "B", "name": "B", "type": "object"}
        ]
        # 'inside' is not supported
        constraints = [
            {"type": "inside", "object_a": "A", "object_b": "B"}
        ]
        is_valid, contradictions = simulate_physics(objects, constraints, "test_6")
        self.assertTrue(is_valid)
        self.assertEqual(len(contradictions), 0)

    def test_simulate_physics_mixed_relations(self):
        """Test simulation with a mix of supported and unsupported relations"""
        objects = [
            {"id": "A", "name": "A", "type": "object"},
            {"id": "B", "name": "B", "type": "object"},
            {"id": "C", "name": "C", "type": "object"}
        ]
        constraints = [
            {"type": "on", "object_a": "A", "object_b": "B"},
            {"type": "inside", "object_a": "B", "object_b": "C"}, # Unsupported
            {"type": "above", "object_a": "A", "object_b": "C"}
        ]
        is_valid, contradictions = simulate_physics(objects, constraints, "test_7")
        # A on B and A above C is valid
        self.assertTrue(is_valid)
        self.assertEqual(len(contradictions), 0)

if __name__ == '__main__':
    unittest.main()