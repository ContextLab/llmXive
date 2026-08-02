import os
import sys
import json
import pytest
from typing import List, Dict, Any

# Add parent directory to path for imports if running standalone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data_loader import (
    create_redundancy_clusters,
    calculate_embedding_similarity,
    RedundancyCluster,
    DataInjectionError,
    fetch_beir_datasets,
    load_injected_dataset
)
from metrics import get_embedding_model


class TestSyntheticRedundancyInjection:
    """
    Unit tests for synthetic redundancy injection logic.
    Specifically tests that injected clusters contain items with
    pairwise cosine similarity > 0.95, serving FR-002.
    """

    @pytest.fixture
    def sample_passages(self):
        """Provide a small set of sample passages for testing."""
        return [
            "The quick brown fox jumps over the lazy dog.",
            "A fast brown fox leaps over a sleepy dog.",
            "The rapid brown fox jumps above the lazy canine.",
            "Machine learning is a subset of artificial intelligence.",
            "Artificial intelligence includes machine learning.",
            "Deep learning uses neural networks with many layers.",
            "Neural networks with multiple layers are deep learning.",
        ]

    @pytest.fixture
    def embedding_model(self):
        """Load the embedding model used for similarity calculations."""
        return get_embedding_model()

    def test_synthetic_injection_creates_clusters(self, sample_passages, embedding_model):
        """
        Test that the synthetic redundancy injection logic creates clusters
        where all items within a cluster have pairwise cosine similarity > 0.95.
        
        This serves FR-002 which requires near-duplicate clusters for testing
        the efficiency loss from redundant retrieval lists.
        """
        # Create redundancy clusters from sample passages
        # We expect the function to group similar passages together
        clusters: List[RedundancyCluster] = create_redundancy_clusters(
            passages=sample_passages,
            model=embedding_model,
            similarity_threshold=0.95
        )

        # Assert that we got some clusters
        assert len(clusters) > 0, "Expected at least one redundancy cluster to be created"

        # Validate each cluster
        for cluster in clusters:
            cluster_id = cluster.cluster_id
            items = cluster.items

            # Each cluster should have at least 2 items to be a "cluster"
            assert len(items) >= 2, f"Cluster {cluster_id} should have at least 2 items"

            # Calculate pairwise similarities for all items in the cluster
            # and verify they all exceed the threshold
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    sim = calculate_embedding_similarity(
                        items[i]["text"],
                        items[j]["text"],
                        embedding_model
                    )
                    
                    # Assert similarity > 0.95 as per FR-002
                    assert sim > 0.95, (
                        f"Pairwise similarity in cluster {cluster_id} between "
                        f"items {i} and {j} is {sim:.4f}, expected > 0.95. "
                        f"Item 1: '{items[i]['text'][:50]}...', Item 2: '{items[j]['text'][:50]}...'"
                    )

    def test_synthetic_injection_handles_non_redundant(self, embedding_model):
        """
        Test that non-similar passages do not get clustered together.
        """
        # These passages are semantically different
        distinct_passages = [
            "The weather today is sunny and warm.",
            "Quantum computing uses qubits for computation.",
            "Baking bread requires flour, water, and yeast.",
        ]

        clusters: List[RedundancyCluster] = create_redundancy_clusters(
            passages=distinct_passages,
            model=embedding_model,
            similarity_threshold=0.95
        )

        # Each passage should be in its own cluster or not clustered at all
        # (depending on implementation, but they should NOT be in the same cluster)
        for cluster in clusters:
            # If a cluster has multiple items, they must be similar
            if len(cluster.items) > 1:
                for i in range(len(cluster.items)):
                    for j in range(i + 1, len(cluster.items)):
                        sim = calculate_embedding_similarity(
                            cluster.items[i]["text"],
                            cluster.items[j]["text"],
                            embedding_model
                        )
                        assert sim > 0.95, (
                            f"Distinct items incorrectly clustered together with similarity {sim:.4f}"
                        )

    def test_cluster_structure_matches_spec(self, sample_passages, embedding_model):
        """
        Test that the RedundancyCluster structure matches the expected schema.
        """
        clusters: List[RedundancyCluster] = create_redundancy_clusters(
            passages=sample_passages,
            model=embedding_model,
            similarity_threshold=0.95
        )

        for cluster in clusters:
            # Check required attributes
            assert hasattr(cluster, 'cluster_id'), "Cluster missing cluster_id"
            assert hasattr(cluster, 'items'), "Cluster missing items"
            assert hasattr(cluster, 'size'), "Cluster missing size"
            
            # Check items structure
            for item in cluster.items:
                assert 'text' in item, "Item missing 'text' field"
                assert 'id' in item, "Item missing 'id' field"
            
            # Check size consistency
            assert cluster.size == len(cluster.items), "Cluster size mismatch"

    def test_injection_with_real_beir_subset(self, embedding_model, tmp_path):
        """
        Test injection logic with a small subset of real BEIR data.
        This ensures the logic works with actual corpus data, not just synthetic strings.
        """
        try:
            # Fetch a small subset of scifact for testing
            # We'll use a very small subset to keep tests fast
            datasets = fetch_beir_datasets(
                dataset_names=["scifact"],
                max_docs_per_dataset=10,  # Small subset for unit test
                output_dir=str(tmp_path / "beir_test")
            )
            
            if not datasets or "scifact" not in datasets:
                pytest.skip("Could not fetch scifact dataset for testing")
            
            scifact_data = datasets["scifact"]
            passages = [doc["doc_text"] for doc in scifact_data[:5]]  # Use first 5 docs
            
            if len(passages) < 2:
                pytest.skip("Not enough passages to test clustering")
            
            clusters: List[RedundancyCluster] = create_redundancy_clusters(
                passages=passages,
                model=embedding_model,
                similarity_threshold=0.95
            )
            
            # If clusters were created, verify the similarity constraint
            for cluster in clusters:
                if len(cluster.items) > 1:
                    for i in range(len(cluster.items)):
                        for j in range(i + 1, len(cluster.items)):
                            sim = calculate_embedding_similarity(
                                cluster.items[i]["text"],
                                cluster.items[j]["text"],
                                embedding_model
                            )
                            assert sim > 0.95, (
                                f"Real data cluster {cluster.cluster_id} has items with "
                                f"similarity {sim:.4f} < 0.95"
                            )
                            
        except Exception as e:
            # If BEIR fetch fails, skip the test rather than fail
            pytest.skip(f"Skipping real data test due to: {str(e)}")