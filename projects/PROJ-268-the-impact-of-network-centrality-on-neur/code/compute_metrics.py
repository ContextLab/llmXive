import os
import sys
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path

# Import existing utilities and error handlers
from utils import load_and_validate_subject_matrices, check_disk_usage
from error_handling import raise_data_gap_error, check_and_raise_storage_limit
from logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

def compute_functional_synchrony(fc_matrix: np.ndarray) -> float:
    """
    Compute the mean absolute correlation (functional synchrony) from an FC matrix.
    
    Args:
        fc_matrix: 2D numpy array representing the functional connectivity matrix.
        
    Returns:
        float: The mean absolute correlation value.
    """
    if fc_matrix.size == 0:
        return 0.0
    
    # Mask diagonal to avoid self-correlation (which is 1.0)
    n = fc_matrix.shape[0]
    mask = ~np.eye(n, dtype=bool)
    
    # Calculate mean of absolute upper triangle values
    # We use upper triangle to avoid double counting
    upper_tri = fc_matrix[mask]
    mean_abs_corr = np.mean(np.abs(upper_tri))
    
    return float(mean_abs_corr)

def compute_all_metrics(sc_matrix: np.ndarray) -> dict:
    """
    Compute node-level centrality metrics (degree, betweenness, eigenvector) 
    from a structural connectivity matrix.
    
    Args:
        sc_matrix: 2D numpy array representing the structural connectivity matrix.
        
    Returns:
        dict: Dictionary containing degree_centrality, betweenness_centrality, 
              and eigenvector_centrality as lists of floats.
    """
    if sc_matrix.size == 0:
        return {
            'degree_centrality': [],
            'betweenness_centrality': [],
            'eigenvector_centrality': []
        }
    
    # Create a NetworkX graph from the adjacency matrix
    # Use the matrix directly as edge weights
    G = nx.from_numpy_array(sc_matrix)
    
    # Compute centrality metrics
    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    
    try:
        eigenvector_centrality = nx.eigenvector_centrality(G, max_iter=1000)
    except nx.PowerIterationFailedConvergence:
        # Fallback to a simpler metric if convergence fails
        logger.warning("Eigenvector centrality failed to converge, using degree centrality as fallback")
        eigenvector_centrality = degree_centrality
    
    # Sort by node index to ensure consistent ordering
    n_nodes = len(degree_centrality)
    degree_list = [degree_centrality[i] for i in range(n_nodes)]
    betweenness_list = [betweenness_centrality[i] for i in range(n_nodes)]
    eigenvector_list = [eigenvector_centrality.get(i, 0.0) for i in range(n_nodes)]
    
    return {
        'degree_centrality': degree_list,
        'betweenness_centrality': betweenness_list,
        'eigenvector_centrality': eigenvector_list
    }

def process_all_subjects(subject_ids: list, data_dir: Path) -> dict:
    """
    Process all subjects to compute centrality and synchrony metrics.
    
    Args:
        subject_ids: List of subject IDs to process.
        data_dir: Path to the directory containing processed data.
        
    Returns:
        dict: Dictionary mapping subject_id to a dict containing 
              'centrality' (dict) and 'synchrony' (float).
    """
    results = {}
    
    # Check disk usage before processing
    check_disk_usage()
    
    for subject_id in subject_ids:
        logger.info(f"Processing subject: {subject_id}")
        
        try:
            # Load and validate matrices for this subject
            sc_matrix, fc_matrix = load_and_validate_subject_matrices(
                subject_id, data_dir
            )
            
            # Compute centrality metrics from structural matrix
            centrality_metrics = compute_all_metrics(sc_matrix)
            
            # Compute functional synchrony from functional matrix
            synchrony_value = compute_functional_synchrony(fc_matrix)
            
            # Store results
            results[subject_id] = {
                'centrality': centrality_metrics,
                'synchrony': synchrony_value
            }
            
            logger.info(f"Successfully processed subject {subject_id}")
            
        except Exception as e:
            logger.error(f"Failed to process subject {subject_id}: {str(e)}")
            # Continue with next subject rather than halting the entire pipeline
            continue
    
    # Check storage limit after processing
    check_and_raise_storage_limit()
    
    if not results:
        raise_data_gap_error("No valid subjects could be processed.")
        
    return results

def main():
    """
    Main entry point for computing metrics across all subjects.
    """
    # Define paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "processed"
    
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        raise_data_gap_error("Processed data directory not found.")
    
    # Get list of subject files
    # Assuming files are named centrality_<subject_id>.csv or similar pattern
    # We need to identify subjects from the data directory
    subject_files = list(data_dir.glob("sc_*.npy")) or list(data_dir.glob("fc_*.npy"))
    
    if not subject_files:
        # Try to find subjects from parquet or other sources
        # For now, we'll assume subjects are identified by the pattern in the directory
        logger.warning("No subject files found in expected format. Attempting to infer subjects...")
        # This is a fallback; in a real scenario, we'd have a manifest or explicit list
        # For this implementation, we'll try to load from the parquet dataset if available
        # But since T012 handles the download, we assume data is already in data/processed
        raise_data_gap_error("No subject data found in processed directory.")
    
    # Extract subject IDs from file names
    # Assuming format: sc_<subject_id>.npy or fc_<subject_id>.npy
    subject_ids = set()
    for file in subject_files:
        # Extract subject ID from filename
        # e.g., "sc_sub-001.npy" -> "sub-001"
        parts = file.stem.split("_")
        if len(parts) >= 2:
            subject_id = parts[1]
            subject_ids.add(subject_id)
    
    subject_ids = sorted(list(subject_ids))
    logger.info(f"Found {len(subject_ids)} subjects to process: {subject_ids}")
    
    # Process all subjects
    results = process_all_subjects(subject_ids, data_dir)
    
    # Log summary
    logger.info(f"Processed {len(results)} subjects successfully")
    
    # Return results for further processing (e.g., saving to files in T023)
    return results

if __name__ == "__main__":
    main()