"""
Connectivity module for computing Pearson correlation matrices from preprocessed fMRI time series.

This module implements Task T018: Compute Pearson correlation matrices from preprocessed time series
(retain positive edges only).
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import nibabel as nib
import json

# Import logging utilities from the project's existing API
import sys
from pathlib import Path as LocalPath
sys.path.insert(0, str(LocalPath(__file__).parent.parent))
from utils.logging import get_logger, info, warning, error, debug

# Import config for paths
try:
    from config import ensure_directories, validate_config
except ImportError:
    # Fallback for standalone execution
    from code.config import ensure_directories, validate_config

logger = get_logger(__name__)

def load_time_series_from_processed(
    subject_id: str,
    processed_dir: Path,
    time_series_file_pattern: str = "{subject_id}_preprocessed_ts.csv"
) -> Optional[np.ndarray]:
    """
    Load preprocessed time series for a specific subject from disk.
    
    Args:
        subject_id: The subject identifier (e.g., '100104')
        processed_dir: Path to the data/processed directory
        time_series_file_pattern: Pattern for the time series file name
        
    Returns:
        2D numpy array of shape (n_timepoints, n_regions) or None if not found
    """
    file_path = processed_dir / time_series_file_pattern.format(subject_id=subject_id)
    
    if not file_path.exists():
        error(f"Time series file not found for subject {subject_id}: {file_path}")
        return None
    
    try:
        df = pd.read_csv(file_path)
        # Assume the first column is subject_id and the rest are time series
        # If the file has a header, skip it; if not, assume all columns are data
        if df.columns[0] == 'subject_id' or df.columns[0] == 'timepoint':
            ts_data = df.iloc[:, 1:].values
        else:
            ts_data = df.values
        
        if ts_data.ndim != 2:
            error(f"Unexpected time series shape for {subject_id}: {ts_data.shape}")
            return None
        
        info(f"Loaded time series for {subject_id}: {ts_data.shape}")
        return ts_data
    except Exception as e:
        error(f"Failed to load time series for {subject_id}: {e}")
        return None

def compute_correlation_matrix(
    time_series: np.ndarray,
    method: str = 'pearson'
) -> np.ndarray:
    """
    Compute the correlation matrix from a time series array.
    
    Args:
        time_series: 2D array of shape (n_timepoints, n_regions)
        method: Correlation method ('pearson', 'spearman')
        
    Returns:
        2D correlation matrix of shape (n_regions, n_regions)
    """
    if time_series.ndim != 2:
        raise ValueError(f"Time series must be 2D, got {time_series.ndim}D")
    
    if method == 'pearson':
        corr_matrix = np.corrcoef(time_series, rowvar=False)
    elif method == 'spearman':
        from scipy.stats import spearmanr
        # spearmanr returns a tuple (correlation, p-value)
        # We need to compute it manually or use a different approach
        # For simplicity, we'll use numpy's corrcoef on rank-transformed data
        ranked_data = np.argsort(np.argsort(time_series, axis=0), axis=0)
        corr_matrix = np.corrcoef(ranked_data, rowvar=False)
    else:
        raise ValueError(f"Unsupported correlation method: {method}")
    
    # Handle NaN values that might arise from constant time series
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    return corr_matrix

def retain_positive_edges(
    correlation_matrix: np.ndarray,
    threshold: float = 0.0
) -> np.ndarray:
    """
    Retain only positive edges in the correlation matrix.
    
    Args:
        correlation_matrix: 2D correlation matrix
        threshold: Minimum correlation value to retain (default: 0.0)
        
    Returns:
        Correlation matrix with negative edges set to 0
    """
    if correlation_matrix.ndim != 2 or correlation_matrix.shape[0] != correlation_matrix.shape[1]:
        raise ValueError("Correlation matrix must be square")
    
    positive_matrix = np.where(correlation_matrix > threshold, correlation_matrix, 0.0)
    
    return positive_matrix

def compute_connectivity_for_subject(
    subject_id: str,
    processed_dir: Path,
    output_dir: Path,
    method: str = 'pearson',
    retain_positive: bool = True,
    time_series_file_pattern: str = "{subject_id}_preprocessed_ts.csv"
) -> Optional[Tuple[np.ndarray, Path]]:
    """
    Compute connectivity matrix for a single subject.
    
    Args:
        subject_id: Subject identifier
        processed_dir: Path to processed data directory
        output_dir: Path to save results
        method: Correlation method
        retain_positive: Whether to retain only positive edges
        time_series_file_pattern: Pattern for time series files
        
    Returns:
        Tuple of (correlation_matrix, output_path) or None if failed
    """
    # Load time series
    time_series = load_time_series_from_processed(
        subject_id, processed_dir, time_series_file_pattern
    )
    
    if time_series is None:
        return None
    
    # Compute correlation matrix
    try:
        corr_matrix = compute_correlation_matrix(time_series, method)
        info(f"Computed correlation matrix for {subject_id}: {corr_matrix.shape}")
    except Exception as e:
        error(f"Failed to compute correlation for {subject_id}: {e}")
        return None
    
    # Retain positive edges if requested
    if retain_positive:
        corr_matrix = retain_positive_edges(corr_matrix)
        info(f"Retained positive edges for {subject_id}")
    
    # Save the matrix
    output_file = output_dir / f"{subject_id}_connectivity_matrix.npy"
    try:
        np.save(output_file, corr_matrix)
        info(f"Saved connectivity matrix to {output_file}")
        
        # Also save as CSV for easier inspection
        csv_file = output_dir / f"{subject_id}_connectivity_matrix.csv"
        pd.DataFrame(corr_matrix).to_csv(csv_file, index=False, header=False)
        info(f"Saved connectivity matrix CSV to {csv_file}")
        
        return corr_matrix, output_file
    except Exception as e:
        error(f"Failed to save connectivity matrix for {subject_id}: {e}")
        return None

def compute_all_connectivity(
    subject_ids: List[str],
    processed_dir: Path,
    output_dir: Path,
    method: str = 'pearson',
    retain_positive: bool = True,
    time_series_file_pattern: str = "{subject_id}_preprocessed_ts.csv"
) -> Dict[str, Dict[str, Union[str, int]]]:
    """
    Compute connectivity matrices for all subjects.
    
    Args:
        subject_ids: List of subject identifiers
        processed_dir: Path to processed data directory
        output_dir: Path to save results
        method: Correlation method
        retain_positive: Whether to retain only positive edges
        time_series_file_pattern: Pattern for time series files
        
    Returns:
        Dictionary mapping subject_id to metadata (status, file_path, shape)
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    info(f"Output directory created/verified: {output_dir}")
    
    results = {}
    success_count = 0
    failure_count = 0
    
    for subject_id in subject_ids:
        result = compute_connectivity_for_subject(
            subject_id,
            processed_dir,
            output_dir,
            method,
            retain_positive,
            time_series_file_pattern
        )
        
        if result is not None:
            corr_matrix, output_path = result
            results[subject_id] = {
                'status': 'success',
                'file_path': str(output_path),
                'shape': list(corr_matrix.shape),
                'n_edges': int(np.sum(corr_matrix > 0))
            }
            success_count += 1
        else:
            results[subject_id] = {
                'status': 'failed',
                'file_path': None,
                'shape': None,
                'n_edges': None
            }
            failure_count += 1
    
    info(f"Connectivity computation complete: {success_count} succeeded, {failure_count} failed")
    return results

