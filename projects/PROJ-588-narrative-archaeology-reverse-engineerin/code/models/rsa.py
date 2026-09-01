"""
Representational Similarity Analysis (RSA) utilities.
Computes dissimilarity matrices for Early vs. Late event phases and writes results to JSON.
"""
import numpy as np
import json
import logging
from pathlib import Path
from scipy.spatial.distance import pdist, squareform

import code.config as config
from code.data.roi_masker import extract_all_rois

logger = logging.getLogger(__name__)

def compute_dissimilarity_matrix(timecourses):
    """
    Compute the dissimilarity matrix (1 - correlation) for a set of timecourses.
    
    Args:
        timecourses (np.array): 2D array (n_events, n_voxels) or 3D (n_events, n_timepoints, n_voxels).
    
    Returns:
        np.array: Dissimilarity matrix.
    """
    if timecourses.ndim == 3:
        # Average over timepoints if necessary
        timecourses = timecourses.mean(axis=1)
    
    # Use correlation distance
    # pdist with 'correlation' computes 1 - Pearson correlation
    dist = pdist(timecourses, metric='correlation')
    dissimilarity_matrix = squareform(dist)
    return dissimilarity_matrix

def compare_early_late(early_matrix, late_matrix):
    """
    Compare Early vs. Late event dissimilarity matrices.
    
    Returns:
        float: Mean difference in dissimilarity (Early - Late).
    """
    diff = np.mean(early_matrix) - np.mean(late_matrix)
    logger.info(f"Mean Early-Late dissimilarity difference: {diff}")
    return diff

def run_rsa_analysis():
    """
    Main entry point for Task T021.
    Loads ROI timecourses (T013 output), computes Early vs. Late RSA matrices,
    and writes results to results/rsa_matrices.json.
    """
    # Ensure output directory exists
    output_dir = Path(config.get_output_path("results"))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "rsa_matrices.json"

    # Load ROI timecourses from T013
    # Expected path: data/processed/roi_timecourses.h5
    input_path = Path(config.get_data_path("processed/roi_timecourses.h5"))
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Ensure T013 (ROI Masker) has completed successfully."
        )

    import h5py
    logger.info(f"Loading ROI timecourses from {input_path}")
    
    with h5py.File(input_path, 'r') as f:
        # Expected structure: {roi_name: {phase: (n_events, n_voxels)}}
        # We need to extract Early and Late phases for each ROI
        roi_data = {}
        
        for roi in f.keys():
            roi_group = f[roi]
            
            if 'early' in roi_group and 'late' in roi_group:
                early_data = np.array(roi_group['early'])
                late_data = np.array(roi_group['late'])
                
                logger.info(f"Processing ROI: {roi}, Early shape: {early_data.shape}, Late shape: {late_data.shape}")
                
                # Compute dissimilarity matrices
                early_rdm = compute_dissimilarity_matrix(early_data)
                late_rdm = compute_dissimilarity_matrix(late_data)
                
                # Compute mean dissimilarity for Early-Early and Late-Late
                # (Diagonal is 0, so we average the upper/lower triangle excluding diagonal)
                n = early_rdm.shape[0]
                early_early_mean = np.sum(early_rdm) / (n * (n - 1)) if n > 1 else 0.0
                late_late_mean = np.sum(late_rdm) / (n * (n - 1)) if n > 1 else 0.0
                
                # Compute Early-Late cross-dissimilarity
                # This requires computing correlation between early and late vectors
                # We'll compute the full cross-dissimilarity matrix and take the mean
                if early_data.ndim == 3:
                    early_data = early_data.mean(axis=1)
                if late_data.ndim == 3:
                    late_data = late_data.mean(axis=1)
                
                # Concatenate for cross-correlation
                combined = np.vstack([early_data, late_data])
                combined_rdm = compute_dissimilarity_matrix(combined)
                
                # Extract cross-dissimilarity block (early rows, late cols)
                n_early = early_data.shape[0]
                n_late = late_data.shape[0]
                early_late_block = combined_rdm[:n_early, n_early:]
                early_late_mean = np.mean(early_late_block)
                
                roi_data[roi] = {
                    "early_early": float(early_early_mean),
                    "late_late": float(late_late_mean),
                    "early_late": float(early_late_mean)
                }
    
    # Write results to JSON
    with open(output_file, 'w') as f:
        json.dump(roi_data, f, indent=2)
    
    logger.info(f"RSA analysis complete. Results written to {output_file}")
    return roi_data

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    run_rsa_analysis()
