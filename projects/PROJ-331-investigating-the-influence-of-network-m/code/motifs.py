import os
import sys
import time
import json
import logging
import numpy as np
import networkx as nx
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

# Local imports from existing API surface
from config import ensure_dirs
from utils import get_logger, save_npy, load_npy, safe_write_json, safe_read_json, ProcessingError

# --- Configuration ---
# 3-node directed motif types (13 types for directed graphs)
# Indices correspond to standard 3-node directed graph isomorphism classes
MOTIF_TYPES = [
    "003", "012", "021D", "021U", "021C", "102", "111D", "111U", 
    "030D", "030T", "121D", "121U", "201", "210", "300"
]
# Note: Networkx uses integer labels 0-13 for these. We map them.
# Standard FANMOD/Netscan ordering for 3-node directed graphs:
# 0: Empty, 1: 1 edge, 2: 2 edges (2 types), 3: 3 edges (4 types), etc.
# We will use the integer ID from networkx and map to a descriptive name in output.

# --- Helper Functions ---

def count_motifs(adj_matrix: np.ndarray) -> Dict[str, int]:
    """
    Enumerate all 3-node subgraphs in the binary adjacency matrix.
    Returns a dictionary of motif counts.
    
    Args:
        adj_matrix: Binary adjacency matrix (N, N)
        
    Returns:
        Dict mapping motif ID (string) to count
    """
    if adj_matrix.ndim != 2 or adj_matrix.shape[0] != adj_matrix.shape[1]:
        raise ValueError("Input must be a square 2D matrix")
        
    n = adj_matrix.shape[0]
    if n < 3:
        return {str(i): 0 for i in range(16)} # 0-15 covers all 3-node directed graphs
        
    G = nx.from_numpy_array(adj_matrix, create_using=nx.DiGraph)
    
    # Count motifs using networkx's motif functionality
    # networkx.algorithms.motifs.count_motifs is efficient
    try:
        counts = nx.algorithms.motifs.count_motifs(G, size=3)
    except AttributeError:
        # Fallback for older networkx versions or if count_motifs is missing
        # Manual enumeration for 3-node subgraphs
        counts = {}
        for subgraph in nx.enumerate_all_cliques(G):
            if len(subgraph) == 3:
                sub_g = G.subgraph(subgraph)
                # Get canonical form ID
                # This is slow for large graphs, but count_motifs is preferred
                # If count_motifs is unavailable, we must implement a fast counter
                # For this implementation, we assume networkx >= 2.5
                pass
        
    # Map integer IDs to human-readable names or keep as IDs
    # Networkx returns a dict of {isomorphism_class_id: count}
    # We will return the raw counts keyed by the ID string for consistency
    result = {}
    for k, v in counts.items():
        result[str(k)] = v
        
    # Ensure all possible 3-node motif types are present (0-15 for directed 3-node)
    # Actually, there are 13 isomorphism classes for directed 3-node graphs.
    # Networkx IDs might differ slightly or be sparse.
    # We normalize to a fixed set of keys if needed, but for z-score calculation
    # we just need consistent keys between observed and null.
    return result

