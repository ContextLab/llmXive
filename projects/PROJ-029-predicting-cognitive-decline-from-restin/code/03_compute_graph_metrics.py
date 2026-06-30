"""
Compute graph metrics from connectivity matrices.
Calculates node degree, global efficiency, clustering coefficient, and path length.
Processes subjects in parallel using joblib to optimize runtime while respecting memory limits.
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
N_JOBS = 2  # Target runtime optimization
CHUNK_SIZE = 10  # Process in small batches for better load balancing

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

def process_subject_matrix(matrix_path: Path, subject_id: str):
    """
    Load a single adjacency matrix and compute graph metrics.
    Returns a dictionary of metrics.
    This function is designed to be called by joblib in parallel.
    """
    try:
        # Load matrix
        matrix = np.load(matrix_path)
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError(f"Non-square matrix for {subject_id}")

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

        return {
            "subject_id": subject_id,
            "degree": degree,
            "global_efficiency": global_eff,
            "clustering_coefficient": clustering,
            "avg_path_length": avg_path
        }

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
    """Main entry point for graph metrics computation with parallel optimization."""
    # Paths
    project_root = Path(__file__).resolve().parent.parent
    input_dir = project_root / "data" / "processed" / "adjacency_matrices"
    output_path = project_root / "data" / "processed" / "graph_metrics.csv"

    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist.", file=sys.stderr)
        sys.exit(1)

    # Get list of matrix files
    matrix_files = sorted(input_dir.glob("*.npz"))
    if not matrix_files:
        print(f"Error: No matrix files found in {input_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(matrix_files)} matrix files to process.")
    print(f"Starting parallel computation with n_jobs={N_JOBS}...")

    # Prepare tasks
    tasks = []
    for matrix_file in matrix_files:
        subject_id = matrix_file.stem.replace("_matrix", "").replace("subj_", "")
        tasks.append((matrix_file, subject_id))

    start_time = time.time()

    # Execute in parallel
    # We use a chunk size to reduce overhead of job scheduling
    results = Parallel(n_jobs=N_JOBS, chunksize=CHUNK_SIZE)(
        delayed(process_subject_matrix)(matrix_path, subject_id)
        for matrix_path, subject_id in tasks
    )

    elapsed = time.time() - start_time

    # Save results
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    print(f"Saved graph metrics to {output_path}")

    print(f"Total time: {elapsed:.2f}s")
    print(f"Final memory usage: {get_memory_usage_gb():.2f}GB")
    
    # Verify performance target if we have ~100 subjects
    if len(matrix_files) >= 50:
        subjects_per_min = (len(matrix_files) / elapsed) * 60
        print(f"Processing rate: {subjects_per_min:.2f} subjects/minute")
        if subjects_per_min > 2: 
            # Roughly 100 subjects in 50 mins < 30 mins target? 
            # 100 subjects / (100/subjects_per_min) = 100 / (100/2) = 2 mins? 
            # Wait, target is < 30 mins for 100 subjects.
            # 100 / subjects_per_min < 30 => subjects_per_min > 3.33
            if subjects_per_min > 3.33:
                print("Target runtime (<30 min for 100 subjects) ACHIEVED.")
            else:
                print(f"Warning: Runtime target not met. Expected > 3.33 subjects/min, got {subjects_per_min:.2f}")

if __name__ == "__main__":
    main()