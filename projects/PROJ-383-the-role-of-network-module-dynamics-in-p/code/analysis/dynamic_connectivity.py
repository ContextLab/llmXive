import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union

import numpy as np
import pandas as pd
import leidenalg
import networkx as nx
from scipy.stats import pearsonr

# Import config for seeds and window parameters
from utils.config import set_all_seeds

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIN_TIMEPOINTS_REQUIRED = 10  # Minimum time points to form a valid window
DEFAULT_WINDOW_LENGTH = 60    # Seconds (will be converted to frames)
DEFAULT_STEP_SIZE = 30        # Seconds (will be converted to frames)
DEFAULT_TR = 0.72             # HCP TR in seconds

def load_scrubbed_timeseries(file_path: str) -> pd.DataFrame:
    """Load scrubbed timeseries data from Parquet file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Timeseries file not found: {file_path}")
    
    df = pd.read_parquet(path)
    logger.info(f"Loaded timeseries: {df.shape[0]} timepoints, {df.shape[1]} regions")
    return df

def compute_correlation_matrix(timeseries: np.ndarray) -> np.ndarray:
    """Compute Pearson correlation matrix for a given timeseries."""
    # Ensure timeseries is float64 for numerical stability
    timeseries = timeseries.astype(np.float64)
    
    # Compute correlation matrix
    corr_matrix = np.corrcoef(timeseries.T)
    
    # Handle NaN values (can occur if a region has zero variance)
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    return corr_matrix

def generate_sliding_windows(
    timeseries: np.ndarray,
    window_length: int,
    step_size: int
) -> List[np.ndarray]:
    """
    Generate sliding windows from timeseries data.
    
    Args:
        timeseries: Array of shape (timepoints, regions)
        window_length: Number of time points in each window
        step_size: Number of time points to step between windows
        
    Returns:
        List of 2D arrays, each of shape (window_length, regions)
    """
    n_timepoints = timeseries.shape[0]
    windows = []
    
    if window_length > n_timepoints:
        raise ValueError(
            f"Window length ({window_length}) exceeds available timepoints ({n_timepoints})"
        )
    
    if window_length < MIN_TIMEPOINTS_REQUIRED:
        raise ValueError(
            f"Window length ({window_length}) is too small. "
            f"Minimum required is {MIN_TIMEPOINTS_REQUIRED}."
        )
    
    for start in range(0, n_timepoints - window_length + 1, step_size):
        end = start + window_length
        window = timeseries[start:end, :]
        windows.append(window)
    
    logger.info(f"Generated {len(windows)} sliding windows")
    return windows

def compute_dynamic_connectivity(
    timeseries: np.ndarray,
    window_length: int,
    step_size: int
) -> List[np.ndarray]:
    """
    Compute dynamic connectivity matrices using sliding windows.
    
    Args:
        timeseries: Array of shape (timepoints, regions)
        window_length: Number of time points in each window
        step_size: Number of time points to step between windows
        
    Returns:
        List of correlation matrices, one per window
    """
    windows = generate_sliding_windows(timeseries, window_length, step_size)
    connectivity_matrices = []
    
    for i, window in enumerate(windows):
        corr_mat = compute_correlation_matrix(window)
        connectivity_matrices.append(corr_mat)
    
    logger.info(f"Computed {len(connectivity_matrices)} connectivity matrices")
    return connectivity_matrices

def _build_multilayer_graph(
    connectivity_matrices: List[np.ndarray],
    coupling_strength: float = 1.0
) -> nx.Graph:
    """
    Build a multilayer graph from a sequence of connectivity matrices.
    
    This creates a graph where nodes are (time_layer, region) pairs.
    Intra-layer edges come from the connectivity matrix.
    Inter-layer edges connect the same region across consecutive layers.
    """
    G = nx.Graph()
    n_regions = connectivity_matrices[0].shape[0]
    n_layers = len(connectivity_matrices)
    
    # Add nodes and intra-layer edges
    for layer_idx, conn_mat in enumerate(connectivity_matrices):
        for i in range(n_regions):
            for j in range(i + 1, n_regions):
                weight = conn_mat[i, j]
                if weight > 0:  # Only positive correlations
                    G.add_edge(
                        (layer_idx, i),
                        (layer_idx, j),
                        weight=weight
                    )
        
        # Add self-loops to ensure nodes exist even if no edges
        for i in range(n_regions):
            G.add_node((layer_idx, i))
    
    # Add inter-layer edges (coupling between same region in adjacent layers)
    for layer_idx in range(n_layers - 1):
        for region in range(n_regions):
            G.add_edge(
                (layer_idx, region),
                (layer_idx + 1, region),
                weight=coupling_strength
            )
    
    return G

def _compute_leiden_communities(
    G: nx.Graph,
    resolution: float = 1.0,
    n_iterations: int = 100
) -> List[Dict[int, int]]:
    """
    Compute Leiden communities for each layer of the multilayer graph.
    
    Returns:
        List of dictionaries, one per layer, mapping node index to community ID
    """
    # Convert to weighted graph for Leiden
    # Leidenalg expects a graph with edge weights
    partition_type = leidenalg.RBConfigurationVertexPartition
    
    # We need to run Leiden on each layer separately but with the multilayer structure
    # For simplicity, we'll run on the full multilayer graph and then extract per-layer assignments
    
    # Create a partition object
    partition = leidenalg.find_partition(
        G,
        partition_type,
        resolution_parameter=resolution,
        n_iterations=n_iterations,
        seed=42
    )
    
    # Extract community assignments per layer
    layer_assignments = []
    n_layers = len(G.nodes()) // (len(list(G.nodes())[0][1:])) + 1 if G.nodes() else 0
    
    # Reconstruct layer assignments
    # The partition object returns a membership list
    membership = partition.membership
    
    # Map (layer, node) to community
    node_to_community = {}
    for idx, node in enumerate(G.nodes()):
        node_to_community[node] = membership[idx]
    
    # Group by layer
    n_regions = G.nodes()[0][1] if G.nodes() else 0
    for layer_idx in range(n_layers):
        layer_communities = {}
        for region in range(n_regions):
            node = (layer_idx, region)
            if node in node_to_community:
                layer_communities[region] = node_to_community[node]
        layer_assignments.append(layer_communities)
    
    return layer_assignments

def compute_flexibility_metric(
    layer_assignments: List[Dict[int, int]]
) -> float:
    """
    Compute temporal flexibility metric.
    
    Flexibility is defined as the probability that a node switches community
    between consecutive time windows.
    
    Returns:
        Float between 0 and 1 representing flexibility
    """
    if len(layer_assignments) < 2:
        return 0.0
    
    n_regions = len(layer_assignments[0])
    total_switches = 0
    total_opportunities = 0
    
    for layer_idx in range(len(layer_assignments) - 1):
        current_layer = layer_assignments[layer_idx]
        next_layer = layer_assignments[layer_idx + 1]
        
        for region in range(n_regions):
            if region in current_layer and region in next_layer:
                total_opportunities += 1
                if current_layer[region] != next_layer[region]:
                    total_switches += 1
    
    if total_opportunities == 0:
        return 0.0
    
    flexibility = total_switches / total_opportunities
    return float(flexibility)

def process_subject_dynamic_connectivity(
    subject_id: str,
    timeseries_path: str,
    window_length: Optional[int] = None,
    step_size: Optional[int] = None,
    resolution: float = 1.0,
    n_iterations: int = 100,
    tr: float = DEFAULT_TR
) -> Dict[str, Union[float, str, bool]]:
    """
    Process a single subject to compute flexibility metric.
    
    Args:
        subject_id: Subject identifier
        timeseries_path: Path to scrubbed timeseries parquet file
        window_length: Window length in seconds (defaults to config)
        step_size: Step size in seconds (defaults to config)
        resolution: Leiden resolution parameter
        n_iterations: Number of Leiden iterations
        tr: Repetition time in seconds
        
    Returns:
        Dictionary with flexibility score or error information
    """
    # Set seeds for reproducibility
    set_all_seeds(42)
    
    result = {
        'subject_id': subject_id,
        'success': False,
        'flexibility_score': None,
        'error': None,
        'window_length_frames': None,
        'step_size_frames': None,
        'n_windows': None
    }
    
    try:
        # Load timeseries
        df = load_scrubbed_timeseries(timeseries_path)
        timeseries = df.values
        
        # Convert window parameters from seconds to frames
        if window_length is None:
            window_length_sec = DEFAULT_WINDOW_LENGTH
        else:
            window_length_sec = window_length
        
        if step_size is None:
            step_size_sec = DEFAULT_STEP_SIZE
        else:
            step_size_sec = step_size
        
        window_length_frames = int(window_length_sec / tr)
        step_size_frames = int(step_size_sec / tr)
        
        # Ensure minimum window length
        if window_length_frames < MIN_TIMEPOINTS_REQUIRED:
            logger.warning(
                f"Subject {subject_id}: Window length {window_length_frames} "
                f"frames is below minimum {MIN_TIMEPOINTS_REQUIRED}. Skipping."
            )
            result['error'] = (
                f"Window length {window_length_frames} frames is below minimum "
                f"{MIN_TIMEPOINTS_REQUIRED}. Skipping subject."
            )
            return result
        
        # Check if we have enough time points
        n_timepoints = timeseries.shape[0]
        if n_timepoints < window_length_frames:
            logger.warning(
                f"Subject {subject_id}: Only {n_timepoints} timepoints available, "
                f"need {window_length_frames} for window. Skipping."
            )
            result['error'] = (
                f"Insufficient timepoints: {n_timepoints} available, "
                f"need {window_length_frames}. Skipping subject."
            )
            return result
        
        # Calculate maximum possible windows
        max_windows = (n_timepoints - window_length_frames) // step_size_frames + 1
        if max_windows < 2:
            logger.warning(
                f"Subject {subject_id}: Only {max_windows} window(s) possible. "
                f"Need at least 2 to compute flexibility. Skipping."
            )
            result['error'] = (
                f"Insufficient windows: {max_windows} window(s) possible, "
                f"need at least 2. Skipping subject."
            )
            return result
        
        result['window_length_frames'] = window_length_frames
        result['step_size_frames'] = step_size_frames
        
        # Compute dynamic connectivity
        logger.info(f"Processing subject {subject_id}...")
        connectivity_matrices = compute_dynamic_connectivity(
            timeseries,
            window_length_frames,
            step_size_frames
        )
        
        result['n_windows'] = len(connectivity_matrices)
        
        # Build multilayer graph
        G = _build_multilayer_graph(connectivity_matrices)
        
        # Compute communities
        layer_assignments = _compute_leiden_communities(
            G,
            resolution=resolution,
            n_iterations=n_iterations
        )
        
        # Compute flexibility
        flexibility = compute_flexibility_metric(layer_assignments)
        
        # Validate flexibility score
        if not (0.0 <= flexibility <= 1.0):
            logger.warning(
                f"Subject {subject_id}: Flexibility score {flexibility} "
                f"outside [0, 1] range. Clamping."
            )
            flexibility = max(0.0, min(1.0, flexibility))
        
        result['flexibility_score'] = flexibility
        result['success'] = True
        
        logger.info(
            f"Subject {subject_id}: Flexibility score = {flexibility:.4f}, "
            f"{len(connectivity_matrices)} windows processed"
        )
        
    except Exception as e:
        error_msg = f"Error processing subject {subject_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        result['error'] = error_msg
    
    return result

def save_dynamic_connectivity_results(
    results: List[Dict],
    output_path: str
) -> None:
    """Save flexibility results to a Parquet file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    df = pd.DataFrame(results)
    df.to_parquet(path, index=False)
    logger.info(f"Saved results to {output_path}")

