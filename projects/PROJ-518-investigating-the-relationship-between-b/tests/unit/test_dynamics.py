"""
Unit tests for dynamics analysis functions.
"""
import numpy as np
import pytest
from analysis.dynamics import detect_communities, calculate_flexibility

def test_detect_communities_structure():
    """Test that detect_communities returns a list of integers matching matrix size."""
    # Create a simple 4x4 correlation matrix with clear community structure
    # Nodes 0,1 strongly connected; Nodes 2,3 strongly connected; cross-connection weak
    matrix = np.array([
        [1.0, 0.9, 0.1, 0.1],
        [0.9, 1.0, 0.1, 0.1],
        [0.1, 0.1, 1.0, 0.9],
        [0.1, 0.1, 0.9, 1.0]
    ])
    
    labels = detect_communities(matrix, gamma=1.0)
    
    assert len(labels) == 4
    assert all(isinstance(l, int) for l in labels)
    # In this structure, we expect two communities
    # Nodes 0 and 1 should be in one, nodes 2 and 3 in another
    # The exact labels (0,1 vs 1,0) may vary, but the grouping should be consistent
    assert labels[0] == labels[1], "Nodes 0 and 1 should be in the same community"
    assert labels[2] == labels[3], "Nodes 2 and 3 should be in the same community"
    assert labels[0] != labels[2], "Nodes 0 and 2 should be in different communities"

def test_calculate_flexibility_no_changes():
    """Test flexibility is 0.0 when community labels never change."""
    # Same community assignment across all windows
    community_labels = [
        [0, 0, 1, 1],
        [0, 0, 1, 1],
        [0, 0, 1, 1]
    ]
    
    flexibility = calculate_flexibility(community_labels)
    
    assert flexibility == 0.0

def test_calculate_flexibility_max_changes():
    """Test flexibility is 1.0 when community labels change every window."""
    # Each window has completely different assignments
    community_labels = [
        [0, 1, 2, 3],
        [1, 2, 3, 0],
        [2, 3, 0, 1]
    ]
    
    flexibility = calculate_flexibility(community_labels)
    
    # Every ROI changes in every step (2 changes out of 2 possible)
    assert flexibility == 1.0

def test_calculate_flexibility_partial_changes():
    """Test flexibility calculation with partial changes."""
    # ROI 0 changes every time, ROI 1 never changes
    community_labels = [
        [0, 1],
        [1, 1],
        [0, 1]
    ]
    
    flexibility = calculate_flexibility(community_labels)
    
    # ROI 0: 2 changes / 2 possible = 1.0
    # ROI 1: 0 changes / 2 possible = 0.0
    # Average = 0.5
    assert flexibility == 0.5

def test_calculate_flexibility_single_window():
    """Test that single window returns 0.0 flexibility."""
    community_labels = [[0, 1, 2]]
    
    flexibility = calculate_flexibility(community_labels)
    
    assert flexibility == 0.0

def test_calculate_flexibility_empty():
    """Test that empty list returns 0.0 flexibility."""
    community_labels = []
    
    flexibility = calculate_flexibility(community_labels)
    
    assert flexibility == 0.0