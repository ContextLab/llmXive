import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import nibabel as nib
from nilearn.mass_univariate import fdr_correction

def setup_logging(log_file: str) -> logging.Logger:
    """Sets up logging to a file."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

def load_t_stat_map(filepath: str) -> np.ndarray:
    """Loads a t-statistic map from a NIfTI file."""
    img = nib.load(filepath)
    data = img.get_fdata()
    return data

def apply_fdr_correction(t_stat_map: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """Applies FDR correction to a t-statistic map."""
    corrected_t_stat_map, p_vals = fdr_correction(t_stat_map, method='fdr_bh')
    return corrected_t_stat_map, p_vals

def extract_clusters(p_vals: np.ndarray, threshold: float = 0.05) -> List[Tuple[int, int, int]]:
    """Extracts significant clusters from a p-value map."""
    # This is a placeholder; a proper clustering algorithm would be needed for real use.
    clusters = []
    for i in range(p_vals.shape[0]):
        for j in range(p_vals.shape[1]):
            for k in range(p_vals.shape[2]):
                if p_vals[i, j, k] < threshold:
                    clusters.append((i, j, k))
    return clusters

def save_thresholded_map(data: np.ndarray, filepath: str) -> None:
    """Saves a thresholded map to a NIfTI file."""
    img = nib.Nifti1Image(data, np.eye(4))
    nib.save(img, filepath)

def save_cluster_metadata(clusters: List[Tuple[int, int, int]], filepath: str) -> None:
    """Saves cluster metadata to a JSON file."""
    with open(filepath, 'w') as f:
        json.dump(clusters, f)

def main():
    """Main function to apply FDR correction and extract clusters."""
    logger = setup_logging("data/processed/fdr_correction.log")
    t_stat_map_path = "data/processed/t_stat_map.nii.gz"  # Replace with actual path
    output_map_path = "data/processed/fdr_mask.nii.gz"
    cluster_metadata_path = "data/processed/fdr_clusters.csv"

    try:
        t_stat_map = load_t_stat_map(t_stat_map_path)
        corrected_t_stat_map, p_vals = apply_fdr_correction(t_stat_map)
        clusters = extract_clusters(p_vals, threshold=0.05)

        if not clusters:
            logger.warning("No clusters survived FDR correction.")
            # Save uncorrected map and log the message
            save_thresholded_map(t_stat_map, "data/processed/uncorrected_map.nii.gz")
        else:
            save_thresholded_map(corrected_t_stat_map, output_map_path)
            save_cluster_metadata(clusters, cluster_metadata_path)

        logger.info("FDR correction and cluster extraction completed successfully.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()