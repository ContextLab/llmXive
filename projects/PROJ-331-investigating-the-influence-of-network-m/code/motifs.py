import os
import sys
import time
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

# Import shared utilities
from utils import get_logger, safe_read_json, safe_write_json, safe_mkdir
from config import ensure_dirs

# Configure logger
logger = get_logger(__name__)

def get_motif_id(edges: tuple) -> str:
    """
    Convert a set of edges (u, v) into a canonical motif ID string.
    For 3-node motifs, edges are expected as a tuple of tuples.
    """
    nodes = sorted(list(set([n for edge in edges for n in edge])))
    if len(nodes) != 3:
        return "invalid"
    
    # Canonical representation: sort edges by (min, max) then by tuple
    canonical_edges = []
    for u, v in edges:
        if u > v:
            u, v = v, u
        canonical_edges.append((u, v))
    
    canonical_edges.sort()
    return str(tuple(canonical_edges))

def count_motifs(adj_matrix: np.ndarray) -> Dict[str, int]:
    """
    Count all 3-node subgraphs (motifs) in a directed graph represented by adj_matrix.
    Returns a dictionary mapping motif ID (canonical edge tuple string) to count.
    """
    n = adj_matrix.shape[0]
    counts = {}
    
    # Iterate over all unique triplets of nodes
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                nodes = [i, j, k]
                # Extract subgraph edges
                edges = []
                for u in nodes:
                    for v in nodes:
                        if u != v and adj_matrix[u, v] > 0:
                            edges.append((u, v))
                
                if edges:
                    motif_id = get_motif_id(tuple(edges))
                    counts[motif_id] = counts.get(motif_id, 0) + 1
                
    return counts

def generate_null_model(adj_matrix: np.ndarray, iterations: int = 100) -> list:
    """
    Generate degree-preserving null models using Maslov-Sneppen edge rewiring.
    Returns a list of motif counts for each iteration.
    """
    n = adj_matrix.shape[0]
    null_counts_list = []
    
    # Create a copy to rewire
    current_adj = adj_matrix.copy()
    
    # Get non-zero edges
    edges = np.argwhere(current_adj > 0)
    m = len(edges)
    
    if m < 2:
        # Not enough edges to rewire
        for _ in range(iterations):
            null_counts_list.append(count_motifs(adj_matrix))
        return null_counts_list
    
    for _ in range(iterations):
        # Perform edge rewiring (Maslov-Sneppen)
        # Select two edges (a,b) and (c,d)
        idx1, idx2 = np.random.choice(m, 2, replace=False)
        a, b = edges[idx1]
        c, d = edges[idx2]
        
        # Ensure we don't create self-loops or duplicate edges
        if a != d and c != b and (a, d) not in edges and (c, b) not in edges:
            # Rewire: (a,b), (c,d) -> (a,d), (c,b)
            current_adj[a, b] = 0
            current_adj[c, d] = 0
            current_adj[a, d] = 1
            current_adj[c, b] = 1
            
            # Update edges list for next iteration
            edges[idx1] = [a, d]
            edges[idx2] = [c, b]
        
        # Count motifs for this null model
        null_counts_list.append(count_motifs(current_adj))
    
    return null_counts_list

def compute_z_scores(observed_counts: Dict[str, int], null_counts_list: list) -> Dict[str, float]:
    """
    Compute z-scores for motif prevalence: z = (observed - mean_null) / std_null
    """
    z_scores = {}
    
    # Get all unique motif IDs from observed and nulls
    all_motif_ids = set(observed_counts.keys())
    for null_counts in null_counts_list:
        all_motif_ids.update(null_counts.keys())
    
    for motif_id in all_motif_ids:
        observed = observed_counts.get(motif_id, 0)
        null_values = [nc.get(motif_id, 0) for nc in null_counts_list]
        
        mean_null = np.mean(null_values)
        std_null = np.std(null_values)
        
        if std_null == 0:
            # Avoid division by zero; if mean equals observed, z=0, else undefined (set to 0 or large)
            z = 0.0 if observed == mean_null else 1e6 * np.sign(observed - mean_null)
        else:
            z = (observed - mean_null) / std_null
        
        z_scores[motif_id] = float(z)
    
    return z_scores

