"""
Connectivity Analysis Module for PROJ-056.

Computes Pearson correlation between ROIs (AAL/Schaefer atlas) and applies Fisher z-transform.
Implements chunked loading/streaming to ensure memory usage remains under 7GB.
"""

import os
import logging
import numpy as np
import pandas as pd
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

# Import project utilities
from utils.logging import get_logger
from utils.memory_monitor import check_memory_limit, get_current_memory_mb, MemoryLimitExceeded
from data.models import ConnectivityMatrix

logger = get_logger(__name__)

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_CHECK_INTERVAL = 100  # Check memory every N rows processed
FISHER_Z_THRESHOLD = 0.9999  # Clamp correlations to avoid log(0)

def fisher_z_transform(r: np.ndarray) -> np.ndarray:
    """
    Apply Fisher's r-to-z transformation to correlation coefficients.
    
    Args:
        r: Array of correlation coefficients (-1 to 1).
        
    Returns:
        Array of Fisher z-transformed values.
    """
    # Clamp values to avoid log(0) or log(negative)
    r_clamped = np.clip(r, -FISHER_Z_THRESHOLD, FISHER_Z_THRESHOLD)
    return 0.5 * np.log((1 + r_clamped) / (1 - r_clamped))

def compute_pearson_correlation_chunked(
    fMRI_data_path: str,
    atlas: str = "schaefer",
    n_rois: Optional[int] = None,
    chunk_size: int = 1000
) -> Tuple[np.ndarray, List[str]]:
    """
    Compute Pearson correlation matrix between ROIs using chunked loading
    to prevent memory overflow.
    
    Args:
        fMRI_data_path: Path to the fMRI data file (NIfTI or CSV).
        atlas: Name of the atlas used (e.g., 'schaefer', 'aal').
        n_rois: Expected number of ROIs. If None, inferred from data.
        chunk_size: Number of time points to process at once.
        
    Returns:
        Tuple of (correlation_matrix, roi_labels).
        
    Raises:
        MemoryLimitExceeded: If memory usage exceeds the limit.
        FileNotFoundError: If the data file is not found.
    """
    logger.info(f"Starting chunked correlation computation for {fMRI_data_path}")
    
    # Load data in chunks if it's a large CSV or NIfTI
    # For this implementation, we assume a CSV format: timepoints x ROIs
    # In a real scenario, this would handle NIfTI loading via nibabel with memory mapping
    try:
        # Check memory before starting
        check_memory_limit(MEMORY_LIMIT_GB)
        
        # Attempt to load data. If it's a CSV, we use pandas with chunking.
        # If it's NIfTI, we would use nibabel and iterate over volumes.
        # For this generic implementation, we handle CSV as the primary case for processed data.
        
        if not os.path.exists(fMRI_data_path):
            raise FileNotFoundError(f"Data file not found: {fMRI_data_path}")
        
        # Determine ROI labels if possible, otherwise generate generic ones
        # In a real pipeline, these would come from the atlas definition
        roi_labels = [f"ROI_{i}" for i in range(n_rois)] if n_rois else []
        
        # Initialize accumulator for correlation calculation
        # We use the Welford's online algorithm or incremental update for large matrices
        # However, for correlation, we need the full time series or sufficient statistics.
        # To stay memory safe, we compute the covariance matrix incrementally.
        
        # Strategy: Compute Sum, SumSq, and SumXY incrementally
        n_timepoints = 0
        sum_x = None
        sum_x_sq = None
        sum_xy = None
        n_cols = None
        
        chunk_iterator = pd.read_csv(fMRI_data_path, chunksize=chunk_size)
        
        first_chunk = True
        
        for chunk in chunk_iterator:
            check_memory_limit(MEMORY_LIMIT_GB)
            
            # Convert to numpy array
            data = chunk.values.astype(np.float64)
            n_rows, n_cols = data.shape
            
            if n_cols == 0:
                continue
                
            if first_chunk:
                n_cols = n_cols
                sum_x = np.zeros(n_cols)
                sum_x_sq = np.zeros(n_cols)
                sum_xy = np.zeros((n_cols, n_cols))
                roi_labels = [f"ROI_{i}" for i in range(n_cols)]
                first_chunk = False
                
            n_timepoints += n_rows
            
            # Update sums
            sum_x += data.sum(axis=0)
            sum_x_sq += (data ** 2).sum(axis=0)
            
            # Update cross-product matrix (outer product sum)
            # sum_xy += data.T @ data
            # To save memory on the outer product if n_cols is large, we do it in chunks if needed
            # But usually n_cols (ROIs) is < 400, so data.T @ data is fine.
            sum_xy += data.T @ data
            
            # Periodic memory check
            if n_timepoints % (chunk_size * MEMORY_CHECK_INTERVAL) == 0:
                current_mem = get_current_memory_mb()
                logger.debug(f"Memory usage after {n_timepoints} timepoints: {current_mem:.2f} MB")

        if n_timepoints == 0 or n_cols is None:
            raise ValueError("No valid data found in the file.")

        # Calculate Means
        mean_x = sum_x / n_timepoints
        
        # Calculate Covariance Matrix
        # Cov(X, Y) = (SumXY - n * meanX * meanY) / (n - 1)
        # We need the outer product of mean_x
        mean_outer = np.outer(mean_x, mean_x)
        
        # Numerator for covariance: SumXY - n * mean_outer
        cov_numerator = sum_xy - n_timepoints * mean_outer
        
        # Denominator: n - 1
        denom = n_timepoints - 1
        
        # Variance (diagonal of covariance)
        var_x = (sum_x_sq - n_timepoints * (mean_x ** 2)) / denom
        
        # Standard Deviation
        std_x = np.sqrt(var_x)
        
        # Correlation Matrix
        # Corr(X, Y) = Cov(X, Y) / (stdX * stdY)
        # Create a denominator matrix: std_x * std_x.T
        std_outer = np.outer(std_x, std_x)
        
        # Avoid division by zero
        std_outer = np.where(std_outer == 0, 1e-10, std_outer)
        
        corr_matrix = cov_numerator / std_outer
        
        # Ensure diagonal is 1.0 (numerical stability)
        np.fill_diagonal(corr_matrix, 1.0)
        
        logger.info(f"Correlation matrix computed successfully. Shape: {corr_matrix.shape}")
        return corr_matrix, roi_labels
        
    except MemoryLimitExceeded:
        logger.error("Memory limit exceeded during correlation computation.")
        raise
    except Exception as e:
        logger.error(f"Error computing correlation: {e}")
        raise

