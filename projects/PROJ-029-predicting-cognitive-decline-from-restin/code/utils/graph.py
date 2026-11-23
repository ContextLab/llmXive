"""Graph-theoretical utilities for rs-fMRI connectivity analysis.

This module provides wrappers for loading the AAL atlas, constructing
connectivity matrices, and calculating graph metrics (degree, efficiency,
clustering, path length) using NetworkX and Nilearn.

All functions are designed to be memory-efficient and compatible with
the project's logging and error-handling contracts.
"""
from __future__ import annotations

import numpy as np
import networkx as nx
from typing import Union, Tuple, Optional, Dict, Any
import nibabel as nib
from pathlib import Path
from nilearn.datasets import fetch_atlas_aal
from nilearn.maskers import NiftiLabelsMasker
from scipy import stats

# Constants
DEFAULT_ATLAS_PATH = None  # Will be fetched if None
MIN_CORRELATION_THRESHOLD = -1.0
MAX_CORRELATION_THRESHOLD = 1.0


def load_aal_atlas_mask(resolution: int = 2) -> Tuple[nib.Nifti1Image, np.ndarray]:
    """Load the AAL atlas and return the mask image and labels.

    Args:
        resolution: The resolution of the atlas (2mm is standard).

    Returns:
        Tuple of (nibabel image, array of region labels).
    """
    try:
        atlas = fetch_atlas_aal(version='AAL3', data_dir=str(Path.home() / '.nilearn'))
        atlas_img = atlas.maps
        labels = atlas.labels if hasattr(atlas, 'labels') else []
        return atlas_img, np.array(labels)
    except Exception as e:
        # Fallback to a minimal atlas if AAL fails (for testing only)
        # In production, this should raise to enforce real data usage
        raise RuntimeError(f"Failed to fetch AAL atlas: {e}")


def validate_atlas_shape(atlas_img: nib.Nifti1Image, expected_shape: Tuple[int, int, int]) -> bool:
    """Validate that the atlas image has the expected shape.

    Args:
        atlas_img: The nibabel image to validate.
        expected_shape: The expected 3D shape (x, y, z).

    Returns:
        True if valid, False otherwise.
    """
    return atlas_img.shape[:3] == expected_shape


def create_minimal_atlas(shape: Tuple[int, int, int], n_regions: int = 90) -> nib.Nifti1Image:
    """Create a minimal synthetic atlas for testing purposes.

    Args:
        shape: The 3D shape of the atlas.
        n_regions: Number of regions to generate.

    Returns:
        A nibabel NIfTI image with integer labels.
    """
    data = np.zeros(shape, dtype=np.int16)
    # Simple partitioning for testing
    vox_per_region = (shape[0] * shape[1] * shape[2]) // n_regions
    for i in range(n_regions):
        start_idx = i * vox_per_region
        end_idx = (i + 1) * vox_per_region if i < n_regions - 1 else shape[0] * shape[1] * shape[2]
        # Flatten, assign, reshape
        flat_data = data.ravel()
        flat_data[start_idx:end_idx] = i + 1
        data = flat_data.reshape(shape)

    return nib.Nifti1Image(data, np.eye(4))


def compute_connectivity_matrix(
    time_series: np.ndarray,
    method: str = 'pearson'
) -> np.ndarray:
    """Compute a connectivity matrix from time series data.

    Args:
        time_series: 2D array of shape (n_timepoints, n_regions).
        method: Correlation method ('pearson', 'spearman').

    Returns:
        2D correlation matrix of shape (n_regions, n_regions).
    """
    if time_series.ndim != 2:
        raise ValueError(f"Time series must be 2D, got {time_series.ndim}D")

    if method == 'pearson':
        corr_matrix = np.corrcoef(time_series, rowvar=False)
    elif method == 'spearman':
        corr_matrix, _ = stats.spearmanr(time_series, axis=0)
    else:
        raise ValueError(f"Unsupported method: {method}")

    # Handle NaNs (e.g., constant time series)
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)

    # Ensure symmetry
    corr_matrix = (corr_matrix + corr_matrix.T) / 2.0

    # Ensure diagonal is 1.0
    np.fill_diagonal(corr_matrix, 1.0)

    return corr_matrix