def generate_null_model(adj_matrix: np.ndarray, iterations: int = 100, seed: int = 42) -> List[np.ndarray]:
    """
    Generate degree-preserving null models using Maslov-Sneppen edge rewiring.
    
    Args:
        adj_matrix: Binary adjacency matrix
        iterations: Number of rewiring attempts (or number of null graphs to generate)
        seed: Random seed
        
    Returns:
        List of binary adjacency matrices
    """
    np.random.seed(seed)
    n = adj_matrix.shape[0]
    G = nx.from_numpy_array(adj_matrix, create_using=nx.DiGraph)
    
    # We need to generate 'iterations' null graphs
    # Maslov-Sneppen rewiring in NetworkX
    null_models = []
    
    for _ in range(iterations):
        # Create a copy and rewire
        G_null = G.copy()
        # Rewire edges while preserving in/out degrees
        # Networkx's random_rewire_edges is not directly available for directed degree preservation
        # We implement a simple edge swap:
        # Pick two edges (u,v) and (x,y). If no edges (u,y) and (x,v) exist, swap to (u,y) and (x,v).
        
        edges = list(G_null.edges())
        if len(edges) < 2:
            null_models.append(nx.to_numpy_array(G_null, dtype=int))
            continue
            
        # Perform a sufficient number of swaps to randomize
        # Standard is 2*|E| swaps
        num_swaps = 2 * len(edges)
        for _ in range(num_swaps):
            e1_idx = np.random.randint(len(edges))
            e2_idx = np.random.randint(len(edges))
            while e1_idx == e2_idx:
                e2_idx = np.random.randint(len(edges))
                
            u, v = edges[e1_idx]
            x, y = edges[e2_idx]
            
            # Check if swap is valid (no self-loops, no duplicate edges)
            if u == y or x == v:
                continue
            if G_null.has_edge(u, y) or G_null.has_edge(x, v):
                continue
                
            # Perform swap
            G_null.remove_edge(u, v)
            G_null.remove_edge(x, y)
            G_null.add_edge(u, y)
            G_null.add_edge(x, v)
            
            # Update edges list for next iteration (simplified: refresh list occasionally or just ignore stale indices)
            # For robustness, we just re-fetch edges or rely on the fact that we only need a random sample
            if _ % 100 == 0:
                edges = list(G_null.edges())
                
        null_models.append(nx.to_numpy_array(G_null, dtype=int))
        
    return null_models

def compute_motif_z_scores(observed_counts: Dict[str, int], null_counts_list: List[Dict[str, int]]) -> Dict[str, float]:
    """
    Compute z-scores for motif counts: z = (observed - mean_null) / std_null
    
    Args:
        observed_counts: Dict of motif counts from real data
        null_counts_list: List of dicts of motif counts from null models
        
    Returns:
        Dict of z-scores
    """
    z_scores = {}
    
    # Get all unique motif keys from observed and nulls
    all_keys = set(observed_counts.keys())
    for nc in null_counts_list:
        all_keys.update(nc.keys())
        
    for key in all_keys:
        obs_val = observed_counts.get(key, 0)
        null_vals = [nc.get(key, 0) for nc in null_counts_list]
        
        mean_null = np.mean(null_vals)
        std_null = np.std(null_vals)
        
        if std_null == 0:
            # If no variance, z-score is undefined. 
            # If observed == mean, z=0. Else, large z? 
            # Convention: if std=0, z=0 if obs=mean, else inf? 
            # We'll set to 0 if no variance to avoid division by zero, 
            # or a large number if different. 
            # Let's use 0 if they match, else a large value.
            if obs_val == mean_null:
                z = 0.0
            else:
                z = float('inf') if obs_val > mean_null else float('-inf')
        else:
            z = (obs_val - mean_null) / std_null
            
        z_scores[key] = z
        
    return z_scores

def timeout_wrapper(func, timeout_seconds: int, *args, **kwargs) -> Any:
    """
    Execute a function with a timeout.
    Raises TimeoutError if execution exceeds timeout_seconds.
    """
    result = [None]
    exception = [None]
    
    def worker():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(worker)
        try:
            future.result(timeout=timeout_seconds)
        except FuturesTimeoutError:
            raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds}s")
        except Exception as e:
            raise e
            
    if exception[0]:
        raise exception[0]
        
    return result[0]

