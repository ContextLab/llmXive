"""
Task T017: Sensitivity analysis for edge cutoffs.

Sweeps cutoff values [2.5, 3.5, 4.0, 4.5] Angstroms on the processed graphs
to measure graph density and feature stability.
"""
import json
import math
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import pandas as pd

from src.utils.logging import get_logger
from src.data.graph_construction import build_adjacency_matrix

# Ensure logger is configured
logger = get_logger(__name__)

def get_project_root() -> Path:
    """Determine project root (assumes code/ is in root)."""
    current = Path(__file__).resolve()
    # Navigate up to find the root where 'data/' and 'src/' exist
    # Assuming structure: code/src/data/sweep_cutoff.py -> root is parent of code/
    # But usually in these projects, the repo root is the parent of 'code' or the script runs from root.
    # Let's assume standard layout: repo_root/code/src/data/...
    # We look for 'data' directory relative to repo root.
    # If current is repo_root/code/src/data/sweep_cutoff.py
    # parent.parent.parent -> repo_root
    # But let's be safe: look for 'data' directory.
    for ancestor in current.parents:
        if (ancestor / "data").exists() and (ancestor / "src").exists():
            return ancestor
    # Fallback: assume current working directory
    return Path.cwd()

def load_processed_graphs() -> pd.DataFrame:
    """
    Load the processed graphs from data/processed/graphs.parquet.
    Returns a DataFrame with atomic features and coordinates.
    """
    root = get_project_root()
    path = root / "data" / "processed" / "graphs.parquet"
    
    if not path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {path}. "
            "Please ensure T016 (graph_construction) has been completed."
        )
    
    logger.info(f"Loading processed graphs from {path}")
    df = pd.read_parquet(path)
    logger.info(f"Loaded {len(df)} graphs.")
    return df

