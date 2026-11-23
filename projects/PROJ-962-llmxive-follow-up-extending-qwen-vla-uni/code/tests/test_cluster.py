"""
Integration test for the clustering pipeline with synthetic data.

This test verifies that the clustering pipeline produces valid results:
- Silhouette score > 0.25
- Cluster count <= 50
- Minimum samples per cluster met
"""
import unittest
import sys
import os
import tempfile
import shutil
import json
import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.seeds import set_global_seed
from utils.kinematics import extract_kinematic_features, normalize_joint_angles
from utils.config import get_clustering_params


class TestClusteringPipeline(unittest.TestCase):
    """Integration tests for the clustering pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        set_global_seed(42)
        self.temp_dir = tempfile.mkdtemp()
        
        # Generate synthetic trajectory data
        self.num_samples = 1000
        self.num_joints = 7
        self.trajectory_length = 50
        
        # Create synthetic data with clear clusters
        self.data = []
        self.labels = []
        
        # Cluster 0: Low velocity, low acceleration
        for _ in range(400):
            traj = np.random.uniform(-0.1, 0.1, (self.trajectory_length, self.num_joints))
            self.data.append(traj.flatten())
            self.labels.append(0)
            
        # Cluster 1: High velocity, high acceleration
        for _ in range(400):
            traj = np.random.uniform(-1.0, 1.0, (self.trajectory_length, self.num_joints))
            self.data.append(traj.flatten())
            self.labels.append(1)
            
        # Cluster 2: Medium velocity
        for _ in range(200):
            traj = np.random.uniform(-0.5, 0.5, (self.trajectory_length, self.num_joints))
            self.data.append(traj.flatten())
            self.labels.append(2)
            
        self.df = pd.DataFrame({
            'trajectory': self.data,
            'true_label': self.labels
        })

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_clustering_quality(self):
        """Test that clustering produces valid results."""
        # Import clustering functions
        from code.utils.validation import validate_cluster_assignments
        from code.utils.config import get_config
        
        # Extract features
        features = []
        for _, row in self.df.iterrows():
            traj = np.array(row['trajectory']).reshape(self.trajectory_length, self.num_joints)
            feats = extract_kinematic_features(traj)
            # Use velocity as feature
            vel = feats['velocities'].flatten()
            features.append(vel)
            
        X = np.array(features)
        
        # Normalize
        X_norm = (X - X.mean(axis=0)) / X.std(axis=0)
        
        # Run K-means with k=3
        from sklearn.cluster import KMeans
        k = 3
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X_norm)
        
        # Calculate silhouette score
        if k > 1 and len(set(cluster_labels)) > 1:
            score = silhouette_score(X_norm, cluster_labels)
            self.assertGreater(score, 0.25, f"Silhouette score {score:.4f} is below 0.25 threshold")
        else:
            self.skipTest("Cannot calculate silhouette score with single cluster")
            
        # Check cluster count
        unique_clusters = len(set(cluster_labels))
        self.assertLessEqual(unique_clusters, 50, f"Cluster count {unique_clusters} exceeds 50")
        
        # Check minimum samples per cluster
        min_samples = min(np.bincount(cluster_labels))
        self.assertGreaterEqual(min_samples, 100, f"Minimum cluster size {min_samples} is below 100")

    def test_clustering_with_validation_params(self):
        """Test clustering respects configuration parameters."""
        params = get_clustering_params()
        k_reduction_step = params.get('k_reduction_step_size', 5)
        max_attempts = params.get('max_k_reduction_attempts', 10)
        
        self.assertIsInstance(k_reduction_step, int)
        self.assertGreater(k_reduction_step, 0)
        self.assertIsInstance(max_attempts, int)
        self.assertGreater(max_attempts, 0)


if __name__ == '__main__':
    unittest.main()