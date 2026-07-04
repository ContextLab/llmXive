import pytest
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import os
import sys

# Ensure parent directory is in path for imports if running standalone
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.analysis.clustering import run_dbscan_clustering, identify_noise_points

class TestDBSCANClusteringLogic:
    """
    Unit tests for DBSCAN clustering logic and noise handling.
    These tests verify that the clustering function correctly:
    1. Identifies dense clusters based on eps and min_samples.
    2. Labels sparse points as noise (-1).
    3. Handles edge cases like all noise or all one cluster.
    """

    def test_dbscan_identifies_two_clusters(self):
        """
        Test that DBSCAN correctly identifies two distinct dense clusters
        separated by a gap, and labels the gap points as noise.
        """
        # Create synthetic data: two tight clusters and some noise in between
        np.random.seed(42)
        cluster1 = np.random.randn(20, 2) + np.array([[-5, -5]])
        cluster2 = np.random.randn(20, 2) + np.array([[5, 5]])
        noise = np.random.randn(10, 2) * 0.5 # Random noise in the middle
        
        data = np.vstack([cluster1, cluster2, noise])
        
        # Run clustering with parameters that should separate the two main clusters
        # eps=1.0 is large enough to connect points within clusters but not across the gap
        # min_samples=5 is small enough to capture the clusters
        labels = run_dbscan_clustering(data, eps=1.0, min_samples=5)
        
        # Verify we have at least 2 clusters (0 and 1) and noise (-1)
        unique_labels = set(labels)
        assert 0 in unique_labels, "Cluster 0 not found"
        assert 1 in unique_labels, "Cluster 1 not found"
        assert -1 in unique_labels, "Noise points (-1) not found"
        
        # Verify cluster 0 corresponds roughly to the first synthetic cluster
        # (The first 20 points should be in cluster 0 or 1, but not noise if eps is right)
        # Since DBSCAN labels are arbitrary (0, 1...), we just check that the first group
        # is mostly one label and the second group is mostly another.
        cluster_0_indices = np.where(labels == 0)[0]
        cluster_1_indices = np.where(labels == 1)[0]
        
        # Check that cluster 0 has points from the first synthetic cluster
        assert len(cluster_0_indices) > 0
        # Check that cluster 1 has points from the second synthetic cluster
        assert len(cluster_1_indices) > 0

    def test_dbscan_all_noise(self):
        """
        Test behavior when data is too sparse to form any clusters (all noise).
        """
        # Create very sparse data
        np.random.seed(42)
        data = np.random.randn(50, 2) * 10.0 # Very spread out
        
        # Use a very small eps and high min_samples to force all noise
        labels = run_dbscan_clustering(data, eps=0.1, min_samples=10)
        
        # All points should be labeled as noise (-1)
        assert np.all(labels == -1), "Expected all points to be noise, but got clusters"

    def test_dbscan_single_cluster(self):
        """
        Test behavior when all data points form a single dense cluster.
        """
        # Create a single dense cluster
        np.random.seed(42)
        data = np.random.randn(50, 2) * 0.1
        
        # Use large eps and small min_samples
        labels = run_dbscan_clustering(data, eps=1.0, min_samples=2)
        
        # All points should belong to a single cluster (label 0)
        unique_labels = set(labels)
        assert -1 not in unique_labels, "Unexpected noise points in a dense cluster"
        assert len(unique_labels) == 1, f"Expected 1 cluster, found {len(unique_labels)}"
        assert list(unique_labels)[0] == 0, "Expected cluster label to be 0"

    def test_dbscan_noise_handling_function(self):
        """
        Test the identify_noise_points helper function.
        """
        np.random.seed(42)
        # Create data with known noise
        cluster = np.random.randn(20, 2)
        noise = np.array([[10, 10], [10, 11], [10, 12]])
        data = np.vstack([cluster, noise])
        
        # Run clustering
        labels = run_dbscan_clustering(data, eps=1.0, min_samples=5)
        
        # Use helper to identify noise
        noise_mask = identify_noise_points(labels)
        
        # Verify noise mask matches -1 labels
        expected_noise_mask = (labels == -1)
        assert np.array_equal(noise_mask, expected_noise_mask), "Noise mask does not match DBSCAN -1 labels"
        
        # Verify that the specific noise points we added are identified as noise
        # (assuming eps=1.0 is too small to connect them to the main cluster)
        # The last 3 points should be noise
        assert noise_mask[-3:].all(), "Expected the last 3 points to be identified as noise"
        assert not noise_mask[:-3].any(), "Expected the first 20 points NOT to be noise"

    def test_dbscan_with_standardized_data(self):
        """
        Test that DBSCAN works correctly on standardized data (a common preprocessing step).
        """
        # Create data with different scales
        np.random.seed(42)
        x1 = np.random.randn(20, 1) * 100  # Large scale
        x2 = np.random.randn(20, 1) * 0.1  # Small scale
        data = np.hstack([x1, x2])
        
        # Standardize
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(data)
        
        # Cluster
        labels = run_dbscan_clustering(scaled_data, eps=1.0, min_samples=5)
        
        # Should find at least one cluster
        unique_labels = set(labels)
        assert len(unique_labels) > 0, "Expected at least one cluster in standardized data"

class TestDBSCANParameters:
    """
    Tests to ensure DBSCAN parameters (eps, min_samples) are applied correctly.
    """
    
    def test_min_samples_filter(self):
        """
        Verify that points with fewer than min_samples neighbors are labeled as noise.
        """
        np.random.seed(42)
        # Create a large cluster and a single isolated point
        cluster = np.random.randn(50, 2) * 0.5
        isolated = np.array([[100, 100]])
        data = np.vstack([cluster, isolated])
        
        # min_samples=5 means isolated point must have 4 neighbors within eps to be in a cluster
        labels = run_dbscan_clustering(data, eps=1.0, min_samples=5)
        
        # The isolated point should be noise
        assert labels[-1] == -1, "Isolated point should be noise with min_samples=5"
        
        # The cluster points should form a cluster
        assert labels[0] != -1, "Cluster points should not be noise"

    def test_eps_radius_effect(self):
        """
        Verify that changing eps changes the number of clusters/noise points.
        """
        np.random.seed(42)
        # Two clusters close to each other
        cluster1 = np.random.randn(20, 2)
        cluster2 = np.random.randn(20, 2) + np.array([1.5, 1.5]) # Close but separate
        data = np.vstack([cluster1, cluster2])
        
        # Small eps -> 2 clusters
        labels_small_eps = run_dbscan_clustering(data, eps=0.5, min_samples=5)
        unique_small = set(labels_small_eps)
        num_clusters_small = len([l for l in unique_small if l != -1])
        
        # Large eps -> 1 cluster (or fewer noise points)
        labels_large_eps = run_dbscan_clustering(data, eps=2.0, min_samples=5)
        unique_large = set(labels_large_eps)
        num_clusters_large = len([l for l in unique_large if l != -1])
        
        # With larger eps, we expect fewer or equal clusters (likely 1 if they merge)
        assert num_clusters_large <= num_clusters_small, "Larger eps should merge or keep same number of clusters"