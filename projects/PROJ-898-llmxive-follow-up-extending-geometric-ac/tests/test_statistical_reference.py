"""
Tests for statistical reference distribution computation (T010b).
"""

import json
import os
import tempfile
import unittest
from typing import Dict, Any

import numpy as np

# Import the module under test
try:
    from statistical_reference import (
        load_physics_states,
        extract_state_vectors,
        compute_statistics,
        save_reference_stats,
        compute_reference_stats_from_file
    )
except ImportError:
    # For running tests directly
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
    from statistical_reference import (
        load_physics_states,
        extract_state_vectors,
        compute_statistics,
        save_reference_stats,
        compute_reference_stats_from_file
    )


class TestLoadPhysicsStates(unittest.TestCase):
    """Tests for load_physics_states function."""

    def test_load_valid_file(self):
        """Test loading a valid physics states file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "data"}, f)
            temp_path = f.name

        try:
            result = load_physics_states(temp_path)
            self.assertEqual(result, {"test": "data"})
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        """Test that loading a nonexistent file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_physics_states("nonexistent_file.json")


class TestExtractStateVectors(unittest.TestCase):
    """Tests for extract_state_vectors function."""

    def test_single_topology_with_vertices(self):
        """Test extraction from single topology with vertex positions."""
        states = {
            "topology_id": "test_001",
            "timesteps": [
                {
                    "vertex_positions": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
                    "joint_angles": [0.5],
                    "timestamp": 0.0
                },
                {
                    "vertex_positions": [[0.1, 0.0, 0.0], [1.1, 0.0, 0.0]],
                    "joint_angles": [0.6],
                    "timestamp": 1.0
                }
            ]
        }

        vectors = extract_state_vectors(states)
        
        self.assertEqual(vectors.shape[0], 2)  # 2 timesteps
        self.assertEqual(vectors.shape[1], 7)  # 6 vertex coords + 1 joint angle

    def test_single_topology_with_joints_only(self):
        """Test extraction from single topology with only joint angles."""
        states = {
            "topology_id": "test_002",
            "timesteps": [
                {"joint_angles": [1.0, 2.0, 3.0], "timestamp": 0.0},
                {"joint_angles": [1.1, 2.1, 3.1], "timestamp": 1.0}
            ]
        }

        vectors = extract_state_vectors(states)
        
        self.assertEqual(vectors.shape[0], 2)
        self.assertEqual(vectors.shape[1], 3)

    def test_empty_timesteps(self):
        """Test that empty timesteps raise ValueError."""
        states = {
            "topology_id": "test_003",
            "timesteps": []
        }

        with self.assertRaises(ValueError):
            extract_state_vectors(states)


class TestComputeStatistics(unittest.TestCase):
    """Tests for compute_statistics function."""

    def test_basic_computation(self):
        """Test basic mean and covariance computation."""
        vectors = np.array([
            [1.0, 2.0, 3.0],
            [2.0, 3.0, 4.0],
            [3.0, 4.0, 5.0]
        ])

        mean, cov = compute_statistics(vectors)

        expected_mean = np.array([2.0, 3.0, 4.0])
        self.assertTrue(np.allclose(mean, expected_mean))
        
        self.assertEqual(cov.shape, (3, 3))
        # Covariance should be symmetric
        self.assertTrue(np.allclose(cov, cov.T))

    def test_insufficient_samples(self):
        """Test that less than 2 samples raises ValueError."""
        vectors = np.array([[1.0, 2.0, 3.0]])
        
        with self.assertRaises(ValueError):
            compute_statistics(vectors)

    def test_negative_eigenvalue_handling(self):
        """Test that negative eigenvalues are handled with regularization."""
        # Create a case that might produce numerical issues
        vectors = np.array([
            [1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0]
        ])
        
        # This should not raise an error due to regularization
        mean, cov = compute_statistics(vectors)
        
        # Covariance should be positive semi-definite
        eigvals = np.linalg.eigvalsh(cov)
        self.assertTrue(np.all(eigvals >= -1e-10))


class TestSaveReferenceStats(unittest.TestCase):
    """Tests for save_reference_stats function."""

    def test_save_and_load(self):
        """Test saving and loading reference statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_stats.json")
            
            mean = np.array([1.0, 2.0, 3.0])
            cov = np.array([
                [1.0, 0.1, 0.2],
                [0.1, 1.0, 0.3],
                [0.2, 0.3, 1.0]
            ])
            
            metadata = {"test": "value"}
            save_reference_stats(mean, cov, output_path, metadata)
            
            # Verify file exists
            self.assertTrue(os.path.exists(output_path))
            
            # Verify content
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            self.assertTrue(np.allclose(np.array(loaded["mean"]), mean))
            self.assertTrue(np.allclose(np.array(loaded["covariance"]), cov))
            self.assertEqual(loaded["n_features"], 3)


class TestComputeReferenceStatsFromFile(unittest.TestCase):
    """Tests for compute_reference_stats_from_file function."""

    def test_end_to_end(self):
        """Test end-to-end computation from file to output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "physics_states.json")
            output_path = os.path.join(tmpdir, "reference_stats.json")
            
            # Create test input
            test_states = {
                "topology_id": "test",
                "timesteps": [
                    {
                        "vertex_positions": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
                        "joint_angles": [0.5],
                        "timestamp": 0.0
                    },
                    {
                        "vertex_positions": [[0.1, 0.0, 0.0], [1.1, 0.0, 0.0]],
                        "joint_angles": [0.6],
                        "timestamp": 1.0
                    }
                ]
            }
            
            with open(input_path, 'w') as f:
                json.dump(test_states, f)
            
            result = compute_reference_stats_from_file(input_path, output_path)
            
            # Verify result structure
            self.assertIn("n_samples", result)
            self.assertIn("n_features", result)
            self.assertIn("output_path", result)
            
            # Verify output file exists
            self.assertTrue(os.path.exists(output_path))
            
            # Verify output content
            with open(output_path, 'r') as f:
                stats = json.load(f)
            
            self.assertIn("mean", stats)
            self.assertIn("covariance", stats)
            self.assertEqual(stats["n_features"], 7)  # 6 vertex + 1 joint


if __name__ == "__main__":
    unittest.main()
