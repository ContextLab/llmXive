"""
Runtime Verification Script for Task T030a.

Executes the full pipeline on a subset (N=5) of simulated data to verify
pipeline flow and performance. Captures timing logs to data/logs/runtime_subset.log.

Pass Criteria: Runtime < 1 minute for N=5.
"""
import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any

# Add project root to path if running as script
if os.path.basename(os.getcwd()) == 'PROJ-486-investigating-the-impact-of-network-topo':
    sys.path.insert(0, '.')
elif 'code' in os.getcwd():
    sys.path.insert(0, '..')
else:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import run_us1_pipeline, ensure_directories
from config import RANDOM_SEED
from data_loader import generate_simulated_raw_matrices
import pandas as pd

LOG_DIR = "data/logs"
LOG_FILE = os.path.join(LOG_DIR, "runtime_subset.log")
SUBSET_SIZE = 5

def log_message(msg: str, log_data: Dict[str, Any] = None):
    """Write a timestamped message to the log file."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry + "\n")
        if log_data:
            f.write(json.dumps(log_data) + "\n")
        f.write("-" * 40 + "\n")

def run_subset_pipeline():
    """
    Runs the US1 pipeline on a subset of N=5 subjects.
    Returns total runtime in seconds.
    """
    start_time = time.time()
    log_message("Starting Runtime Verification (N=5 subset)...")
    
    try:
        # Ensure directories exist
        ensure_directories()
        log_message("Directories ensured.")

        # Generate fresh simulated data for the subset to ensure reproducibility
        # We override the standard generation to only create N=5 subjects
        log_message(f"Generating simulated raw matrices for N={SUBSET_SIZE} subjects...")
        
        # We need to patch the data generation or force the pipeline to use N=5.
        # Since the main pipeline expects data to exist, we will generate the 
        # raw matrices for N=5, then let the pipeline run its join and analysis logic.
        # Note: The existing generate_simulated_raw_matrices creates N subjects.
        # We will call it with a temporary config or patch the count if possible.
        # However, to keep it simple and compliant with existing API, we will
        # generate the full set but the analysis might filter or we rely on the 
        # fact that the pipeline handles whatever is in data/raw.
        # To strictly follow "subset N=5", we will generate a specific file for N=5
        # if the main pipeline supports reading a specific file, or we generate
        # a fresh run with N=5.
        
        # Strategy: Regenerate the raw data for exactly N=5 subjects.
        # The existing function generate_simulated_raw_matrices uses config for N.
        # We will assume the pipeline reads from data/raw/correlation_matrices.csv
        # We will generate this file with N=5.
        
        # Check if we can override N via environment or config. 
        # Since we cannot easily change config.py without side effects, 
        # we will generate the data directly here using the same logic as data_loader.
        
        from config import RANDOM_SEED
        import numpy as np
        import networkx as nx

        # Replicate logic from data_loader for generating matrices but for N=5
        # We assume Schaefer 200 nodes as per T006
        N_NODES = 200
        N_SUBJECTS = SUBSET_SIZE
        
        # Create output path
        raw_data_path = "data/raw/correlation_matrices.csv"
        
        # Generate data
        np.random.seed(RANDOM_SEED)
        records = []
        
        for i in range(N_SUBJECTS):
            # Generate a random correlation matrix (positive semi-definite)
            # Method: Generate random matrix, multiply by transpose, normalize
            A = np.random.randn(N_NODES, N_NODES)
            corr_matrix = np.dot(A, A.T)
            d = np.sqrt(np.diag(corr_matrix))
            corr_matrix = corr_matrix / np.outer(d, d)
            
            # Ensure symmetry and diagonal
            corr_matrix = (corr_matrix + corr_matrix.T) / 2
            np.fill_diagonal(corr_matrix, 1.0)
            
            # Flatten upper triangle
            upper_tri = corr_matrix[np.triu_indices(N_NODES, k=1)]
            
            records.append({
                "subject_id": f"SUBJ_{i+1:03d}",
                "matrix_data": upper_tri.tolist()
            })
        
        df = pd.DataFrame(records)
        df.to_csv(raw_data_path, index=False)
        log_message(f"Generated simulated raw data for {N_SUBJECTS} subjects at {raw_data_path}")

        # Now run the US1 pipeline
        log_message("Running US1 Pipeline (Correlation Analysis)...")
        pipeline_start = time.time()
        
        # The main pipeline expects the data to be in place.
        # It will load, validate, join, compute metrics, etc.
        run_us1_pipeline()
        
        pipeline_end = time.time()
        log_message(f"US1 Pipeline completed in {pipeline_end - pipeline_start:.2f} seconds.")

        # Check outputs
        required_outputs = [
            "data/processed/correlation_results.csv",
            "data/visualizations/scatter_topology_entrainment.png",
            "data/processed/summary_report.txt"
        ]
        
        missing = []
        for path in required_outputs:
            if not os.path.exists(path):
                missing.append(path)
        
        if missing:
            log_message("ERROR: Missing required output files", {"missing": missing})
            return None
        
        log_message("All required output files generated successfully.")
        
        end_time = time.time()
        total_runtime = end_time - start_time
        
        log_message(f"Runtime Verification Complete. Total Runtime: {total_runtime:.2f} seconds.", {
            "total_runtime_seconds": total_runtime,
            "subjects_processed": N_SUBJECTS,
            "status": "SUCCESS" if total_runtime < 60 else "WARNING: Runtime > 60s"
        })
        
        return total_runtime

    except Exception as e:
        log_message(f"ERROR: Pipeline execution failed: {str(e)}")
        raise

def main():
    print("Starting Runtime Verification (Task T030a)...")
    try:
        runtime = run_subset_pipeline()
        if runtime is not None:
            if runtime < 60:
                print(f"SUCCESS: Runtime verification passed. Time: {runtime:.2f}s (< 60s).")
                return 0
            else:
                print(f"WARNING: Runtime verification failed. Time: {runtime:.2f}s (>= 60s).")
                return 1
        else:
            print("FAILURE: Pipeline did not complete successfully.")
            return 1
    except Exception as e:
        print(f"FAILURE: Exception during verification: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
