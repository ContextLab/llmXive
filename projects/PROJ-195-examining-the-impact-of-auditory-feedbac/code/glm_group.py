"""
Group-Level Analysis Module for PROJ-195.

Implements a one-sample t-test against zero on contrast maps generated from
first-level GLMs. Performs FDR correction and handles edge cases where
no clusters survive correction.

Dependencies:
    - T023: Generates contrast maps in data/processed/
    - T004: Defines FDR threshold (q < 0.05)
    - T010: Spec amendment confirming one-sample t-test logic
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json

import numpy as np
import nibabel as nib
from nilearn import image
from nilearn.glm.second_level import second_level_input
from nilearn.glm.thresholding import fdr_threshold
from nilearn.glm.second_level import non_parametric_inference
from scipy import stats
from nilearn.masking import apply_mask
from nilearn.reporting import get_clusters_table

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'
OUTPUT_DIR = PROJECT_ROOT / 'data' / 'derivatives' / 'group_analysis'
VALID_SUBJECTS_FILE = PROCESSED_DIR / 'valid_subjects.txt'
STAT_MAP_PATH = OUTPUT_DIR / 'group_stat_map.nii.gz'
CLUSTER_TABLE_PATH = OUTPUT_DIR / 'cluster_table.csv'
NULL_RESULT_LOG_PATH = PROCESSED_DIR / 'null_result_log.json'
FDR_THRESHOLD = 0.05  # q-value threshold
UNCORRECTED_P_THRESHOLD = 0.001


def load_contrast_maps() -> List[Path]:
    """
    Load paths to contrast maps (perturbed > normal) for all valid subjects.
    Expects files named: sub-XX_contrast_perturbed.nii.gz in data/processed/
    
    Returns:
        List[Path]: Sorted list of contrast map file paths.
    """
    if not VALID_SUBJECTS_FILE.exists():
        raise FileNotFoundError(
            f"Valid subjects file not found: {VALID_SUBJECTS_FILE}. "
            "Run T018 (subject filtering) first."
        )

    with open(VALID_SUBJECTS_FILE, 'r') as f:
        subjects = [line.strip() for line in f if line.strip()]

    contrast_maps = []
    for sub in subjects:
        # Assuming T023 saves maps as sub-XX_contrast_perturbed.nii.gz
        # Adjust pattern if T023 uses a different naming convention
        map_path = PROCESSED_DIR / f"{sub}_contrast_perturbed.nii.gz"
        if not map_path.exists():
            # Fallback: check for common variations
            alt_path = PROCESSED_DIR / f"{sub}_contrast_perturbed_effect_size.nii.gz"
            if alt_path.exists():
                map_path = alt_path
            else:
                logger.error(f"Contrast map not found for {sub}. Skipping.")
                continue
        
        contrast_maps.append(map_path)

    if not contrast_maps:
        raise RuntimeError("No valid contrast maps found for group analysis.")

    logger.info(f"Loaded {len(contrast_maps)} contrast maps for group analysis.")
    return sorted(contrast_maps)


def run_group_analysis(
    contrast_maps: List[Path],
    output_dir: Path = OUTPUT_DIR
) -> Dict:
    """
    Perform one-sample t-test against zero on the list of contrast maps.
    
    Args:
        contrast_maps: List of paths to first-level contrast maps.
        output_dir: Directory to save results.
        
    Returns:
        Dict: Analysis results including stat map path, cluster table, and status.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert to list of Niimg-like objects
    # nilearn's second_level_input handles paths directly
    second_level_input = [str(p) for p in contrast_maps]
    
    logger.info("Running second-level one-sample t-test...")
    
    # Create the second-level model (one-sample t-test against 0)
    # We use nilearn's second_level_input which defaults to a one-sample t-test
    # if no design matrix is provided and input is a list of images.
    # However, to be explicit and robust, we can use the `non_parametric_inference`
    # or standard `second_level_model` approach.
    # Given the requirement for FDR and standard t-test, we use the standard approach.
    
    from nilearn.glm.second_level import SecondLevelModel
    
    # Standard one-sample t-test
    slm = SecondLevelModel(mask_img=None, smoothing_fwhm=6.0)
    slm = slm.fit(second_level_input)
    
    # Compute the t-statistic map (contrast of means)
    # For one-sample t-test, the contrast is just [1] (testing if mean != 0)
    z_map = slm.compute_contrast(output_type='z')
    
    # Save the statistical map
    stat_map_path = output_dir / 'group_z_map.nii.gz'
    z_map.to_filename(stat_map_path)
    logger.info(f"Saved group Z-statistic map to {stat_map_path}")
    
    # Apply FDR thresholding
    logger.info(f"Applying FDR correction (q < {FDR_THRESHOLD})...")
    
    # nilearn's fdr_threshold requires a stat map and returns a threshold value
    # We need to threshold the map
    from nilearn.glm.thresholding import fdr_threshold
    
    # Get the data array to apply threshold
    z_img = image.load_img(stat_map_path)
    z_data = z_img.get_fdata()
    mask_data = z_data != 0  # Create a simple mask of non-zero voxels
    
    # Calculate FDR threshold
    # fdr_threshold returns the threshold value
    fdr_thresh = fdr_threshold(z_data, fdr=FDR_THRESHOLD, two_sided=True)
    logger.info(f"FDR threshold calculated: {fdr_thresh:.4f}")
    
    # Create thresholded image
    thresholded_data = np.where(np.abs(z_data) > fdr_thresh, z_data, 0)
    thresholded_img = image.new_img_like(z_img, thresholded_data)
    
    thresholded_path = output_dir / 'group_z_map_fdr.nii.gz'
    thresholded_img.to_filename(thresholded_path)
    logger.info(f"Saved FDR-thresholded map to {thresholded_path}")
    
    # Extract clusters
    logger.info("Extracting significant clusters...")
    clusters_table = get_clusters_table(thresholded_img, 0, 0, 0) # 0 for stat threshold since we already thresholded
    
    # If no clusters found, handle edge case
    if clusters_table.empty:
        logger.warning("No clusters survived FDR correction.")
        return {
            'status': 'null_result',
            'stat_map': str(stat_map_path),
            'thresholded_map': str(thresholded_path),
            'clusters': [],
            'fdr_threshold': fdr_thresh,
            'message': 'No clusters survived FDR correction. See T027 for fallback.'
        }
    
    # Save cluster table
    clusters_table.to_csv(CLUSTER_TABLE_PATH, index=False)
    logger.info(f"Saved cluster table to {CLUSTER_TABLE_PATH}")
    
    return {
        'status': 'success',
        'stat_map': str(stat_map_path),
        'thresholded_map': str(thresholded_path),
        'clusters': clusters_table.to_dict(orient='records'),
        'fdr_threshold': fdr_thresh,
        'num_clusters': len(clusters_table)
    }


