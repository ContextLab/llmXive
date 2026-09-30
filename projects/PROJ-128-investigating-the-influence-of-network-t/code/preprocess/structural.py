"""
Structural Preprocessing Module for Brain Network Analysis.

This module handles the calculation of graph theoretical metrics from structural
connectivity matrices (derived from dMRI tractography) and performs sensitivity
analyses on graph density thresholds.
"""

import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import json
import os

from config import get_config_dict


def calculate_graph_metrics(adjacency_matrix: np.ndarray, density: Optional[float] = None) -> Dict[str, float]:
    """
    Calculate standard graph theoretical metrics for a given adjacency matrix.

    Parameters
    ----------
    adjacency_matrix : np.ndarray
        Square 2D array representing the adjacency matrix of the brain network.
        Must be symmetric for undirected graphs.
    density : float, optional
        If provided, the adjacency matrix will be thresholded to retain only
        the top 'density' fraction of edges (proportional thresholding).
        If None, the matrix is used as-is (assuming it is already thresholded).

    Returns
    -------
    Dict[str, float]
        Dictionary containing calculated metrics:
        - global_efficiency
        - average_clustering_coefficient
        - modularity (using Louvain algorithm)
        - characteristic_path_length (if graph is connected)
        - number_of_nodes
        - number_of_edges
        - actual_density

    Raises
    ------
    ValueError
        If the adjacency matrix is not square or contains negative values.
    """
    if adjacency_matrix.ndim != 2 or adjacency_matrix.shape[0] != adjacency_matrix.shape[1]:
        raise ValueError("Adjacency matrix must be a square 2D array.")
    if np.any(adjacency_matrix < 0):
        raise ValueError("Adjacency matrix cannot contain negative values.")

    # Apply proportional density threshold if specified
    if density is not None:
        if not (0.0 < density <= 1.0):
            raise ValueError("Density must be between 0 and 1 (exclusive of 0).")
        
        # Flatten upper triangle (excluding diagonal) to get unique edge weights
        n = adjacency_matrix.shape[0]
        upper_tri_indices = np.triu_indices(n, k=1)
        edge_weights = adjacency_matrix[upper_tri_indices]
        
        # Calculate threshold value corresponding to the desired density
        num_edges_to_keep = int(np.ceil(density * len(edge_weights)))
        if num_edges_to_keep == 0:
            # If density is too low to keep any edges, return empty graph metrics
            return {
                "global_efficiency": 0.0,
                "average_clustering_coefficient": 0.0,
                "modularity": 0.0,
                "characteristic_path_length": float('inf'),
                "number_of_nodes": n,
                "number_of_edges": 0,
                "actual_density": 0.0
            }
        
        threshold = np.sort(edge_weights)[-num_edges_to_keep]
        
        # Create thresholded adjacency matrix
        thresholded_matrix = (adjacency_matrix >= threshold).astype(float)
        # Ensure we don't keep more edges than intended due to ties at threshold
        if np.sum(thresholded_matrix - np.eye(n, dtype=int)) / 2 > num_edges_to_keep:
            # Need to be more precise: keep exactly top N edges
            flat_matrix = adjacency_matrix.flatten()
            flat_matrix[np.eye(n, dtype=bool)] = -1  # Ignore diagonal
            sorted_indices = np.argsort(flat_matrix)[-num_edges_to_keep:]
            thresholded_matrix = np.zeros_like(adjacency_matrix)
            for idx in sorted_indices:
                row, col = np.unravel_index(idx, adjacency_matrix.shape)
                thresholded_matrix[row, col] = 1.0
                thresholded_matrix[col, row] = 1.0
        else:
            thresholded_matrix = (adjacency_matrix >= threshold).astype(float)
    else:
        thresholded_matrix = adjacency_matrix

    # Create NetworkX graph
    G = nx.from_numpy_array(thresholded_matrix)
    
    # Calculate metrics
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    actual_density = nx.density(G)
    
    # Global Efficiency
    if n_nodes > 1:
        try:
            global_eff = nx.global_efficiency(G)
        except nx.NetworkXError:
            global_eff = 0.0
    else:
        global_eff = 0.0
    
    # Average Clustering Coefficient
    try:
        avg_clustering = nx.average_clustering(G)
    except nx.NetworkXError:
        avg_clustering = 0.0
    
    # Modularity (using Louvain algorithm)
    # Note: Louvain requires the graph to be undirected and weighted (or unweighted)
    try:
        if n_edges > 0:
            # For unweighted graphs, we can still calculate modularity
            # We need to ensure the graph is connected for meaningful modularity
            # But modularity can be calculated on disconnected graphs too
            from networkx.algorithms.community import louvain_communities
            communities = louvain_communities(G)
            modularity = nx.community.modularity(G, communities)
        else:
            modularity = 0.0
    except (nx.NetworkXError, ImportError):
        modularity = 0.0
    
    # Characteristic Path Length (only if graph is connected)
    if nx.is_connected(G) and n_nodes > 1:
        try:
            char_path_length = nx.average_shortest_path_length(G)
        except nx.NetworkXError:
            char_path_length = float('inf')
    else:
        # If not connected, use harmonic mean or infinity
        try:
            char_path_length = nx.average_shortest_path_length(G, weight=None)
        except nx.NetworkXError:
            char_path_length = float('inf')

    return {
        "global_efficiency": float(global_eff),
        "average_clustering_coefficient": float(avg_clustering),
        "modularity": float(modularity),
        "characteristic_path_length": float(char_path_length),
        "number_of_nodes": int(n_nodes),
        "number_of_edges": int(n_edges),
        "actual_density": float(actual_density)
    }