def process_subject_connectivity(
    subject_data_path: str,
    subject_id: str,
    atlas: str = "schaefer",
    output_path: Optional[str] = None
) -> ConnectivityMatrix:
    """
    Process a single subject's fMRI data to generate a ConnectivityMatrix.
    
    Args:
        subject_data_path: Path to the subject's preprocessed fMRI data.
        subject_id: Unique identifier for the subject.
        atlas: Atlas name.
        output_path: Optional path to save the raw correlation matrix.
        
    Returns:
        ConnectivityMatrix object.
    """
    logger.info(f"Processing connectivity for subject {subject_id}")
    
    # Compute correlation matrix
    corr_matrix, roi_labels = compute_pearson_correlation_chunked(
        subject_data_path, 
        atlas=atlas
    )
    
    # Apply Fisher Z-transform
    z_matrix = fisher_z_transform(corr_matrix)
    
    # Create ConnectivityMatrix object
    # The model expects data as a 2D numpy array and metadata
    connectivity_obj = ConnectivityMatrix(
        subject_id=subject_id,
        data=z_matrix,
        roi_labels=roi_labels,
        atlas=atlas,
        method="pearson_fisher_z"
    )
    
    # Validate against schema if possible
    # connectivity_obj.validate() # Assuming validation exists in model
    
    if output_path:
        # Save raw correlation or Z-matrix as CSV for inspection
        df = pd.DataFrame(z_matrix, columns=roi_labels, index=roi_labels)
        df.to_csv(output_path)
        logger.info(f"Saved connectivity matrix to {output_path}")
        
    return connectivity_obj

def generate_group_connectivity_results(
    subjects_dir: str,
    output_csv: str
) -> None:
    """
    Iterate through subject files in a directory, compute connectivity,
    and aggregate results into a single CSV for group analysis.
    
    Args:
        subjects_dir: Directory containing subject data files.
        output_csv: Path to the output CSV file.
    """
    logger.info(f"Generating group connectivity results from {subjects_dir}")
    
    results = []
    subject_files = [f for f in os.listdir(subjects_dir) if f.endswith('.csv')]
    
    if not subject_files:
        logger.warning(f"No CSV files found in {subjects_dir}")
        # Create empty output file with headers
        pd.DataFrame(columns=['subject_id', 'roi_a', 'roi_b', 'z_score', 'correlation']).to_csv(output_csv, index=False)
        return

    for filename in subject_files:
        # Extract subject ID from filename (assumes format: subject_id.csv or similar)
        # Adjust parsing logic based on actual naming convention
        subject_id = Path(filename).stem
        if subject_id.startswith('subject_'):
            subject_id = subject_id.replace('subject_', '')
        
        full_path = os.path.join(subjects_dir, filename)
        
        try:
            # Check memory before processing each subject
            check_memory_limit(MEMORY_LIMIT_GB)
            
            conn_obj = process_subject_connectivity(
                full_path, 
                subject_id=subject_id
            )
            
            # Flatten the matrix to long format for the results CSV
            # Format: subject_id, roi_a, roi_b, z_score, correlation
            n_rois = conn_obj.data.shape[0]
            for i in range(n_rois):
                for j in range(i + 1, n_rois):  # Upper triangle only
                    results.append({
                        'subject_id': subject_id,
                        'roi_a': conn_obj.roi_labels[i],
                        'roi_b': conn_obj.roi_labels[j],
                        'z_score': conn_obj.data[i, j],
                        'correlation': 0.5 * (np.exp(2 * conn_obj.data[i, j]) - 1) / (np.exp(2 * conn_obj.data[i, j]) + 1)
                    })
                    
        except Exception as e:
            logger.error(f"Failed to process subject {subject_id}: {e}")
            continue
    
    # Write results
    if results:
        df_results = pd.DataFrame(results)
        df_results.to_csv(output_csv, index=False)
        logger.info(f"Saved {len(results)} connections to {output_csv}")
    else:
        logger.warning("No valid connections were generated.")
        # Write empty file with headers
        pd.DataFrame(columns=['subject_id', 'roi_a', 'roi_b', 'z_score', 'correlation']).to_csv(output_csv, index=False)

def main():
    """
    Entry point for the connectivity analysis script.
    Expects arguments: --input-dir <path> --output <path>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute functional connectivity matrices.")
    parser.add_argument("--input-dir", required=True, help="Directory containing subject fMRI data.")
    parser.add_argument("--output", required=True, help="Output CSV path for connectivity results.")
    parser.add_argument("--atlas", default="schaefer", help="Atlas name.")
    
    args = parser.parse_args()
    
    try:
        generate_group_connectivity_results(args.input_dir, args.output)
        print(f"Connectivity analysis complete. Results saved to {args.output}")
    except MemoryLimitExceeded as e:
        print(f"ERROR: Memory limit exceeded. {e}")
        exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()