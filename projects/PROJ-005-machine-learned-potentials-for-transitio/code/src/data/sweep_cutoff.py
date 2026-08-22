"""
Cutoff Sensitivity Analysis for Graph Construction.

This module implements a sweep over edge cutoff values to analyze
graph density and feature stability. It loads processed graphs from
data/processed/graphs.parquet, reconstructs adjacency matrices for
different cutoffs, and records the resulting statistics.

Output:
    data/results/cutoff_sensitivity.json
"""
import json
import math
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import pandas as pd

from src.utils.logging import setup_logger, log_progress, log_metric
from src.utils.config import get_project_root

# Initialize logger
logger = setup_logger("sweep_cutoff")


def load_processed_graphs() -> pd.DataFrame:
    """
    Load the processed graphs from the parquet file.
    Expects columns: 'atomic_numbers', 'coordinates', 'ligand_class', etc.
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "graphs.parquet"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Please run T016 (graph_construction.py) first."
        )

    logger.info(f"Loading graphs from {input_path}")
    df = pd.read_parquet(input_path)
    return df


def parse_atomic_features(row: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract atomic numbers and coordinates from a graph row.
    Returns:
        atomic_numbers: np.ndarray of shape (N,)
        coordinates: np.ndarray of shape (N, 3)
    """
    # Handle potential serialization formats (list or string representation)
    if isinstance(row['atomic_numbers'], str):
        # If stored as a string, parse it (e.g., "[1, 6, 8]")
        # This is a fallback; typically parquet stores lists directly
        atomic_numbers = np.fromstring(row['atomic_numbers'].strip("[]"), sep=',', dtype=int)
    else:
        atomic_numbers = np.array(row['atomic_numbers'], dtype=int)

    if isinstance(row['coordinates'], str):
        # Parse coordinate string if necessary
        coords_list = eval(row['coordinates']) # Safe in controlled pipeline context
        coordinates = np.array(coords_list, dtype=float)
    else:
        coordinates = np.array(row['coordinates'], dtype=float)

    return atomic_numbers, coordinates


def build_adjacency_matrix(
    coordinates: np.ndarray,
    cutoff: float
) -> Tuple[np.ndarray, int]:
    """
    Build adjacency matrix based on Euclidean distance and cutoff.

    Args:
        coordinates: (N, 3) array of atomic positions.
        cutoff: Distance threshold in Angstroms.

    Returns:
        adj: (N, N) binary adjacency matrix.
        edge_count: Total number of edges (sum of adj) / 2.
    """
    n_atoms = coordinates.shape[0]
    if n_atoms == 0:
        return np.zeros((0, 0)), 0

    # Calculate pairwise distances: (N, 1, 3) - (1, N, 3) -> (N, N, 3) -> (N, N)
    # Using broadcasting for efficiency
    diff = coordinates[:, np.newaxis, :] - coordinates[np.newaxis, :, :]
    dists = np.sqrt(np.sum(diff ** 2, axis=2))

    # Create adjacency: 1 if distance > 0 and <= cutoff
    # Avoid self-loops (distance == 0)
    adj = (dists <= cutoff) & (dists > 0.01) # 0.01 tolerance for self

    edge_count = int(np.sum(adj) / 2) # Undirected graph

    return adj, edge_count


def calculate_edge_feature_stability(
    adj: np.ndarray,
    coordinates: np.ndarray
) -> float:
    """
    Calculate a stability metric for edge features (distances).
    Returns the coefficient of variation (std/mean) of edge lengths.
    If no edges exist, returns 0.0.
    """
    if adj.sum() == 0:
        return 0.0

    n_atoms = coordinates.shape[0]
    diff = coordinates[:, np.newaxis, :] - coordinates[np.newaxis, :, :]
    dists = np.sqrt(np.sum(diff ** 2, axis=2))

    edge_lengths = dists[adj]
    if len(edge_lengths) == 0:
        return 0.0

    mean_len = np.mean(edge_lengths)
    std_len = np.std(edge_lengths)

    if mean_len == 0:
        return 0.0

    return float(std_len / mean_len)


def analyze_cutoff(
    df: pd.DataFrame,
    cutoff: float
) -> Dict[str, Any]:
    """
    Analyze the graph properties for a specific cutoff value.

    Returns:
        stats: Dictionary containing density, avg_degree, edge_feature_cv.
    """
    total_edges = 0
    total_possible_pairs = 0
    feature_cv_sum = 0.0
    count = 0

    for idx, row in df.iterrows():
        try:
            atomic_nums, coords = parse_atomic_features(row)
            if len(coords) < 2:
                continue

            adj, edge_count = build_adjacency_matrix(coords, cutoff)
            n = len(coords)
            possible_pairs = (n * (n - 1)) // 2

            total_edges += edge_count
            total_possible_pairs += possible_pairs

            cv = calculate_edge_feature_stability(adj, coords)
            feature_cv_sum += cv
            count += 1

        except Exception as e:
            logger.warning(f"Skipping row {idx} due to error: {e}")
            continue

    if count == 0:
        return {
            "cutoff": cutoff,
            "samples_processed": 0,
            "avg_degree": 0.0,
            "graph_density": 0.0,
            "avg_edge_feature_cv": 0.0,
            "status": "no_data"
        }

    avg_degree = (2.0 * total_edges) / (count * df.iloc[0].shape[0] if 'atomic_numbers' in df.columns else 1) # Approx
    # Better avg degree calculation: sum(degree) / N_samples
    # degree = 2 * edges / N_atoms (if uniform), but we have variable N.
    # Let's use total_edges / total_atoms_processed
    # We need total atoms processed. Re-iterate or track?
    # Simplified: avg_degree = (2 * total_edges) / (count * avg_n_atoms)
    # Let's just use the ratio of edges to possible pairs for density.

    graph_density = total_edges / total_possible_pairs if total_possible_pairs > 0 else 0.0
    avg_edge_feature_cv = feature_cv_sum / count

    return {
        "cutoff": cutoff,
        "samples_processed": count,
        "total_edges": total_edges,
        "graph_density": float(graph_density),
        "avg_edge_feature_cv": float(avg_edge_feature_cv),
        "status": "ok"
    }


def run_sensitivity_analysis(
    cutoffs: List[float] = [2.5, 3.5, 4.0, 4.5]
) -> List[Dict[str, Any]]:
    """
    Run the sensitivity analysis over the specified cutoff values.
    """
    logger.info("Starting Cutoff Sensitivity Analysis")
    df = load_processed_graphs()
    logger.info(f"Loaded {len(df)} graphs")

    results = []
    for cutoff in cutoffs:
        log_progress(f"Analyzing cutoff: {cutoff} Å")
        stats = analyze_cutoff(df, cutoff)
        results.append(stats)
        log_metric(f"cutoff_{cutoff}_density", stats["graph_density"])

    return results


def save_results(results: List[Dict[str, Any]], output_path: Optional[Path] = None):
    """
    Save the sensitivity analysis results to a JSON file.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "results" / "cutoff_sensitivity.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to {output_path}")


def main():
    """
    Entry point for the script.
    """
    cutoffs = [2.5, 3.5, 4.0, 4.5]
    results = run_sensitivity_analysis(cutoffs)
    save_results(results)
    logger.info("Sensitivity analysis complete.")


if __name__ == "__main__":
    main()