def process_subject_structural_metrics(adjacency_matrix: np.ndarray, 
                                       subject_id: str,
                                       density_thresholds: Optional[List[float]] = None) -> Tuple[Dict, List[Dict]]:
    """
    Process structural metrics for a single subject across multiple density thresholds.

    Parameters
    ----------
    adjacency_matrix : np.ndarray
        The full connectivity matrix for the subject.
    subject_id : str
        Unique identifier for the subject.
    density_thresholds : List[float], optional
        List of density thresholds to test. If None, uses a single threshold
        (default 0.15) or no thresholding.

    Returns
    -------
    Tuple[Dict, List[Dict]]
        First element: Primary metrics at baseline density (or full matrix).
        Second element: List of metrics dictionaries for each density threshold.
    """
    config = get_config_dict()
    
    if density_thresholds is None:
        density_thresholds = [config.get('DENSITY_THRESHOLD_BASELINE', 0.15)]
    
    results = []
    primary_metrics = None
    
    for density in density_thresholds:
        metrics = calculate_graph_metrics(adjacency_matrix, density=density)
        metrics['subject_id'] = subject_id
        metrics['density_threshold'] = float(density)
        results.append(metrics)
        
        # If this is the baseline density, mark it as primary
        if abs(density - config.get('DENSITY_THRESHOLD_BASELINE', 0.15)) < 1e-6:
            primary_metrics = metrics
    
    # If no baseline was found in the list, use the first one as primary
    if primary_metrics is None and results:
        primary_metrics = results[0]
        
    return primary_metrics, results


def run_structural_pipeline(subject_ids: List[str], 
                            dmri_data: Dict[str, np.ndarray],
                            output_path: Path) -> Dict[str, any]:
    """
    Run the structural analysis pipeline for a cohort of subjects.

    Parameters
    ----------
    subject_ids : List[str]
        List of subject identifiers.
    dmri_data : Dict[str, np.ndarray]
        Dictionary mapping subject_id to adjacency matrix.
    output_path : Path
        Path to the output directory for saving results.

    Returns
    -------
    Dict[str, any]
        Summary of the pipeline execution including counts of processed subjects.
    """
    config = get_config_dict()
    density_variations = config.get('DENSITY_THRESHOLD_VARIATIONS', [0.10, 0.15, 0.20])
    
    all_results = []
    processed_count = 0
    excluded_count = 0
    exclusion_log = []
    
    for subject_id in subject_ids:
        if subject_id not in dmri_data:
            exclusion_log.append({
                "subject_id": subject_id,
                "reason": "Missing DMRI data",
                "timestamp": pd.Timestamp.now().isoformat()
            })
            excluded_count += 1
            continue
        
        adjacency_matrix = dmri_data[subject_id]
        
        # Validate matrix
        if adjacency_matrix.shape[0] != adjacency_matrix.shape[1]:
            exclusion_log.append({
                "subject_id": subject_id,
                "reason": f"Non-square adjacency matrix: {adjacency_matrix.shape}",
                "timestamp": pd.Timestamp.now().isoformat()
            })
            excluded_count += 1
            continue
        
        try:
            primary_metrics, sensitivity_results = process_subject_structural_metrics(
                adjacency_matrix, 
                subject_id,
                density_thresholds=density_variations
            )
            
            all_results.extend(sensitivity_results)
            processed_count += 1
            
        except Exception as e:
            exclusion_log.append({
                "subject_id": subject_id,
                "reason": f"Processing error: {str(e)}",
                "timestamp": pd.Timestamp.now().isoformat()
            })
            excluded_count += 1
    
    # Save sensitivity analysis results
    if all_results:
        df = pd.DataFrame(all_results)
        output_file = output_path / "structural_density_sensitivity.csv"
        df.to_csv(output_file, index=False)
        
        # Also save primary metrics (baseline density) separately if needed
        baseline_results = [r for r in all_results if abs(r['density_threshold'] - config.get('DENSITY_THRESHOLD_BASELINE', 0.15)) < 1e-6]
        if baseline_results:
            baseline_df = pd.DataFrame(baseline_results)
            baseline_file = output_path / "structural_metrics.csv"
            baseline_df.to_csv(baseline_file, index=False)
    
    return {
        "processed_count": processed_count,
        "excluded_count": excluded_count,
        "output_file": str(output_path / "structural_density_sensitivity.csv") if all_results else None,
        "exclusion_log": exclusion_log
    }


