import os
import sys
import time
import json
import logging
import numpy as np
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from functools import wraps
from pathlib import Path

# Import shared utilities
from utils import get_logger, PipelineError, log_error

# Ensure logger is configured
logger = get_logger('motifs')

def get_motif_id(edges, n_nodes=3):
    """
    Convert a set of edges in a 3-node subgraph to a canonical motif ID.
    Edges should be tuples (u, v) where u < v for undirected, or (u, v) for directed.
    This function assumes undirected graphs for canonicalization (u < v).
    Returns a string ID representing the motif type.
    """
    # Canonicalize edges: sort node indices within edge, sort edges list
    canonical_edges = tuple(sorted([tuple(sorted(e)) for e in edges]))
    # Simple hash or string representation for motif ID
    return str(canonical_edges)

def count_motifs(adj_matrix):
    """
    Enumerate all 3-node subgraphs in the adjacency matrix and count motif occurrences.
    Uses networkx for subgraph enumeration.
    """
    import networkx as nx
    
    # Convert adjacency matrix to networkx graph
    G = nx.from_numpy_array(adj_matrix, create_using=nx.DiGraph)
    
    motif_counts = {}
    total_subgraphs = 0
    
    # Enumerate all 3-node induced subgraphs
    # Note: For large graphs, this can be slow. We rely on the timeout wrapper.
    for nodes in nx.enumerate_all_cliques(G):
        if len(nodes) == 3:
            total_subgraphs += 1
            subgraph = G.subgraph(nodes)
            edges = list(subgraph.edges())
            motif_id = get_motif_id(edges)
            motif_counts[motif_id] = motif_counts.get(motif_id, 0) + 1
            
    return motif_counts, total_subgraphs

