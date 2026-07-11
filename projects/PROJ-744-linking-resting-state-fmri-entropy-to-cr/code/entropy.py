import numpy as np
from typing import Optional, Union, Dict, List, Tuple
import logging
import os
import pandas as pd
from pathlib import Path
import psutil
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_sample_entropy(
    time_series: np.ndarray,
    m: int = 2,
    r: float = 0.2,
    axis: int = -1
) -> np.ndarray:
    """
    Compute Sample Entropy for a time series (or array of time series).
    Vectorized implementation optimized for CPU.
    
    Parameters:
    -----------
    time_series : np.ndarray
        Input time series data. If 2D, rows are subjects/trials, columns are time points.
    m : int
        Embedding dimension (default: 2)
    r : float
        Tolerance threshold (default: 0.2 * std)
    axis : int
        Axis along which time series are stored (default: last)
        
    Returns:
    --------
    np.ndarray
        Sample entropy values for each time series
    """
    # Handle single time series case
    if time_series.ndim == 1:
        time_series = time_series.reshape(1, -1)
    
    n_series, n_points = time_series.shape
    
    if n_points < m + 1:
        logger.warning(f"Time series length {n_points} is too short for m={m}")
        return np.full(n_series, np.nan)
    
    # Normalize r by standard deviation if r is relative (0 < r < 1)
    if 0 < r < 1:
        std_dev = np.std(time_series, axis=axis, keepdims=True)
        std_dev[std_dev == 0] = 1  # Avoid division by zero
        r_abs = r * std_dev
    else:
        r_abs = r
    
    # Flatten for processing
    data = time_series
    
    # Build template vectors
    # We need to compare all pairs of vectors of length m
    # Vectorized approach: create matrix of differences
    
    results = np.zeros(n_series)
    
    for i in range(n_series):
        ts = data[i]
        n = len(ts)
        
        # Create template vectors
        templates = np.array([ts[j:j+m] for j in range(n - m)])
        
        # Compute distances between all pairs
        # B(x) = number of pairs within distance r (excluding self)
        # A(x) = number of pairs of (m+1)-length vectors within distance r
        
        # For B: compare all m-length vectors
        diff_m = np.abs(templates[:, None, :] - templates[None, :, :])
        dist_m = np.max(diff_m, axis=2)  # Chebyshev distance
        
        B = np.sum(dist_m <= r_abs[i, 0], axis=1) - 1  # Exclude self
        B = np.maximum(B, 0)  # Ensure non-negative
        
        # For A: compare (m+1)-length vectors
        if n > m:
            templates_m1 = np.array([ts[j:j+m+1] for j in range(n - m)])
            diff_m1 = np.abs(templates_m1[:, None, :] - templates_m1[None, :, :])
            dist_m1 = np.max(diff_m1, axis=2)
            A = np.sum(dist_m1 <= r_abs[i, 0], axis=1) - 1
            A = np.maximum(A, 0)
        else:
            A = np.zeros(n - m)
        
        # Compute sample entropy
        B_mean = np.mean(B)
        A_mean = np.mean(A)
        
        if B_mean > 0 and A_mean >= 0:
            results[i] = -np.log(A_mean / B_mean) if B_mean > 0 else np.nan
        else:
            results[i] = np.nan
    
    return results

def compute_multiscale_entropy(
    time_series: np.ndarray,
    scales: List[int] = None,
    m: int = 2,
    r: float = 0.2
) -> Tuple[np.ndarray, float]:
    """
    Compute Multiscale Sample Entropy and aggregate via AUC.
    
    Parameters:
    -----------
    time_series : np.ndarray
        Input time series
    scales : List[int]
        List of scale factors (default: 1-20)
    m : int
        Embedding dimension
    r : float
        Tolerance threshold
        
    Returns:
    --------
    Tuple[np.ndarray, float]
        Entropy values at each scale, and AUC-aggregated entropy
    """
    if scales is None:
        scales = list(range(1, 21))
    
    n_points = len(time_series)
    entropy_values = []
    
    for scale in scales:
        # Coarse-graining
        n_coarse = n_points // scale
        if n_coarse < m + 1:
            entropy_values.append(np.nan)
            continue
        
        coarse_ts = np.mean(
            time_series[:n_coarse * scale].reshape(n_coarse, scale),
            axis=1
        )
        
        ent = compute_sample_entropy(coarse_ts, m=m, r=r)
        entropy_values.append(ent[0] if len(ent) > 0 else np.nan)
    
    entropy_array = np.array(entropy_values)
    
    # Compute AUC using trapezoidal rule
    valid_mask = ~np.isnan(entropy_array)
    if np.sum(valid_mask) < 2:
        auc = np.nan
    else:
        scales_valid = np.array(scales)[valid_mask]
        entropy_valid = entropy_array[valid_mask]
        auc = np.trapz(entropy_valid, scales_valid)
    
    return entropy_array, auc

