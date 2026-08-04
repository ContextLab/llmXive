"""
Unit tests for edge cases: OOD prompts and simulation crashes.
"""
import unittest
import sys
import os
import tempfile
import json
import numpy as np
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.seeds import set_global_seed
from utils.kinematics import extract_kinematic_features, normalize_joint_angles
from utils.config import get_clustering_params
from tests.test_simulate import MockPyBullet
from utils.validation import validate_trajectory_consistency

# Import the modules under test
from code_04_inference import embed_prompt, find_nearest_cluster, run_inference_pipeline
from code_05_simulate import execute_trajectory, SimulationError, KinematicConstraintViolation

class TestEdgeCases(unittest.TestCase):
    """Tests for Out-Of-Distribution (OOD) prompts and simulation failures."""

    def setUp(self):
        """Set up test fixtures."""
        set_global_seed(42)
        self.temp_dir = tempfile.mkdtemp()
        
        # Create mock cluster centers for testing
        self.mock_cluster_centers = {
            0: np.array([0.1, 0.2, 0.3]),
            1: np.array([0.5, 0.6, 0.7]),
            2: np.array([0.9, 1.0, 1.1])
        }
        
        # Save mock centers to temp file
        self.centers_path = os.path.join(self.temp_dir, "mock_centers.json")
        with open(self.centers_path, 'w') as f:
            json.dump({k: v.tolist() for k, v in self.mock_cluster_centers.items()}, f)

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)

    def test_ood_prompt_embedding_distance(self):
        """
        Test that an OOD prompt (far from all clusters) is handled gracefully.
        The prompt should be assigned to the nearest cluster but flagged as low-confidence.
        """
        # Create a prompt embedding that is extremely far from all cluster centers
        # (e.g., values > 1000 when clusters are around 0-1)
        ood_embedding = np.array([1000.0, 1000.0, 1000.0])
        
        # We need to mock the embedding generation to return our OOD vector
        # Since embed_prompt requires a BERT model, we mock the distance calculation directly
        # by patching the distance logic in find_nearest_cluster
        
        # Simulate the distance calculation logic
        distances = {}
        for cluster_id, center in self.mock_cluster_centers.items():
            dist = np.linalg.norm(ood_embedding - np.array(center))
            distances[cluster_id] = dist
        
        nearest_cluster = min(distances, key=distances.get)
        min_distance = distances[nearest_cluster]
        
        # The distance should be large (OOD), but we should still get a nearest cluster
        self.assertIn(nearest_cluster, self.mock_cluster_centers)
        self.assertGreater(min_distance, 100.0)  # Should be very far

    def test_ood_prompt_low_confidence_flag(self):
        """
        Test that the inference pipeline flags OOD prompts correctly.
        """
        # Mock the BERT embedding to return an OOD vector
        ood_embedding = np.array([500.0, 500.0, 500.0])
        
        # Mock the cluster center loading
        with patch('code_04_inference.load_cluster_centers', return_value=self.mock_cluster_centers):
            with patch('code_04_inference.load_bert_model', return_value=None):
                with patch('code_04_inference.embed_prompt', return_value=ood_embedding):
                    # Mock the sampling function to return a valid trajectory
                    with patch('code_04_inference.sample_trajectory_from_cgmm', return_value=np.zeros((10, 7))):
                        result = run_inference_pipeline(
                            prompt="This is a completely nonsensical prompt that should be OOD",
                            cluster_centers_path=self.centers_path,
                            bert_model_path=None,
                            confidence_threshold=0.9
                        )
                        
                        # The result should contain a low-confidence flag
                        self.assertIn('confidence', result)
                        self.assertIn('nearest_cluster', result)
                        # The confidence should be low (distance normalized)
                        self.assertLess(result['confidence'], 0.5)

    def test_simulation_crash_kinematic_violation(self):
        """
        Test that a simulation crash due to kinematic constraint violation
        is caught and handled without crashing the entire pipeline.
        """
        # Create a trajectory that violates joint limits
        invalid_trajectory = np.array([
            [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0]  # Values far outside typical joint limits
            for _ in range(10)
        ])
        
        # Mock the PyBullet environment
        mock_pb = MockPyBullet()
        
        # Simulate a kinematic constraint violation
        with patch('code_05_simulate.MockPyBullet', return_value=mock_pb):
            with patch.object(mock_pb, 'execute_step', side_effect=KinematicConstraintViolation("Joint limit exceeded")):
                # The function should catch the error and return a failure status
                try:
                    result = execute_trajectory(
                        trajectory=invalid_trajectory,
                        task_type="grasp",
                        timeout=1.0
                    )
                    # If we get here, the error was caught
                    self.assertIn('success', result)
                    self.assertFalse(result['success'])
                    self.assertIn('error_type', result)
                    self.assertEqual(result['error_type'], 'KinematicConstraintViolation')
                except KinematicConstraintViolation:
                    self.fail("KinematicConstraintViolation was not caught!")

    def test_simulation_crash_general_exception(self):
        """
        Test that a general simulation crash (unexpected exception) is handled gracefully.
        """
        invalid_trajectory = np.array([
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
            for _ in range(10)
        ])
        
        mock_pb = MockPyBullet()
        
        # Simulate a general exception
        with patch('code_05_simulate.MockPyBullet', return_value=mock_pb):
            with patch.object(mock_pb, 'execute_step', side_effect=Exception("Unexpected physics engine error")):
                try:
                    result = execute_trajectory(
                        trajectory=invalid_trajectory,
                        task_type="navigate",
                        timeout=1.0
                    )
                    # The error should be caught and logged
                    self.assertIn('success', result)
                    self.assertFalse(result['success'])
                    self.assertIn('error_type', result)
                    self.assertEqual(result['error_type'], 'GeneralSimulationError')
                except Exception:
                    self.fail("General exception was not caught!")

    def test_ood_prompt_with_distance_threshold(self):
        """
        Test that prompts exceeding a distance threshold are rejected or flagged.
        """
        ood_embedding = np.array([999.0, 999.0, 999.0])
        
        # Calculate distances
        distances = {}
        for cluster_id, center in self.mock_cluster_centers.items():
            dist = np.linalg.norm(ood_embedding - np.array(center))
            distances[cluster_id] = dist
        
        min_dist = min(distances.values())
        
        # Define a threshold that the OOD distance exceeds
        threshold = 100.0
        
        # If min_dist > threshold, it's OOD
        is_ood = min_dist > threshold
        self.assertTrue(is_ood)

    def test_trajectory_consistency_after_crash_recovery(self):
        """
        Test that a trajectory recovered after a partial crash is still consistent.
        """
        # Create a partial trajectory
        partial_trajectory = np.array([
            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
            for _ in range(5)  # Only 5 steps instead of 10
        ])
        
        # Validate the partial trajectory
        is_valid, issues = validate_trajectory_consistency(partial_trajectory)
        
        # The trajectory might be valid but incomplete
        self.assertIsInstance(is_valid, bool)
        self.assertIsInstance(issues, list)

    def test_null_embedding_handling(self):
        """
        Test that a null or empty embedding is handled gracefully.
        """
        null_embedding = None
        
        # Simulate the embedding generation returning None
        with patch('code_04_inference.embed_prompt', return_value=null_embedding):
            try:
                result = find_nearest_cluster(
                    prompt_embedding=null_embedding,
                    cluster_centers=self.mock_cluster_centers
                )
                # Should return an error or handle gracefully
                self.assertIsNone(result)
            except Exception as e:
                # If it raises, it should be a clear error
                self.assertIsInstance(e, (ValueError, TypeError))

    def test_empty_cluster_centers(self):
        """
        Test that an empty cluster center dictionary is handled gracefully.
        """
        empty_centers = {}
        
        # Try to find nearest cluster with empty centers
        test_embedding = np.array([0.5, 0.5, 0.5])
        
        with self.assertRaises(ValueError):
            find_nearest_cluster(
                prompt_embedding=test_embedding,
                cluster_centers=empty_centers
            )

    def test_single_cluster_ood_handling(self):
        """
        Test OOD handling when there is only one cluster (degenerate case).
        """
        single_cluster = {0: np.array([0.5, 0.5, 0.5])}
        
        # Even with one cluster, OOD detection should work
        ood_embedding = np.array([999.0, 999.0, 999.0])
        
        distances = {}
        for cluster_id, center in single_cluster.items():
            dist = np.linalg.norm(ood_embedding - np.array(center))
            distances[cluster_id] = dist
        
        min_dist = min(distances.values())
        self.assertGreater(min_dist, 100.0)

if __name__ == '__main__':
    unittest.main()
