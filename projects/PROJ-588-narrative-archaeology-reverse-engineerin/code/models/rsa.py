"""
Representational Similarity Analysis (RSA) for Early vs. Late Event phases.

Implements the Semantic Drift fallback (Early vs. Late) as per FR-008 due to 
missing delayed task data.

Formula: RDM[i,j] = 1 - corr(timecourse_i, timecourse_j)
"""
import numpy as np
import json
import logging
from pathlib import Path
from scipy.spatial.distance import pdist, squareform
import h5py
from scipy.stats import pearsonr

import code.config as config

logger = logging.getLogger(__name__)

def compute_dissimilarity_matrix(timecourses):
    """
    Compute the Representational Dissimilarity Matrix (RDM) from timecourses.
    
    Uses 1 - Pearson correlation as the dissimilarity metric.
    
    Args:
        timecourses (np.ndarray): Array of shape (n_events, n_voxels) or (n_events, n_roi_features).
    
    Returns:
        np.ndarray: Square dissimilarity matrix of shape (n_events, n_events).
    """
    if timecourses.shape[0] < 2:
        logger.warning("Insufficient events to compute dissimilarity matrix.")
        return np.array([[0.0]])
    
    # Normalize to handle potential constant vectors
    # Avoid division by zero
    norms = np.linalg.norm(timecourses, axis=1, keepdims=True)
    norms[norms == 0] = 1e-10
    normalized = timecourses / norms
    
    # Compute correlation matrix via dot product of normalized vectors
    corr_matrix = np.dot(normalized, normalized.T)
    
    # Clip to [-1, 1] to handle floating point errors
    corr_matrix = np.clip(corr_matrix, -1.0, 1.0)
    
    # Convert to dissimilarity: 1 - corr
    rdm = 1.0 - corr_matrix
    
    # Ensure diagonal is exactly 0
    np.fill_diagonal(rdm, 0.0)
    
    return rdm

def compare_early_late(early_timecourses, late_timecourses):
    """
    Compare Early vs. Late event phases.
    
    Computes the mean dissimilarity between Early and Late events,
    and between Early and Early events (within-group).
    
    Args:
        early_timecourses (np.ndarray): Array of shape (n_early, features).
        late_timecourses (np.ndarray): Array of shape (n_late, features).
    
    Returns:
        dict: Dictionary with 'early_late' (cross-phase dissimilarity) 
              and 'early_early' (within-phase dissimilarity).
    """
    results = {}
    
    # Early vs Late dissimilarity
    if early_timecourses.shape[0] > 0 and late_timecourses.shape[0] > 0:
        combined = np.vstack([early_timecourses, late_timecourses])
        rdm = compute_dissimilarity_matrix(combined)
        
        n_early = early_timecourses.shape[0]
        n_late = late_timecourses.shape[0]
        
        # Extract Early-Late block (upper right or lower left)
        # RDM indices: 0..n_early-1 are Early, n_early..n_early+n_late-1 are Late
        early_late_block = rdm[:n_early, n_early:]
        results['early_late'] = float(np.mean(early_late_block))
    else:
        logger.warning("Cannot compute early_late dissimilarity: missing data.")
        results['early_late'] = float('nan')
    
    # Early vs Early dissimilarity (within-group)
    if early_timecourses.shape[0] > 1:
        rdm_early = compute_dissimilarity_matrix(early_timecourses)
        # Extract upper triangle (excluding diagonal)
        triu_indices = np.triu_indices_from(rdm_early, k=1)
        results['early_early'] = float(np.mean(rdm_early[triu_indices]))
    else:
        logger.warning("Cannot compute early_early dissimilarity: insufficient events.")
        results['early_early'] = float('nan')
    
    return results

def run_rsa_analysis(roi_timecourses_path, output_path):
    """
    Run the full RSA analysis pipeline for all ROIs.
    
    Loads timecourses from an HDF5 file, splits into Early and Late phases,
    computes dissimilarity metrics, and saves results to JSON.
    
    Args:
        roi_timecourses_path (str or Path): Path to the HDF5 file containing ROI timecourses.
        output_path (str or Path): Path to the output JSON file.
    """
    roi_timecourses_path = Path(roi_timecourses_path)
    output_path = Path(output_path)
    
    if not roi_timecourses_path.exists():
        raise FileNotFoundError(f"ROI timecourses file not found: {roi_timecourses_path}")
    
    logger.info(f"Loading ROI timecourses from {roi_timecourses_path}")
    
    all_results = {}
    
    with h5py.File(roi_timecourses_path, 'r') as f:
        # Expected structure: groups by ROI name, each containing 'early' and 'late' datasets
        for roi_name in f.keys():
            roi_group = f[roi_name]
            
            if 'early' not in roi_group or 'late' not in roi_group:
                logger.warning(f"Skipping ROI {roi_name}: missing 'early' or 'late' data.")
                continue
            
            early_data = np.array(roi_group['early'])
            late_data = np.array(roi_group['late'])
            
            logger.info(f"Processing ROI: {roi_name} (Early: {early_data.shape[0]}, Late: {late_data.shape[0]})")
            
            roi_results = compare_early_late(early_data, late_data)
            all_results[roi_name] = roi_results
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving RSA results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Verification check
    for roi, metrics in all_results.items():
        if not isinstance(metrics.get('early_late'), (int, float)) or np.isnan(metrics.get('early_late', np.nan)):
            logger.warning(f"Result for {roi} may be invalid: early_late = {metrics.get('early_late')}")
        if not isinstance(metrics.get('early_early'), (int, float)) or np.isnan(metrics.get('early_early', np.nan)):
            logger.warning(f"Result for {roi} may be invalid: early_early = {metrics.get('early_early')}")
    
    return all_results

def main():
    """Main entry point for running RSA analysis."""
    # Paths from config or defaults
    timecourses_path = config.get_data_path() / "processed" / "roi_timecourses.h5"
    output_path = config.get_data_path().parent / "results" / "rsa_matrices.json"
    
    # If config paths are not set, use defaults relative to project root
    if not timecourses_path.exists():
        # Fallback for testing if config paths differ
        timecourses_path = Path("data/processed/roi_timecourses.h5")
        output_path = Path("results/rsa_matrices.json")
    
    run_rsa_analysis(timecourses_path, output_path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()