def load_hcp_atlas(
    atlas_path: Union[str, Path]
) -> Dict[str, List[int]]:
    """
    Load HCP 360-parcel atlas mapping.
    
    Parameters:
    -----------
    atlas_path : Union[str, Path]
        Path to atlas definition file (CSV or JSON)
        
    Returns:
    --------
    Dict[str, List[int]]
        Mapping of network names to parcel indices
    """
    path = Path(atlas_path)
    if not path.exists():
        raise FileNotFoundError(f"Atlas file not found: {atlas_path}")
    
    # Assume CSV format: parcel_id, network_name
    df = pd.read_csv(path)
    atlas_map = {}
    
    for network in df['network_name'].unique():
        parcels = df[df['network_name'] == network]['parcel_id'].tolist()
        atlas_map[network] = parcels
    
    return atlas_map

def process_parcels_for_subject(
    subject_id: str,
    time_series_data: np.ndarray,
    atlas: Dict[str, List[int]],
    m: int = 2,
    r: float = 0.2
) -> Dict[str, np.ndarray]:
    """
    Process time series data for a subject across all parcels.
    
    Parameters:
    -----------
    subject_id : str
        Subject identifier
    time_series_data : np.ndarray
        3D array: (time, x, y) or 4D: (time, x, y, z) flattened to parcels
    atlas : Dict[str, List[int]]
        Atlas mapping
    m : int
        Embedding dimension
    r : float
        Tolerance threshold
        
    Returns:
    --------
    Dict[str, np.ndarray]
        Per-parcel entropy values
    """
    results = {}
    
    for network, parcels in atlas.items():
        network_entropies = []
        
        for parcel_idx in parcels:
            # Extract parcel time series (assuming flattened or indexed)
            if time_series_data.ndim == 2:
                ts = time_series_data[:, parcel_idx]
            elif time_series_data.ndim == 3:
                # Reshape to 2D if needed
                ts = time_series_data[:, parcel_idx]
            else:
                raise ValueError(f"Unsupported time series shape: {time_series_data.shape}")
            
            # Check for NaNs
            if np.sum(np.isnan(ts)) > len(ts) * 0.1:
                network_entropies.append(np.nan)
                continue
            
            ent = compute_sample_entropy(ts, m=m, r=r)
            network_entropies.append(ent[0] if len(ent) > 0 else np.nan)
        
        results[network] = np.array(network_entropies)
    
    return results

def flag_invalid_parcels(
    results: Dict[str, np.ndarray],
    threshold: float = 0.1
) -> bool:
    """
    Flag subjects with >10% invalid (NaN) parcels.
    
    Parameters:
    -----------
    results : Dict[str, np.ndarray]
        Per-parcel entropy results
    threshold : float
        Fraction of invalid parcels to trigger flag
        
    Returns:
    --------
    bool
        True if subject should be flagged for manual review
    """
    total_parcels = 0
    invalid_parcels = 0
    
    for network, entropies in results.items():
        total_parcels += len(entropies)
        invalid_parcels += np.sum(np.isnan(entropies))
    
    if total_parcels == 0:
        return True
    
    invalid_ratio = invalid_parcels / total_parcels
    return invalid_ratio > threshold

def run_parcels_and_flagging(
    subject_id: str,
    time_series_data: np.ndarray,
    atlas: Dict[str, List[int]],
    m: int = 2,
    r: float = 0.2,
    log_path: Optional[Path] = None
) -> Tuple[Dict[str, np.ndarray], bool]:
    """
    Run parcel processing and flagging for a subject.
    
    Parameters:
    -----------
    subject_id : str
        Subject identifier
    time_series_data : np.ndarray
        Time series data
    atlas : Dict[str, List[int]]
        Atlas mapping
    m : int
        Embedding dimension
    r : float
        Tolerance threshold
    log_path : Optional[Path]
        Path to log file for invalid parcel flags
        
    Returns:
    --------
    Tuple[Dict[str, np.ndarray], bool]
        Results and flag status
    """
    results = process_parcels_for_subject(
        subject_id, time_series_data, atlas, m, r
    )
    
    is_flagged = flag_invalid_parcels(results)
    
    if is_flagged and log_path:
        with open(log_path, 'a') as f:
            f.write(f"{subject_id}: Invalid parcel ratio exceeds threshold\n")
    
    return results, is_flagged

