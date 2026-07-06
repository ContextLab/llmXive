import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from nilearn import image, masking
from scipy import signal
import networkx as nx
from sklearn.covariance import EmpiricalCovariance

from utils.config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_atlas_labels(atlas_path: str) -> pd.DataFrame:
    """Load Schaefer atlas labels."""
    if not os.path.exists(atlas_path):
        raise FileNotFoundError(f"Atlas file not found: {atlas_path}")
    # Assuming CSV format: label, network, ...
    df = pd.read_csv(atlas_path)
    return df

def load_network_mapping(mapping_path: str) -> pd.DataFrame:
    """Load network mapping CSV if it exists."""
    if os.path.exists(mapping_path):
        return pd.read_csv(mapping_path)
    return None

def get_region_to_network_map(atlas_df: pd.DataFrame, mapping_df: Optional[pd.DataFrame] = None) -> Dict[int, str]:
    """Map region IDs to network names."""
    region_map = {}
    if mapping_df is not None:
        # Use mapped labels if available
        for _, row in mapping_df.iterrows():
            region_id = int(row['region_id'])
            mapped_label = row['mapped_label']
            region_map[region_id] = mapped_label
    else:
        # Fallback to atlas network column
        for _, row in atlas_df.iterrows():
            region_id = int(row['region_id']) # Assuming column name
            network = row['network_name']
            region_map[region_id] = network
    return region_map

def parcellate_nifti(nifti_path: str, atlas_mask_path: str) -> np.ndarray:
    """Extract time series from NIfTI using atlas mask."""
    if not os.path.exists(nifti_path):
        raise FileNotFoundError(f"NIfTI file not found: {nifti_path}")
    if not os.path.exists(atlas_mask_path):
        raise FileNotFoundError(f"Atlas mask not found: {atlas_mask_path}")

    img = image.load_img(nifti_path)
    mask_img = image.load_img(atlas_mask_path)

    # Extract time series
    ts = masking.apply_mask(img, mask_img)
    return ts

def calculate_sliding_window_correlation(time_series: np.ndarray, window_size: int, step_size: int) -> List[np.ndarray]:
    """
    Calculate sliding window correlation matrices.

    Args:
        time_series: 2D array (time x regions)
        window_size: Number of time points in the window
        step_size: Number of time points to step forward

    Returns:
        List of correlation matrices (one per window)
    """
    n_timepoints, n_regions = time_series.shape
    if n_timepoints < window_size:
        raise ValueError(f"Time series length ({n_timepoints}) is less than window size ({window_size})")

    correlations = []
    start = 0
    while start + window_size <= n_timepoints:
        window_data = time_series[start:start + window_size]
        
        # Calculate correlation matrix
        # Handle constant signals to avoid NaN
        corr_matrix = np.corrcoef(window_data.T)
        
        # Replace NaN with 0 (or handle appropriately)
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
        
        correlations.append(corr_matrix)
        start += step_size

    return correlations

def calculate_metrics(correlation_windows: List[np.ndarray], region_to_network_map: Dict[int, str], network_names: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Calculate network flexibility and stability metrics.
    
    This is a placeholder for the logic that will be implemented in subsequent tasks (T028-T030).
    T027 specifically focuses on generating the correlation windows.
    """
    # Placeholder return structure
    metrics = {}
    for net in network_names:
        metrics[net] = {
            'flexibility': 0.0,
            'stability': 0.0
        }
    return metrics

def process_subject(subject_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single subject: load data, parcellate, calculate sliding window correlations.
    
    T027 Implementation: Focuses on the sliding window correlation step.
    """
    raw_dir = Path(config['data_paths']['raw'])
    processed_dir = Path(config['data_paths']['processed'])
    atlas_dir = Path(config['data_paths']['atlas'])
    
    # Paths
    nifti_path = processed_dir / f"sub-{subject_id}_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
    atlas_mask_path = atlas_dir / "schaefer100_mask.nii.gz"
    atlas_labels_path = atlas_dir / "schaefer100_labels.csv"
    mapping_path = atlas_dir / "network_label_map.csv"
    
    if not nifti_path.exists():
        logger.warning(f"Preprocessed NIfTI not found for {subject_id}")
        return None

    # Load Atlas
    try:
        atlas_df = load_atlas_labels(str(atlas_labels_path))
        mapping_df = load_network_mapping(str(mapping_path))
        region_map = get_region_to_network_map(atlas_df, mapping_df)
    except Exception as e:
        logger.error(f"Failed to load atlas for {subject_id}: {e}")
        return None

    # Parcellate
    try:
        time_series = parcellate_nifti(str(nifti_path), str(atlas_mask_path))
    except Exception as e:
        logger.error(f"Failed to parcellate {subject_id}: {e}")
        return None

    # T027: Calculate Sliding Window Correlation
    window_size = config.get('window_size', 30)
    step_size = config.get('step_size', 10)
    
    logger.info(f"Calculating sliding window correlation for {subject_id} (win={window_size}, step={step_size})")
    
    try:
        correlation_windows = calculate_sliding_window_correlation(time_series, window_size, step_size)
        logger.info(f"Generated {len(correlation_windows)} windows for {subject_id}")
    except Exception as e:
        logger.error(f"Sliding window calculation failed for {subject_id}: {e}")
        return None

    # Placeholder for future metric calculation (T028-T030)
    network_names = ['DMN', 'Salience', 'Hippocampal-Memory']
    metrics = calculate_metrics(correlation_windows, region_map, network_names)

    return {
        'subject_id': subject_id,
        'windows_count': len(correlation_windows),
        'metrics': metrics
    }

def main():
    """Main entry point for running metrics extraction."""
    config = get_config()
    
    # Load valid subjects
    valid_subjects_path = Path(config['data_paths']['raw']) / "valid_subjects.json"
    if not valid_subjects_path.exists():
        logger.error(f"valid_subjects.json not found at {valid_subjects_path}")
        sys.exit(1)

    with open(valid_subjects_path, 'r') as f:
        subjects = json.load(f)

    all_results = []
    
    for subj in subjects:
        sid = subj['subject_id']
        result = process_subject(sid, config)
        if result:
            all_results.append(result)

    # Save results
    output_path = Path(config['data_paths']['metrics']) / "subject_metrics.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Flatten results for CSV
    rows = []
    for res in all_results:
        row = {'subject_id': res['subject_id'], 'windows_count': res['windows_count']}
        for net, vals in res['metrics'].items():
            row[f"{net}_flexibility"] = vals['flexibility']
            row[f"{net}_stability"] = vals['stability']
        rows.append(row)
        
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved metrics to {output_path}")

if __name__ == "__main__":
    main()