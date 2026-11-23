"""
Entropy computation module for resting-state fMRI analysis.
Implements Multiscale Sample Entropy (MSE) calculation, aggregation, and orchestration.
"""

import numpy as np
from typing import Optional, Union, Dict, List, Tuple
import logging
import os
import pandas as pd
from pathlib import Path
import psutil
import time

from config import Config
from utils import ensure_dir, setup_logging

# Configure logging
logger = logging.getLogger(__name__)

# Global peak RAM tracker for the current process
_peak_ram_mb = 0.0

def _update_peak_ram():
    """Update the global peak RAM usage tracker."""
    global _peak_ram_mb
    process = psutil.Process(os.getpid())
    current_ram_mb = process.memory_info().rss / (1024 * 1024)
    if current_ram_mb > _peak_ram_mb:
        _peak_ram_mb = current_ram_mb

def _reset_peak_ram():
    """Reset the peak RAM tracker."""
    global _peak_ram_mb
    _peak_ram_mb = 0.0

def _log_peak_ram(output_path: Path):
    """Log the peak RAM usage to the specified file."""
    ensure_dir(output_path.parent)
    with open(output_path, 'a') as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] Peak RAM during entropy computation: {_peak_ram_mb:.2f} MB\n")

def load_hcp_atlas(atlas_path: Union[str, Path]) -> Dict[str, List[int]]:
    """
    Load the HCP 360-parcel atlas mapping.
    Returns a dictionary mapping network names to lists of parcel indices.
    """
    atlas_path = Path(atlas_path)
    if not atlas_path.exists():
        raise FileNotFoundError(f"Atlas file not found: {atlas_path}")
    
    # Assuming a CSV format: parcel_id, network_name
    df = pd.read_csv(atlas_path)
    mapping = {}
    for network in df['network_name'].unique():
        parcels = df[df['network_name'] == network]['parcel_id'].tolist()
        mapping[network] = parcels
    return mapping

def compute_sample_entropy(time_series: np.ndarray, m: int = 2, r: float = 0.2) -> float:
    """
    Compute Sample Entropy for a 1D time series.
    
    Args:
        time_series: 1D numpy array of fMRI signal.
        m: Template length (default: 2).
        r: Tolerance threshold (default: 0.2 * std of time series).
    
    Returns:
        Sample Entropy value.
    """
    n = len(time_series)
    if n < m + 2:
        return float('nan')
    
    # Normalize r if it's a scalar relative to std
    if isinstance(r, float) and r < 1.0:
        r = r * np.std(time_series)
    
    # Precompute differences for efficiency
    # Create template vectors
    templates = np.lib.stride_tricks.as_strided(
        time_series,
        shape=(n - m + 1, m),
        strides=(time_series.strides[0], time_series.strides[0])
    )
    
    # Compute distances between all pairs of templates
    # B(i, j) = max |u(i) - u(j)|
    diff = np.abs(templates[:, None, :] - templates[None, :, :])
    max_diff = np.max(diff, axis=2)
    
    # Count matches within tolerance r (excluding self-matches)
    B_m = np.sum((max_diff <= r).astype(int), axis=1) - 1  # Exclude self
    
    if m == 1:
        # For m=1, we count matches for length 1 (which is just the number of points)
        # But Sample Entropy is defined as -ln(A/B) where A is matches for m+1 and B for m
        # Here we are computing B_m (matches for length m)
        pass

    # Compute matches for length m+1
    if n < m + 2:
        return float('nan')
    
    templates_m1 = np.lib.stride_tricks.as_strided(
        time_series,
        shape=(n - m, m + 1),
        strides=(time_series.strides[0], time_series.strides[0])
    )
    
    diff_m1 = np.abs(templates_m1[:, None, :] - templates_m1[None, :, :])
    max_diff_m1 = np.max(diff_m1, axis=2)
    
    B_m1 = np.sum((max_diff_m1 <= r).astype(int), axis=1) - 1
    
    # Avoid division by zero
    if np.any(B_m == 0) or np.any(B_m1 == 0):
        # If no matches, entropy is undefined or infinity, return nan
        return float('nan')
    
    # Sample Entropy = -ln( (sum B_m1) / (sum B_m) )
    phi_m = np.mean(np.log(B_m))
    phi_m1 = np.mean(np.log(B_m1))
    
    sampen = phi_m - phi_m1
    return float(sampen)