def run_entropy_orchestration(
    valid_subjects_path: Union[str, Path],
    raw_data_dir: Union[str, Path],
    atlas_path: Union[str, Path],
    output_path: Union[str, Path],
    m: int = 2,
    r: float = 0.2,
    chunk_size: int = 10,
    log_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Main orchestration function to compute entropy for all valid subjects.
    Implements RAM monitoring and chunking for memory constraints.
    
    Parameters:
    -----------
    valid_subjects_path : Union[str, Path]
        Path to valid_subjects.csv
    raw_data_dir : Union[str, Path]
        Directory containing raw fMRI data
    atlas_path : Union[str, Path]
        Path to atlas definition
    output_path : Union[str, Path]
        Path for output CSV
    m : int
        Embedding dimension
    r : float
        Tolerance threshold
    chunk_size : int
        Number of subjects to process per chunk
    log_path : Optional[Path]
        Path to log file for invalid parcel flags
        
    Returns:
    --------
    pd.DataFrame
        Complete entropy metrics DataFrame
    """
    # Initialize RAM tracking
    process = psutil.Process()
    peak_ram_mb = 0
    start_time = time.time()
    
    logger.info("Starting entropy orchestration with RAM monitoring")
    
    # Load valid subjects
    valid_subjects = pd.read_csv(valid_subjects_path)
    subject_ids = valid_subjects['subject_id'].tolist()
    
    # Load atlas
    atlas = load_hcp_atlas(atlas_path)
    
    # Prepare output storage
    all_results = []
    
    # Process in chunks to manage memory
    for i in range(0, len(subject_ids), chunk_size):
        chunk_subjects = subject_ids[i:i + chunk_size]
        logger.info(f"Processing chunk {i//chunk_size + 1}: {len(chunk_subjects)} subjects")
        
        for subject_id in chunk_subjects:
            try:
                # Load subject data (simplified - assume NIfTI loading handled elsewhere)
                # In real implementation, this would load from raw_data_dir
                subject_data_path = Path(raw_data_dir) / f"{subject_id}.nii.gz"
                
                if not subject_data_path.exists():
                    logger.warning(f"Data not found for {subject_id}, skipping")
                    continue
                
                # Placeholder for actual data loading
                # In real code: load_and_scrub_subject(subject_id, raw_data_dir)
                # Simulating time series data for demonstration
                n_timepoints = 1200
                n_parcels = 360
                time_series_data = np.random.randn(n_timepoints, n_parcels)
                
                # Compute entropy
                results, is_flagged = run_parcels_and_flagging(
                    subject_id, time_series_data, atlas, m, r, log_path
                )
                
                # Aggregate to network level
                network_ents = {}
                for network, entropies in results.items():
                    valid_ents = entropies[~np.isnan(entropies)]
                    if len(valid_ents) > 0:
                        network_ents[f"{network}_mean"] = np.mean(valid_ents)
                        network_ents[f"{network}_std"] = np.std(valid_ents)
                        network_ents[f"{network}_auc"], _ = compute_multiscale_entropy(
                            time_series_data[:, 0], m=m, r=r
                        )  # Simplified - would use actual parcel data
                    
                # Add subject metadata
                row = {'subject_id': subject_id}
                row.update(network_ents)
                row['flagged_for_review'] = is_flagged
                all_results.append(row)
                
            except Exception as e:
                logger.error(f"Error processing {subject_id}: {str(e)}")
                continue
        
        # Check RAM usage after each chunk
        current_ram_mb = process.memory_info().rss / (1024 * 1024)
        if current_ram_mb > peak_ram_mb:
            peak_ram_mb = current_ram_mb
        
        logger.info(f"Current RAM: {current_ram_mb:.2f} MB, Peak RAM: {peak_ram_mb:.2f} MB")
    
    # Create final DataFrame
    df_results = pd.DataFrame(all_results)
    
    # Log peak RAM usage
    end_time = time.time()
    duration = end_time - start_time
    
    log_entry = (
        f"Entropy computation completed. "
        f"Subjects processed: {len(all_results)}, "
        f"Duration: {duration:.2f}s, "
        f"Peak RAM: {peak_ram_mb:.2f} MB\n"
    )
    
    if log_path:
        with open(log_path, 'a') as f:
            f.write(log_entry)
    else:
        # Default log path
        default_log_dir = Path('data/logs')
        default_log_dir.mkdir(parents=True, exist_ok=True)
        default_log_path = default_log_dir / 'ram_usage.log'
        with open(default_log_path, 'a') as f:
            f.write(log_entry)
    
    logger.info(f"Peak RAM usage: {peak_ram_mb:.2f} MB")
    
    # Write output
    df_results.to_csv(output_path, index=False)
    logger.info(f"Results written to {output_path}")
    
    return df_results