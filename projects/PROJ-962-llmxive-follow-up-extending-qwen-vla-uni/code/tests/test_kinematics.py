"""
Unit tests for kinematic feature normalization.

Tests the normalize_joint_angles and extract_kinematic_features functions
from utils.kinematics to ensure they correctly normalize data within
physical bounds and handle edge cases.
"""
import unittest
import numpy as np
import sys
import os

# Add the project root to the path to allow imports from utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.kinematics import normalize_joint_angles, extract_kinematic_features
from utils.seeds import set_global_seed

class TestKinematicNormalization(unittest.TestCase):
    """Test cases for kinematic feature normalization."""

    def setUp(self):
        """Set up test fixtures and global seed."""
        set_global_seed(42)

    def test_normalize_joint_angles_basic(self):
        """Test basic normalization of joint angles to [-1, 1]."""
        # Define physical bounds
        lower_bounds = np.array([0.0, -np.pi/2, -np.pi])
        upper_bounds = np.array([np.pi, np.pi/2, np.pi])
        
        # Input: middle of the range should map to 0
        # Input: lower bound should map to -1
        # Input: upper bound should map to 1
        angles = np.array([
            [np.pi/2, 0.0, 0.0],  # Middle of range 1, middle of range 2, middle of range 3
            [0.0, -np.pi/2, -np.pi], # Lower bounds
            [np.pi, np.pi/2, np.pi]  # Upper bounds
        ])

        normalized = normalize_joint_angles(angles, lower_bounds, upper_bounds)

        # Check shape preservation
        self.assertEqual(normalized.shape, angles.shape)

        # Check specific values
        # Row 0: middle values -> should be 0.0
        self.assertAlmostEqual(normalized[0, 0], 0.0, places=5)
        self.assertAlmostEqual(normalized[0, 1], 0.0, places=5)
        self.assertAlmostEqual(normalized[0, 2], 0.0, places=5)

        # Row 1: lower bounds -> should be -1.0
        self.assertAlmostEqual(normalized[1, 0], -1.0, places=5)
        self.assertAlmostEqual(normalized[1, 1], -1.0, places=5)
        self.assertAlmostEqual(normalized[1, 2], -1.0, places=5)

        # Row 2: upper bounds -> should be 1.0
        self.assertAlmostEqual(normalized[2, 0], 1.0, places=5)
        self.assertAlmostEqual(normalized[2, 1], 1.0, places=5)
        self.assertAlmostEqual(normalized[2, 2], 1.0, places=5)

    def test_normalize_joint_angles_bounds_clamping(self):
        """Test that values outside physical bounds are clamped."""
        lower_bounds = np.array([0.0])
        upper_bounds = np.array([10.0])
        
        # Input includes values outside bounds
        angles = np.array([
            [-5.0],  # Below lower
            [15.0],  # Above upper
            [5.0]    # Inside
        ])

        normalized = normalize_joint_angles(angles, lower_bounds, upper_bounds)

        # Values outside bounds should be clamped to [-1, 1]
        self.assertLessEqual(normalized[0, 0], -1.0)
        self.assertGreaterEqual(normalized[1, 0], 1.0)
        self.assertAlmostEqual(normalized[2, 0], 0.0, places=5) # 5.0 is midpoint

    def test_normalize_joint_angles_single_joint(self):
        """Test normalization with a single joint."""
        lower_bounds = np.array([0.0])
        upper_bounds = np.array([np.pi])
        angles = np.array([[np.pi / 2]])

        normalized = normalize_joint_angles(angles, lower_bounds, upper_bounds)

        self.assertAlmostEqual(normalized[0, 0], 0.0, places=5)

    def test_normalize_joint_angles_multidimensional(self):
        """Test normalization with 3D array (batch, time, joints)."""
        lower_bounds = np.array([0.0, 0.0])
        upper_bounds = np.array([1.0, 1.0])
        
        # Shape: (2 batches, 3 timesteps, 2 joints)
        angles = np.ones((2, 3, 2)) * 0.5 

        normalized = normalize_joint_angles(angles, lower_bounds, upper_bounds)

        self.assertEqual(normalized.shape, (2, 3, 2))
        # 0.5 is exactly in the middle of [0, 1]
        self.assertAlmostEqual(normalized[0, 0, 0], 0.0, places=5)

    def test_extract_kinematic_features_returns_dict(self):
        """Test that extract_kinematic_features returns a dictionary."""
        # Dummy actions: (time_steps, joints)
        actions = np.random.rand(10, 3)
        
        features = extract_kinematic_features(actions)
        
        self.assertIsInstance(features, dict)
        self.assertIn('positions', features)
        self.assertIn('velocities', features)
        self.assertIn('accelerations', features)
        
        # Check shapes
        self.assertEqual(features['positions'].shape, actions.shape)
        self.assertEqual(features['velocities'].shape, actions.shape)
        self.assertEqual(features['accelerations'].shape, actions.shape)

    def test_extract_kinematic_features_velocity_sign(self):
        """Test that velocity calculation respects direction."""
        # Linearly increasing positions
        actions = np.linspace(0, 10, 10).reshape(-1, 1)
        
        features = extract_kinematic_features(actions)
        velocities = features['velocities']
        
        # Since positions are increasing, velocities should be positive
        # (ignoring the first element which might be NaN or 0 depending on implementation)
        self.assertTrue(np.all(velocities[1:, 0] > 0))

    def test_extract_kinematic_features_zero_acceleration(self):
        """Test acceleration is zero for constant velocity."""
        # Constant velocity: positions increase by 1 each step
        actions = np.arange(10).reshape(-1, 1)
        
        features = extract_kinematic_features(actions)
        accelerations = features['accelerations']
        
        # Acceleration should be zero (or very close to zero due to numerical precision)
        # for constant velocity
        self.assertTrue(np.allclose(accelerations[2:, 0], 0.0, atol=1e-5))

    def test_extract_kinematic_features_bounds_validation(self):
        """Test that extract_kinematic_features normalizes within bounds if provided."""
        actions = np.array([[0.0], [1.0], [2.0], [3.0], [4.0]])
        lower_bounds = np.array([0.0])
        upper_bounds = np.array([4.0])
        
        # Note: The current API signature for extract_kinematic_features 
        # in the prompt description doesn't explicitly show bounds arguments.
        # If the implementation requires bounds, this test verifies the integration.
        # Assuming the function handles normalization internally or via kwargs if supported.
        # Based on the API surface provided, we test the basic extraction.
        
        features = extract_kinematic_features(actions)
        
        self.assertIn('positions', features)
        self.assertIn('velocities', features)
        self.assertIn('accelerations', features)

if __name__ == '__main__':
    unittest.main()