def run_sensitivity_analysis(subject_ids: List[str],
                             dmri_data: Dict[str, np.ndarray],
                             output_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Execute the mandatory sensitivity analysis on graph density as per FR-008.
    
    This function iterates through DENSITY_THRESHOLD_VARIATIONS defined in config,
    calculates graph metrics for each threshold, and saves the results to a CSV.
    
    Parameters
    ----------
    subject_ids : List[str]
        List of subject identifiers to process.
    dmri_data : Dict[str, np.ndarray]
        Dictionary mapping subject_id to adjacency matrix.
    output_dir : str or Path, optional
        Directory to save output files. If None, uses default 'data/processed'.
    
    Returns
    -------
    Path
        Path to the generated CSV file containing sensitivity analysis results.
    
    Raises
    ------
    RuntimeError
        If no real data is available or processing fails completely.
    """
    config = get_config_dict()
    
    if output_dir is None:
        output_dir = Path("data/processed")
    else:
        output_dir = Path(output_dir)
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    density_variations = config.get('DENSITY_THRESHOLD_VARIATIONS', [0.10, 0.15, 0.20])
    
    if not density_variations:
        raise ValueError("DENSITY_THRESHOLD_VARIATIONS must be a non-empty list in config.")
    
    all_results = []
    processed_count = 0
    
    for subject_id in subject_ids:
        if subject_id not in dmri_data:
            continue
          
        adjacency_matrix = dmri_data[subject_id]
        
        # Validate matrix
        if adjacency_matrix.shape[0] != adjacency_matrix.shape[1]:
            continue
          
        try:
            # Process each density threshold
            for density in density_variations:
                metrics = calculate_graph_metrics(adjacency_matrix, density=density)
                metrics['subject_id'] = subject_id
                metrics['density_threshold'] = float(density)
                all_results.append(metrics)
            processed_count += 1
        except Exception as e:
            # Log but continue processing other subjects
            print(f"Warning: Failed to process subject {subject_id}: {e}")
            continue
  
    if not all_results:
        raise RuntimeError("Sensitivity analysis failed: No results generated. "
                         "Ensure real DMRI data is provided and DENSITY_THRESHOLD_VARIATIONS is valid.")
    
    # Create DataFrame and save
    df = pd.DataFrame(all_results)
    output_file = output_dir / "structural_density_sensitivity.csv"
    df.to_csv(output_file, index=False)
    
    print(f"Sensitivity analysis complete. Results saved to: {output_file}")
    print(f"Processed {processed_count} subjects across {len(density_variations)} density thresholds.")
    print(f"Columns: {list(df.columns)}")
    
    return output_file


def save_structural_metrics_to_csv(metrics_list: List[Dict], output_path: Union[str, Path]) -> Path:
    """
    Save a list of structural metrics dictionaries to a CSV file.

    Parameters
    ----------
    metrics_list : List[Dict]
        List of dictionaries containing metrics for each subject/density.
    output_path : str or Path
        Path to the output CSV file.

    Returns
    -------
    Path
        Path to the saved file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df = pd.DataFrame(metrics_list)
    df.to_csv(output_path, index=False)
    return output_path


def main():
    """
    Main entry point for structural preprocessing when run as a script.
    
    This function demonstrates the usage of the sensitivity analysis
    by loading sample data (if available) and running the pipeline.
    """
    import sys
    
    # Check if we have access to real data
    # In a real execution, this would be provided by the main pipeline
    print("Structural Preprocessing Module - Sensitivity Analysis")
    print("This module is designed to be called from main.py or run_sensitivity_analysis()")
    print("")
    print("To run the full pipeline, execute: python code/main.py")
    print("")
    
    # Validate configuration
    try:
        config = get_config_dict()
        print(f"Configuration loaded successfully.")
        print(f"DENSITY_THRESHOLD_BASELINE: {config.get('DENSITY_THRESHOLD_BASELINE')}")
        print(f"DENSITY_THRESHOLD_VARIATIONS: {config.get('DENSITY_THRESHOLD_VARIATIONS')}")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
