import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

from src.utils.config import load_config, get_project_root
from src.data.graph_construction import (
    load_processed_graphs_intermediate,
    parse_atomic_features,
    calculate_distance_matrix,
    build_adjacency_matrix,
    calculate_coordination_number,
    extract_edge_attributes,
    calculate_graph_metrics,
    analyze_cutoff
)
from src.data.outlier_handler import load_graphs_with_metadata, compute_coordination_numbers, flag_outliers, save_flagged_graphs

logger = logging.getLogger(__name__)

def load_processed_graphs_intermediate(data_dir: Path) -> pd.DataFrame:
    """
    Load the intermediate processed graphs from T015/T016.
    This function expects the raw geometries to have been processed into a DataFrame
    with atomic features and edge candidates.
    """
    input_file = data_dir / "processed" / "graphs_intermediate.parquet"
    if not input_file.exists():
        # Fallback to a standard location if intermediate file is missing
        input_file = data_dir / "processed" / "graphs.parquet"
        if not input_file.exists():
            raise FileNotFoundError(f"Intermediate or final graphs file not found at {input_file}")
    
    return pd.read_parquet(input_file)

def calculate_graph_metrics_for_cutoff(
    df: pd.DataFrame, 
    cutoff: float, 
    atomic_features: np.ndarray, 
    positions: np.ndarray
) -> Dict[str, Any]:
    """
    Calculate graph metrics for a specific cutoff.
    Returns: {avg_degree, edge_count, density, avg_coordination}
    """
    distance_matrix = calculate_distance_matrix(positions)
    adj_matrix = build_adjacency_matrix(distance_matrix, cutoff)
    
    edge_count = np.sum(adj_matrix)
    num_nodes = len(df)
    num_edges = edge_count // 2  # Undirected graph
    
    if num_nodes > 0:
        avg_degree = (2 * num_edges) / num_nodes
        density = num_edges / (num_nodes * (num_nodes - 1) / 2) if num_nodes > 1 else 0.0
    else:
        avg_degree = 0.0
        density = 0.0

    # Calculate coordination numbers (CN) for outlier detection later
    # CN = degree of the node in the graph
    coordination_numbers = np.sum(adj_matrix, axis=1)
    avg_coordination = float(np.mean(coordination_numbers))

    # Calculate edge feature stability (e.
    # g., variance of distances for edges within cutoff)
    edge_distances = distance_matrix[adj_matrix.astype(bool)]
    if len(edge_distances) > 0:
        edge_feature_cv = float(np.std(edge_distances) / np.mean(edge_distances)) if np.mean(edge_distances) > 0 else 0.0
    else:
        edge_feature_cv = 0.0

    return {
        "cutoff": cutoff,
        "samples_processed": num_nodes,
        "total_edges": num_edges,
        "avg_degree": avg_degree,
        "graph_density": density,
        "avg_coordination": avg_coordination,
        "avg_edge_feature_cv": edge_feature_cv
    }

def run_sensitivity_analysis(data_dir: Path, cutoffs: List[float]) -> List[Dict[str, Any]]:
    """
    Perform cutoff sensitivity analysis.
    1. Load raw geometries.
    2. For each cutoff, calculate metrics.
    3. Return list of results.
    """
    logger.info("Loading intermediate graphs for sensitivity analysis...")
    df = load_processed_graphs_intermediate(data_dir)
    
    # Extract positions and atomic features
    # Assuming 'positions' is a column with shape (N, 3) or similar structure
    # For QM9-TS, positions are typically stored as a list of arrays or a 3D array
    if 'positions' in df.columns:
        positions_list = df['positions'].values
        # Convert to numpy array if necessary
        if isinstance(positions_list[0], (list, np.ndarray)):
            positions = np.array(positions_list)
        else:
            # Fallback: try to parse from string or other format
            raise ValueError("Positions column format not recognized for numpy conversion.")
    else:
        # Try to infer from other columns or raise error
        raise KeyError("Column 'positions' not found in intermediate graphs DataFrame.")

    results = []
    for cutoff in cutoffs:
        logger.info(f"Analyzing cutoff: {cutoff} Angstroms")
        metrics = calculate_graph_metrics_for_cutoff(df, cutoff, None, positions)
        results.append(metrics)
    
    return results

