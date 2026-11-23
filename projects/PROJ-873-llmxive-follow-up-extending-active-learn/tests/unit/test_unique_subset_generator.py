import pytest
import json
import os
import tempfile
from code.unique_subset_generator import (
    identify_unique_representatives,
    filter_to_unique_subset,
    generate_unique_subset,
    UniqueSubsetResult
)
from code.data_loader import RedundancyCluster
from code.models import CandidateList

@pytest.fixture
def sample_clusters():
    """Create sample redundancy clusters for testing."""
    return [
        RedundancyCluster(cluster_id=0, indices=[0, 1, 2], similarity_scores=[0.96, 0.97, 0.95]),
        RedundancyCluster(cluster_id=1, indices=[5, 6], similarity_scores=[0.98, 0.96]),
        RedundancyCluster(cluster_id=2, indices=[10, 11, 12, 13], similarity_scores=[0.96, 0.97, 0.95, 0.96]),
    ]

@pytest.fixture
def sample_candidate_list():
    """Create a sample candidate list for testing."""
    documents = [f"Document {i}" for i in range(20)]
    scores = [1.0 - (i * 0.05) for i in range(20)]
    query_ids = [1] * 20
    
    return CandidateList(
        documents=documents,
        scores=scores,
        query_ids=query_ids,
        original_indices=list(range(20))
    )

def test_identify_unique_representatives(sample_clusters):
    """Test that unique representatives are correctly identified."""
    representative_map, unique_indices = identify_unique_representatives(sample_clusters)
    
    # Check that each cluster has exactly one representative
    assert len(unique_indices) == 3
    
    # Check that representatives are the first items in each cluster
    assert unique_indices == [0, 5, 10]
    
    # Check that all cluster members map to their representative
    assert representative_map[0] == 0
    assert representative_map[1] == 0
    assert representative_map[2] == 0
    
    assert representative_map[5] == 5
    assert representative_map[6] == 5
    
    assert representative_map[10] == 10
    assert representative_map[11] == 10
    assert representative_map[12] == 10
    assert representative_map[13] == 10

def test_filter_to_unique_subset(sample_candidate_list, sample_clusters):
    """Test that filtering removes near-duplicates correctly."""
    unique_subset = filter_to_unique_subset(sample_candidate_list, sample_clusters)
    
    # Original had 20 items, we removed clusters:
    # Cluster 0: 3 items -> keep 1 (remove 2)
    # Cluster 1: 2 items -> keep 1 (remove 1)
    # Cluster 2: 4 items -> keep 1 (remove 3)
    # Total removed: 2 + 1 + 3 = 6
    # Expected unique: 20 - 6 = 14
    
    assert len(unique_subset.documents) == 14
    assert len(unique_subset.scores) == 14
    assert len(unique_subset.query_ids) == 14
    
    # Check that unique items are the representatives
    expected_indices = [0, 3, 4, 5, 7, 8, 9, 10, 14, 15, 16, 17, 18, 19]
    # Plus the cluster representatives: 0, 5, 10
    # But 0, 5, 10 are already in the list
    # So the unique indices should be: 0, 3, 4, 5, 7, 8, 9, 10, 14, 15, 16, 17, 18, 19
    
    # Actually, let's recalculate:
    # All items: 0-19
    # Cluster 0: [0, 1, 2] -> keep 0, remove 1, 2
    # Cluster 1: [5, 6] -> keep 5, remove 6
    # Cluster 2: [10, 11, 12, 13] -> keep 10, remove 11, 12, 13
    # Non-cluster items: 3, 4, 7, 8, 9, 14, 15, 16, 17, 18, 19
    # Total unique: 3 (representatives) + 11 (non-clusters) = 14
    
    expected_unique_indices = [0, 3, 4, 5, 7, 8, 9, 10, 14, 15, 16, 17, 18, 19]
    assert unique_subset.original_indices == expected_unique_indices

def test_generate_unique_subset_integration():
    """Integration test for the full unique subset generation pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample dataset
        dataset_path = os.path.join(tmpdir, "dataset.json")
        clusters_path = os.path.join(tmpdir, "clusters.json")
        output_path = os.path.join(tmpdir, "unique_subset.json")
        
        documents = [f"Document {i}" for i in range(20)]
        scores = [1.0 - (i * 0.05) for i in range(20)]
        query_ids = [1] * 20
        
        dataset_data = {
            "documents": documents,
            "scores": scores,
            "query_ids": query_ids
        }
        
        with open(dataset_path, 'w') as f:
            json.dump(dataset_data, f)
        
        clusters = [
            {"cluster_id": 0, "indices": [0, 1, 2], "similarity_scores": [0.96, 0.97, 0.95]},
            {"cluster_id": 1, "indices": [5, 6], "similarity_scores": [0.98, 0.96]},
        ]
        
        with open(clusters_path, 'w') as f:
            json.dump(clusters, f)
        
        # Generate unique subset
        result = generate_unique_subset(
            dataset_path=dataset_path,
            clusters_path=clusters_path,
            output_path=output_path,
            force_overwrite=True
        )
        
        # Verify result
        assert isinstance(result, UniqueSubsetResult)
        assert result.total_original_items == 20
        assert result.total_unique_items == 17  # 20 - 2 (from cluster 0) - 1 (from cluster 1)
        assert result.removed_duplicates == 3
        assert result.removal_percentage == 15.0
        assert os.path.exists(output_path)
        
        # Verify output file contents
        with open(output_path, 'r') as f:
            output_data = json.load(f)
        
        assert output_data["total_original_items"] == 20
        assert output_data["total_unique_items"] == 17
        assert len(output_data["documents"]) == 17

def test_empty_clusters():
    """Test handling of empty clusters."""
    clusters = [
        RedundancyCluster(cluster_id=0, indices=[], similarity_scores=[]),
        RedundancyCluster(cluster_id=1, indices=[5], similarity_scores=[]),
    ]
    
    candidate_list = CandidateList(
        documents=[f"Doc {i}" for i in range(10)],
        scores=[1.0] * 10,
        query_ids=[1] * 10
    )
    
    unique_subset = filter_to_unique_subset(candidate_list, clusters)
    
    # Empty cluster should be ignored, single-item cluster should be kept
    # Only index 5 is in a cluster, so 9 items should remain (all except none removed)
    # Actually, a single-item cluster means no duplicates, so all 10 items remain
    assert len(unique_subset.documents) == 10

def test_no_clusters():
    """Test handling when there are no clusters."""
    clusters = []
    
    candidate_list = CandidateList(
        documents=[f"Doc {i}" for i in range(10)],
        scores=[1.0] * 10,
        query_ids=[1] * 10
    )
    
    unique_subset = filter_to_unique_subset(candidate_list, clusters)
    
    # No clusters means no duplicates to remove
    assert len(unique_subset.documents) == 10
    assert unique_subset.original_indices == list(range(10))