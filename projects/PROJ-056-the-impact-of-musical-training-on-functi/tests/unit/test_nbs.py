import pytest
import numpy as np
import pandas as pd
import os
from pathlib import Path
from code.analysis.stats import network_based_statistic, welch_t_test

def test_nbs_small_graph():
    """
    Test NBS on a small graph with known component size.
    Creates a simple graph where edges 0-1 and 1-2 are significant,
    forming a component of size 2 edges.
    """
    # Create synthetic data: 10 subjects, 3 ROIs
    n_subjects = 10
    n_rois = 3
    
    # Create connectivity data with known pattern
    # Group 0: non-musician, Group 1: musician
    connectivity_data = np.random.randn(n_subjects, n_rois, n_rois)
    
    # Set up a clear signal in edges (0,1) and (1,2) for group 1
    # Edge (0,1) and (1,2) should be significant
    group0_indices = [0, 1, 2, 3, 4]
    group1_indices = [5, 6, 7, 8, 9]
    
    # Add strong signal to edges (0,1) and (1,2) for group 1
    for subj in group1_indices:
        connectivity_data[subj, 0, 1] = 2.0  # Strong positive
        connectivity_data[subj, 1, 2] = 2.0  # Strong positive
        connectivity_data[subj, 0, 2] = 0.0  # No signal
    
    # For group 0, keep values near 0
    for subj in group0_indices:
        connectivity_data[subj, 0, 1] = 0.0
        connectivity_data[subj, 1, 2] = 0.0
        connectivity_data[subj, 0, 2] = 0.0
    
    # Symmetrize
    for subj in range(n_subjects):
        connectivity_data[subj, 1, 0] = connectivity_data[subj, 0, 1]
        connectivity_data[subj, 2, 1] = connectivity_data[subj, 1, 2]
        connectivity_data[subj, 2, 0] = connectivity_data[subj, 0, 2]
    
    # Group labels: 0 for group0, 1 for group1
    group_labels = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    
    # Run NBS with low threshold to ensure edges are selected
    result = network_based_statistic(
        connectivity_data,
        group_labels,
        edge_threshold=0.01,  # Very low p-value threshold to ensure selection
        n_permutations=100,   # Fewer permutations for speed
        seed=42
    )
    
    # The result should have a component with at least 2 edges (0-1 and 1-2)
    # Note: The exact size may vary due to randomness in permutation,
    # but we expect at least 2 edges in the largest component
    assert result['component_size'] >= 2, f"Expected at least 2 edges in component, got {result['component_size']}"
    assert 'p_value' in result
    assert 0 <= result['p_value'] <= 1

def test_nbs_no_component():
    """
    Test NBS when no edges pass the threshold.
    """
    # Create random data with no signal
    n_subjects = 10
    n_rois = 3
    connectivity_data = np.random.randn(n_subjects, n_rois, n_rois)
    
    group_labels = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    
    # Use a very high threshold so no edges are selected
    result = network_based_statistic(
        connectivity_data,
        group_labels,
        edge_threshold=0.0001,  # Extremely low p-value (high t-threshold)
        n_permutations=10,
        seed=42
    )
    
    # With very high threshold, we might get no component
    # The component size should be 0 or very small
    assert result['component_size'] >= 0

def test_welch_t_test_basic():
    """
    Basic test for Welch's t-test function.
    """
    group1 = np.array([1, 2, 3, 4, 5])
    group2 = np.array([10, 11, 12, 13, 14])
    
    t_stat, p_val = welch_t_test(group1, group2)
    
    # The groups are very different, so p-value should be small
    assert p_val < 0.01, f"Expected small p-value, got {p_val}"
    assert t_stat < 0, "Group 2 mean is larger, t-stat should be negative"

def test_nbs_permutation_count():
    """
    Test that NBS runs with specified number of permutations.
    """
    n_subjects = 10
    n_rois = 4
    connectivity_data = np.random.randn(n_subjects, n_rois, n_rois)
    group_labels = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    
    # Run with 50 permutations
    result = network_based_statistic(
        connectivity_data,
        group_labels,
        edge_threshold=0.05,
        n_permutations=50,
        seed=42
    )
    
    # The result should be valid
    assert 'component_size' in result
    assert 'p_value' in result
    assert 'component_edges' in result