def compute_multiscale_entropy(time_series: np.ndarray, m: int = 2, r: float = 0.2, max_scale: int = 20) -> Tuple[np.ndarray, float]:
    """
    Compute Multiscale Sample Entropy across scales 1 to max_scale.
    Returns the entropy profile and the Area Under the Curve (AUC).
    
    Args:
        time_series: 1D numpy array.
        m: Template length.
        r: Tolerance threshold.
        max_scale: Maximum scale factor.
    
    Returns:
        Tuple of (entropy_profile, auc_value).
    """
    scales = np.arange(1, max_scale + 1)
    entropy_profile = []
    
    for scale in scales:
        # Coarse-graining: average non-overlapping windows of length 'scale'
        ts_len = len(time_series)
        num_windows = ts_len // scale
        if num_windows < m + 2:
            entropy_profile.append(np.nan)
            continue
        
        coarse_ts = np.mean(time_series[:num_windows * scale].reshape(num_windows, scale), axis=1)
        ent = compute_sample_entropy(coarse_ts, m, r)
        entropy_profile.append(ent)
    
    entropy_profile = np.array(entropy_profile)
    
    # Compute AUC using trapezoidal rule
    auc = np.trapz(entropy_profile[~np.isnan(entropy_profile)], 
                   scales[~np.isnan(entropy_profile)])
    
    return entropy_profile, auc

def process_parcels_for_subject(subject_id: str, ts_data: Dict[int, np.ndarray], 
                                atlas_mapping: Dict[str, List[int]], 
                                m: int = 2, r: float = 0.2, max_scale: int = 20) -> Dict[str, Dict[str, float]]:
    """
    Process all parcels for a single subject and compute entropy metrics.
    
    Args:
        subject_id: Subject identifier.
        ts_data: Dictionary mapping parcel_id -> time series array.
        atlas_mapping: Dictionary mapping network -> list of parcel_ids.
        m, r, max_scale: Entropy parameters.
    
    Returns:
        Dictionary with subject_id as key, containing parcel and network metrics.
    """
    results = {
        'subject_id': subject_id,
        'parcels': {},
        'networks': {}
    }
    
    invalid_count = 0
    total_parcels = 0
    
    # Compute parcel-level entropy
    for network, parcel_ids in atlas_mapping.items():
        network_values = []
        for pid in parcel_ids:
            if pid not in ts_data:
                continue
            ts = ts_data[pid]
            if np.any(np.isnan(ts)):
                invalid_count += 1
                results['parcels'][pid] = {'entropy': np.nan}
                continue
            
            total_parcels += 1
            _, auc = compute_multiscale_entropy(ts, m, r, max_scale)
            results['parcels'][pid] = {'entropy': auc}
            if not np.isnan(auc):
                network_values.append(auc)
        
        # Aggregate network entropy (mean of parcel entropies)
        if network_values:
            results['networks'][network] = np.mean(network_values)
        else:
            results['networks'][network] = np.nan
    
    results['invalid_parcels_count'] = invalid_count
    results['total_parcels_count'] = total_parcels
    
    return results

def flag_invalid_parcels(subject_results: Dict, threshold: float = 0.10, log_path: Optional[Path] = None):
    """
    Flag subjects where >10% of parcels are invalid (NaN).
    Logs to invalid_parcels.log if log_path is provided.
    """
    total = subject_results.get('total_parcels_count', 0)
    invalid = subject_results.get('invalid_parcels_count', 0)
    
    if total == 0:
        is_invalid = False
    else:
        ratio = invalid / total
        is_invalid = ratio > threshold
    
    if is_invalid and log_path:
        ensure_dir(log_path.parent)
        with open(log_path, 'a') as f:
            f.write(f"Subject {subject_results['subject_id']}: {invalid}/{total} parcels invalid ({ratio:.2%})\n")
    
    return is_invalid

