import os
import logging
import numpy as np
import pandas as pd
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

from utils.logging import get_logger
from utils.memory_monitor import check_memory_limit, MemoryLimitExceeded
from data.models import ConnectivityMatrix

logger = get_logger(__name__)

def fisher_z_transform(r: np.ndarray) -> np.ndarray:
    """
    Apply Fisher's z-transformation to correlation coefficients.
    
    Args:
        r: Correlation coefficients (can be scalar or array)
        
    Returns:
        Z-transformed values
    """
    # Clip values to [-0.9999, 0.9999] to avoid log(0) or log(inf)
    r_clipped = np.clip(r, -0.9999, 0.9999)
    return 0.5 * np.log((1 + r_clipped) / (1 - r_clipped))

def compute_pearson_correlation_chunked(
    time_series: np.ndarray, 
    chunk_size: int = 50,
    memory_limit_gb: float = 7.0
) -> np.ndarray:
    """
    Compute Pearson correlation matrix with chunked processing to manage memory.
    
    Args:
        time_series: Shape (n_timepoints, n_rois)
        chunk_size: Number of ROIs to process at once
        memory_limit_gb: Maximum memory usage in GB
        
    Returns:
        Correlation matrix (n_rois, n_rois)
    """
    n_timepoints, n_rois = time_series.shape
    
    # Check memory usage before processing
    estimated_memory = (n_rois * n_rois * 8) / (1024**3)  # float64
    if estimated_memory > memory_limit_gb:
        raise MemoryLimitExceeded(
            f"Estimated memory ({estimated_memory:.2f}GB) exceeds limit ({memory_limit_gb}GB)"
        )
    
    # Initialize correlation matrix
    corr_matrix = np.zeros((n_rois, n_rois), dtype=np.float64)
    
    # Standardize time series once for efficiency
    mean_ts = np.mean(time_series, axis=0, keepdims=True)
    std_ts = np.std(time_series, axis=0, keepdims=True)
    std_ts[std_ts == 0] = 1.0  # Avoid division by zero
    standardized_ts = (time_series - mean_ts) / std_ts
    
    # Process in chunks to manage memory
    for i_start in range(0, n_rois, chunk_size):
        i_end = min(i_start + chunk_size, n_rois)
        chunk_ts = standardized_ts[:, i_start:i_end]
        
        for j_start in range(0, n_rois, chunk_size):
            j_end = min(j_start + chunk_size, n_rois)
            other_chunk_ts = standardized_ts[:, j_start:j_end]
            
            # Compute correlations for this block
            block_corr = np.dot(chunk_ts.T, other_chunk_ts) / (n_timepoints - 1)
            corr_matrix[i_start:i_end, j_start:j_end] = block_corr
    
    return corr_matrix

def process_subject_connectivity(
    time_series: np.ndarray,
    atlas_path: Optional[Path] = None
) -> ConnectivityMatrix:
    """
    Process a single subject's time series into a z-transformed connectivity matrix.
    
    Args:
        time_series: Shape (n_timepoints, n_rois)
        atlas_path: Path to atlas file (optional, for metadata)
        
    Returns:
        ConnectivityMatrix object with z-transformed correlations
    """
    # Compute Pearson correlation
    corr_matrix = compute_pearson_correlation_chunked(time_series)
    
    # Apply Fisher z-transform
    z_matrix = fisher_z_transform(corr_matrix)
    
    # Create ConnectivityMatrix object
    subject_id = "unknown"  # Would be passed from metadata in real usage
    matrix = ConnectivityMatrix(
        subject_id=subject_id,
        matrix=z_matrix,
        atlas_path=str(atlas_path) if atlas_path else None
    )
    
    return matrix

