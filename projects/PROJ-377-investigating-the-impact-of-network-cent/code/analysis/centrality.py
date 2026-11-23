"""
Centrality analysis module for network centrality calculations.
Implements float32 optimization and batch processing.
"""
import os
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

from utils.config import get_centrality_config, get_output_paths
from analysis.optimization_utils import (
    ensure_float32,
    optimize_memory_usage,
    load_connectivity_matrix_optimized,
    batch_process_subjects,
    validate_float32_compliance
)

logger = logging.getLogger(__name__)

def get_subject_list_from_directory(data_dir: str) -> List[str]:
    """
    Get list of subject IDs from the data directory.
    
    Args:
        data_dir: Path to the data directory containing subject folders
        
    Returns:
        List of subject IDs
    """
    path = Path(data_dir)
    if not path.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return []
        
    subject_dirs = [d for d in path.iterdir() if d.is_dir() and d.name.startswith('sub-')]
    subject_ids = [d.name.replace('sub-', '') for d in subject_dirs]
    logger.info(f"Found {len(subject_ids)} subjects in {data_dir}")
    return sorted(subject_ids)

def load_connectivity_matrix(subject_id: str, data_dir: str) -> np.ndarray:
    """
    Load connectivity matrix for a subject.
    
    Args:
        subject_id: Subject ID
        data_dir: Path to data directory
        
    Returns:
        Connectivity matrix as float32 numpy array
    """
    # Construct path to connectivity matrix
    matrix_path = Path(data_dir) / f"sub-{subject_id}" / "connectivity_matrix.npy"
    
    if not matrix_path.exists():
        logger.warning(f"Connectivity matrix not found for subject {subject_id}")
        return None
        
    # Load with optimization
    matrix = load_connectivity_matrix_optimized(str(matrix_path))
    return matrix

def extract_connectivity_matrix_for_subject(
    subject_id: str,
    fmriprep_dir: str,
    atlas_file: str
) -> np.ndarray:
    """
    Extract functional connectivity matrix for a subject from preprocessed fMRI data.
    
    Args:
        subject_id: Subject ID
        fmriprep_dir: Path to fMRIPrep output directory
        atlas_file: Path to atlas file
        
    Returns:
        Connectivity matrix as float32 numpy array
    """
    from nilearn.connectome import ConnectivityMeasure
    from nilearn import datasets
    from nilearn.image import load_img
    
    # Load atlas
    atlas_img = load_img(atlas_file)
    
    # Find preprocessed functional image
    func_path = Path(fmriprep_dir) / f"sub-{subject_id}" / "func"
    func_files = list(func_path.glob("*space-MNI_desc-preproc_bold.nii.gz"))
    
    if not func_files:
        logger.warning(f"No preprocessed functional image found for subject {subject_id}")
        return None
        
    func_img = load_img(str(func_files[0]))
    
    # Extract time series
    connectivity_measure = ConnectivityMeasure(
        kind='correlation',
        standardize=True
    )
    
    time_series = connectivity_measure.fit_transform([func_img], atlas_img=atlas_img)
    
    # Convert to float32 and return
    matrix = ensure_float32(time_series[0])
    logger.debug(f"Extracted connectivity matrix for {subject_id}: shape {matrix.shape}")
    return matrix

