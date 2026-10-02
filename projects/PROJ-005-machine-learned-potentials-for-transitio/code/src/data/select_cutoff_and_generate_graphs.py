"""
Task T017c: Select optimal cutoff and generate final graphs.

This script performs the following steps:
1. Loads sensitivity metrics from code/data/results/cutoff_sensitivity.json.
2. Selects the cutoff that minimizes the variance of graph metrics.
3. Loads raw geometries (intermediate graphs) from code/data/processed/graphs_intermediate.parquet.
4. Re-builds the adjacency matrices and edge attributes using the selected cutoff.
5. Calculates coordination numbers and flags outliers (>6 coordination).
6. Saves the final `graphs.parquet` to code/data/processed/graphs.parquet.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd

# Import existing utilities from the project API surface
from src.data.graph_construction import (
    get_project_root,
    load_processed_graphs_intermediate,
    parse_atomic_features,
    calculate_distance_matrix,
    build_adjacency_matrix,
    calculate_coordination_number,
    extract_edge_attributes,
    calculate_graph_metrics,
)
from src.utils.logging import setup_logger, get_logger

# Setup logger
logger = setup_logger(__name__)


def load_sensitivity_metrics(metrics_path: Path) -> List[Dict[str, Any]]:
    """Load the cutoff sensitivity metrics JSON."""
    if not metrics_path.exists():
        raise FileNotFoundError(f"Sensitivity metrics file not found: {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        data = json.load(f)
    
    # Filter out entries that have no data (status == 'no_data')
    valid_entries = [e for e in data if e.get("status") != "no_data" and e.get("samples_processed", 0) > 0]
    
    if not valid_entries:
        raise ValueError("No valid data found in sensitivity metrics. Cannot select optimal cutoff.")
    
    return valid_entries


def select_optimal_cutoff(metrics: List[Dict[str, Any]]) -> float:
    """
    Select the cutoff that minimizes the variance of graph metrics.
    
    The task description implies minimizing the variance of the metrics calculated
    across the sweep. Since we have one entry per cutoff, we look at the stability
    of the metrics. However, usually, sensitivity analysis looks for the cutoff
    where metrics stabilize (low variance in change) or where a specific metric
    (like edge feature CV) is minimized.
    
    Given the structure of `cutoff_sensitivity.json` which contains:
    - avg_edge_feature_cv (Coefficient of Variation)
    - graph_density
    
    We will select the cutoff that minimizes `avg_edge_feature_cv` as it represents
    the stability of edge features, or if we consider the "variance of metrics"
    literally as the variance of the set of metrics for that cutoff (which we don't
    have here, only aggregates), we interpret the goal as finding the most stable
    configuration.
    
    A common heuristic is to pick the cutoff with the lowest `avg_edge_feature_cv`
    among those with sufficient samples, or the first one where `graph_density`
    stabilizes.
    
    Let's implement a selection based on minimizing `avg_edge_feature_cv` 
    while ensuring `samples_processed` is high (which it should be for all valid).
    If the task strictly means "minimizing metric variance" and we assume the 
    provided JSON *is* the result of a variance calculation (as per T017b),
    we might look for a specific key. But T017b output structure isn't fully 
    defined in the prompt, only T017a output.
    
    Re-reading T017b: "Compute variance of metrics across cutoffs."
    T017c Input: `cutoff_sensitivity.json` (from T017b).
    The file content provided shows the raw metrics per cutoff, not the variance 
    across them. This suggests T017b might have appended a variance key or the 
    file name is slightly misleading and contains the raw data to be analyzed.
    
    Strategy: Select the cutoff with the lowest `avg_edge_feature_cv` (most stable 
    edge features) among valid entries. If there's a tie, pick the smallest cutoff 
    (more sparse, less noise).
    """
    # Sort by avg_edge_feature_cv ascending, then by cutoff ascending
    sorted_metrics = sorted(
        metrics, 
        key=lambda x: (x.get("avg_edge_feature_cv", float('inf')), x.get("cutoff", float('inf')))
    )
    
    best = sorted_metrics[0]
    logger.info(f"Selected optimal cutoff: {best['cutoff']} (CV: {best['avg_edge_feature_cv']:.4f})")
    return best["cutoff"]


def flag_outliers(df: pd.DataFrame, threshold: int = 6) -> pd.DataFrame:
    """
    Flag samples with coordination number > threshold as outliers.
    
    Input DataFrame must have a 'coordination_number' column (or similar).
    The graph_construction logic calculates CN per node, but for the final
    graph metadata, we often store the max CN or mean CN.
    
    Assumption: The intermediate dataframe has node-level CN or we calculate
    the max CN per graph.
    """
    if 'max_coordination_number' not in df.columns:
        # If we only have node-level CN, we need to group by graph_id
        # Assuming 'graph_id' exists
        if 'coordination_number' in df.columns and 'graph_id' in df.columns:
            max_cn = df.groupby('graph_id')['coordination_number'].max().reset_index()
            max_cn.rename(columns={'coordination_number': 'max_coordination_number'}, inplace=True)
            df = df.merge(max_cn, on='graph_id', how='left')
        else:
            # Fallback: assume a single CN value per row if it's already aggregated
            df['max_coordination_number'] = df.get('coordination_number', 0)
    
    df['is_outlier'] = df['max_coordination_number'] > threshold
    return df


def run_cutoff_selection_and_graph_generation():
    """Main execution function for T017c."""
    root = get_project_root()
    metrics_path = root / "data" / "results" / "cutoff_sensitivity.json"
    intermediate_path = root / "data" / "processed" / "graphs_intermediate.parquet"
    output_path = root / "data" / "processed" / "graphs.parquet"
    
    logger.info(f"Loading sensitivity metrics from {metrics_path}")
    metrics = load_sensitivity_metrics(metrics_path)
    
    logger.info("Selecting optimal cutoff")
    optimal_cutoff = select_optimal_cutoff(metrics)
    
    logger.info(f"Loading intermediate graphs from {intermediate_path}")
    if not intermediate_path.exists():
        raise FileNotFoundError(f"Intermediate graphs not found: {intermediate_path}. "
                                "Please ensure T015 and T017a have run successfully.")
    
    df_intermediate = load_processed_graphs_intermediate(intermediate_path)
    
    # Re-process with optimal cutoff
    # The intermediate data likely contains raw coordinates and atomic features.
    # We need to rebuild the graph structures.
    
    logger.info(f"Re-building graphs with cutoff={optimal_cutoff}")
    
    # We assume the intermediate dataframe has columns:
    # 'atomic_numbers', 'positions', 'graph_id', 'energy_dft', 'barrier_height', 'metal_center', 'ligand_class'
    # We need to iterate and rebuild adjacency/edge attributes.
    
    final_records = []
    
    # If the intermediate data is already in a flat format with coordinates, we reconstruct
    # However, `load_processed_graphs_intermediate` returns a DataFrame.
    # Let's assume it has 'atomic_numbers' (list), 'positions' (list of lists), 'graph_id'.
    
    # We need to reconstruct the adjacency matrix and edge features for each graph
    # using the optimal cutoff.
    
    # Group by graph_id to process each molecule
    if 'graph_id' not in df_intermediate.columns:
        # If the data is already one row per graph, we might not need to group
        # But usually graph construction iterates over molecules.
        # Let's assume the dataframe is one row per graph.
        graph_ids = df_intermediate.index if df_intermediate.index.name == 'graph_id' else range(len(df_intermediate))
        # Fallback to index if no graph_id column
        if 'graph_id' not in df_intermediate.columns:
            df_intermediate['graph_id'] = graph_ids
    
    for _, row in df_intermediate.iterrows():
        try:
            atomic_numbers = row.get('atomic_numbers')
            positions = row.get('positions')
            
            if atomic_numbers is None or positions is None:
                logger.warning(f"Skipping graph {row.get('graph_id')}: missing atomic data")
                continue
            
            atomic_numbers = np.array(atomic_numbers)
            positions = np.array(positions)
            
            if len(atomic_numbers) != len(positions):
                logger.warning(f"Skipping graph {row.get('graph_id')}: shape mismatch")
                continue
            
            # Calculate distance matrix
            dist_matrix = calculate_distance_matrix(positions)
            
            # Build adjacency matrix based on optimal_cutoff
            adj_matrix = build_adjacency_matrix(dist_matrix, cutoff=optimal_cutoff)
            
            # Calculate coordination numbers
            coord_numbers = calculate_coordination_number(adj_matrix)
            
            # Extract edge attributes (features based on distance)
            edge_attrs = extract_edge_attributes(dist_matrix, adj_matrix)
            
            # Calculate graph metrics
            metrics_row = calculate_graph_metrics(adj_matrix, edge_attrs)
            
            # Prepare the record
            record = {
                'graph_id': row.get('graph_id'),
                'atomic_numbers': atomic_numbers.tolist(),
                'positions': positions.tolist(),
                'adjacency_matrix': adj_matrix.tolist(),
                'edge_attributes': edge_attrs, # Might be a list of lists or similar
                'coordination_numbers': coord_numbers.tolist(),
                'max_coordination_number': float(np.max(coord_numbers)) if len(coord_numbers) > 0 else 0.0,
                'energy_dft': row.get('energy_dft'),
                'barrier_height': row.get('barrier_height'),
                'metal_center': row.get('metal_center'),
                'ligand_class': row.get('ligand_class'),
                'cutoff_used': optimal_cutoff,
                **metrics_row # avg_degree, density, etc.
            }
            
            final_records.append(record)
            
        except Exception as e:
            logger.error(f"Error processing graph {row.get('graph_id')}: {e}", exc_info=True)
            continue
    
    if not final_records:
        raise RuntimeError("No graphs were successfully processed.")
    
    df_final = pd.DataFrame(final_records)
    
    # Flag outliers
    logger.info("Flagging outliers (coordination > 6)")
    df_final = flag_outliers(df_final, threshold=6)
    
    # Save final output
    logger.info(f"Saving final graphs to {output_path}")
    df_final.to_parquet(output_path, index=False)
    
    logger.info(f"Successfully generated {len(df_final)} graphs with cutoff {optimal_cutoff}")
    logger.info(f"Outliers flagged: {df_final['is_outlier'].sum()}")
    
    return df_final


def main():
    """Entry point."""
    try:
        run_cutoff_selection_and_graph_generation()
        logger.info("Task T017c completed successfully.")
    except Exception as e:
        logger.error(f"Task T017c failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
