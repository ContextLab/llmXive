import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from utils import setup_logger, get_seeded_rng, check_fd, log_exclusion

# Initialize logger specific to metrics computation
logger = setup_logger("metrics_logger", "data/metrics_log.txt")

def compute_sliding_window(
    time_series: np.ndarray,
    window_size: int = 60,
    step_size: int = 10,
    rng: Optional[np.random.Generator] = None
) -> List[np.ndarray]:
    """
    Compute functional connectivity matrices using a sliding window approach.
    
    Args:
        time_series: Shape (n_timepoints, n_parcels)
        window_size: Number of timepoints in each window
        step_size: Number of timepoints to shift the window
        rng: Random number generator (optional, for reproducibility if needed)
    
    Returns:
        List of correlation matrices, one per window.
    """
    n_timepoints, n_parcels = time_series.shape
    if window_size >= n_timepoints:
        raise ValueError(f"Window size {window_size} must be less than time series length {n_timepoints}")
    
    windows = []
    for start in range(0, n_timepoints - window_size + 1, step_size):
        end = start + window_size
        window_data = time_series[start:end, :]
        
        # Compute Pearson correlation
        # Center the data
        window_data_centered = window_data - np.mean(window_data, axis=0)
        # Avoid division by zero
        std_dev = np.std(window_data_centered, axis=0)
        std_dev[std_dev == 0] = 1e-10
        window_data_normalized = window_data_centered / std_dev
        
        corr_matrix = np.corrcoef(window_data_normalized.T)
        windows.append(corr_matrix)
    
    return windows

def extract_reconfigurability(
    windows: List[np.ndarray],
    rng: Optional[np.random.Generator] = None,
    seed: int = 42,
    max_retries: int = 3
) -> Tuple[int, bool]:
    """
    Extract network reconfigurability metric (community state transition count)
    using Louvain community detection.
    
    Args:
        windows: List of correlation matrices
        rng: Random number generator
        seed: Seed for reproducibility
        max_retries: Maximum number of retries for Louvain convergence
    
    Returns:
        Tuple of (transition_count, success_flag)
    """
    if rng is None:
        rng = get_seeded_rng(seed)
    
    if not windows:
        return 0, True
    
    try:
        import networkx as nx
        from networkx.algorithms.community import louvain_communities
    except ImportError:
        raise ImportError("networkx is required for Louvain community detection")
    
    transitions = 0
    prev_partition = None
    
    for i, corr_matrix in enumerate(windows):
        G = nx.from_numpy_array(corr_matrix)
        
        # Retry logic for convergence
        success = False
        attempts = 0
        current_partition = None
        
        while not success and attempts < max_retries:
            try:
                # Use the specific partition resolution if needed, default is 1.0
                current_partition = louvain_communities(G, seed=rng.integers(0, 2**31))
                success = True
            except Exception as e:
                attempts += 1
                logger.warning(f"Louvain attempt {attempts} failed: {e}")
                if attempts == max_retries:
                    logger.error(f"Louvain failed to converge after {max_retries} attempts for window {i}")
                    return 0, False
        
        if success:
            # Convert partition to a list of sets for comparison
            current_sets = [set(nodes) for nodes in current_partition]
            
            if prev_partition is not None:
                # Check if partition changed
                if current_sets != prev_partition:
                    transitions += 1
            
            prev_partition = current_sets
    
    return transitions, True

def save_metrics_to_json(
    subject_id: str,
    transition_count: int,
    output_path: Path
) -> None:
    """
    Save computed metrics to a JSON file.
    
    Args:
        subject_id: Subject identifier
        transition_count: Number of community state transitions
        output_path: Path to save the JSON file
    """
    metrics = {
        "subject_id": subject_id,
        "transition_count": transition_count
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Saved metrics for subject {subject_id} to {output_path}")

def aggregate_metrics_to_tsv(
    json_files: List[Path],
    output_path: Path
) -> None:
    """
    Aggregate all JSON metric files into a single TSV file.
    
    Args:
        json_files: List of paths to JSON metric files
        output_path: Path to save the aggregated TSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("subject_id\ttransition_count\n")
        
        for json_file in json_files:
            with open(json_file, 'r') as jf:
                data = json.load(jf)
                f.write(f"{data['subject_id']}\t{data['transition_count']}\n")
    
    logger.info(f"Aggregated {len(json_files)} metrics to {output_path}")

def main():
    """
    Main entry point for metrics computation.
    This function demonstrates the workflow:
    1. Load preprocessed data (simulated for this example)
    2. Compute sliding window correlations
    3. Extract reconfigurability metrics
    4. Save results
    5. Log all steps and exclusions to data/metrics_log.txt
    """
    # Setup logging
    logger.info("Starting metrics computation pipeline")
    
    # Example: Simulate a subject ID and data path
    # In a real scenario, this would iterate over subjects from data/processed
    subject_id = "sub_001"
    # Simulate time series data (n_timepoints=120, n_parcels=100)
    # Replace with actual loading from preprocessed NIfTI files
    time_series = np.random.randn(120, 100)
    
    # Check for motion artifacts (QC)
    # Simulated FD value
    fd_value = 0.3
    if not check_fd(fd_value, threshold=0.5):
        log_exclusion("High motion (FD > 0.5)", subject_id)
        logger.error(f"Subject {subject_id} excluded due to high motion (FD={fd_value})")
        return
    
    logger.info(f"Subject {subject_id} passed QC (FD={fd_value})")
    
    # Compute sliding window correlations
    logger.info(f"Computing sliding window correlations for {subject_id}")
    windows = compute_sliding_window(time_series, window_size=60, step_size=10)
    logger.info(f"Generated {len(windows)} windows")
    
    # Extract reconfigurability
    logger.info(f"Extracting reconfigurability metrics for {subject_id}")
    transition_count, success = extract_reconfigurability(windows)
    
    if not success:
        log_exclusion("Louvain convergence failure", subject_id)
        logger.error(f"Subject {subject_id} excluded due to Louvain convergence failure")
        return
    
    logger.info(f"Transition count for {subject_id}: {transition_count}")
    
    # Save metrics
    output_path = Path("data/results/metrics_sub_001.json")
    save_metrics_to_json(subject_id, transition_count, output_path)
    
    logger.info("Metrics computation pipeline completed successfully")

if __name__ == "__main__":
    main()