def run_parcels_and_flagging(subject_ids: List[str], 
                             data_dir: Path, 
                             atlas_path: Path, 
                             output_csv: Path,
                             log_path: Optional[Path] = None,
                             m: int = 2, r: float = 0.2, max_scale: int = 20,
                             chunk_size: int = 10):
    """
    Process parcels for multiple subjects in chunks to manage memory.
    """
    global _peak_ram_mb
    _peak_ram_mb = 0.0
    
    atlas_mapping = load_hcp_atlas(atlas_path)
    
    all_results = []
    
    for i in range(0, len(subject_ids), chunk_size):
        chunk = subject_ids[i:i+chunk_size]
        logger.info(f"Processing chunk {i//chunk_size + 1}: {len(chunk)} subjects")
        
        for sid in chunk:
            try:
                # Simulate loading time series for parcels (in real impl, load from NIfTI)
                # Placeholder for actual data loading logic
                ts_data = {}
                # In real implementation, load from data_dir/sid/parcels/
                # For now, assume we have a way to get ts_data
                
                # Since we cannot load real data here without the full pipeline,
                # we assume the data is available via a loader function from data_loader
                from data_loader import load_and_scrub_subject
                ts_data = load_and_scrub_subject(sid, data_dir)
                
                if not ts_data:
                    logger.warning(f"No data for subject {sid}")
                    continue
                
                results = process_parcels_for_subject(sid, ts_data, atlas_mapping, m, r, max_scale)
                flag_invalid_parcels(results, log_path=log_path)
                
                # Flatten results for CSV
                row = {'subject_id': sid}
                for net, val in results['networks'].items():
                    row[f'network_{net}'] = val
                for pid, vals in results['parcels'].items():
                    row[f'parcel_{pid}'] = vals['entropy']
                row['invalid_parcels_count'] = results['invalid_parcels_count']
                row['total_parcels_count'] = results['total_parcels_count']
                
                all_results.append(row)
                
                _update_peak_ram()
                
            except Exception as e:
                logger.error(f"Error processing subject {sid}: {e}")
                continue
    
    # Write results
    df = pd.DataFrame(all_results)
    ensure_dir(output_csv.parent)
    df.to_csv(output_csv, index=False)
    logger.info(f"Wrote {len(all_results)} subjects to {output_csv}")

def run_entropy_orchestration(config: Config, log_ram_path: Optional[Path] = None):
    """
    Main orchestration function to run entropy computation for all valid subjects.
    Includes RAM usage logging.
    """
    global _peak_ram_mb
    _reset_peak_ram()
    
    logger.info("Starting entropy orchestration...")
    start_time = time.time()
    
    # Load valid subjects
    valid_subjects_path = Path(config.PROCESSED_DATA_DIR) / 'valid_subjects.csv'
    if not valid_subjects_path.exists():
        raise FileNotFoundError(f"Valid subjects file not found: {valid_subjects_path}")
    
    df_valid = pd.read_csv(valid_subjects_path)
    subject_ids = df_valid['subject_id'].tolist()
    
    # Define paths
    atlas_path = Path(config.ATLAS_PATH)
    output_csv = Path(config.PROCESSED_DATA_DIR) / 'entropy_metrics.csv'
    invalid_log = Path(config.LOGS_DIR) / 'invalid_parcels.log'
    
    # Run processing
    run_parcels_and_flagging(
        subject_ids=subject_ids,
        data_dir=Path(config.RAW_DATA_DIR),
        atlas_path=atlas_path,
        output_csv=output_csv,
        log_path=invalid_log,
        m=config.M,
        r=config.R,
        max_scale=config.MAX_SCALE,
        chunk_size=config.CHUNK_SIZE
    )
    
    elapsed = time.time() - start_time
    logger.info(f"Entropy computation completed in {elapsed:.2f} seconds")
    
    # Log RAM usage if requested
    if log_ram_path:
        _log_peak_ram(log_ram_path)
        logger.info(f"Peak RAM logged to {log_ram_path}")

if __name__ == "__main__":
    # Example usage for testing
    config = Config()
    run_entropy_orchestration(config, log_ram_path=Path(config.LOGS_DIR) / 'ram_usage.log')