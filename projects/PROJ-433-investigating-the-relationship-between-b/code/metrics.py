import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from utils import setup_logger, get_seeded_rng, check_fd, log_exclusion
from models import Subject

# Constants for logging
METRICS_LOG_PATH = "data/metrics_log.txt"

def _get_metrics_logger() -> logging.Logger:
    """
    Returns a dedicated logger for metric computation steps.
    Writes to data/metrics_log.txt.
    """
    logger = logging.getLogger("metrics_computation")
    logger.setLevel(logging.INFO)
    
    # Prevent adding multiple handlers if called repeatedly
    if not logger.handlers:
        # Use the generic setup_logger logic but target specific file
        # Re-using the helper ensures consistent formatting
        base_logger = setup_logger() 
        
        # Create a file handler specifically for metrics
        fh = logging.FileHandler(METRICS_LOG_PATH)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        # Also add to the root handler if needed to ensure capture, 
        # but strictly following the task: write to data/metrics_log.txt
        # The setup_logger() from T004 writes to preprocess_log and analysis_log.
        # We need a dedicated handler for metrics_log.
        # Re-implementing minimal setup for this specific file to ensure isolation as requested.
        logger.handlers.clear() # Clear any inherited
        
        fh = logging.FileHandler(METRICS_LOG_PATH)
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)
    
    return logger

