import os
import json
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path
from typing import Dict, List

from config import get_data_root
from utils.logger import get_logger

logger = get_logger(__name__)

def compute_degree_centrality(matrix: np.ndarray) -> np.ndarray:
    G = nx.from_numpy_array(matrix)
    return np.array(list(nx.degree_centrality(G).values()))

def compute_clustering_coefficient(matrix: np.ndarray) -> float:
    G = nx.from_numpy_array(matrix)
    return nx.average_clustering(G)

def compute_rich_club_coefficient(matrix: np.ndarray) -> float:
    # Simplified rich-club calculation
    G = nx.from_numpy_array(matrix)
    # Use networkx rich club coefficient
    rc = nx.rich_club_coefficient(G, normalized=False)
    # Return average over degrees
    if rc:
        return np.mean(list(rc.values()))
    return 0.0

def run_metrics_pipeline(data_root: Path):
    """Runs metrics pipeline for all subjects."""
    conn_dir = data_root / "processed" / "connectomes"
    if not conn_dir.exists():
        return
    
    results = []
    for sub_dir in conn_dir.iterdir():
        if sub_dir.is_dir() and sub_dir.name.startswith("sub-"):
            conn_file = sub_dir / "connectome.npy"
            if conn_file.exists():
                matrix = np.load(conn_file)
                
                degree = compute_degree_centrality(matrix)
                clustering = compute_clustering_coefficient(matrix)
                rich_club = compute_rich_club_coefficient(matrix)
                
                results.append({
                    "subject_id": sub_dir.name,
                    "mean_degree": np.mean(degree),
                    "clustering_coefficient": clustering,
                    "rich_club_coefficient": rich_club
                })
    
    # Save results
    out_file = data_root / "processed" / "metrics.csv"
    pd.DataFrame(results).to_csv(out_file, index=False)
    logger.info(f"Saved metrics to {out_file}")

def main():
    data_root = get_data_root()
    run_metrics_pipeline(data_root)

if __name__ == "__main__":
    main()
