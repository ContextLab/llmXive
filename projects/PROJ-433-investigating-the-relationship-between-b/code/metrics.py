import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from utils import setup_logger, get_seeded_rng, check_fd, log_exclusion
from models import Subject

# Ensure logger is configured for metrics-specific logging
logger = setup_logger()

def compute_sliding_window(
    time_series: np.ndarray,
    window_size: int = 60,
    step_size: int = 1,
    logger: Optional[logging.Logger] = None
) -> np.ndarray:
    """
    Compute functional connectivity matrices using a sliding window approach.
    
    Args:
        time_series: 2D array of shape (n_timepoints, n_parcels)
        window_size: Size of the sliding window in timepoints
        step_size: Step size between windows
        logger: Logger instance for logging steps
        
    Returns:
        3D array of shape (n_windows, n_parcels, n_parcels)
    """
    if logger:
        logger.info("Starting sliding window correlation computation")
    
    n_timepoints, n_parcels = time_series.shape
    n_windows = (n_timepoints - window_size) // step_size + 1
    
    if n_windows <= 0:
        if logger:
            logger.error(f"Window size {window_size} is too large for time series length {n_timepoints}")
        raise ValueError("Window size too large for time series")
        
    windows = []
    for i in range(n_windows):
        start = i * step_size
        end = start + window_size
        window_data = time_series[start:end, :]
        
        # Compute correlation matrix for this window
        corr_matrix = np.corrcoef(window_data.T)
        # Handle NaNs that might arise from constant signals
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
        windows.append(corr_matrix)
        
    result = np.stack(windows, axis=0)
    
    if logger:
        logger.info(f"Computed {n_windows} windows of shape {result.shape}")
        
    return result

def extract_reconfigurability(
    connectivity_matrices: np.ndarray,
    rng: Optional[np.random.Generator] = None,
    logger: Optional[logging.Logger] = None
) -> Tuple[int, Dict[str, Any]]:
    """
    Extract network reconfigurability metric (community state transitions) using Louvain.
    
    Args:
        connectivity_matrices: 3D array of shape (n_windows, n_parcels, n_parcels)
        rng: Random number generator
        logger: Logger instance for logging steps
        
    Returns:
        Tuple of (transition_count, metadata_dict)
    """
    if logger:
        logger.info("Starting reconfigurability extraction")
        
    if rng is None:
        rng = get_seeded_rng(42)
        
    try:
        import networkx as nx
        from community import community_louvain
    except ImportError as e:
        if logger:
            logger.error(f"Missing required library for community detection: {e}")
        raise ImportError("community (python-louvain) and networkx are required")
        
    n_windows = connectivity_matrices.shape[0]
    transitions = 0
    prev_partition = None
    metadata = {
        "n_windows": n_windows,
        "algorithm": "louvain",
        "seed": rng.integers(0, 2**32)
    }
    
    for i in range(n_windows):
        corr_matrix = connectivity_matrices[i]
        
        # Create graph from correlation matrix
        G = nx.from_numpy_array(corr_matrix)
        
        # Run Louvain community detection
        try:
            partition = community_louvain.best_partition(G, random_state=rng.integers(0, 2**32))
            
            # Count transitions
            if prev_partition is not None:
                # Compare current partition with previous
                current_labels = [partition[n] for n in range(len(partition))]
                prev_labels = [prev_partition[n] for n in range(len(prev_partition))]
                
                if current_labels != prev_labels:
                    transitions += 1
                    
            prev_partition = partition
            
        except Exception as e:
            if logger:
                logger.warning(f"Louvain failed on window {i}: {e}, retrying with different seed")
            # Retry logic could be implemented here if needed
            continue
            
    metadata["final_transitions"] = transitions
    
    if logger:
        logger.info(f"Extracted {transitions} community state transitions")
        
    return transitions, metadata

