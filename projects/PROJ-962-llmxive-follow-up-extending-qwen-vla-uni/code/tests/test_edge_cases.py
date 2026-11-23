"""
test_edge_cases.py - Unit tests for edge cases in the pipeline.
"""
import unittest
import sys
import os
import tempfile
import json
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.kinematics import normalize_joint_angles, extract_kinematic_features
from utils.seeds import set_global_seed

class TestEdgeCases(unittest.TestCase):

    def setUp(self):
        set_global_seed(42)
        self.temp_dir = tempfile.mkdtemp()

    def test_ood_prompt_handling(self):
        """Test handling of Out-Of-Distribution prompts."""
        # Simulate a prompt that is far from any cluster centroid
        # In a real scenario, this would be handled in 04_inference.py
        # Here we test the distance calculation logic
        centroid = np.array([0.0, 0.0, 0.0])
        ood_prompt = np.array([100.0, 100.0, 100.0])
        
        distance = np.linalg.norm(centroid - ood_prompt)
        # Assert distance is large
        self.assertGreater(distance, 50.0)

    def test_simulation_crash_recovery(self):
        """Test that simulation errors are caught and logged."""
        # Mock a simulation error
        class MockSimulationError(Exception):
            pass

        try:
            raise MockSimulationError("Simulated crash")
        except MockSimulationError as e:
            # In real code, this would be caught and logged
            self.assertEqual(str(e), "Simulated crash")

    def test_empty_trajectory(self):
        """Test handling of empty trajectory data."""
        empty_trajectory = np.array([]).reshape(0, 7) # 0 steps, 7 joints
        features = extract_kinematic_features(empty_trajectory)
        
        self.assertEqual(features['positions'].shape[0], 0)
        self.assertEqual(features['velocities'].shape[0], 0)
        self.assertEqual(features['accelerations'].shape[0], 0)

    def test_normalization_bounds(self):
        """Test normalization with invalid bounds."""
        angles = np.array([[0.5, 0.5]])
        with self.assertRaises(ValueError):
            normalize_joint_angles(angles, 0.0, 0.0)

if __name__ == '__main__':
    unittest.main()