def compute_centrality_metrics(matrix: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Compute centrality metrics from a connectivity matrix.
    
    Args:
        matrix: Connectivity matrix (float32)
        
    Returns:
        Dictionary with centrality metrics
    """
    # Create graph from matrix
    G = nx.from_numpy_array(matrix)
    
    # Compute metrics
    degree_centrality = np.array(list(nx.degree_centrality(G).values()))
    betweenness_centrality = np.array(list(nx.betweenness_centrality(G).values()))
    eigenvector_centrality = np.array(list(nx.eigenvector_centrality(G).values()))
    
    # Ensure float32
    metrics = {
        'degree': ensure_float32(degree_centrality),
        'betweenness': ensure_float32(betweenness_centrality),
        'eigenvector': ensure_float32(eigenvector_centrality)
    }
    
    return metrics

def process_subject(subject_id: str, data_dir: str, atlas_file: str) -> Optional[Dict]:
    """
    Process a single subject: load matrix and compute centrality metrics.
    
    Args:
        subject_id: Subject ID
        data_dir: Path to data directory
        atlas_file: Path to atlas file
        
    Returns:
        Dictionary with subject metrics or None if failed
    """
    try:
        # Load connectivity matrix
        matrix = load_connectivity_matrix(subject_id, data_dir)
        
        if matrix is None:
            logger.warning(f"Could not load matrix for {subject_id}")
            return None
            
        # Compute centrality metrics
        metrics = compute_centrality_metrics(matrix)
        
        # Get region names from atlas
        # Assuming AAL3 atlas with ~90 regions
        n_regions = matrix.shape[0]
        region_names = [f"Region_{i}" for i in range(n_regions)]
        
        # Create results
        results = []
        for i in range(n_regions):
            results.append({
                'subject_id': subject_id,
                'region_id': i,
                'region_name': region_names[i],
                'degree': float(metrics['degree'][i]),
                'betweenness': float(metrics['betweenness'][i]),
                'eigenvector': float(metrics['eigenvector'][i])
            })
            
        return results
        
    except Exception as e:
        logger.error(f"Error processing subject {subject_id}: {e}")
        return None

def calculate_mean_fd(subject_id: str, fmriprep_dir: str) -> Optional[float]:
    """
    Calculate mean Framewise Displacement for a subject.
    
    Args:
        subject_id: Subject ID
        fmriprep_dir: Path to fMRIPrep output directory
        
    Returns:
        Mean FD value or None if failed
    """
    confounds_path = Path(fmriprep_dir) / f"sub-{subject_id}" / "func" / "desc-confounds_timeseries.tsv"
    
    if not confounds_path.exists():
        logger.warning(f"Confounds file not found for {subject_id}")
        return None
        
    try:
        confounds = pd.read_csv(confounds_path, sep='\t')
        if 'framewise_displacement' in confounds.columns:
            mean_fd = confounds['framewise_displacement'].mean()
            return float(mean_fd)
        else:
            logger.warning(f"framewise_displacement column not found for {subject_id}")
            return None
    except Exception as e:
        logger.error(f"Error calculating FD for {subject_id}: {e}")
        return None

def run_centrality_analysis(
    data_dir: str,
    fmriprep_dir: str,
    atlas_file: str,
    output_file: str
) -> pd.DataFrame:
    """
    Run centrality analysis for all subjects.
    
    Args:
        data_dir: Path to data directory
        fmriprep_dir: Path to fMRIPrep output directory
        atlas_file: Path to atlas file
        output_file: Path to output CSV file
        
    Returns:
        DataFrame with centrality metrics
    """
    config = get_centrality_config()
    output_paths = get_output_paths()
    
    # Get subject list
    subject_ids = get_subject_list_from_directory(data_dir)
    
    if not subject_ids:
        logger.error("No subjects found")
        return pd.DataFrame()
        
    logger.info(f"Processing {len(subject_ids)} subjects with batch size {config.batch_size}")
    
    # Process subjects in batches
    all_results = []
    
    for i in range(0, len(subject_ids), config.batch_size):
        batch_ids = subject_ids[i:i+config.batch_size]
        logger.info(f"Processing batch {i//config.batch_size + 1}: {len(batch_ids)} subjects")
        
        for subject_id in batch_ids:
            result = process_subject(subject_id, data_dir, atlas_file)
            if result:
                all_results.extend(result)
                
        # Garbage collection
        import gc
        gc.collect()
        
    # Create DataFrame and optimize memory
    df = pd.DataFrame(all_results)
    df = optimize_memory_usage(df)
    
    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    logger.info(f"Saved centrality metrics to {output_file}")
    
    return df

def main():
    """Main entry point for centrality analysis."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    logger.info("Centrality analysis module loaded")
    logger.info("Functions available: get_subject_list_from_directory, load_connectivity_matrix, "
               "extract_connectivity_matrix_for_subject, compute_centrality_metrics, "
               "process_subject, calculate_mean_fd, run_centrality_analysis")

if __name__ == "__main__":
    main()