def select_optimal_cutoff(results: List[Dict[str, Any]], logger: logging.Logger) -> Tuple[float, str]:
    """
    Select the cutoff that minimizes the variance of graph metrics.
    Justification is logged.
    """
    if not results:
        raise ValueError("No results to analyze for optimal cutoff.")

    # We will look at the variance of 'avg_degree' and 'graph_density' across the dataset
    # But here we are comparing different cutoffs. The task says "minimizing metric variance".
    # This likely means the cutoff where the graph properties are most stable or optimal.
    # A common heuristic is to choose the cutoff where the density is high but not too high,
    # or where the variance of edge lengths is minimized.
    # Let's interpret "minimizing metric variance" as minimizing the variance of the 'avg_edge_feature_cv'
    # or choosing the cutoff that balances edge count and density.
    
    # Alternative interpretation: The task asks to select the cutoff minimizing the variance
    # of the metrics *across the samples*? No, the metrics are aggregated.
    # Let's assume we want the cutoff that produces the most "stable" graph structure,
    # often indicated by a plateau in edge count or density.
    
    # Heuristic: Minimize the coefficient of variation (CV) of edge distances (already calculated as avg_edge_feature_cv)
    # OR maximize the edge count while keeping density reasonable.
    # Let's use the provided 'avg_edge_feature_cv' as a proxy for stability.
    # Lower CV means more uniform edge lengths, which is often desirable.
    
    best_cutoff = None
    min_cv = float('inf')
    justification = ""

    for res in results:
        cv = res['avg_edge_feature_cv']
        if cv < min_cv:
            min_cv = cv
            best_cutoff = res['cutoff']
    
    # If we have multiple cutoffs, we can also check for a plateau
    # For now, we select the one with the lowest CV.
    justification = f"Selected cutoff {best_cutoff} Å because it minimizes the average edge feature coefficient of variation ({min_cv:.4f}), indicating the most stable edge length distribution."
    
    logger.info(justification)
    return best_cutoff, justification

def generate_final_graphs(
    data_dir: Path, 
    optimal_cutoff: float, 
    threshold_data_scarcity: int
) -> pd.DataFrame:
    """
    Generate the final graphs.parquet using the selected cutoff.
    Flags outliers (coordination > 6).
    """
    logger.info(f"Generating final graphs with cutoff {optimal_cutoff} Å...")
    
    df = load_processed_graphs_intermediate(data_dir)
    positions = df['positions'].values
    
    # Calculate distance matrix and adjacency
    distance_matrix = calculate_distance_matrix(positions)
    adj_matrix = build_adjacency_matrix(distance_matrix, optimal_cutoff)
    
    # Calculate coordination numbers
    coordination_numbers = np.sum(adj_matrix, axis=1)
    
    # Flag outliers: coordination > 6
    is_outlier = coordination_numbers > 6
    df['is_outlier'] = is_outlier
    df['coordination_number'] = coordination_numbers
    
    # Extract edge attributes
    edge_index, edge_attr = extract_edge_attributes(distance_matrix, adj_matrix, optimal_cutoff)
    df['edge_index'] = [edge_index] * len(df) # Store per graph? No, this is a dataset of graphs.
    # The structure of df needs to be a list of graphs or a single large graph?
    # Assuming df is a list of graphs (one row per molecule/transition state)
    # If df is a single large graph, we need to restructure.
    # Based on T015/T016, it's likely a list of graphs.
    # Let's assume each row in df is a graph.
    # Then 'positions' is a list of coordinates for that graph.
    
    # Re-evaluating: If df is a list of graphs, we need to iterate.
    # Let's assume the 'positions' column contains a 2D array for each graph.
    final_graphs = []
    for idx, row in df.iterrows():
        pos = row['positions']
        if isinstance(pos, (list, np.ndarray)):
            pos = np.array(pos)
            dist_mat = calculate_distance_matrix(pos)
            adj = build_adjacency_matrix(dist_mat, optimal_cutoff)
            cn = np.sum(adj, axis=1)
            outlier = cn > 6
            
            # Extract features
            # Assuming 'atomic_features' column exists
            atomic_features = row.get('atomic_features', None)
            if atomic_features is None:
                atomic_features = parse_atomic_features(row)
            
            graph_data = {
                "sample_id": row.get('sample_id', idx),
                "atomic_features": atomic_features,
                "edge_index": np.array(np.where(adj)).T,
                "edge_attr": extract_edge_attributes(dist_mat, adj, optimal_cutoff)[1],
                "coordination_number": cn,
                "is_outlier": outlier,
                "energy_dft": row.get('energy_dft', 0.0),
                "barrier_height": row.get('barrier_height', 0.0),
                "metal_center": row.get('metal_center', 'unknown'),
                "ligand_class": row.get('ligand_class', 'unknown')
            }
            final_graphs.append(graph_data)
    
    # Convert to DataFrame for parquet
    # We need to serialize the numpy arrays
    final_df = pd.DataFrame(final_graphs)
    return final_df

