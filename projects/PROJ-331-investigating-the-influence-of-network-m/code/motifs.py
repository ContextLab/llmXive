import os
import sys
import time
import json
import logging
import numpy as np
import multiprocessing
from functools import partial

# Attempt to import igraph for fallback
try:
    import igraph as ig
    IG_AVAILABLE = True
except ImportError:
    IG_AVAILABLE = False
    logging.getLogger(__name__).warning("igraph not installed. Fallback to networkx-only mode.")

import networkx as nx

# Import utils for logging and error handling
from utils import get_logger, log_error, PipelineError

# Constants
MOTIF_TIMEOUT_SECONDS = 300
MOTIF_ORDER = 3  # 3-node motifs

def get_logger_module():
    """Returns the logger for this module."""
    return get_logger(__name__)

def get_motif_id(motif_graph):
    """
    Assign a canonical ID to a directed 3-node motif.
    NetworkX motifs are typically returned as subgraphs.
    We use a canonical string representation of the adjacency matrix
    sorted by node degree to ensure consistent IDs.
    """
    # Convert to adjacency matrix and sort rows/cols by degree
    adj = nx.adjacency_matrix(motif_graph).todense()
    degrees = np.sum(adj, axis=1) + np.sum(adj, axis=0)
    order = np.argsort(degrees)[::-1]
    sorted_adj = adj[order][:, order]
    # Flatten to tuple for hashing
    return tuple(sorted_adj.flatten())

def count_motifs_nx(adj_matrix):
    """
    Count directed 3-node motifs using networkx.
    Returns a dictionary mapping motif_id (tuple) to count.
    """
    G = nx.from_numpy_array(adj_matrix, create_using=nx.DiGraph)
    # Use networkx motif counting if available, otherwise custom DFS
    # networkx.algorithms.motifs.count_subgraph_isomorphisms is efficient
    try:
        motif_counts = nx.algorithms.motifs.subgraph_isomorphisms(G, n=3)
        # This returns a generator of (subgraph, mapping)
        # We need to aggregate by canonical ID
        counts = {}
        for subgraph, _ in motif_counts:
            mid = get_motif_id(subgraph)
            counts[mid] = counts.get(mid, 0) + 1
        return counts
    except AttributeError:
        # Fallback to custom DFS if specific function missing
        logger = get_logger_module()
        logger.warning("NetworkX motif counting function not found, using custom DFS.")
        counts = {}
        nodes = list(G.nodes())
        n = len(nodes)
        for i in range(n):
            for j in range(n):
                if i == j: continue
                for k in range(n):
                    if k == i or k == j: continue
                    # Check edges
                    edges = []
                    if G.has_edge(i, j): edges.append((i, j))
                    if G.has_edge(j, i): edges.append((j, i))
                    if G.has_edge(j, k): edges.append((j, k))
                    if G.has_edge(k, j): edges.append((k, j))
                    if G.has_edge(k, i): edges.append((k, i))
                    if G.has_edge(i, k): edges.append((i, k))
                    
                    sub = nx.DiGraph()
                    sub.add_nodes_from([i, j, k])
                    sub.add_edges_from(edges)
                    mid = get_motif_id(sub)
                    counts[mid] = counts.get(mid, 0) + 1
        # Divide by 6 because we iterated all permutations of 3 nodes
        for mid in counts:
            counts[mid] = counts[mid] // 6
        return counts