def generate_null_model(adj_matrix, iterations=1000):
    """
    Generate a degree-preserving null model using Maslov-Sneppen edge rewiring.
    Returns the mean and std of motif counts over iterations.
    """
    import networkx as nx
    
    G = nx.from_numpy_array(adj_matrix, create_using=nx.DiGraph)
    original_degree_sequence = [d for n, d in G.degree()]
    
    null_motif_counts = []
    
    for i in range(iterations):
        # Create a copy to rewire
        G_null = G.copy()
        
        # Maslov-Sneppen rewiring: swap edges to preserve degree sequence
        # We attempt to rewire a fraction of edges
        edges = list(G_null.edges())
        n_edges = len(edges)
        if n_edges < 2:
            continue
            
        # Try to rewire a portion of edges
        rewires = min(n_edges // 2, 100)  # Limit rewires per iteration for speed
        for _ in range(rewires):
            if len(edges) < 2:
                break
            # Pick two random edges
            idx1, idx2 = np.random.choice(len(edges), 2, replace=False)
            u1, v1 = edges[idx1]
            u2, v2 = edges[idx2]
            
            # Proposed new edges: (u1, v2) and (u2, v1)
            # Check for self-loops and duplicate edges
            if u1 != v2 and u2 != v1:
                if not G_null.has_edge(u1, v2) and not G_null.has_edge(u2, v1):
                    # Perform swap
                    G_null.remove_edge(u1, v1)
                    G_null.remove_edge(u2, v2)
                    G_null.add_edge(u1, v2)
                    G_null.add_edge(u2, v1)
                    # Update edges list for next iteration (simplified)
                    edges = list(G_null.edges())
        
        # Count motifs in the null graph
        counts, _ = count_motifs(nx.to_numpy_array(G_null))
        null_motif_counts.append(counts)
        
    if not null_motif_counts:
        return {}, {}
        
    # Compute mean and std for each motif ID
    all_motif_ids = set()
    for counts in null_motif_counts:
        all_motif_ids.update(counts.keys())
        
    mean_counts = {m: 0.0 for m in all_motif_ids}
    std_counts = {m: 0.0 for m in all_motif_ids}
    
    for m_id in all_motif_ids:
        values = [c.get(m_id, 0) for c in null_motif_counts]
        mean_counts[m_id] = np.mean(values)
        std_counts[m_id] = np.std(values) if len(values) > 1 else 0.0
        
    return mean_counts, std_counts

def compute_motif_z_scores(observed_counts, mean_null, std_null):
    """
    Compute z-scores for motif counts: z = (observed - mean) / std
    """
    z_scores = {}
    for m_id, obs in observed_counts.items():
        mean_val = mean_null.get(m_id, 0.0)
        std_val = std_null.get(m_id, 1.0)
        if std_val == 0:
            # Avoid division by zero; if std is 0, z is 0 if obs == mean, else undefined
            # We'll set it to 0 if obs == mean, else a large value or skip
            z_scores[m_id] = 0.0 if obs == mean_val else float('inf')
        else:
            z_scores[m_id] = (obs - mean_val) / std_val
    return z_scores

def timeout_wrapper(func, timeout_seconds=300):
    """
    Wrapper to enforce a time limit on motif enumeration.
    If the function takes longer than timeout_seconds, it raises a TimeoutError
    and logs a warning.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = None
        exception_raised = None
        
        try:
            # Run the function in a thread to allow timeout enforcement
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    result = future.result(timeout=timeout_seconds)
                except FuturesTimeoutError:
                    elapsed = time.time() - start_time
                    logger.warning(f"Timeout warning: Motif enumeration exceeded {timeout_seconds}s (elapsed: {elapsed:.2f}s). Aborting gracefully.")
                    raise TimeoutError(f"Motif enumeration timed out after {timeout_seconds}s")
        except Exception as e:
            elapsed = time.time() - start_time
            log_error(logger, f"Error in motif processing after {elapsed:.2f}s", e)
            raise
        
        elapsed = time.time() - start_time
        logger.info(f"Motif enumeration completed successfully in {elapsed:.2f}s")
        return result
        
    return wrapper

def process_motif_analysis(adj_matrix_path, timeout_seconds=300):
    """
    Process a single subject's motif analysis with timeout enforcement.
    Loads the adjacency matrix, runs motif counting and null model generation,
    and returns z-scores.
    """
    import networkx as nx
    
    # Load adjacency matrix
    adj_matrix = np.load(adj_matrix_path)
    
    # Define the analysis function to be wrapped
    def run_analysis():
        # 1. Count observed motifs
        logger.info(f"Starting motif enumeration for {adj_matrix_path}")
        observed_counts, total_subgraphs = count_motifs(adj_matrix)
        logger.info(f"Found {len(observed_counts)} unique motif types out of {total_subgraphs} subgraphs")
        
        # 2. Generate null model and compute statistics
        logger.info("Generating degree-preserving null models...")
        # Use a fixed number of iterations for consistency
        mean_null, std_null = generate_null_model(adj_matrix, iterations=500)
        
        # 3. Compute z-scores
        z_scores = compute_motif_z_scores(observed_counts, mean_null, std_null)
        return z_scores, observed_counts
        
    # Wrap with timeout
    wrapped_analysis = timeout_wrapper(run_analysis, timeout_seconds=timeout_seconds)
    
    try:
        z_scores, observed_counts = wrapped_analysis()
        return z_scores, observed_counts
    except TimeoutError:
        # Re-raise to be caught by caller if needed
        raise

def aggregate_motif_profiles(z_scores_list):
    """
    Aggregate z-scores from multiple thresholds (e.g., 10%, 20%, 30%) using median.
    Input: list of dicts (one per threshold)
    Output: dict of median z-scores
    """
    if not z_scores_list:
        return {}
        
    all_motif_ids = set()
    for z_dict in z_scores_list:
        all_motif_ids.update(z_dict.keys())
        
    aggregated = {}
    for m_id in all_motif_ids:
        values = [z_dict.get(m_id, 0.0) for z_dict in z_scores_list]
        # Filter out inf values for median calculation if necessary
        finite_values = [v for v in values if np.isfinite(v)]
        if finite_values:
            aggregated[m_id] = float(np.median(finite_values))
        else:
            aggregated[m_id] = 0.0
            
    return aggregated

def main():
    """
    Main entry point for motif analysis.
    Expected to be called with input paths and timeout settings.
    """
    logger.info("Starting motif analysis pipeline")
    
    # Example: Process a specific adjacency matrix with timeout
    # In a real pipeline, this would be driven by a configuration or loop over subjects
    input_path = "data/processed/binary_adj_10p.npy" # Default example path
    if os.path.exists(input_path):
        try:
            z_scores, observed = process_motif_analysis(input_path, timeout_seconds=300)
            logger.info(f"Motif analysis completed. Unique motifs: {len(z_scores)}")
            # In a full pipeline, save results here
        except Exception as e:
            logger.error(f"Motif analysis failed for {input_path}: {e}")
    else:
        logger.warning(f"Input file not found: {input_path}. Skipping.")

if __name__ == "__main__":
    main()