def main():
    """
    Main entry point for group-level analysis.
    """
    try:
        # Load contrast maps
        contrast_maps = load_contrast_maps()
        
        # Run analysis
        results = run_group_analysis(contrast_maps)
        
        # Log results
        logger.info(f"Group analysis completed with status: {results['status']}")
        if results['status'] == 'success':
            logger.info(f"Found {results['num_clusters']} significant clusters.")
            logger.info(f"FDR threshold: {results['fdr_threshold']:.4f}")
        else:
            logger.warning(results['message'])
            
        # Save results summary
        summary_path = OUTPUT_DIR / 'analysis_summary.json'
        with open(summary_path, 'w') as f:
            # Convert numpy types for JSON serialization
            json_results = {}
            for k, v in results.items():
                if isinstance(v, np.floating):
                    json_results[k] = float(v)
                elif isinstance(v, list) and v and isinstance(v[0], dict):
                    # Handle cluster records
                    json_results[k] = []
                    for item in v:
                        item_copy = {}
                        for ik, iv in item.items():
                            if isinstance(iv, (np.floating, np.integer)):
                                item_copy[ik] = float(iv) if isinstance(iv, np.floating) else int(iv)
                            else:
                                item_copy[ik] = iv
                        json_results[k].append(item_copy)
                else:
                    json_results[k] = v
            json.dump(json_results, f, indent=2)
            
        logger.info(f"Saved analysis summary to {summary_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Group analysis failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