def main():
    """Main entry point for dynamic connectivity analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Compute temporal flexibility metric from fMRI timeseries'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/processed/scrubbed_timeseries.parquet',
        help='Path to scrubbed timeseries parquet file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed/flexibility_scores.parquet',
        help='Path to output flexibility scores'
    )
    parser.add_argument(
        '--window-length',
        type=int,
        default=None,
        help='Window length in seconds (default: 60)'
    )
    parser.add_argument(
        '--step-size',
        type=int,
        default=None,
        help='Step size in seconds (default: 30)'
    )
    parser.add_argument(
        '--resolution',
        type=float,
        default=1.0,
        help='Leiden resolution parameter (default: 1.0)'
    )
    parser.add_argument(
        '--n-iterations',
        type=int,
        default=100,
        help='Number of Leiden iterations (default: 100)'
    )
    
    args = parser.parse_args()
    
    # Load all subjects
    df = pd.read_parquet(args.input)
    
    # Assume first column is subject_id, rest are time series
    # This is a simplification - real data might have different structure
    subject_ids = df['subject_id'].unique() if 'subject_id' in df.columns else ['subject_001']
    
    results = []
    for subject_id in subject_ids:
        # Filter data for this subject
        if 'subject_id' in df.columns:
            subject_data = df[df['subject_id'] == subject_id].copy()
            subject_data = subject_data.drop(columns=['subject_id'])
        else:
            subject_data = df
        
        # Save to temp file for processing
        temp_path = f"/tmp/{subject_id}_timeseries.parquet"
        subject_data.to_parquet(temp_path)
        
        result = process_subject_dynamic_connectivity(
            subject_id=subject_id,
            timeseries_path=temp_path,
            window_length=args.window_length,
            step_size=args.step_size,
            resolution=args.resolution,
            n_iterations=args.n_iterations
        )
        
        results.append(result)
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    # Save results
    save_dynamic_connectivity_results(results, args.output)
    
    # Print summary
    successful = sum(1 for r in results if r['success'])
    logger.info(f"Processed {len(results)} subjects: {successful} successful, {len(results) - successful} failed")
    
    return results

if __name__ == '__main__':
    main()