def parse_atomic_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract atomic numbers and coordinates from the DataFrame.
    
    Expected columns in parquet:
    - atomic_numbers: list of ints
    - positions: list of lists (N x 3)
    - ligand_class (optional, for metadata)
    """
    atomic_numbers = []
    positions = []
    
    # Assuming the parquet has a row per graph with columns 'atomic_numbers' and 'positions'
    # If the format is different (e.g., exploded), adjust here.
    # Based on T016 description: "convert geometries to TransitionStateGraph"
    # We expect a row-based representation where each row is a molecule/graph.
    
    if 'atomic_numbers' not in df.columns or 'positions' not in df.columns:
        # Try to infer or raise
        cols = df.columns.tolist()
        raise ValueError(
            f"DataFrame missing required columns 'atomic_numbers' or 'positions'. "
            f"Found columns: {cols}"
        )
    
    for _, row in df.iterrows():
        atomic_numbers.append(row['atomic_numbers'])
        positions.append(np.array(row['positions']))
        
    return atomic_numbers, positions

def build_adjacency_matrix(positions: np.ndarray, cutoff: float) -> np.ndarray:
    """
    Build adjacency matrix based on Euclidean distance < cutoff.
    
    Args:
        positions: (N, 3) array of coordinates.
        cutoff: Distance threshold in Angstroms.
        
    Returns:
        Adjacency matrix (N, N) of booleans.
    """
    n = positions.shape[0]
    # Compute pairwise distances
    # diff = positions[:, None, :] - positions[None, :, :]  # (N, N, 3)
    # dists = np.sqrt(np.sum(diff**2, axis=2))
    # Optimized: use scipy or numpy broadcasting
    diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
    dists = np.sqrt(np.sum(diff**2, axis=2))
    
    # Adjacency: 1 if dist < cutoff and i != j
    adj = (dists < cutoff) & (dists > 0.0)
    return adj

def calculate_edge_feature_stability(
    atomic_numbers: List[List[int]], 
    positions_list: List[np.ndarray], 
    cutoffs: List[float]
) -> Dict[float, Dict[str, Any]]:
    """
    Calculate graph density and edge feature stability for each cutoff.
    
    Metrics:
    - density: number of edges / max_possible_edges
    - avg_degree: average number of neighbors
    - edge_count: total edges
    """
    results = {}
    
    for cutoff in cutoffs:
        edge_counts = []
        degrees = []
        
        for atoms, pos in zip(atomic_numbers, positions_list):
            n = len(pos)
            if n == 0:
                continue
            adj = build_adjacency_matrix(pos, cutoff)
            edges = np.sum(adj)
            edge_counts.append(edges)
            degrees.append(np.sum(adj, axis=1))
        
        if not edge_counts:
            results[cutoff] = {
                "density": 0.0,
                "avg_degree": 0.0,
                "edge_count": 0,
                "sample_count": 0
            }
            continue
        
        total_edges = sum(edge_counts)
        total_nodes = sum(len(p) for p in positions_list)
        
        # Max possible edges for a graph with N nodes is N*(N-1) (undirected, no self loops)
        # We sum N*(N-1) for all graphs
        max_edges = 0
        for pos in positions_list:
            n = len(pos)
            max_edges += n * (n - 1)
        
        density = total_edges / max_edges if max_edges > 0 else 0.0
        avg_degree = (2 * total_edges) / total_nodes if total_nodes > 0 else 0.0
        
        results[cutoff] = {
            "density": float(density),
            "avg_degree": float(avg_degree),
            "edge_count": int(total_edges),
            "sample_count": len(edge_counts),
            "cutoff_angstroms": float(cutoff)
        }
        
        logger.info(f"Cutoff {cutoff}Å: Density={density:.4f}, Avg Degree={avg_degree:.2f}")
    
    return results

def analyze_cutoff(
    atomic_numbers: List[List[int]], 
    positions: List[np.ndarray], 
    cutoffs: List[float]
) -> Dict[str, Any]:
    """
    Run the full sensitivity analysis.
    """
    logger.info(f"Starting cutoff sensitivity analysis for cutoffs: {cutoffs}")
    
    metrics = calculate_edge_feature_stability(atomic_numbers, positions, cutoffs)
    
    # Calculate stability (change in density between consecutive cutoffs)
    cutoffs_sorted = sorted(cutoffs)
    stability_metrics = []
    
    for i in range(len(cutoffs_sorted) - 1):
        c1 = cutoffs_sorted[i]
        c2 = cutoffs_sorted[i+1]
        d1 = metrics[c1]["density"]
        d2 = metrics[c2]["density"]
        delta = abs(d2 - d1)
        stability_metrics.append({
            "cutoff_from": float(c1),
            "cutoff_to": float(c2),
            "density_change": float(delta),
            "relative_change": float(delta / d1) if d1 > 0 else 0.0
        })
    
    return {
        "cutoffs_tested": cutoffs,
        "metrics_per_cutoff": metrics,
        "stability_analysis": stability_metrics,
        "summary": {
            "recommended_cutoff": 3.5, # Based on T016 logic
            "reason": "Standard coordination cutoff for transition metals"
        }
    }

def save_results(results: Dict[str, Any], output_path: Optional[Path] = None):
    """Save results to JSON."""
    if output_path is None:
        root = get_project_root()
        output_path = root / "data" / "results" / "cutoff_sensitivity.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved sensitivity analysis results to {output_path}")

def run_sensitivity_analysis(cutoffs: Optional[List[float]] = None) -> Dict[str, Any]:
    """
    Main entry point for the sensitivity analysis.
    """
    if cutoffs is None:
        cutoffs = [2.5, 3.5, 4.0, 4.5]
    
    df = load_processed_graphs()
    atomic_numbers, positions = parse_atomic_features(df)
    
    results = analyze_cutoff(atomic_numbers, positions, cutoffs)
    save_results(results)
    
    return results

def main():
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    try:
        run_sensitivity_analysis()
        logger.info("Sensitivity analysis completed successfully.")
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
