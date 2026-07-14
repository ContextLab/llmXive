"""Visualization module for sleep quality prediction interpretation.

Generates brain surface plots highlighting top predictive connections
using Nilearn's plot_connectome.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any

import numpy as np
from nilearn import plotting
from nilearn.image import load_img

# Import from project utils
from utils.logging import get_logger, log_operation, log_stage_start, log_stage_complete, log_stage_error
from config import get_paths, get_hyperparameter

# Import interpret module to load coefficients
from modeling.interpret import load_model_coefficients, extract_nonzero_edges


def load_connectivity_matrix_from_features(
    feature_path: str,
    n_regions: int
) -> np.ndarray:
    """Reconstruct connectivity matrix from flattened feature vector.

    Args:
        feature_path: Path to .npy file containing flattened connectivity features
        n_regions: Number of brain regions (Schaefer atlas parcels)

    Returns:
        Symmetric connectivity matrix of shape (n_regions, n_regions)
    """
    features = np.load(feature_path)
    n_features = features.shape[0] if len(features.shape) == 1 else features.shape[1]

    # Calculate expected number of edges: n*(n-1)/2
    expected_edges = n_regions * (n_regions - 1) // 2

    if n_features != expected_edges:
        raise ValueError(
            f"Feature dimension {n_features} does not match expected "
            f"edges {expected_edges} for {n_regions} regions"
        )

    # Initialize symmetric matrix
    matrix = np.zeros((n_regions, n_regions))

    # Fill upper triangle and mirror to lower
    idx = 0
    for i in range(n_regions):
        for j in range(i + 1, n_regions):
            matrix[i, j] = features[idx]
            matrix[i, i] = 0  # Diagonal is zero (no self-loops)
            idx += 1

    # Mirror upper to lower triangle
    matrix = matrix + matrix.T

    return matrix


def extract_top_connections(
    connectivity_matrix: np.ndarray,
    coefficients: np.ndarray,
    n_top: int = 50
) -> Tuple[List[Tuple[int, int, float]], np.ndarray]:
    """Extract top N predictive connections based on model coefficients.

    Args:
        connectivity_matrix: Full connectivity matrix
        coefficients: Model coefficients for each edge
        n_top: Number of top connections to extract (default 50)

    Returns:
        Tuple of (list of (i, j, value) tuples, mask array)
    """
    n_regions = connectivity_matrix.shape[0]
    n_edges = n_regions * (n_regions - 1) // 2

    # Get upper triangular indices
    rows, cols = np.triu_indices(n_regions, k=1)

    # Create edge list with values and coefficients
    edge_list = []
    for idx, (i, j) in enumerate(zip(rows, cols)):
        edge_list.append({
            'i': i,
            'j': j,
            'value': connectivity_matrix[i, j],
            'coefficient': coefficients[idx]
        })

    # Sort by absolute coefficient magnitude
    edge_list.sort(key=lambda x: abs(x['coefficient']), reverse=True)

    # Handle case where fewer edges exist than requested
    actual_n = min(n_top, len(edge_list))
    if actual_n < n_top:
        logging.warning(
            f"Only {actual_n} non-zero coefficients found, "
            f"plotting all available instead of requested {n_top}"
        )

    # Extract top connections
    top_connections = [
        (edge['i'], edge['j'], edge['value'])
        for edge in edge_list[:actual_n]
    ]

    # Create mask for visualization
    mask = np.zeros((n_regions, n_regions), dtype=bool)
    for i, j, _ in top_connections:
        mask[i, j] = True
        mask[j, i] = True

    return top_connections, mask


def generate_brain_plot(
    connectivity_matrix: np.ndarray,
    top_connections: List[Tuple[int, int, float]],
    output_path: str,
    threshold: Optional[float] = None
) -> str:
    """Generate brain surface plot using Nilearn plot_connectome.

    Args:
        connectivity_matrix: Full connectivity matrix
        top_connections: List of (i, j, value) tuples for top connections
        output_path: Path to save the plot
        threshold: Optional threshold for edge strength

    Returns:
        Path to saved plot file
    """
    # Get node coordinates (using default MNI template)
    # For Schaefer atlas, we need to load the atlas to get coordinates
    # Using a standard template for demonstration
    from nilearn.datasets import load_mni152_template

    # Load MNI template to get brain mask
    template = load_mni152_template()

    # Create a simple node coordinate set based on atlas regions
    # In practice, these would come from the Schaefer atlas definition
    n_regions = connectivity_matrix.shape[0]

    # Generate coordinates for each region (simplified approach)
    # Using a grid-like distribution in MNI space
    coords = []
    for i in range(n_regions):
        # Simple deterministic coordinate generation
        x = -80 + (i % 8) * 20
        y = -80 + ((i // 8) % 8) * 20
        z = -40 + ((i // 64) % 4) * 20
        coords.append([x, y, z])

    coords = np.array(coords)

    # Extract edge values for top connections
    edge_values = [val for _, _, val in top_connections]

    # Determine threshold if not provided
    if threshold is None and len(edge_values) > 0:
        # Use median absolute value as threshold
        threshold = np.median(np.abs(edge_values))

    # Prepare edge list for plotting
    edge_list = []
    for i, j, val in top_connections:
        if threshold is None or abs(val) >= threshold:
            edge_list.append([coords[i], coords[j], val])

    if not edge_list:
        logging.warning("No edges meet the threshold, using all top connections")
        edge_list = [[coords[i], coords[j], val] for i, j, val in top_connections]

    # Create node coordinates array
    node_coords = coords

    # Generate plot
    try:
        plot = plotting.plot_connectome(
            node_coords,
            np.array([[e[2] for e in edge_list]]).T if edge_list else np.zeros((1, 1)),
            node_coords=node_coords,
            edge_threshold="90%",
            display_mode="lyrz",
            title="Top Predictive Sleep Quality Connections",
            figsize=(12, 8)
        )

        # Save the plot
        plot.savefig(output_path)
        plot.close()

        logging.info(f"Brain plot saved to {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"Failed to generate brain plot: {e}")
        raise


def run_visualization_pipeline(
    feature_path: str,
    coefficient_path: str,
    output_dir: str,
    n_top: int = 50,
    n_regions: int = 400
) -> Dict[str, Any]:
    """Run the complete visualization pipeline.

    Args:
        feature_path: Path to connectivity features .npy file
        coefficient_path: Path to model coefficients .npy file
        output_dir: Directory to save output plots
        n_top: Number of top connections to visualize
        n_regions: Number of brain regions in the atlas

    Returns:
        Dictionary with output paths and metadata
    """
    logger = get_logger()
    log_stage_start(logger, "Visualization Pipeline", {"n_top": n_top, "n_regions": n_regions})

    try:
        # Load connectivity matrix
        log_stage_start(logger, "Loading Connectivity Matrix", {"path": feature_path})
        connectivity_matrix = load_connectivity_matrix_from_features(feature_path, n_regions)
        log_stage_complete(logger, "Loading Connectivity Matrix")

        # Load model coefficients
        log_stage_start(logger, "Loading Model Coefficients", {"path": coefficient_path})
        coefficients = np.load(coefficient_path)
        log_stage_complete(logger, "Loading Model Coefficients")

        # Extract top connections
        log_stage_start(logger, "Extracting Top Connections", {"n_top": n_top})
        top_connections, mask = extract_top_connections(
            connectivity_matrix, coefficients, n_top
        )
        log_stage_complete(logger, "Extracting Top Connections", {
            "count": len(top_connections)
        })

        # Generate brain plot
        output_path = os.path.join(output_dir, "top_connections_brain.png")
        log_stage_start(logger, "Generating Brain Plot", {"output": output_path})
        plot_path = generate_brain_plot(
            connectivity_matrix, top_connections, output_path
        )
        log_stage_complete(logger, "Generating Brain Plot")

        return {
            "plot_path": plot_path,
            "n_connections": len(top_connections),
            "n_regions": n_regions,
            "n_top_requested": n_top
        }

    except Exception as e:
        log_stage_error(logger, "Visualization Pipeline", str(e))
        raise


def main():
    """Main entry point for visualization pipeline."""
    # Get configuration
    paths = get_paths()
    n_top = get_hyperparameter("n_top_connections", 50)
    n_regions = get_hyperparameter("n_regions", 400)

    # Define paths
    feature_path = paths["processed_features"]
    coefficient_path = paths["model_coefficients"]
    output_dir = paths["results"]

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Run pipeline
    result = run_visualization_pipeline(
        feature_path=feature_path,
        coefficient_path=coefficient_path,
        output_dir=output_dir,
        n_top=n_top,
        n_regions=n_regions
    )

    print(f"Visualization complete. Plot saved to: {result['plot_path']}")
    print(f"Number of connections visualized: {result['n_connections']}")

    return result


if __name__ == "__main__":
    main()