def timeout_wrapper(func, timeout_seconds: int = 300):
    """
    Simple timeout wrapper using signal (Unix only). For cross-platform, 
    a thread-based approach or joblib would be needed, but we stick to 
    standard library where possible.
    """
    import signal
    
    def handler(signum, frame):
        raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds}s")
    
    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout_seconds)
    
    try:
        result = func()
        return result
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def process_motif_analysis(adj_matrix: np.ndarray, threshold: float, timeout: int = 300) -> Dict[str, float]:
    """
    Run full motif analysis for a specific threshold:
    1. Binarize adjacency based on density threshold
    2. Count motifs
    3. Generate null models
    4. Compute z-scores
    """
    logger.info(f"Processing motif analysis for threshold {threshold}")
    
    # Binarize based on density
    n = adj_matrix.shape[0]
    total_possible = n * (n - 1)
    target_edges = int(total_possible * threshold)
    
    # Flatten and sort edges to select top ones
    edges = adj_matrix.flatten()
    # Mask self-loops
    mask = ~np.eye(n, dtype=bool)
    valid_edges = edges[mask]
    
    if len(valid_edges) == 0:
        logger.warning("No valid edges found in adjacency matrix.")
        return {}
    
    # Select top edges
    threshold_val = np.sort(valid_edges)[-target_edges] if target_edges > 0 else 0
    binary_adj = (adj_matrix >= threshold_val).astype(float)
    np.fill_diagonal(binary_adj, 0)
    
    # Count observed motifs
    observed_counts = count_motifs(binary_adj)
    
    # Generate null models
    logger.info("Generating null models...")
    null_counts_list = generate_null_model(binary_adj, iterations=100)
    
    # Compute z-scores
    z_scores = compute_z_scores(observed_counts, null_counts_list)
    
    return z_scores

def aggregate_motif_profiles(raw_data: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """
    Aggregate z-scores from multiple thresholds using median.
    Input: {'threshold_10p': {motif_id: z}, 'threshold_20p': {motif_id: z}, ...}
    Output: {motif_id: median_z}
    """
    aggregated = {}
    
    # Collect all motif IDs across thresholds
    all_motif_ids = set()
    for threshold_key, scores in raw_data.items():
        all_motif_ids.update(scores.keys())
    
    for motif_id in all_motif_ids:
        z_values = []
        for threshold_key, scores in raw_data.items():
            if motif_id in scores:
                z_values.append(scores[motif_id])
        
        if z_values:
            aggregated[motif_id] = float(np.median(z_values))
        else:
            aggregated[motif_id] = 0.0
    
    return aggregated

def main():
    """
    Main entry point for T026: Aggregate motif z-scores from raw per-threshold data
    and save final profiles to motif_profiles.json.
    """
    logger.info("Starting T026: Aggregating motif profiles...")
    
    # Ensure directories exist
    ensure_dirs()
    processed_dir = Path("data/processed")
    safe_mkdir(processed_dir)
    
    # Load raw motif z-scores from T025d_raw
    raw_file = processed_dir / "motif_z_raw.json"
    if not raw_file.exists():
        logger.error(f"Raw motif data file not found: {raw_file}")
        logger.error("T025d_raw must be completed before T026.")
        sys.exit(1)
    
    logger.info(f"Loading raw motif data from {raw_file}")
    raw_data = safe_read_json(str(raw_file))
    
    if not raw_data:
        logger.error("Raw motif data is empty or invalid.")
        sys.exit(1)
    
    # Aggregate using median across thresholds
    logger.info("Aggregating z-scores using median...")
    aggregated_scores = aggregate_motif_profiles(raw_data)
    
    # Prepare output structure
    output_profile = {
        "aggregated_z_scores": aggregated_scores,
        "method": "median",
        "source_raw_file": "motif_z_raw.json",
        "description": "Aggregated motif z-scores across density thresholds (10%, 20%, 30%) using median."
    }
    
    # Save final profile
    output_file = processed_dir / "motif_profiles.json"
    logger.info(f"Saving aggregated motif profiles to {output_file}")
    safe_write_json(str(output_file), output_profile)
    
    logger.info("T026 completed successfully.")
    return output_profile

if __name__ == "__main__":
    main()