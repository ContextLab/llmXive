"""
Integration test for the full UMAP -> DBSCAN -> Fisher pipeline.

This test verifies the end-to-end execution of User Story 2:
1. Loads processed descriptor data (output of US1).
2. Applies UMAP dimensionality reduction.
3. Applies DBSCAN clustering.
4. Performs Fisher's exact test for cluster enrichment.
5. Validates that the pipeline produces expected output artifacts
   (embedding, clustering results) without errors.
"""
import os
import sys
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import get_project_root, get_data_processed_path, load_config
from src.analysis.dimensionality import apply_umap
from src.analysis.clustering import run_dbscan, run_fisher_enrichment, run_label_permutation_test


class TestFullClusteringPipeline:
    """Integration tests for the UMAP -> DBSCAN -> Fisher pipeline."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self, tmp_path):
        """
        Setup a temporary directory structure to mimic the project data paths
        for this integration test. This ensures we don't pollute the real
        data directory during testing.
        """
        self.project_root = tmp_path
        self.processed_dir = self.project_root / "data" / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock config file to override paths for this test
        self.config_path = self.project_root / "config.json"
        mock_config = {
            "random_seed": 42,
            "permutation_iterations": 100,  # Reduced for faster testing
            "umap_n_neighbors": 15,
            "umap_min_dist": 0.1,
            "dbscan_eps": 0.5,
            "dbscan_min_samples": 10
        }
        with open(self.config_path, "w") as f:
            json.dump(mock_config, f)

        # Patch the config loading functions to use our temp paths
        # We do this by monkey-patching the specific functions used by the modules
        # or by setting environment variables if the config logic supports it.
        # Since the existing config.py uses a specific path, we will create a
        # temporary config file and ensure the test environment points to it,
        # or we will mock the get_project_root if necessary.
        # However, to keep it simple and robust, we will rely on the fact that
        # the functions accept optional arguments or we can patch the specific
        # config loading behavior.
        #
        # For this integration test, we will assume the functions are called
        # with explicit paths or the global config is updated.
        # We'll create a minimal descriptors.csv to test the pipeline.
        self.descriptors_file = self.processed_dir / "descriptors.csv"
        self.umap_embedding_file = self.processed_dir / "umap_embedding.csv"
        self.clustering_results_file = self.processed_dir / "clustering_results.json"

        # Generate mock descriptor data
        np.random.seed(42)
        n_samples = 100
        n_descriptors = 10
        mock_data = {
            "InChIKey": [f"KEY{i:04d}" for i in range(n_samples)],
            "resistance_frequency": np.random.uniform(0, 1, n_samples),
            **{f"desc_{i}": np.random.uniform(0, 100, n_samples) for i in range(n_descriptors)}
        }
        mock_df = pd.DataFrame(mock_data)
        mock_df.to_csv(self.descriptors_file, index=False)

        # Store references for assertions
        self.tmp_path = tmp_path
        self.descriptors_file = self.descriptors_file
        self.umap_embedding_file = self.umap_embedding_file
        self.clustering_results_file = self.clustering_results_file

    def test_full_pipeline_execution(self):
        """
        Test that the full pipeline (UMAP -> DBSCAN -> Fisher) executes
        without errors and produces the expected output files.
        """
        # 1. Load data
        data = pd.read_csv(self.descriptors_file)
        descriptor_cols = [col for col in data.columns if col.startswith("desc_")]
        X = data[descriptor_cols].values
        resistance = data["resistance_frequency"].values

        # 2. Apply UMAP
        # We need to ensure the config is loaded correctly.
        # Since we are in a temp dir, we need to point the config functions to it.
        # We will patch the get_project_root function temporarily.
        import src.config as config_module
        original_get_project_root = config_module.get_project_root

        def mock_get_project_root():
            return self.tmp_path

        config_module.get_project_root = mock_get_project_root

        try:
            # Run UMAP
            embedding = apply_umap(X, n_components=2)
            assert embedding.shape == (X.shape[0], 2), "UMAP embedding shape mismatch"

            # Save embedding to disk (simulating T022)
            embedding_df = pd.DataFrame(embedding, columns=["UMAP1", "UMAP2"])
            embedding_df["InChIKey"] = data["InChIKey"]
            embedding_df.to_csv(self.umap_embedding_file, index=False)
            assert self.umap_embedding_file.exists(), "UMAP embedding file not created"

            # 3. Apply DBSCAN
            # Run DBSCAN on the embedding
            cluster_labels = run_dbscan(embedding, eps=0.5, min_samples=10)
            assert len(cluster_labels) == len(embedding), "Cluster labels length mismatch"

            # 4. Run Fisher's Exact Test
            # We need to binarize resistance for the test (High/Low)
            # Using median as a simple threshold for the test
            median_res = np.median(resistance)
            binary_resistance = (resistance > median_res).astype(int)

            results = run_fisher_enrichment(
                cluster_labels=cluster_labels,
                binary_resistance=binary_resistance,
                permutation_iterations=100,
                seed=42
            )

            # 5. Verify results structure
            assert isinstance(results, dict), "Fisher results should be a dict"
            assert "clusters" in results, "Results should contain 'clusters' key"
            assert "permutation_p_value" in results, "Results should contain permutation p-value"

            # Save results to disk (simulating T028)
            with open(self.clustering_results_file, "w") as f:
                json.dump(results, f, indent=2)
            assert self.clustering_results_file.exists(), "Clustering results file not created"

            # 6. Run Permutation Test (T026)
            perm_results = run_label_permutation_test(
                cluster_labels=cluster_labels,
                binary_resistance=binary_resistance,
                iterations=100,
                seed=42
            )
            assert "observed_statistic" in perm_results, "Permutation results missing observed statistic"
            assert "null_distribution" in perm_results, "Permutation results missing null distribution"
            assert "p_value" in perm_results, "Permutation results missing p-value"

        finally:
            # Restore original function
            config_module.get_project_root = original_get_project_root

    def test_pipeline_handles_empty_clusters(self):
        """
        Test that the pipeline handles cases where DBSCAN finds no valid clusters
        (e.g., all points are noise or too few points).
        """
        # Load data
        data = pd.read_csv(self.descriptors_file)
        descriptor_cols = [col for col in data.columns if col.startswith("desc_")]
        X = data[descriptor_cols].values
        resistance = data["resistance_frequency"].values

        import src.config as config_module
        original_get_project_root = config_module.get_project_root
        def mock_get_project_root():
            return self.tmp_path
        config_module.get_project_root = mock_get_project_root

        try:
            # Use a very high eps to force all points into one cluster or very few
            # But actually, we want to test the "no clusters" or "insufficient power" case.
            # Let's create a scenario where DBSCAN returns all -1 (noise) or very small clusters.
            # We'll manually simulate this for the Fisher test logic.
            
            # Run UMAP
            embedding = apply_umap(X, n_components=2)
            
            # Simulate a case where all points are noise (label -1)
            cluster_labels = np.full(len(embedding), -1)
            
            median_res = np.median(resistance)
            binary_resistance = (resistance > median_res).astype(int)
            
            # This should not crash, but return a result indicating no valid clusters
            results = run_fisher_enrichment(
                cluster_labels=cluster_labels,
                binary_resistance=binary_resistance,
                permutation_iterations=10, # Small for speed
                seed=42
            )
            
            # Verify that the result structure is valid even with no clusters
            assert isinstance(results, dict)
            # The specific content depends on the implementation of run_fisher_enrichment
            # but it should not raise an exception.
            
        finally:
            config_module.get_project_root = original_get_project_root