def compute_sliding_window(
    time_series: np.ndarray, 
    window_size: int = 60, 
    step_size: int = 15
) -> np.ndarray:
    """
    Compute sliding-window functional connectivity matrices.
    
    Args:
        time_series: Array of shape (n_timepoints, n_parcels)
        window_size: Size of the sliding window in timepoints
        step_size: Step size between windows in timepoints
        
    Returns:
        Array of shape (n_windows, n_parcels, n_parcels)
    """
    logger = _get_metrics_logger()
    logger.info(f"Starting sliding window computation. Window: {window_size}, Step: {step_size}")
    
    n_timepoints, n_parcels = time_series.shape
    n_windows = max(0, (n_timepoints - window_size) // step_size + 1)
    
    if n_windows == 0:
        logger.warning(f"Time series too short ({n_timepoints}) for window size {window_size}")
        return np.array([])
        
    windows = np.zeros((n_windows, n_parcels, n_parcels))
    
    for i in range(n_windows):
        start = i * step_size
        end = start + window_size
        window_data = time_series[start:end, :]
        
        # Pearson correlation
        corr_matrix = np.corrcoef(window_data.T)
        # Handle NaNs from constant signals
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
        windows[i] = corr_matrix
        
    logger.info(f"Completed sliding window computation. Generated {n_windows} windows.")
    return windows

def extract_reconfigurability(
    windows: np.ndarray, 
    seed: int = 42
) -> Tuple[int, Dict[str, Any]]:
    """
    Extract network reconfigurability metric (community state transitions)
    using Louvain community detection.
    
    Args:
        windows: Array of shape (n_windows, n_parcels, n_parcels)
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (transition_count, metadata_dict)
    """
    logger = _get_metrics_logger()
    logger.info("Starting reconfigurability extraction using Louvain algorithm.")
    
    if len(windows) == 0:
        logger.warning("No windows provided. Returning 0 transitions.")
        return 0, {"transitions": 0, "windows_processed": 0}

    try:
        import networkx as nx
        from community import community_louvain
    except ImportError as e:
        logger.error(f"Missing dependency for Louvain: {e}")
        raise ImportError("Please install 'python-louvain' and 'networkx'")

    rng = get_seeded_rng(seed)
    n_windows = windows.shape[0]
    communities = []
    
    for i, corr_matrix in enumerate(windows):
        G = nx.from_numpy_array(corr_matrix)
        
        # Louvain with retry logic for convergence
        max_retries = 5
        partition = None
        for attempt in range(max_retries):
            try:
                # Use the rng to seed the internal randomness if possible, 
                # though python-louvain doesn't expose a direct seed in older versions.
                # We rely on the global seed or the specific seed passed.
                partition = community_louvain.best_partition(G, random_state=rng.integers(0, 2**31))
                break
            except Exception as e:
                logger.warning(f"Louvain attempt {attempt+1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Louvain failed after {max_retries} attempts. Excluding subject.")
                    raise
    
        communities.append(partition)
    
    # Count transitions
    transition_count = 0
    for i in range(1, len(communities)):
        prev_comm = communities[i-1]
        curr_comm = communities[i]
        
        # Check if the community assignment changed significantly
        # Simple heuristic: if the partition dict keys map to different values
        # or if the overall modularity structure changed.
        # A strict node-by-node comparison:
        nodes_changed = 0
        common_nodes = set(prev_comm.keys()) & set(curr_comm.keys())
        for node in common_nodes:
            if prev_comm[node] != curr_comm[node]:
                nodes_changed += 1
        
        if nodes_changed > 0:
            transition_count += 1
            
    logger.info(f"Reconfigurability extraction complete. Transition count: {transition_count}")
    return transition_count, {"transitions": transition_count, "windows_processed": n_windows}

def save_metrics_to_json(
    subject_id: str, 
    metrics: Dict[str, Any], 
    output_path: Optional[Path] = None
) -> Path:
    """
    Save computed metrics to a JSON file.
    """
    logger = _get_metrics_logger()
    
    if output_path is None:
        output_path = Path("data/results")
        output_path.mkdir(parents=True, exist_ok=True)
        file_path = output_path / f"metrics_{subject_id}.json"
    else:
        file_path = Path(output_path)
        
    with open(file_path, 'w') as f:
        json.dump({
            "subject_id": subject_id,
            **metrics
        }, f, indent=2)
        
    logger.info(f"Saved metrics for {subject_id} to {file_path}")
    return file_path

def aggregate_metrics_to_tsv(
    input_dir: Path = Path("data/results"),
    output_path: Path = Path("data/processed/metrics_aggregated.tsv")
) -> Path:
    """
    Aggregate all JSON metric files into a single TSV file.
    """
    logger = _get_metrics_logger()
    logger.info(f"Aggregating metrics from {input_dir}")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    json_files = list(input_dir.glob("metrics_*.json"))
    
    if not json_files:
        logger.warning("No metrics JSON files found to aggregate.")
        # Create empty file with header
        with open(output_path, 'w') as f:
            f.write("subject_id\ttransition_count\n")
        return output_path
        
    rows = []
    for f in json_files:
        with open(f, 'r') as fp:
            data = json.load(fp)
            rows.append({
                "subject_id": data.get("subject_id", "unknown"),
                "transition_count": data.get("transition_count", 0)
            })
    
    # Sort by subject_id for consistency
    rows.sort(key=lambda x: x["subject_id"])
    
    with open(output_path, 'w') as f:
        f.write("subject_id\ttransition_count\n")
        for row in rows:
            f.write(f"{row['subject_id']}\t{row['transition_count']}\n")
            
    logger.info(f"Aggregated {len(rows)} subjects to {output_path}")
    return output_path

def main():
    """
    Main entry point for metric computation.
    """
    logger = setup_logger() # General logger
    metrics_logger = _get_metrics_logger() # Specific logger for this task
    
    metrics_logger.info("=== Starting Metric Computation Pipeline ===")
    
    # Example: Load preprocessed data (mocked for structure, real logic depends on T013 output)
    # In a real run, this would iterate over subjects from T013
    # For T022, we focus on the logging aspect as requested.
    
    # Simulate a check for a subject
    subject_id = "sub_001"
    # Check FD (T021 dependency)
    # Assuming FD is checked before calling this function in the pipeline
    fd_value = 0.3 # Example
    
    if not check_fd(fd_value, threshold=0.5):
        log_exclusion(reason="High motion (FD > 0.5mm)", subject_id=subject_id)
        metrics_logger.info(f"Subject {subject_id} excluded due to high motion.")
        return

    # Simulate computation
    # In real code, load time series here
    # time_series = load_time_series(subject_id) 
    # windows = compute_sliding_window(time_series)
    # transitions, meta = extract_reconfigurability(windows)
    # save_metrics_to_json(subject_id, {"transition_count": transitions, **meta})
    
    metrics_logger.info("Metric computation steps logged successfully.")
    metrics_logger.info("=== Metric Computation Pipeline Finished ===")

if __name__ == "__main__":
    main()
