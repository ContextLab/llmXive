"""
Sensitivity analysis for edge cutoff values in graph construction.

This script tests multiple cutoff distances [2.5, 3.5, 4.0, 4.5] Angstroms
to analyze how graph density and feature stability vary with the cutoff parameter.

Output:
    data/results/cutoff_sensitivity.json: Contains metrics for each cutoff tested.
"""
import json
import math
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd

from src.data.graph_construction import calculate_coordination_number, build_adjacency_matrix, extract_edge_attributes
from src.utils.config import get_project_root
from src.utils.logging import setup_logger, log_metric, log_progress

# Constants
CUTOFF_VALUES = [2.5, 3.5, 4.0, 4.5]  # Angstroms
OUTPUT_FILE = "data/results/cutoff_sensitivity.json"

logger = setup_logger("sweep_cutoff")

def load_processed_graphs() -> pd.DataFrame:
    """
    Load the processed graphs from the previous step (T016).
    Expects data/processed/graphs.parquet to exist.
    """
    root = get_project_root()
    path = root / "data" / "processed" / "graphs.parquet"
    
    if not path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {path}. "
            "Please ensure T016 (graph_construction.py) has been run successfully."
        )
    
    logger.info(f"Loading processed graphs from {path}")
    df = pd.read_parquet(path)
    return df

def parse_atomic_features(row: Any) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract atomic numbers and positions from a row in the parquet file.
    Assumes columns 'atomic_numbers' and 'positions' exist and contain list-like data.
    """
    atomic_numbers = np.array(row['atomic_numbers'])
    positions = np.array(row['positions'])
    return atomic_numbers, positions

def analyze_cutoff(
    atomic_numbers: np.ndarray,
    positions: np.ndarray,
    cutoff: float
) -> Dict[str, Any]:
    """
    Analyze graph properties for a specific cutoff value.
    
    Returns:
        Dictionary containing:
            - cutoff: float (Angstroms)
            - num_nodes: int
            - num_edges: int
            - density: float
            - avg_coordination: float
            - max_coordination: int
            - unique_edge_lengths: int (count of distinct edge lengths)
            - feature_stability_score: float (variance of edge lengths)
    """
    num_nodes = len(atomic_numbers)
    
    # Build adjacency matrix for this cutoff
    adjacency = build_adjacency_matrix(positions, cutoff)
    num_edges = int(np.sum(adjacency) // 2)  # Undirected graph
    
    if num_nodes > 1:
        max_edges = (num_nodes * (num_nodes - 1)) // 2
        density = num_edges / max_edges if max_edges > 0 else 0.0
    else:
        density = 0.0
    
    # Calculate coordination numbers
    coords = calculate_coordination_number(adjacency)
    avg_coord = float(np.mean(coords)) if len(coords) > 0 else 0.0
    max_coord = int(np.max(coords)) if len(coords) > 0 else 0
    
    # Extract edge attributes to analyze stability
    edge_indices = np.argwhere(adjacency == 1)
    edge_lengths = []
    
    if len(edge_indices) > 0:
        for i, j in edge_indices:
            if i < j:  # Avoid double counting
                dist = np.linalg.norm(positions[i] - positions[j])
                edge_lengths.append(dist)
        
        edge_lengths = np.array(edge_lengths)
        unique_lengths = len(np.unique(np.round(edge_lengths, decimals=4)))
        length_variance = float(np.var(edge_lengths)) if len(edge_lengths) > 1 else 0.0
    else:
        unique_lengths = 0
        length_variance = 0.0
    
    # Stability score: lower variance implies more stable features across the graph
    # We normalize variance by the square of the mean length to get a relative metric
    mean_length = float(np.mean(edge_lengths)) if len(edge_lengths) > 0 else 0.0
    if mean_length > 0:
        stability_score = 1.0 / (1.0 + length_variance / (mean_length ** 2))
    else:
        stability_score = 0.0
    
    return {
        "cutoff": cutoff,
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "density": density,
        "avg_coordination": avg_coord,
        "max_coordination": max_coord,
        "unique_edge_lengths": unique_lengths,
        "feature_stability_score": stability_score
    }

def run_sensitivity_analysis(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Run the sensitivity analysis across all defined cutoff values.
    """
    results = []
    total_samples = len(df)
    
    logger.info(f"Starting sensitivity analysis on {total_samples} graphs")
    
    for idx, cutoff in enumerate(CUTOFF_VALUES):
        log_progress(f"Testing cutoff {cutoff}A ({idx+1}/{len(CUTOFF_VALUES)})")
        
        sample_results = []
        
        for _, row in df.iterrows():
            try:
                atomic_numbers, positions = parse_atomic_features(row)
                if len(atomic_numbers) == 0:
                    continue
                
                metrics = analyze_cutoff(atomic_numbers, positions, cutoff)
                sample_results.append(metrics)
            except Exception as e:
                logger.warning(f"Error processing sample: {e}")
                continue
        
        if not sample_results:
            logger.warning(f"No valid samples for cutoff {cutoff}")
            continue
        
        # Aggregate metrics for this cutoff
        aggregated = {
            "cutoff": cutoff,
            "num_samples_processed": len(sample_results),
            "avg_num_nodes": float(np.mean([r["num_nodes"] for r in sample_results])),
            "avg_num_edges": float(np.mean([r["num_edges"] for r in sample_results])),
            "avg_density": float(np.mean([r["density"] for r in sample_results])),
            "avg_coordination": float(np.mean([r["avg_coordination"] for r in sample_results])),
            "max_coordination_observed": int(np.max([r["max_coordination"] for r in sample_results])),
            "avg_unique_edge_lengths": float(np.mean([r["unique_edge_lengths"] for r in sample_results])),
            "avg_feature_stability_score": float(np.mean([r["feature_stability_score"] for r in sample_results])),
            "std_density": float(np.std([r["density"] for r in sample_results])),
            "std_coordination": float(np.std([r["avg_coordination"] for r in sample_results]))
        }
        
        results.append(aggregated)
        log_metric(f"Cutoff {cutoff}A", "avg_density", aggregated["avg_density"])
        
    return results

def save_results(results: List[Dict[str, Any]]) -> Path:
    """
    Save the sensitivity analysis results to JSON.
    """
    root = get_project_root()
    output_path = root / OUTPUT_FILE
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "analysis_type": "edge_cutoff_sensitivity",
        "cutoffs_tested": CUTOFF_VALUES,
        "timestamp": str(pd.Timestamp.now()),
        "results": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return output_path

def main():
    """
    Main entry point for the sensitivity analysis.
    """
    try:
        # 1. Load data
        df = load_processed_graphs()
        
        # 2. Run analysis
        results = run_sensitivity_analysis(df)
        
        # 3. Save results
        save_results(results)
        
        logger.info("Sensitivity analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Missing data: {e}")
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
