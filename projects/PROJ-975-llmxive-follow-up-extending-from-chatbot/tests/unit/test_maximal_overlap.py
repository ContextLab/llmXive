import pytest
import json
import os
import numpy as np
from unittest.mock import patch, MagicMock

from code.generate_data import (
    handle_maximal_overlap,
    calculate_similarity_metrics,
    MAXIMAL_OVERLAP_THRESHOLD,
    MINIMAL_RETRIEVAL_PRECISION
)

@pytest.fixture
def mock_skills():
    return [
        {'id': 'skill_000', 'description': 'test', 'code': 'pass', 'usage_count': 0},
        {'id': 'skill_001', 'description': 'test', 'code': 'pass', 'usage_count': 0},
    ]

@pytest.fixture
def mock_tasks():
    return [
        {'id': 'task_000', 'ground_truth_path': ['skill_000']},
    ]

def test_handle_maximal_overlap_detected(mock_skills, mock_tasks):
    """Test that maximal overlap detection triggers correct behavior."""
    similarity_metrics = {
        'mean_pairwise_similarity': 0.96,  # Above threshold
        'high_similarity_pairs_count': 10,
        'total_pairs': 10
    }
    seed_a = 42

    result = handle_maximal_overlap(similarity_metrics, mock_skills, mock_tasks, seed_a)

    # Verify maximal_overlap_detected flag is set
    assert result['metadata']['maximal_overlap_detected'] is True
    assert result['metadata']['mean_pairwise_similarity'] == 0.96
    assert result['metadata']['retrieval_precision_baseline'] == MINIMAL_RETRIEVAL_PRECISION
    assert result['metadata']['tie_breaking_method'] == 'deterministic_random_selection'
    assert result['metadata']['seed_used'] == seed_a

    # Verify each skill has the flag
    for skill in result['skills']:
        assert skill.get('maximal_overlap_detected') is True

def test_handle_maximal_overlap_not_detected(mock_skills, mock_tasks):
    """Test that normal case doesn't trigger maximal overlap handling."""
    similarity_metrics = {
        'mean_pairwise_similarity': 0.45,  # Below threshold
        'high_similarity_pairs_count': 2,
        'total_pairs': 10
    }
    seed_a = 42

    result = handle_maximal_overlap(similarity_metrics, mock_skills, mock_tasks, seed_a)

    # Verify maximal_overlap_detected flag is NOT set
    assert result['metadata']['maximal_overlap_detected'] is False
    assert 'maximal_overlap_detected' not in result['skills'][0]

def test_boundary_threshold(mock_skills, mock_tasks):
    """Test behavior exactly at the threshold."""
    similarity_metrics = {
        'mean_pairwise_similarity': MAXIMAL_OVERLAP_THRESHOLD,  # Exactly 0.95
        'high_similarity_pairs_count': 10,
        'total_pairs': 10
    }
    seed_a = 42

    result = handle_maximal_overlap(similarity_metrics, mock_skills, mock_tasks, seed_a)

    # Should trigger at exactly the threshold
    assert result['metadata']['maximal_overlap_detected'] is True

def test_similarity_metrics_calculation():
    """Test that similarity metrics are calculated correctly."""
    # Create a simple embedding matrix
    embeddings = np.array([
        [1.0, 0.0, 0.0],
        [0.99, 0.1, 0.0],  # Very similar to first
        [0.98, 0.2, 0.0],  # Very similar to first
    ])

    metrics = calculate_similarity_metrics(embeddings)

    assert 'mean_pairwise_similarity' in metrics
    assert 'high_similarity_pairs_count' in metrics
    assert 'total_pairs' in metrics
    assert metrics['mean_pairwise_similarity'] > 0.95  # Should be high