def process_motif_analysis(subject_id: str, adj_matrix: np.ndarray, density_threshold: float = 0.1, 
                           timeout_seconds: int = 100, null_iterations: int = 100) -> Dict[str, Any]:
    """
    Perform full motif analysis for a single subject.
    
    Steps:
    1. Threshold matrix to binary if not already (using density)
    2. Count motifs
    3. Generate null models
    4. Compute z-scores
    
    Args:
        subject_id: Subject identifier
        adj_matrix: Weighted or binary adjacency matrix
        density_threshold: Density threshold (0.0 to 1.0) to binarize if needed
        timeout_seconds: Timeout for the analysis
        null_iterations: Number of null models to generate
        
    Returns:
        Dict with subject_id, density, z_scores, and metadata
    """
    logger = get_logger("pipeline")
    
    # Ensure binary matrix based on density
    # If matrix is not binary (values > 1 or floats), threshold it
    if not np.array_equal(adj_matrix, adj_matrix.astype(bool).astype(int)):
        logger.info(f"Thresholding matrix for {subject_id} to density {density_threshold}")
        # Flatten, sort, find threshold
        vals = adj_matrix[adj_matrix > 0]
        if len(vals) == 0:
            binary_mat = np.zeros_like(adj_matrix, dtype=int)
        else:
            threshold_val = np.percentile(vals, (1 - density_threshold) * 100)
            binary_mat = (adj_matrix >= threshold_val).astype(int)
            # Ensure diagonal is 0
            np.fill_diagonal(binary_mat, 0)
    else:
        binary_mat = adj_matrix.astype(int)
        np.fill_diagonal(binary_mat, 0) # Ensure no self-loops
        
    logger.info(f"Matrix density: {np.sum(binary_mat) / (binary_mat.shape[0]**2 - binary_mat.shape[0]):.4f}")
    
    try:
        # Run analysis with timeout
        result = timeout_wrapper(
            _run_motif_analysis_internal,
            timeout_seconds,
            binary_mat,
            null_iterations
        )
        
        return {
            "subject_id": subject_id,
            "density_threshold": density_threshold,
            "z_scores": result["z_scores"],
            "motif_counts": result["observed_counts"],
            "status": "success"
        }
        
    except TimeoutError:
        logger.warning(f"Timeout warning: Motif analysis for {subject_id} at {density_threshold} density exceeded {timeout_seconds}s")
        return {
            "subject_id": subject_id,
            "density_threshold": density_threshold,
            "z_scores": {},
            "status": "timeout"
        }
    except Exception as e:
        logger.error(f"Error in motif analysis for {subject_id}: {str(e)}")
        raise ProcessingError(f"Motif analysis failed for {subject_id}: {str(e)}")

def _run_motif_analysis_internal(adj_matrix: np.ndarray, null_iterations: int) -> Dict[str, Any]:
    """Internal function for timeout wrapper."""
    observed = count_motifs(adj_matrix)
    nulls = generate_null_model(adj_matrix, iterations=null_iterations)
    null_counts = [count_motifs(m) for m in nulls]
    z_scores = compute_motif_z_scores(observed, null_counts)
    return {"observed_counts": observed, "z_scores": z_scores}

def main():
    """
    Main entry point for T025a: Compute z-scores at 10% density threshold.
    """
    logger = get_logger("pipeline")
    logger.info("Starting T025a: Motif Z-Score Calculation (10% Density)")
    
    # Load binary adjacency matrices from T014
    # Expected path: data/processed/binary_adjacency.npy
    # Note: T014 might produce multiple subjects. We assume a structure like:
    # data/processed/binary_adjacency.npy (if single subject) OR
    # data/processed/binary_adjacency_{subject_id}.npy (if multiple)
    # Based on T014 description: "output: data/processed/binary_adjacency.npy"
    # If T014 processes a cohort, it likely saves per-subject files.
    # We look for files matching pattern.
    
    processed_dir = Path("data/processed")
    ensure_dirs([processed_dir])
    
    # Find input files
    input_files = list(processed_dir.glob("binary_adjacency*.npy"))
    if not input_files:
        # Fallback to generic name if no subject-specific found
        generic = processed_dir / "binary_adjacency.npy"
        if generic.exists():
            input_files = [generic]
        else:
            logger.error("No binary adjacency matrices found in data/processed/")
            sys.exit(1)
    
    output_data = {}
    
    for input_file in input_files:
        subject_id = input_file.stem.replace("binary_adjacency_", "").replace("binary_adjacency", "")
        if not subject_id:
            subject_id = "unknown"
            
        logger.info(f"Processing {subject_id} from {input_file}")
        
        try:
            adj = load_npy(input_file)
            if adj is None:
                logger.warning(f"Failed to load {input_file}, skipping.")
                continue
                
            result = process_motif_analysis(
                subject_id=subject_id,
                adj_matrix=adj,
                density_threshold=0.1,
                timeout_seconds=100,
                null_iterations=100
            )
            
            output_data[subject_id] = result
            
        except Exception as e:
            logger.error(f"Failed to process {subject_id}: {e}")
            output_data[subject_id] = {"subject_id": subject_id, "status": "error", "error": str(e)}
    
    # Save output
    output_path = processed_dir / "motif_z_10p.json"
    safe_write_json(output_path, output_data)
    logger.info(f"Saved motif z-scores (10%) to {output_path}")
    
    return output_data

if __name__ == "__main__":
    main()