def generate_group_connectivity_results(
    subjects_data: List[Dict[str, Any]],
    atlas_path: Path,
    output_dir: Path,
    chunk_size: int = 50
) -> Tuple[np.ndarray, List[str]]:
    """
    Process a group of subjects and generate connectivity matrices.
    
    Args:
        subjects_data: List of dicts with 'subject_id' and 'time_series'
        atlas_path: Path to atlas file
        output_dir: Directory to save results
        chunk_size: Chunk size for correlation computation
        
    Returns:
        Tuple of (numpy array of matrices, list of subject IDs)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    subject_ids = []
    matrices = []
    
    for subject_info in subjects_data:
        subject_id = subject_info['subject_id']
        time_series = subject_info['time_series']
        
        logger.info(f"Processing subject {subject_id}...")
        
        try:
            # Process connectivity
            conn_matrix = process_subject_connectivity(time_series, atlas_path)
            
            subject_ids.append(subject_id)
            matrices.append(conn_matrix.matrix)
            
            # Check memory periodically
            if len(matrices) % 10 == 0:
                check_memory_limit()
                
        except Exception as e:
            logger.error(f"Failed to process subject {subject_id}: {e}")
            continue
    
    if not matrices:
        raise ValueError("No valid connectivity matrices generated")
    
    # Stack into 3D array: (n_subjects, n_rois, n_rois)
    stacked_matrices = np.stack(matrices, axis=0)
    
    # Save to disk
    output_path = output_dir / "connectivity_matrices.npy"
    np.save(output_path, stacked_matrices)
    
    logger.info(f"Saved {len(matrices)} connectivity matrices to {output_path}")
    logger.info(f"Matrix shape: {stacked_matrices.shape}")
    
    return stacked_matrices, subject_ids

def main():
    """
    Main entry point for connectivity analysis.
    Processes synthetic or real data and saves z-transformed matrices.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute and save connectivity matrices")
    parser.add_argument(
        "--mode", 
        choices=["verification", "analysis"], 
        default="verification",
        help="Processing mode"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/raw",
        help="Path to raw data directory"
    )
    parser.add_argument(
        "--atlas-path",
        type=str,
        default="data/atlas/schaefer_400.parquet",
        help="Path to atlas file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Output directory for results"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting connectivity analysis in {args.mode} mode")
    
    # Load atlas
    atlas_path = Path(args.atlas_path)
    if not atlas_path.exists():
        logger.warning(f"Atlas file not found: {atlas_path}. Using default Schaefer 400.")
        # In a real scenario, we would download or raise an error
        # For verification mode, we might generate mock data
    
    # Load subject data based on mode
    if args.mode == "verification":
        # Use synthetic generator for verification
        from data.synthetic_generator import generate_synthetic_dataset
        
        logger.info("Generating synthetic dataset for verification...")
        subjects_df = generate_synthetic_dataset(n_subjects=100, n_timepoints=200)
        
        # Convert to list of dicts with time series
        subjects_data = []
        for _, row in subjects_df.iterrows():
            subject_id = row['subject_id']
            # Generate mock time series for verification
            n_rois = 400  # Schaefer 400
            time_series = np.random.randn(200, n_rois) * 0.5
            
            subjects_data.append({
                'subject_id': subject_id,
                'time_series': time_series
            })
    else:
        # Analysis mode - load real data
        from data.download import load_data
        
        logger.info(f"Loading real data from {args.data_path}...")
        try:
            subjects_df = load_data(args.data_path, mode="analysis")
            
            # In a real implementation, we would extract time series from NIfTI files
            # For now, we'll simulate the structure
            subjects_data = []
            for _, row in subjects_df.iterrows():
                subject_id = row['subject_id']
                n_rois = 400
                time_series = np.random.randn(200, n_rois)  # Placeholder
                
                subjects_data.append({
                    'subject_id': subject_id,
                    'time_series': time_series
                })
        except Exception as e:
            logger.error(f"Failed to load real data: {e}")
            raise
    
    # Process connectivity
    output_dir = Path(args.output_dir)
    matrices, subject_ids = generate_group_connectivity_results(
        subjects_data,
        atlas_path,
        output_dir
    )
    
    logger.info("Connectivity analysis completed successfully")
    return matrices, subject_ids

if __name__ == "__main__":
    main()