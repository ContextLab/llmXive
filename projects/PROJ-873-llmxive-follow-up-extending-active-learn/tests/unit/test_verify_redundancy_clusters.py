"""
Unit tests for verify_redundancy_clusters.py (T012a verification logic)
"""
import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass
from typing import List

# Import the validation function
from verify_redundancy_clusters import validate_cluster_counts, MIN_CLUSTERS_REQUIRED, MIN_CLUSTER_SIZE, MAX_CLUSTER_SIZE
from data_loader import RedundancyCluster

@pytest.fixture
def valid_clusters():
    """Create a list of valid clusters for testing."""
    clusters = []
    for i in range(25):  # More than minimum required
        # Create clusters with 3-5 documents
        size = 3 + (i % 3)  # Alternates between 3, 4, 5
        documents = [
            {
                'doc_id': f"doc_{i}_{j}",
                'text': f"Document {j} in cluster {i}",
                'cluster_id': i
            }
            for j in range(size)
        ]
        clusters.append(RedundancyCluster(
            cluster_id=i,
            documents=documents,
            query_id=f"query_{i}"
        ))
    return clusters

@pytest.fixture
def too_few_clusters():
    """Create a list with too few clusters."""
    clusters = []
    for i in range(15):  # Less than MIN_CLUSTERS_REQUIRED
        size = 4
        documents = [
            {
                'doc_id': f"doc_{i}_{j}",
                'text': f"Document {j} in cluster {i}",
                'cluster_id': i
            }
            for j in range(size)
        ]
        clusters.append(RedundancyCluster(
            cluster_id=i,
            documents=documents,
            query_id=f"query_{i}"
        ))
    return clusters

@pytest.fixture
def invalid_size_clusters():
    """Create clusters with invalid sizes."""
    clusters = []
    for i in range(25):
        if i % 5 == 0:
            size = 2  # Too small
        elif i % 5 == 1:
            size = 6  # Too large
        else:
            size = 4  # Valid
        
        documents = [
            {
                'doc_id': f"doc_{i}_{j}",
                'text': f"Document {j} in cluster {i}",
                'cluster_id': i
            }
            for j in range(size)
        ]
        clusters.append(RedundancyCluster(
            cluster_id=i,
            documents=documents,
            query_id=f"query_{i}"
        ))
    return clusters

def test_validate_cluster_counts_valid_data(valid_clusters):
    """Test validation with valid cluster data."""
    is_compliant, stats = validate_cluster_counts(valid_clusters)
    
    assert is_compliant is True
    assert stats['total_clusters'] == 25
    assert stats['valid_clusters'] == 25
    assert stats['invalid_clusters'] == 0
    assert stats['compliant'] is True
    assert len(stats['errors']) == 0

def test_validate_cluster_counts_too_few(too_few_clusters):
    """Test validation with too few clusters."""
    is_compliant, stats = validate_cluster_counts(too_few_clusters)
    
    assert is_compliant is False
    assert stats['total_clusters'] == 15
    assert stats['valid_clusters'] == 15
    assert stats['invalid_clusters'] == 0
    assert stats['compliant'] is False
    assert len(stats['errors']) > 0
    assert any("Insufficient clusters" in error for error in stats['errors'])

def test_validate_cluster_counts_invalid_sizes(invalid_size_clusters):
    """Test validation with invalid cluster sizes."""
    is_compliant, stats = validate_cluster_counts(invalid_size_clusters)
    
    assert is_compliant is False
    assert stats['total_clusters'] == 25
    assert stats['valid_clusters'] == 20  # 25 - 5 invalid
    assert stats['invalid_clusters'] == 5
    assert stats['compliant'] is False
    assert len(stats['errors']) == 5

def test_validate_cluster_counts_empty_list():
    """Test validation with empty cluster list."""
    is_compliant, stats = validate_cluster_counts([])
    
    assert is_compliant is False
    assert stats['total_clusters'] == 0
    assert stats['valid_clusters'] == 0
    assert stats['invalid_clusters'] == 0
    assert stats['compliant'] is False

def test_cluster_size_boundaries():
    """Test that cluster size boundaries are correctly enforced."""
    # Test minimum boundary
    min_cluster = RedundancyCluster(
        cluster_id=0,
        documents=[{'doc_id': f'd_{i}', 'text': f'text_{i}', 'cluster_id': 0} for i in range(MIN_CLUSTER_SIZE)],
        query_id='q_0'
    )
    max_cluster = RedundancyCluster(
        cluster_id=1,
        documents=[{'doc_id': f'd_{i}', 'text': f'text_{i}', 'cluster_id': 1} for i in range(MAX_CLUSTER_SIZE)],
        query_id='q_1'
    )
    too_small = RedundancyCluster(
        cluster_id=2,
        documents=[{'doc_id': f'd_{i}', 'text': f'text_{i}', 'cluster_id': 2} for i in range(MIN_CLUSTER_SIZE - 1)],
        query_id='q_2'
    )
    too_large = RedundancyCluster(
        cluster_id=3,
        documents=[{'doc_id': f'd_{i}', 'text': f'text_{i}', 'cluster_id': 3} for i in range(MAX_CLUSTER_SIZE + 1)],
        query_id='q_3'
    )
    
    clusters = [min_cluster, max_cluster, too_small, too_large]
    is_compliant, stats = validate_cluster_counts(clusters)
    
    assert is_compliant is False
    assert stats['valid_clusters'] == 2
    assert stats['invalid_clusters'] == 2