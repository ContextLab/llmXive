import pytest
from data_loader import inject_synthetic_redundancy, RedundancyCluster

def test_inject_synthetic_redundancy_creates_clusters():
    """Test that synthetic redundancy injection creates the expected number of clusters."""
    # Mock corpus
    corpus = {
        "doc1": {"title": "Test", "text": "This is a test document."},
        "doc2": {"title": "Test 2", "text": "Another test document."},
        "doc3": {"title": "Test 3", "text": "Third test document."},
        "doc4": {"title": "Test 4", "text": "Fourth test document."},
        "doc5": {"title": "Test 5", "text": "Fifth test document."},
    }
    
    num_clusters = 2
    new_corpus, clusters = inject_synthetic_redundancy(corpus, num_clusters=num_clusters, cluster_size_range=(2, 3))
    
    assert len(clusters) == num_clusters
    assert len(new_corpus) > len(corpus)
    
    for cluster in clusters:
        assert isinstance(cluster, RedundancyCluster)
        assert len(cluster.documents) >= 2

def test_inject_synthetic_redundancy_cluster_size():
    """Test that cluster sizes are within the specified range."""
    corpus = {f"doc{i}": {"title": f"Doc {i}", "text": f"Text {i}"} for i in range(10)}
    
    new_corpus, clusters = inject_synthetic_redundancy(corpus, num_clusters=3, cluster_size_range=(3, 4))
    
    for cluster in clusters:
        assert 3 <= len(cluster.documents) <= 4