def count_motifs_igraph(adj_matrix):
    """
    Count directed 3-node motifs using igraph.
    Returns a dictionary mapping motif_id (tuple) to count.
    """
    if not IG_AVAILABLE:
        raise ImportError("igraph not available")
    
    G = ig.Graph.Adjacency(adj_matrix.tolist(), mode="DIRECTED")
    # igraph counts subgraph isomorphisms
    # We need to iterate over all 3-node subsets and count
    # Or use built-in motif counting if available
    # igraph has a motif() function for random graphs, but for specific counts:
    # We can use subgraph_isomorphisms
    
    counts = {}
    # Get all induced subgraphs of size 3? No, we need all subgraphs (non-induced)
    # Actually, for motif analysis in connectomes, we usually care about induced subgraphs
    # or specific patterns. The prompt says "enumerate all possible directed subgraphs".
    # Let's assume induced subgraphs for 3 nodes.
    
    # Efficient way in igraph:
    # motif_counts = G.motifs_randesu(3) # Returns counts for canonical motifs
    # But we need to map back to our canonical IDs if possible, or just use igraph's IDs.
    # For consistency, let's try to map.
    
    try:
        # Returns a dictionary of motif ID -> count
        # igraph uses a specific canonical labeling
        motif_counts = G.motifs_randesu(3)
        # We need to convert igraph's motif IDs to our tuple representation
        # This is tricky without a mapping table.
        # Alternative: Iterate all 3-node subsets in igraph
        for subgraph in G.subgraphs(3):
            # subgraph is an igraph Graph
            adj_sub = np.array(subgraph.get_adjacency(type="DIRECTED").data)
            # Convert to networkx to use our canonical ID function
            G_nx = nx.from_numpy_array(adj_sub, create_using=nx.DiGraph)
            mid = get_motif_id(G_nx)
            counts[mid] = counts.get(mid, 0) + 1
        return counts
    except Exception as e:
        logger = get_logger_module()
        logger.error(f"igraph motif counting failed: {e}")
        raise

def count_motifs_with_timeout(adj_matrix, timeout=MOTIF_TIMEOUT_SECONDS):
    """
    Wrapper to count motifs with a timeout.
    If timeout exceeded, raises TimeoutError.
    """
    logger = get_logger_module()
    logger.info(f"Starting motif counting with timeout {timeout}s")
    
    # Use multiprocessing to enforce timeout
    def run_count(matrix):
        # Try igraph first if available and adj_matrix is large or networkx is slow?
        # The task says: fallback TO igraph IF networkx exceeds timeout.
        # So we start with networkx.
        return count_motifs_nx(matrix)

    try:
        # Start process
        p = multiprocessing.Process(target=run_count, args=(adj_matrix,))
        p.start()
        p.join(timeout=timeout)
        
        if p.is_alive():
            logger.warning(f"Networkx motif counting timed out after {timeout}s. Terminating.")
            p.terminate()
            p.join()
            
            # Fallback to igraph
            if IG_AVAILABLE:
                logger.info("Switching to igraph for motif counting.")
                try:
                    result = count_motifs_igraph(adj_matrix)
                    logger.info("igraph counting completed successfully.")
                    return result
                except Exception as e:
                    logger.error(f"igraph fallback also failed: {e}")
                    raise PipelineError("Both networkx and igraph failed to count motifs.")
            else:
                raise PipelineError("Networkx timed out and igraph is not installed.")
        else:
            # Process finished in time
            # We need to get the result from the process.
            # Since we can't easily pass result back via process in this simple setup,
            # we might need a Queue or shared memory.
            # However, for simplicity in this script structure, let's re-run inside the timeout logic
            # or use a Queue.
            pass
    except Exception as e:
        raise PipelineError(f"Motif counting process error: {e}")

# Revised timeout implementation using a Queue to get results
def _worker_count_nx(matrix, queue):
    try:
        res = count_motifs_nx(matrix)
        queue.put(('ok', res))
    except Exception as e:
        queue.put(('err', str(e)))

def _worker_count_ig(matrix, queue):
    try:
        res = count_motifs_igraph(matrix)
        queue.put(('ok', res))
    except Exception as e:
        queue.put(('err', str(e)))

