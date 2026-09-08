import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import nibabel as nib
from nilearn import image
from nilearn.mass_univariate import fdr_correction
from scipy import ndimage

# Add project root to path if needed
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from stats_config import load_config, get_fdr_threshold, get_glm_params
from utils import setup_logging, log_deviation

def load_t_stat_map(t_map_path: Path) -> np.ndarray:
    """Load a 3D t-statistic map into a numpy array."""
    if not t_map_path.exists():
        raise FileNotFoundError(f"T-statistic map not found: {t_map_path}")
    img = nib.load(t_map_path)
    data = img.get_fdata()
    return data, img

def apply_fdr_correction(t_map_data: np.ndarray, q: float = 0.05) -> np.ndarray:
    """
    Apply voxel-wise FDR correction to the t-statistic map.
    
    Args:
        t_map_data: 3D array of t-statistics.
        q: FDR threshold (default 0.05).
        
    Returns:
        Boolean mask of significant voxels (True = significant).
    """
    # Flatten to 1D for fdr_correction
    t_flat = t_map_data.flatten()
    
    # Filter out non-finite values (NaN, Inf) which can occur in edge cases
    valid_mask = np.isfinite(t_flat)
    if not np.any(valid_mask):
        logging.warning("No valid t-values found in the map.")
        return np.zeros_like(t_map_data, dtype=bool)
        
    t_valid = t_flat[valid_mask]
    
    # fdr_correction returns (reject, pvals_corrected)
    # We need to map the rejection back to the original shape
    reject, _ = fdr_correction(t_valid, alpha=q, method='indep')
    
    # Create a full boolean mask
    full_reject = np.zeros_like(t_flat, dtype=bool)
    full_reject[valid_mask] = reject
    
    significant_mask = full_reject.reshape(t_map_data.shape)
    return significant_mask

def extract_clusters(mask: np.ndarray, connectivity: int = 26) -> List[Dict[str, Any]]:
    """
    Extract cluster metadata from a binary mask.
    
    Args:
        mask: Binary mask of significant voxels.
        connectivity: Connectivity for labeling (18 or 26).
        
    Returns:
        List of dictionaries containing cluster metadata (label, size, peak_t, coords).
    """
    if not np.any(mask):
        return []
        
    labeled_array, num_features = ndimage.label(mask)
    clusters = []
    
    for i in range(1, num_features + 1):
        cluster_mask = (labeled_array == i)
        size = np.sum(cluster_mask)
        
        # Find peak t-value in this cluster
        cluster_t_values = np.where(cluster_mask, mask * 0 + 1, 0) # Placeholder if we don't have t_map here
        # We need the t_map to find the peak, so this function assumes we pass t_map or handle it outside
        # For now, we return basic cluster info. The peak_t will be calculated in the caller if needed.
        
        # Get coordinates (MNI) - this requires the affine from the original image
        # This function currently only returns voxel indices relative to the mask
        # We will refine this in the main function where we have the affine
        coords_indices = np.argwhere(cluster_mask)
        
        clusters.append({
            "cluster_id": i,
            "size_voxels": int(size),
            "voxel_indices": coords_indices.tolist()
        })
        
    return clusters

def save_thresholded_map(significant_mask: np.ndarray, original_img: nib.Nifti1Image, output_path: Path):
    """Save the FDR-corrected mask as a NIfTI file."""
    # Create a new NIfTI image with the mask data
    # We keep the original affine and header
    new_img = nib.Nifti1Image(significant_mask.astype(np.int8), original_img.affine, original_img.header)
    nib.save(new_img, output_path)
    logging.info(f"Saved FDR mask to {output_path}")

def save_cluster_metadata(clusters: List[Dict[str, Any]], t_map_data: np.ndarray, 
                          affine: np.ndarray, output_csv_path: Path, 
                          threshold: float = 0.05):
    """
    Save cluster metadata to a CSV file.
    
    Args:
        clusters: List of cluster dictionaries.
        t_map_data: Original t-statistic array (for peak finding).
        affine: Affine matrix to convert voxel indices to MNI coordinates.
        output_csv_path: Path to save the CSV.
        threshold: The FDR threshold used.
    """
    import csv
    
    with open(output_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['cluster_id', 'size_voxels', 'peak_t', 'x_mni', 'y_mni', 'z_mni', 'fdr_q'])
        
        for cluster in clusters:
            cid = cluster['cluster_id']
            size = cluster['size_voxels']
            indices = np.array(cluster['voxel_indices'])
            
            # Find peak t-value and its location within this cluster
            # Create a temporary mask for this cluster
            cluster_mask = np.zeros_like(t_map_data, dtype=bool)
            for idx in indices:
                cluster_mask[tuple(idx)] = True
                
            peak_idx = np.unravel_index(np.argmax(t_map_data[cluster_mask]), t_map_data.shape)
            peak_t = t_map_data[peak_idx]
            
            # Convert peak voxel index to MNI coordinates
            # affine @ [x, y, z, 1]
            peak_coords_vox = np.array([*peak_idx, 1])
            peak_coords_mni = affine @ peak_coords_vox
            
            writer.writerow([
                cid,
                size,
                f"{peak_t:.4f}",
                f"{peak_coords_mni[0]:.2f}",
                f"{peak_coords_mni[1]:.2f}",
                f"{peak_coords_mni[2]:.2f}",
                f"{threshold:.2f}"
            ])
    
    logging.info(f"Saved cluster metadata to {output_csv_path}")