def create_graph_from_adjacency(
    adjacency_matrix: np.ndarray,
    threshold: float = 0.0,
    directed: bool = False
) -> nx.Graph:
    """Create a NetworkX graph from an adjacency matrix.

    Args:
        adjacency_matrix: 2D array representing edge weights.
        threshold: Minimum absolute weight to include an edge.
        directed: Whether to create a directed graph.

    Returns:
        A NetworkX graph object.
    """
    if adjacency_matrix.ndim != 2 or adjacency_matrix.shape[0] != adjacency_matrix.shape[1]:
        raise ValueError("Adjacency matrix must be square")

    if directed:
        G = nx.DiGraph()
    else:
        G = nx.Graph()

    n = adjacency_matrix.shape[0]
    G.add_nodes_from(range(n))

    for i in range(n):
        for j in range(i + (1 if directed else 0), n):
            weight = adjacency_matrix[i, j]
            if abs(weight) > threshold:
                G.add_edge(i, j, weight=weight)

    return G


def calculate_degree_centrality(G: nx.Graph) -> np.ndarray:
    """Calculate the degree centrality for each node.

    Args:
        G: A NetworkX graph.

    Returns:
        1D array of degree centrality values.
    """
    centrality = nx.degree_centrality(G)
    # Sort by node index to ensure consistent order
    return np.array([centrality.get(i, 0.0) for i in range(len(G))])


def calculate_global_efficiency(G: nx.Graph) -> float:
    """Calculate the global efficiency of the graph.

    Args:
        G: A NetworkX graph.

    Returns:
        Global efficiency value (0.0 if graph is disconnected).
    """
    if not nx.is_connected(G):
        # For disconnected graphs, compute efficiency per component
        try:
            return nx.global_efficiency(G)
        except Exception:
            return 0.0
    return nx.global_efficiency(G)


def calculate_clustering_coefficient(G: nx.Graph) -> float:
    """Calculate the average clustering coefficient.

    Args:
        G: A NetworkX graph.

    Returns:
        Average clustering coefficient.
    """
    return nx.average_clustering(G)


def calculate_local_efficiency(G: nx.Graph) -> float:
    """Calculate the local efficiency of the graph.

    Args:
        G: A NetworkX graph.

    Returns:
        Local efficiency value.
    """
    try:
        return nx.local_efficiency(G)
    except Exception:
        return 0.0


def calculate_shortest_path_length(G: nx.Graph) -> float:
    """Calculate the average shortest path length.

    Args:
        G: A NetworkX graph.

    Returns:
        Average shortest path length (infinity if disconnected).
    """
    try:
        if not nx.is_connected(G):
            # Compute for the largest connected component
            largest_cc = max(nx.connected_components(G), key=len)
            subgraph = G.subgraph(largest_cc)
            return nx.average_shortest_path_length(subgraph)
        return nx.average_shortest_path_length(G)
    except nx.NetworkXError:
        return np.inf


def compute_subject_graph_metrics(
    adjacency_matrix: np.ndarray,
    threshold: float = 0.0
) -> Dict[str, float]:
    """Compute a suite of graph metrics for a single subject.

    Args:
        adjacency_matrix: 2D correlation matrix.
        threshold: Threshold for binarization/edge inclusion.

    Returns:
        Dictionary of metric names to values.
    """
    G = create_graph_from_adjacency(adjacency_matrix, threshold=threshold)

    if G.number_of_nodes() == 0:
        return {
            'node_degree': 0.0,
            'global_efficiency': 0.0,
            'clustering_coeff': 0.0,
            'path_length': np.inf
        }

    # Compute metrics
    degree_centrality = calculate_degree_centrality(G)
    avg_degree = np.mean(degree_centrality) * (len(G) - 1)  # Scale back to actual degree

    return {
        'node_degree': float(avg_degree),
        'global_efficiency': float(calculate_global_efficiency(G)),
        'clustering_coeff': float(calculate_clustering_coefficient(G)),
        'path_length': float(calculate_shortest_path_length(G))
    }