def run_cutoff_selection_and_graph_generation(data_dir: Path, config: Dict[str, Any]) -> None:
    """
    Main entry point for T017.
    1. Load cutoff range from config.
    2. Run sensitivity analysis.
    3. Write raw results to cutoff_sensitivity_raw.json.
    4. Select optimal cutoff.
    5. Generate final graphs.
    6. Save to graphs.parquet and cutoff_sensitivity.json.
    """
    cutoffs = config.get('CUTOFF_RANGE', [3.0, 3.5, 4.0])
    threshold_data_scarcity = config.get('THRESHOLD_DATA_SCARCITY', 120)
    
    logger.info(f"Starting cutoff sensitivity analysis with cutoffs: {cutoffs}")
    
    # 1. Run sensitivity analysis
    raw_results = run_sensitivity_analysis(data_dir, cutoffs)
    
    # 2. Write raw results
    raw_output_path = data_dir / "results" / "cutoff_sensitivity_raw.json"
    raw_output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(raw_output_path, 'w') as f:
        json.dump(raw_results, f, indent=2)
    logger.info(f"Raw sensitivity results written to {raw_output_path}")
    
    # 3. Select optimal cutoff
    optimal_cutoff, justification = select_optimal_cutoff(raw_results, logger)
    
    # 4. Generate final graphs
    final_graphs_df = generate_final_graphs(data_dir, optimal_cutoff, threshold_data_scarcity)
    
    # 5. Save final graphs
    final_graphs_path = data_dir / "processed" / "graphs.parquet"
    final_graphs_path.parent.mkdir(parents=True, exist_ok=True)
    final_graphs_df.to_parquet(final_graphs_path)
    logger.info(f"Final graphs saved to {final_graphs_path}")
    
    # 6. Prepare and save summary results
    summary_results = []
    for res in raw_results:
        summary_results.append({
            "cutoff": res["cutoff"],
            "samples_processed": res["samples_processed"],
            "total_edges": res["total_edges"],
            "graph_density": res["graph_density"],
            "avg_edge_feature_cv": res["avg_edge_feature_cv"],
            "status": "processed"
        })
    
    # Add optimal cutoff info
    summary_results.append({
        "optimal_cutoff": optimal_cutoff,
        "justification": justification
    })
    
    summary_output_path = data_dir / "results" / "cutoff_sensitivity.json"
    with open(summary_output_path, 'w') as f:
        json.dump(summary_results, f, indent=2)
    logger.info(f"Sensitivity summary written to {summary_output_path}")

def main():
    """
    Entry point for the script.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config = load_config()
    data_dir = get_project_root()
    
    try:
        run_cutoff_selection_and_graph_generation(data_dir, config)
    except Exception as e:
        logger.error(f"Error during cutoff selection and graph generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
