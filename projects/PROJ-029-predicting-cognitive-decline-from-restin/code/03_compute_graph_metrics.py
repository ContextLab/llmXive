"""
Compute graph metrics from connectivity matrices using parallel processing.
Calculates node degree, global efficiency, clustering coefficient, and path length.
Uses joblib.Parallel(n_jobs=2) to reduce runtime while respecting the 7GB RAM limit.
"""
import os
import sys
import time
import psutil
from pathlib import Path
import pandas as pd
import numpy as np
import networkx as nx
from joblib import Parallel, delayed

# Ensure reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# Constants
MEMORY_LIMIT_GB = 7.0
N_JOBS = 2

def get_memory_usage_gb():
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

def check_memory_limit():
    """Check if current memory usage is within limit. Returns True if OK."""
    current = get_memory_usage_gb()
    if current > MEMORY_LIMIT_GB:
        raise MemoryError(f"Memory usage {current:.2f}GB exceeds limit {MEMORY_LIMIT_GB}GB")
    return True

def process_subject_matrix(matrix_path, subject_id):
    """
    Load a single adjacency matrix and compute graph metrics.
    Returns a dictionary of metrics.
    Processes one subject at a time to stay within memory limits.
    This function is designed to be called by joblib.Parallel.
    """
    try:
        # Check memory before processing
        check_memory_limit()

        # Load matrix
        matrix = np.load(matrix_path)
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError(f"Non-square matrix for {subject_id}: {matrix.shape}")

        # Create graph
        G = nx.Graph()
        # Add edges only for non-zero values (thresholding could be added here)
        threshold = 0.0
        indices = np.where(matrix > threshold)
        for i, j in zip(indices[0], indices[1]):
            if i != j:  # No self-loops
                G.add_edge(i, j, weight=matrix[i, j])

        if G.number_of_nodes() == 0:
            return {
                "subject_id": subject_id,
                "degree": np.nan,
                "global_efficiency": np.nan,
                "clustering_coefficient": np.nan,
                "avg_path_length": np.nan
            }

        # Compute metrics
        degree = np.mean([d for n, d in G.degree()])
        
        try:
            global_eff = nx.global_efficiency(G)
        except nx.NetworkXError:
            global_eff = np.nan

        try:
            clustering = nx.average_clustering(G)
        except nx.NetworkXError:
            clustering = np.nan

        try:
            # Average shortest path length (only for connected components)
            if nx.is_connected(G):
                avg_path = nx.average_shortest_path_length(G)
            else:
                # Compute for largest connected component
                largest_cc = max(nx.connected_components(G), key=len)
                subgraph = G.subgraph(largest_cc)
                avg_path = nx.average_shortest_path_length(subgraph)
        except nx.NetworkXError:
            avg_path = np.nan

        # Check memory again after processing
        check_memory_limit()

        return {
            "subject_id": subject_id,
            "degree": degree,
            "global_efficiency": global_eff,
            "clustering_coefficient": clustering,
            "avg_path_length": avg_path
        }

    except MemoryError as e:
        print(f"CRITICAL: {e} for {subject_id}", file=sys.stderr)
        # Re-raise to stop execution if limit exceeded
        raise
    except Exception as e:
        print(f"Error processing {subject_id}: {e}", file=sys.stderr)
        return {
            "subject_id": subject_id,
            "degree": np.nan,
            "global_efficiency": np.nan,
            "clustering_coefficient": np.nan,
            "avg_path_length": np.nan
        }

def main():
    """Main entry point for graph metrics computation with parallel processing."""
    # Paths
    project_root = Path(__file__).resolve().parent.parent
    input_dir = project_root / "data" / "processed" / "adjacency_matrices"
    output_path = project_root / "data" / "processed" / "graph_metrics.csv"

    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist.", file=sys.stderr)
        print("Please run code/02_preprocess_and_parcellate.py first to generate adjacency matrices.", file=sys.stderr)
        sys.exit(1)

    # Get list of matrix files
    matrix_files = sorted(input_dir.glob("*.npz"))
    if not matrix_files:
        print(f"Error: No matrix files found in {input_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(matrix_files)} matrix files to process.")
    print(f"Processing with joblib.Parallel(n_jobs={N_JOBS}) to reduce runtime.")
    print(f"Memory limit: {MEMORY_LIMIT_GB}GB per worker.")

    # Prepare tasks
    tasks = []
    for matrix_file in matrix_files:
        subject_id = matrix_file.stem.replace("_matrix", "").replace("subj_", "")
        tasks.append((str(matrix_file), subject_id))

    start_time = time.time()
    
    # Execute in parallel
    try:
        results = Parallel(n_jobs=N_JOBS, verbose=10)(
            delayed(process_subject_matrix)(matrix_path, subject_id) 
            for matrix_path, subject_id in tasks
        )
    except MemoryError:
        print(f"Stopping due to memory limit exceeded.", file=sys.stderr)
        sys.exit(1)

    elapsed = time.time() - start_time

    # Save results
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    print(f"Saved graph metrics to {output_path}")

    print(f"Total time: {elapsed:.2f}s")
    print(f"Final memory usage: {get_memory_usage_gb():.2f}GB")

    # Log performance for T035 verification
    log_path = project_root / "data" / "artifacts" / "performance_log.json"
    import json
    log_entry = {
        "task": "T035",
        "script": "03_compute_graph_metrics.py",
        "subjects_processed": len(matrix_files),
        "parallel_workers": N_JOBS,
        "total_runtime_seconds": elapsed,
        "target_runtime_minutes": 30,
        "passed_target": elapsed < (30 * 60)
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    print(f"Performance log written to {log_path}")

if __name__ == "__main__":
    main()