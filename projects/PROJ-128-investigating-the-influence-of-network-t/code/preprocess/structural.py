"""
Structural graph metric calculation module.

Computes topological metrics (global efficiency, average clustering, modularity)
from diffusion MRI structural connectivity matrices using NetworkX.
Handles sparsity exclusion (>90% sparsity threshold).
"""
import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import from sibling modules
from preprocess.loader import load_hcp_dmri
from config import get_config

def calculate_graph_metrics(adjacency_matrix: np.ndarray) -> Dict[str, float]:
    """
    Calculate topological graph metrics from an adjacency matrix.

    Parameters
    ----------
    adjacency_matrix : np.ndarray
        Square adjacency matrix representing structural connectivity.

    Returns
    -------
    Dict[str, float]
        Dictionary containing:
        - global_efficiency: Global efficiency of the network
        - average_clustering: Average clustering coefficient
        - modularity: Modularity score (if communities detected)
        - sparsity: Fraction of zero entries in the matrix
    """
    # Ensure matrix is symmetric (undirected graph)
    if not np.allclose(adjacency_matrix, adjacency_matrix.T, rtol=1e-5):
        logger.warning("Adjacency matrix is not symmetric. Symmetrizing...")
        adjacency_matrix = (adjacency_matrix + adjacency_matrix.T) / 2.0

    # Calculate sparsity
    n_nodes = adjacency_matrix.shape[0]
    total_possible_edges = n_nodes * (n_nodes - 1) / 2.0
    non_zero_edges = np.sum(np.triu(adjacency_matrix, k=1) > 0)
    sparsity = 1.0 - (non_zero_edges / total_possible_edges) if total_possible_edges > 0 else 1.0

    # Check sparsity threshold (exclude if >90% sparse)
    if sparsity > 0.90:
        logger.warning(f"Sparsity {sparsity:.4f} exceeds 90% threshold. Returning None metrics.")
        return None

    # Create NetworkX graph
    G = nx.from_numpy_array(adjacency_matrix)

    # Remove self-loops (if any)
    G.remove_edges_from(nx.selfloop_edges(G))

    # Calculate global efficiency
    try:
        global_efficiency = nx.global_efficiency(G)
    except nx.NetworkXError as e:
        logger.warning(f"Error calculating global efficiency: {e}")
        global_efficiency = 0.0

    # Calculate average clustering coefficient
    try:
        average_clustering = nx.average_clustering(G)
    except nx.NetworkXError as e:
        logger.warning(f"Error calculating average clustering: {e}")
        average_clustering = 0.0

    # Calculate modularity (requires community detection)
    modularity = 0.0
    try:
        # Use Louvain method for community detection
        if len(G.nodes()) > 1:
            try:
                from networkx.algorithms.community import louvain_communities
                communities = louvain_communities(G)
                modularity = nx.community.modularity(G, communities)
            except ImportError:
                # Fallback to label propagation if Louvain not available
                from networkx.algorithms.community import label_propagation_communities
                communities = label_propagation_communities(G)
                modularity = nx.community.modularity(G, communities)
            except nx.NetworkXError as e:
                logger.warning(f"Error calculating modularity: {e}")
    except Exception as e:
        logger.warning(f"Modularity calculation failed: {e}")

    return {
        "global_efficiency": float(global_efficiency),
        "average_clustering": float(average_clustering),
        "modularity": float(modularity),
        "sparsity": float(sparsity)
    }

def process_subject_structural_metrics(subject_id: str, adjacency_matrix: np.ndarray) -> Optional[Dict[str, Union[str, float]]]:
    """
    Process structural connectivity matrix for a single subject.

    Parameters
    ----------
    subject_id : str
        Subject identifier.
    adjacency_matrix : np.ndarray
        Structural connectivity adjacency matrix.

    Returns
    -------
    Optional[Dict[str, Union[str, float]]]
        Dictionary with subject_id and metrics, or None if sparsity exceeds threshold.
    """
    metrics = calculate_graph_metrics(adjacency_matrix)

    if metrics is None:
        return None

    return {
        "subject_id": subject_id,
        "global_efficiency": metrics["global_efficiency"],
        "average_clustering": metrics["average_clustering"],
        "modularity": metrics["modularity"],
        "sparsity": metrics["sparsity"]
    }

def run_structural_pipeline(subject_ids: Optional[List[str]] = None,
                             output_path: Optional[Union[str, Path]] = None) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Run structural graph metric calculation pipeline for all subjects.

    Parameters
    ----------
    subject_ids : Optional[List[str]]
        List of subject IDs to process. If None, processes all available subjects.
    output_path : Optional[Union[str, Path]]
        Path to save the output CSV. If None, no file is saved.

    Returns
    -------
    Tuple[pd.DataFrame, List[Dict]]
        - DataFrame containing all subject metrics
        - List of exclusion records (subjects with sparsity > 90%)
    """
    config = get_config()
    exclusion_log = []
    results = []

    # Load all HCP dMRI data
    subjects_data = load_hcp_dmri(subject_ids=subject_ids)

    logger.info(f"Processing {len(subjects_data)} subjects for structural metrics...")

    for subject_id, adjacency_matrix in subjects_data.items():
        logger.info(f"Processing subject: {subject_id}")

        # Validate matrix
        if adjacency_matrix is None or adjacency_matrix.size == 0:
            exclusion_log.append({
                "subject_id": subject_id,
                "reason": "Empty or None adjacency matrix"
            })
            continue

        result = process_subject_structural_metrics(subject_id, adjacency_matrix)

        if result is None:
            exclusion_log.append({
                "subject_id": subject_id,
                "reason": "Sparsity > 90% threshold"
            })
        else:
            results.append(result)

    # Create DataFrame
    df = pd.DataFrame(results)

    # Save to CSV if output_path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Structural metrics saved to {output_path}")

    # Save exclusion log
    exclusion_log_path = Path(config["data"]["processed"]) / "exclusion_log.json"
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(exclusion_log_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    logger.info(f"Exclusion log saved to {exclusion_log_path}")

    return df, exclusion_log

def main():
    """
    Main entry point for structural graph metric calculation.
    """
    config = get_config()
    output_path = Path(config["data"]["processed"]) / "structural_metrics.csv"

    logger.info("Starting structural graph metric calculation pipeline...")

    df, exclusion_log = run_structural_pipeline(output_path=output_path)

    logger.info(f"Pipeline complete. Processed {len(df)} subjects, excluded {len(exclusion_log)} subjects.")

    return df, exclusion_log

if __name__ == "__main__":
    main()