def main():
    """
    Main entry point for computing connectivity matrices.
    
    This function:
    1. Loads the list of subject IDs from the processed data directory
    2. Computes Pearson correlation matrices for each subject
    3. Retains only positive edges
    4. Saves the matrices to data/results/connectivity/
    """
    logger.info("Starting connectivity matrix computation (Task T018)")
    
    # Load configuration
    try:
        validate_config()
    except Exception as e:
        error(f"Failed to validate config: {e}")
        return 1
    
    # Define paths
    processed_dir = Path("data/processed")
    output_dir = Path("data/results/connectivity")
    
    # Ensure directories exist
    ensure_directories()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get list of subjects from processed directory
    subject_files = list(processed_dir.glob("*_preprocessed_ts.csv"))
    if not subject_files:
        error(f"No preprocessed time series files found in {processed_dir}")
        return 1
    
    # Extract subject IDs from file names
    subject_ids = []
    for file_path in subject_files:
        # Assuming file name format: {subject_id}_preprocessed_ts.csv
        subject_id = file_path.stem.replace("_preprocessed_ts", "")
        subject_ids.append(subject_id)
    
    info(f"Found {len(subject_ids)} subjects to process")
    
    # Compute connectivity for all subjects
    results = compute_all_connectivity(
        subject_ids=subject_ids,
        processed_dir=processed_dir,
        output_dir=output_dir,
        method='pearson',
        retain_positive=True
    )
    
    # Save summary results
    summary_file = output_dir / "connectivity_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    info(f"Successfully computed connectivity for {success_count}/{len(subject_ids)} subjects")
    info(f"Summary saved to {summary_file}")
    
    return 0

if __name__ == "__main__":
    exit(main())