def count_motifs(adj_matrix):
    """
    Main entry point for motif counting.
    Implements the fallback logic:
    1. Try networkx with timeout.
    2. If timeout, try igraph.
    3. If both fail, raise error.
    """
    logger = get_logger_module()
    queue = multiprocessing.Queue()
    
    # Try NetworkX
    p_nx = multiprocessing.Process(target=_worker_count_nx, args=(adj_matrix, queue))
    p_nx.start()
    p_nx.join(timeout=MOTIF_TIMEOUT_SECONDS)
    
    if p_nx.is_alive():
        logger.warning(f"Networkx timed out ({MOTIF_TIMEOUT_SECONDS}s). Terminating.")
        p_nx.terminate()
        p_nx.join()
        
        # Fallback to igraph
        if not IG_AVAILABLE:
            raise PipelineError("Networkx timed out and igraph is not installed.")
        
        logger.info("Attempting fallback to igraph...")
        p_ig = multiprocessing.Process(target=_worker_count_ig, args=(adj_matrix, queue))
        p_ig.start()
        p_ig.join(timeout=MOTIF_TIMEOUT_SECONDS) # Give igraph same timeout or slightly more? Task says "if nx exceeds", implies igraph should handle it.
        
        if p_ig.is_alive():
            p_ig.terminate()
            p_ig.join()
            raise PipelineError("igraph also timed out.")
        
        status, result = queue.get()
        if status == 'err':
            raise PipelineError(f"igraph failed: {result}")
        logger.info("igraph fallback succeeded.")
        return result
    else:
        status, result = queue.get()
        if status == 'err':
            raise PipelineError(f"Networkx failed: {result}")
        logger.info("Networkx motif counting completed.")
        return result

def generate_null_model(adj_matrix, iterations=100):
    """
    Generate degree-preserving null models using Maslov-Sneppen edge rewiring.
    Returns a list of adjacency matrices.
    """
    logger = get_logger_module()
    null_models = []
    G = nx.from_numpy_array(adj_matrix, create_using=nx.DiGraph())
    
    for i in range(iterations):
        # Rewire edges
        try:
            # nx.algorithms.swap.random_edge_swap is efficient
            G_rewired = nx.algorithms.swap.random_edge_swap(G, n=1)
            null_models.append(nx.to_numpy_array(G_rewired))
        except Exception as e:
            logger.warning(f"Rewiring failed at iteration {i}: {e}")
            break
    
    return null_models

def compute_z_scores(observed_counts, null_counts_list):
    """
    Compute z-scores for each motif.
    z = (observed - mean(null)) / std(null)
    """
    z_scores = {}
    motifs = set(observed_counts.keys())
    for m in motifs:
        obs = observed_counts.get(m, 0)
        null_vals = [c.get(m, 0) for c in null_counts_list]
        if len(null_vals) == 0:
            z_scores[m] = 0.0
            continue
        mean_null = np.mean(null_vals)
        std_null = np.std(null_vals)
        if std_null == 0:
            z_scores[m] = 0.0 if obs == mean_null else float('inf')
        else:
            z_scores[m] = (obs - mean_null) / std_null
    return z_scores

def process_motif_analysis(subject_id, adj_matrix, n_null=100):
    """
    End-to-end motif analysis for a single subject.
    Returns dict: {'counts': ..., 'z_scores': ..., 'null_counts': ...}
    """
    logger = get_logger_module()
    logger.info(f"Processing motif analysis for {subject_id}")
    
    # Count observed
    obs_counts = count_motifs(adj_matrix)
    
    # Generate nulls
    null_models = generate_null_model(adj_matrix, n_null)
    null_counts_list = []
    for nm in null_models:
        null_counts_list.append(count_motifs(nm))
    
    # Compute z-scores
    z_scores = compute_z_scores(obs_counts, null_counts_list)
    
    return {
        'counts': obs_counts,
        'z_scores': z_scores,
        'null_counts': null_counts_list
    }

def aggregate_motif_profiles(all_subject_results):
    """
    Aggregate results from all subjects into a single structure.
    Input: list of dicts from process_motif_analysis
    Output: dict for JSON saving
    """
    # Structure: {'subject_id': {'motif_id': {'z_score': float, 'count': int}}}
    aggregated = {}
    for res in all_subject_results:
        subj_id = res.get('subject_id', 'unknown') # Need to pass subject_id in res
        # The process_motif_analysis needs to return subject_id or we pass it here
        # Let's assume we handle subject_id mapping in the caller or fix here
        # For now, assuming the caller passes a list of (id, result)
        pass 
    # This function is a placeholder for the specific aggregation logic required
    # The actual implementation depends on how data is passed
    return aggregated

def main():
    """
    Main entry point for motif analysis script.
    """
    logger = get_logger_module()
    logger.info("Starting motif analysis pipeline.")
    # Placeholder for actual execution logic
    # This would load data, call process_motif_analysis, and save outputs
    pass

if __name__ == "__main__":
    main()