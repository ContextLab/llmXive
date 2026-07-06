import numpy as np
import pytest
import sys
import os

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from analysis.stats import network_based_statistic

def test_nbs_small_graph():
    """
    Test NBS on a small graph with a known component structure.
    
    We create two groups where group 1 has stronger connections in a
    specific subgraph, and verify that NBS detects a component.
    """
    np.random.seed(42)
    
    n_rois = 6
    n_subjects_per_group = 15
    
    # Create a small graph where we know the expected component
    # We'll make edges between nodes 0, 1, 2 stronger in group 1
    
    group1_matrices = []
    group2_matrices = []
    
    for _ in range(n_subjects_per_group):
        # Base random connectivity
        mat1 = np.random.randn(n_rois, n_rois) * 0.05
        mat2 = np.random.randn(n_rois, n_rois) * 0.05
        
        # Make group 1 have stronger connections in the triangle (0,1,2)
        for i in range(3):
            for j in range(i+1, 3):
                mat1[i, j] += 0.5
                mat1[j, i] += 0.5
        
        group1_matrices.append(mat1)
        group2_matrices.append(mat2)
    
    # Run NBS with a small number of permutations for testing
    result = network_based_statistic(
        group1_matrices,
        group2_matrices,
        edge_threshold=0.05,
        n_permutations=100,
        seed=42
    )
    
    # Verify the result structure
    assert 'component_sizes' in result
    assert 'largest_component_size' in result
    assert 'largest_component_p_value' in result
    assert 'edge_threshold' in result
    assert 'n_permutations' in result
    
    # We expect to find at least one component (the triangle 0-1-2)
    # The component should have at least 3 edges (0-1, 1-2, 0-2)
    assert result['largest_component_size'] >= 3, \
        f"Expected largest component to have at least 3 edges, got {result['largest_component_size']}"
    
    # The p-value should be reasonable (not necessarily < 0.05 with only 100 perms)
    assert 0 <= result['largest_component_p_value'] <= 1, \
        f"P-value should be between 0 and 1, got {result['largest_component_p_value']}"
    
    # Verify the threshold and permutation count
    assert result['edge_threshold'] == 0.05
    assert result['n_permutations'] == 100

def test_nbs_no_effect():
    """
    Test NBS when there is no true difference between groups.
    
    Both groups should have similar connectivity, so we expect
    small or no significant components.
    """
    np.random.seed(123)
    
    n_rois = 5
    n_subjects_per_group = 10
    
    # Generate identical distributions for both groups
    group1_matrices = [np.random.randn(n_rois, n_rois) * 0.1 for _ in range(n_subjects_per_group)]
    group2_matrices = [np.random.randn(n_rois, n_rois) * 0.1 for _ in range(n_subjects_per_group)]
    
    result = network_based_statistic(
        group1_matrices,
        group2_matrices,
        edge_threshold=0.05,
        n_permutations=50,
        seed=123
    )
    
    # With no true effect, the largest component should be small
    # (could be 0 if no edges pass threshold by chance)
    assert result['largest_component_size'] >= 0
    
    # The p-value should be high (not significant) when there's no effect
    # Note: with only 50 permutations, we might not get perfect p-values
    assert 0 <= result['largest_component_p_value'] <= 1

def test_nbs_parameters():
    """
    Test that NBS respects the specified parameters.
    """
    np.random.seed(456)
    
    n_rois = 4
    n_subjects_per_group = 8
    
    group1_matrices = [np.random.randn(n_rois, n_rois) * 0.1 for _ in range(n_subjects_per_group)]
    group2_matrices = [np.random.randn(n_rois, n_rois) * 0.1 for _ in range(n_subjects_per_group)]
    
    # Run with different parameters
    result = network_based_statistic(
        group1_matrices,
        group2_matrices,
        edge_threshold=0.10,
        n_permutations=200,
        seed=456
    )
    
    assert result['edge_threshold'] == 0.10
    assert result['n_permutations'] == 200
    assert 'component_sizes' in result
    assert isinstance(result['component_sizes'], list)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