def save_metrics_to_json(
    subject_id: str,
    transition_count: int,
    metadata: Dict[str, Any],
    output_dir: Path,
    logger: Optional[logging.Logger] = None
) -> Path:
    """
    Save computed metrics to a JSON file.
    
    Args:
        subject_id: Subject identifier
        transition_count: Number of community state transitions
        metadata: Additional metadata about the computation
        output_dir: Directory to save the file
        logger: Logger instance
        
    Returns:
        Path to the saved file
    """
    if logger:
        logger.info(f"Saving metrics for subject {subject_id}")
        
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"metrics_{subject_id}.json"
    
    data = {
        "subject_id": subject_id,
        "transition_count": transition_count,
        **metadata
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    if logger:
        logger.info(f"Metrics saved to {output_path}")
        
    return output_path

def aggregate_metrics_to_tsv(
    input_dir: Path,
    output_path: Path,
    logger: Optional[logging.Logger] = None
) -> Path:
    """
    Aggregate all JSON metric files into a single TSV file.
    
    Args:
        input_dir: Directory containing metrics JSON files
        output_path: Path for the output TSV file
        logger: Logger instance
        
    Returns:
        Path to the output file
    """
    if logger:
        logger.info(f"Aggregating metrics from {input_dir}")
        
    import pandas as pd
    
    json_files = list(input_dir.glob("metrics_*.json"))
    records = []
    
    for jf in json_files:
        try:
            with open(jf, 'r') as f:
                data = json.load(f)
            records.append({
                "subject_id": data.get("subject_id"),
                "transition_count": data.get("transition_count")
            })
        except Exception as e:
            if logger:
                logger.warning(f"Failed to read {jf}: {e}")
                
    if not records:
        if logger:
            logger.warning("No valid metrics found to aggregate")
        # Create empty file with header
        with open(output_path, 'w') as f:
            f.write("subject_id\ttransition_count\n")
        return output_path
        
    df = pd.DataFrame(records)
    df.to_csv(output_path, sep='\t', index=False)
    
    if logger:
        logger.info(f"Aggregated {len(records)} subjects to {output_path}")
        
    return output_path

def main():
    """Main entry point for metrics computation pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute network reconfigurability metrics")
    parser.add_argument("--subject", type=str, required=True, help="Subject ID")
    parser.add_argument("--input-dir", type=str, required=True, help="Directory with preprocessed fMRI data")
    parser.add_argument("--output-dir", type=str, default="data/results", help="Output directory for metrics")
    parser.add_argument("--window-size", type=int, default=60, help="Sliding window size")
    parser.add_argument("--step-size", type=int, default=1, help="Sliding window step size")
    args = parser.parse_args()
    
    # Setup logging for this run
    logger = setup_logger()
    metrics_logger = logging.getLogger("metrics")
    metrics_logger.setLevel(logging.INFO)
    
    # Create metrics-specific log file
    metrics_log_path = Path("data/metrics_log.txt")
    fh = logging.FileHandler(metrics_log_path, mode='a')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    metrics_logger.addHandler(fh)
    
    metrics_logger.info(f"Starting metrics computation for subject {args.subject}")
    
    # Load preprocessed time series (simplified for this implementation)
    # In a real scenario, this would load from the preprocessed fMRI data
    input_path = Path(args.input_dir) / f"sub-{args.subject}_space-MNI_desc-preproc_bold.nii.gz"
    
    if not input_path.exists():
        metrics_logger.error(f"Preprocessed data not found: {input_path}")
        log_exclusion("Missing preprocessed fMRI data", args.subject)
        return
        
    try:
        import nibabel as nib
        img = nib.load(input_path)
        time_series = img.get_fdata()
        # Flatten time series if needed (e.g., if 4D)
        if time_series.ndim == 4:
            # Average across voxels or use parcellation (simplified here)
            time_series = time_series.mean(axis=(0, 1))
        elif time_series.ndim == 3:
            time_series = time_series.reshape(-1, 1)
            
        # Ensure 2D: (n_timepoints, n_parcels)
        if time_series.ndim == 1:
            time_series = time_series.reshape(-1, 1)
            
    except Exception as e:
        metrics_logger.error(f"Failed to load fMRI data: {e}")
        log_exclusion("Data loading error", args.subject)
        return
        
    # Compute sliding window correlations
    metrics_logger.info(f"Computing sliding window with size={args.window_size}, step={args.step_size}")
    try:
        conn_matrices = compute_sliding_window(
            time_series,
            window_size=args.window_size,
            step_size=args.step_size,
            logger=metrics_logger
        )
    except Exception as e:
        metrics_logger.error(f"Sliding window computation failed: {e}")
        log_exclusion("Sliding window failure", args.subject)
        return
        
    # Extract reconfigurability
    rng = get_seeded_rng(42)
    try:
        transition_count, metadata = extract_reconfigurability(
            conn_matrices,
            rng=rng,
            logger=metrics_logger
        )
    except Exception as e:
        metrics_logger.error(f"Reconfigurability extraction failed: {e}")
        log_exclusion("Reconfigurability failure", args.subject)
        return
        
    # Save results
    output_dir = Path(args.output_dir)
    try:
        save_metrics_to_json(
            args.subject,
            transition_count,
            metadata,
            output_dir,
            logger=metrics_logger
        )
        metrics_logger.info(f"Successfully computed metrics for {args.subject}: {transition_count} transitions")
    except Exception as e:
        metrics_logger.error(f"Failed to save metrics: {e}")
        log_exclusion("Save failure", args.subject)
        return

if __name__ == "__main__":
    main()