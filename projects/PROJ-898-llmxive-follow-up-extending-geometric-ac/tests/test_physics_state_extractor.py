"""
Unit Tests for Physics State Extractor (T010a)

Verifies that the extractor correctly serializes physics states to JSON
and handles edge cases.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

# Import the module under test
from physics_state_extractor import PhysicsStateExtractor


class TestPhysicsStateExtractor(unittest.TestCase):
    """Test cases for PhysicsStateExtractor."""

    def setUp(self):
        """Set up a temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = os.path.join(self.temp_dir, "test_physics_states.json")
        self.extractor = PhysicsStateExtractor(output_path=self.output_path)

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_add_state_basic(self):
        """Test adding a basic state with vertex positions and joint angles."""
        timestamp = 1.0
        body_id = 1
        topology_id = "test_chain"
        object_type = "kinematic_chain"

        vertices = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
        joints = {0: 0.5, 1: 1.0}

        self.extractor.add_state(
            timestamp=timestamp,
            body_id=body_id,
            topology_id=topology_id,
            object_type=object_type,
            vertex_positions=vertices,
            joint_angles=joints
        )

        self.assertEqual(len(self.extractor.state_buffer), 1)
        entry = self.extractor.state_buffer[0]
        self.assertEqual(entry["timestamp"], timestamp)
        self.assertEqual(entry["body_id"], body_id)
        self.assertEqual(entry["topology_id"], topology_id)
        self.assertEqual(entry["object_type"], object_type)
        self.assertEqual(len(entry["vertex_positions"]), 2)
        self.assertEqual(len(entry["joint_angles"]), 2)

    def test_serialize_writes_file(self):
        """Test that serialization creates the JSON file."""
        vertices = np.array([[0.0, 0.0, 0.0]])
        self.extractor.add_state(
            timestamp=0.0,
            body_id=1,
            topology_id="test",
            object_type="deformable",
            vertex_positions=vertices,
            joint_angles={}
        )

        self.extractor.serialize()

        self.assertTrue(os.path.exists(self.output_path))

        with open(self.output_path, 'r') as f:
            data = json.load(f)

        self.assertIn("metadata", data)
        self.assertIn("states", data)
        self.assertEqual(len(data["states"]), 1)

    def test_serialize_empty_buffer(self):
        """Test serialization with an empty buffer."""
        self.extractor.serialize()

        self.assertTrue(os.path.exists(self.output_path))

        with open(self.output_path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data["metadata"]["count"], 0)

    def test_vertex_positions_serialization(self):
        """Test that numpy arrays are correctly converted to lists."""
        vertices = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        self.extractor.add_state(
            timestamp=0.0,
            body_id=1,
            topology_id="test",
            object_type="deformable",
            vertex_positions=vertices,
            joint_angles={}
        )

        self.extractor.serialize()

        with open(self.output_path, 'r') as f:
            data = json.load(f)

        # Verify the list structure matches the numpy array
        serialized_verts = data["states"][0]["vertex_positions"]
        self.assertEqual(serialized_verts, [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])

    def test_joint_angles_serialization(self):
        """Test that joint angles dict is preserved."""
        joints = {0: 0.1, 1: 0.2, 2: 0.3}
        self.extractor.add_state(
            timestamp=0.0,
            body_id=1,
            topology_id="test",
            object_type="kinematic_chain",
            vertex_positions=np.array([[0.0, 0.0, 0.0]]),
            joint_angles=joints
        )

        self.extractor.serialize()

        with open(self.output_path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data["states"][0]["joint_angles"], joints)


if __name__ == "__main__":
    unittest.main()