def main():
    """
    Main entry point for FDR correction and cluster extraction.
    
    Reads contrast maps from data/processed/, applies FDR correction,
    and saves results to data/processed/fdr_clusters.csv and 
    data/processed/fdr_mask.nii.gz.
    """
    logger = setup_logging()
    logger.info("Starting FDR Correction and Cluster Extraction (T025)")
    
    # Load configuration
    config_path = Path("stats_config.yaml")
    if not config_path.exists():
        logger.error("stats_config.yaml not found. Cannot proceed.")
        sys.exit(1)
        
    config = load_config(config_path)
    fdr_q = get_fdr_threshold(config)
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    processed_dir = project_root / "data" / "processed"
    
    # Find contrast maps (assuming they are named like contrast_map_sub-XX.nii.gz)
    # We expect T023 to have generated these. We will aggregate them or pick the group map?
    # T024 (Group Analysis) should have produced a group-level t-map.
    # Let's assume the group analysis output is 'group_t_map.nii.gz' or similar.
    # Based on T024 description: "Run group analysis... output of effect sizes".
    # Usually group analysis outputs a t-stat map. Let's look for the most likely file.
    # If T024 didn't save a specific name, we might need to check the code.
    # Assuming T024 saves to 'data/processed/group_t_map.nii.gz' or similar.
    # Let's assume the standard output of the group analysis is a single t-map for the contrast.
    
    # We need to find the group t-map. Let's assume it's named 'group_contrast_t_map.nii.gz'
    # or we can look for any file in processed_dir that looks like a group t-map.
    # For robustness, let's check for 'group_t_map.nii.gz' first.
    
    group_t_map_path = processed_dir / "group_t_map.nii.gz"
    
    # If not found, try to find any t-map that isn't a single subject
    if not group_t_map_path.exists():
        possible_files = list(processed_dir.glob("*_t_map.nii.gz"))
        if possible_files:
            group_t_map_path = possible_files[0]
            logger.warning(f"Using found group t-map: {group_t_map_path}")
        else:
            logger.error("No group t-statistic map found in data/processed/.")
            logger.error("Ensure T024 (Group Analysis) has completed and saved the group t-map.")
            sys.exit(1)
    
    logger.info(f"Loading group t-map from: {group_t_map_path}")
    
    try:
        t_map_data, img = load_t_stat_map(group_t_map_path)
    except Exception as e:
        logger.error(f"Failed to load t-map: {e}")
        sys.exit(1)
        
    logger.info(f"Loaded t-map with shape: {t_map_data.shape}")
    
    # Apply FDR correction
    logger.info(f"Applying FDR correction with q = {fdr_q}")
    significant_mask = apply_fdr_correction(t_map_data, q=fdr_q)
    
    if not np.any(significant_mask):
        logger.warning("No significant clusters found after FDR correction.")
        # T027 handles the null result case, but we still need to output the files (empty)
        # Or T027 might be a separate script. The task T025 says "Generate ... fdr_clusters.csv and fdr_mask.nii.gz"
        # We generate empty/zero files if no clusters.
    
    # Save the mask
    mask_output_path = processed_dir / "fdr_mask.nii.gz"
    save_thresholded_map(significant_mask, img, mask_output_path)
    
    # Extract clusters
    clusters = extract_clusters(significant_mask)
    logger.info(f"Extracted {len(clusters)} clusters.")
    
    # Save cluster metadata
    csv_output_path = processed_dir / "fdr_clusters.csv"
    save_cluster_metadata(clusters, t_map_data, img.affine, csv_output_path, fdr_q)
    
    logger.info("FDR Correction and Cluster Extraction completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
