"""
Graph Thresholding Module for Brain Network Analysis.

Implements proportional thresholding to generate binary graphs
at specific density levels as required by FR-009/SC-003.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Set
import json
import pickle

from ..utils.logging import get_logger, info, warning, error, debug
from .connectivity import load_time_series_from_processed, compute_correlation_matrix, retain_positive_edges

logger = get_logger(__name__)

# Target densities as specified in FR-009/SC-003
TARGET_DENSITIES: List[float] = [0.15, 0.20, 0.25]

def apply_proportional_threshold(
    correlation_matrix: np.ndarray,
    target_density: float,
    retain_positive_only: bool = True
) -> Tuple[np.ndarray, int, int]:
    """
    Apply proportional threshold to a correlation matrix to achieve a target graph density.

    Args:
        correlation_matrix: Symmetric correlation matrix (N x N).
        target_density: Target density (0.0 to 1.0).
        retain_positive_only: If True, only consider positive edges for thresholding.

    Returns:
        Tuple of:
            - binary_matrix: Binary adjacency matrix (0 or 1).
            - actual_density: The achieved density of the thresholded graph.
            - num_edges: Number of edges in the thresholded graph.
    """
    if not 0.0 <= target_density <= 1.0:
        raise ValueError(f"target_density must be between 0.0 and 1.0, got {target_density}")

    n_nodes = correlation_matrix.shape[0]
    if n_nodes != correlation_matrix.shape[1]:
        raise ValueError("Correlation matrix must be square.")

    # Get upper triangle indices (excluding diagonal)
    upper_tri_indices = np.triu_indices(n_nodes, k=1)
    edges = correlation_matrix[upper_tri_indices]

    if retain_positive_only:
        # Only consider positive edges for thresholding
        positive_edges = edges[edges > 0]
        if len(positive_edges) == 0:
            warning(f"No positive edges found for subject. Cannot threshold.")
            return np.zeros_like(correlation_matrix), 0.0, 0

        # Calculate how many edges we need to keep
        # Total possible edges in a directed graph of N nodes is N*(N-1)
        # But we are working with undirected graphs (upper triangle)
        # Total possible edges = N*(N-1)/2
        total_possible_edges = n_nodes * (n_nodes - 1) / 2
        num_edges_to_keep = int(np.ceil(total_possible_edges * target_density))

        if num_edges_to_keep > len(positive_edges):
            warning(
                f"Requested density {target_density:.2f} requires {num_edges_to_keep} edges, "
                f"but only {len(positive_edges)} positive edges available. "
                f"Using all positive edges (density={len(positive_edges)/total_possible_edges:.4f})."
            )
            num_edges_to_keep = len(positive_edges)

        # Get threshold value: the (num_edges_to_keep)-th largest value
        threshold = np.percentile(positive_edges, 100 * (1 - num_edges_to_keep / len(positive_edges)))

    else:
        # Consider all edges (absolute value or signed)
        # For now, we use absolute values to determine threshold
        abs_edges = np.abs(edges)
        total_possible_edges = n_nodes * (n_nodes - 1) / 2
        num_edges_to_keep = int(np.ceil(total_possible_edges * target_density))

        if num_edges_to_keep > len(abs_edges):
            warning(
                f"Requested density {target_density:.2f} requires {num_edges_to_keep} edges, "
                f"but only {len(abs_edges)} edges available. Using all edges."
            )
            num_edges_to_keep = len(abs_edges)

        threshold = np.percentile(abs_edges, 100 * (1 - num_edges_to_keep / len(abs_edges)))

    # Create binary matrix
    binary_matrix = np.zeros_like(correlation_matrix)
    if retain_positive_only:
        # Only keep positive edges above threshold
        mask = (correlation_matrix >= threshold) & (correlation_matrix > 0)
    else:
        # Keep edges with absolute value above threshold
        mask = np.abs(correlation_matrix) >= threshold

    binary_matrix[mask] = 1.0

    # Calculate actual density
    actual_num_edges = np.sum(binary_matrix) / 2  # Divide by 2 for undirected graph
    actual_density = actual_num_edges / total_possible_edges

    return binary_matrix, actual_density, int(actual_num_edges)

def threshold_connectivity_matrices(
    connectivity_data: Dict[str, np.ndarray],
    densities: Optional[List[float]] = None,
    output_dir: Optional[Path] = None,
    retain_positive_only: bool = True
) -> Dict[str, Dict[str, Dict[str, Union[np.ndarray, float, int]]]]:
    """
    Threshold connectivity matrices for multiple subjects at multiple density levels.

    Args:
        connectivity_data: Dictionary mapping subject_id to correlation matrix.
        densities: List of target densities. Defaults to TARGET_DENSITIES.
        output_dir: Directory to save thresholded matrices. If None, only return in-memory.
        retain_positive_only: Whether to only consider positive edges.

    Returns:
        Dictionary mapping subject_id -> density -> {
            'matrix': binary_matrix,
            'actual_density': float,
            'num_edges': int
        }
    """
    if densities is None:
        densities = TARGET_DENSITIES

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        info(f"Saving thresholded graphs to {output_dir}")

    results: Dict[str, Dict[str, Dict[str, Union[np.ndarray, float, int]]]] = {}

    for subject_id, corr_matrix in connectivity_data.items():
        subject_results: Dict[str, Dict[str, Union[np.ndarray, float, int]]] = {}

        for density in densities:
            binary_matrix, actual_density, num_edges = apply_proportional_threshold(
                corr_matrix,
                density,
                retain_positive_only=retain_positive_only
            )

            subject_results[str(density)] = {
                'matrix': binary_matrix,
                'actual_density': actual_density,
                'num_edges': num_edges
            }

            if output_dir:
                # Save binary matrix
                save_path = output_dir / f"{subject_id}_density_{density:.2f}.npy"
                np.save(save_path, binary_matrix)
                debug(f"Saved thresholded matrix for {subject_id} at density {density}")

        results[subject_id] = subject_results

    return results

def load_thresholded_graphs(
    subject_id: str,
    densities: List[float],
    input_dir: Path
) -> Dict[str, np.ndarray]:
    """
    Load previously thresholded binary graphs for a subject.

    Args:
        subject_id: Subject identifier.
        densities: List of densities to load.
        input_dir: Directory containing thresholded graph files.

    Returns:
        Dictionary mapping density string to binary matrix.
    """
    graphs = {}
    for density in densities:
        file_path = input_dir / f"{subject_id}_density_{density:.2f}.npy"
        if file_path.exists():
            graphs[str(density)] = np.load(file_path)
            debug(f"Loaded thresholded graph for {subject_id} at density {density}")
        else:
            warning(f"Thresholded graph not found: {file_path}")

    return graphs

def validate_thresholding(
    thresholded_graphs: Dict[str, Dict[str, Dict[str, Union[np.ndarray, float, int]]]],
    tolerance: float = 0.01
) -> Dict[str, List[str]]:
    """
    Validate that thresholded graphs meet expected density constraints.

    Args:
        thresholded_graphs: Results from threshold_connectivity_matrices.
        tolerance: Allowed deviation from target density.

    Returns:
        Dictionary mapping subject_id to list of validation messages.
    """
    validation_results: Dict[str, List[str]] = {}

    for subject_id, density_results in thresholded_graphs.items():
        messages: List[str] = []

        for density_str, results in density_results.items():
            target = float(density_str)
            actual = results['actual_density']
            deviation = abs(actual - target)

            if deviation > tolerance:
                messages.append(
                    f"Density {density_str}: Expected {target:.4f}, got {actual:.4f} "
                    f"(deviation: {deviation:.4f})"
                )
            else:
                messages.append(
                    f"Density {density_str}: OK (expected {target:.4f}, got {actual:.4f})"
                )

        validation_results[subject_id] = messages

    return validation_results

def main():
    """
    Main entry point for graph thresholding pipeline.
    Loads preprocessed connectivity matrices, applies thresholding,
    and saves results.
    """
    from config import ensure_directories, RANDOM_SEED
    import os

    # Set random seed for reproducibility
    np.random.seed(RANDOM_SEED)

    # Ensure directories exist
    ensure_directories()

    # Paths
    processed_dir = Path("data/processed")
    connectivity_dir = Path("data/processed/connectivity")
    thresholded_dir = Path("data/processed/thresholded")

    if not processed_dir.exists():
        error(f"Processed data directory not found: {processed_dir}")
        error("Please run preprocessing first (T013).")
        return

    if not connectivity_dir.exists():
        # Try to compute connectivity first
        info("Connectivity directory not found. Attempting to compute connectivity...")
        try:
            from graph.connectivity import compute_all_connectivity
            compute_all_connectivity(processed_dir, connectivity_dir)
        except Exception as e:
            error(f"Failed to compute connectivity: {e}")
            return

    # Create thresholded directory
    thresholded_dir.mkdir(parents=True, exist_ok=True)

    # Load all connectivity matrices
    info(f"Loading connectivity matrices from {connectivity_dir}")
    connectivity_data: Dict[str, np.ndarray] = {}

    for corr_file in connectivity_dir.glob("*.npy"):
        subject_id = corr_file.stem.replace("_correlation", "")
        matrix = np.load(corr_file)
        connectivity_data[subject_id] = matrix

    if not connectivity_data:
        error("No connectivity matrices found.")
        return

    info(f"Loaded {len(connectivity_data)} connectivity matrices")

    # Apply thresholding
    info(f"Applying thresholding at densities: {TARGET_DENSITIES}")
    thresholded_results = threshold_connectivity_matrices(
        connectivity_data,
        densities=TARGET_DENSITIES,
        output_dir=thresholded_dir,
        retain_positive_only=True
    )

    # Validate results
    info("Validating thresholding results...")
    validation = validate_thresholding(thresholded_results)

    # Print validation summary
    all_ok = True
    for subject_id, messages in validation.items():
        for msg in messages:
            if "OK" not in msg:
                all_ok = False
            info(f"[{subject_id}] {msg}")

    if all_ok:
        info("All thresholded graphs within tolerance.")
    else:
        warning("Some thresholded graphs deviate from target density (may be due to limited positive edges).")

    # Save summary statistics
    summary_path = thresholded_dir / "thresholding_summary.json"
    summary_data = {
        "target_densities": TARGET_DENSITIES,
        "subjects_processed": len(thresholded_results),
        "density_details": {}
    }

    for subject_id, density_results in thresholded_results.items():
        summary_data["density_details"][subject_id] = {
            density: {
                "actual_density": data["actual_density"],
                "num_edges": data["num_edges"]
            }
            for density, data in density_results.items()
        }

    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)

    info(f"Thresholding complete. Summary saved to {summary_path}")
    info(f"Binary graphs saved to {thresholded_dir}")

if __name__ == "__main__":
    main()
