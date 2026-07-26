import pytest
from code.visualize import calculate_euclidean_distance_matrix, cluster_matrix
import numpy as np

def test_heatmap_silhouette_score():
    """
    Test that clustering function returns silhouette score and logs it.
    Covers: US3-FR-005 (Visualization with clustering validation)
    
    This test verifies that the clustering implementation correctly calculates
    and returns the silhouette score for validation purposes.
    """
    # Create a simple synthetic enrichment matrix for testing
    # Shape: (5 cell types, 3 motifs)
    data = np.array([
        [0.9, 0.1, 0.2],  # Cell type 1: high for motif 1
        [0.1, 0.9, 0.2],  # Cell type 2: high for motif 2
        [0.1, 0.2, 0.9],  # Cell type 3: high for motif 3
        [0.8, 0.1, 0.1],  # Cell type 4: similar to cell type 1
        [0.1, 0.8, 0.1],  # Cell type 5: similar to cell type 2
    ])
    
    # Calculate distance matrix
    distance_matrix = calculate_euclidean_distance_matrix(data)
    
    assert distance_matrix.shape[0] == data.shape[0], \
        f"Distance matrix rows {distance_matrix.shape[0]} should match data rows {data.shape[0]}"
    assert distance_matrix.shape[1] == data.shape[0], \
        f"Distance matrix columns {distance_matrix.shape[1]} should match data rows {data.shape[0]}"
    
    # Verify distance matrix is symmetric
    assert np.allclose(distance_matrix, distance_matrix.T), \
        "Distance matrix should be symmetric"
    
    # Verify diagonal is zero
    assert np.allclose(np.diag(distance_matrix), 0), \
        "Distance matrix diagonal should be zero"
    
    # Perform clustering and get silhouette score
    clustered_data, silhouette_score = cluster_matrix(data)
    
    # Verify silhouette score is in valid range [-1, 1]
    assert -1 <= silhouette_score <= 1, \
        f"Silhouette score {silhouette_score} is not in [-1, 1]"
    
    # Verify clustered data has same shape as input
    assert clustered_data.shape == data.shape, \
        f"Clustered data shape {clustered_data.shape} should match input shape {data.shape}"
    
    # Log the score (in real implementation, this would be a logging call)
    # Here we just verify the score is returned
    assert isinstance(silhouette_score, float), \
        f"Silhouette score should be float, got {type(silhouette_score)}"

def test_euclidean_distance_calculation():
    """
    Test Euclidean distance calculation with known values.
    """
    # Simple 2D points
    data = np.array([
        [0, 0],
        [3, 4],
        [1, 1]
    ])
    
    distance_matrix = calculate_euclidean_distance_matrix(data)
    
    # Distance between point 0 and 1: sqrt((3-0)^2 + (4-0)^2) = 5
    assert np.isclose(distance_matrix[0, 1], 5.0), \
        f"Distance 0-1 should be 5.0, got {distance_matrix[0, 1]}"
    
    # Distance between point 0 and 2: sqrt((1-0)^2 + (1-0)^2) = sqrt(2)
    assert np.isclose(distance_matrix[0, 2], np.sqrt(2)), \
        f"Distance 0-2 should be sqrt(2), got {distance_matrix[0, 2]}"
    
    # Distance between point 1 and 2: sqrt((3-1)^2 + (4-1)^2) = sqrt(13)
    assert np.isclose(distance_matrix[1, 2], np.sqrt(13)), \
        f"Distance 1-2 should be sqrt(13), got {distance_matrix[1, 2]}"
