import os
import sys
import logging
import json
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing API surface
from glm_fdr_correction import load_t_stat_map, apply_fdr_correction, extract_clusters

# Configure logging
LOG_FILE = Path("data/processed/preprocessing.log")
# Ensure directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def setup_logging():
    """Setup logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def calculate_global_p_value(t_stat_map_path: Path) -> Dict[str, float]:
    """
    Calculate global t-statistic p-value from the t-stat map.
    
    This computes the p-value for the global mean t-statistic against zero,
    effectively testing if the overall activation is significantly different from zero.
    
    Args:
        t_stat_map_path: Path to the t-statistic map file (nii.gz)
        
    Returns:
        Dictionary containing global statistics:
        - mean_t: Mean t-statistic across all voxels
        - std_t: Standard deviation of t-statistics
        - global_p: Two-tailed p-value for the mean t-statistic
        - n_voxels: Number of voxels processed
    """
    if not t_stat_map_path.exists():
        raise FileNotFoundError(f"T-statistic map not found: {t_stat_map_path}")
    
    logger.info(f"Loading t-statistic map: {t_stat_map_path}")
    
    # Load the t-statistic map
    t_stat_img = nib.load(t_stat_map_path)
    t_stat_data = t_stat_img.get_fdata()
    
    # Filter out NaN and zero values for calculation
    valid_mask = ~np.isnan(t_stat_data)
    t_values = t_stat_data[valid_mask]
    
    if len(t_values) == 0:
        raise ValueError("No valid t-statistic values found in the map")
    
    n_voxels = len(t_values)
    mean_t = np.mean(t_values)
    std_t = np.std(t_values, ddof=1)  # Sample standard deviation
    
    # Calculate t-statistic for the mean (one-sample test against zero)
    # t = mean / (std / sqrt(n))
    if std_t == 0:
        # If all values are identical, p-value is 0 if mean != 0, else 1
        global_p = 0.0 if mean_t != 0 else 1.0
    else:
        t_global = mean_t / (std_t / np.sqrt(n_voxels))
        # Two-tailed p-value using scipy
        from scipy import stats
        # Degrees of freedom = n - 1
        df = n_voxels - 1
        global_p = 2 * (1 - stats.t.cdf(abs(t_global), df))
    
    result = {
        'mean_t': float(mean_t),
        'std_t': float(std_t),
        'global_p': float(global_p),
        'n_voxels': int(n_voxels),
        't_global': float(t_global) if std_t != 0 else 0.0
    }
    
    logger.info(f"Global statistics: mean_t={mean_t:.4f}, std_t={std_t:.4f}, "
               f"global_p={global_p:.6f}, n_voxels={n_voxels}")
    
    return result

def save_uncorrected_map(t_stat_map_path: Path, output_path: Path, 
                        threshold: float = 0.001) -> Path:
    """
    Save the uncorrected t-statistic map thresholded at p < 0.001 (uncorrected).
    
    Args:
        t_stat_map_path: Path to the original t-statistic map
        output_path: Path where the thresholded map will be saved
        threshold: Uncorrected p-value threshold (default: 0.001)
        
    Returns:
        Path to the saved uncorrected map
    """
    if not t_stat_map_path.exists():
        raise FileNotFoundError(f"T-statistic map not found: {t_stat_map_path}")
    
    logger.info(f"Creating uncorrected map with threshold p < {threshold}")
    
    # Load the t-statistic map
    t_stat_img = nib.load(t_stat_map_path)
    t_stat_data = t_stat_img.get_fdata()
    affine = t_stat_img.affine
    header = t_stat_img.header
    
    # Convert p-value threshold to t-statistic threshold
    # For large N, we can approximate with standard normal, but let's be precise
    # We need the t-value that corresponds to p < 0.001 (two-tailed)
    # This is approximately 3.29 for large samples
    from scipy import stats
    # Using a large df approximation (e.g., df=1000) for the threshold
    t_threshold = stats.t.ppf(1 - threshold/2, df=1000)
    
    logger.info(f"Converting p < {threshold} to t > {t_threshold:.4f}")
    
    # Apply threshold: keep only voxels with |t| > t_threshold
    thresholded_data = np.zeros_like(t_stat_data)
    thresholded_data[abs(t_stat_data) > t_threshold] = t_stat_data[abs(t_stat_data) > t_threshold]
    
    # Create new NIfTI image
    thresholded_img = nib.Nifti1Image(thresholded_data, affine, header)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the thresholded map
    nib.save(thresholded_img, output_path)
    logger.info(f"Saved uncorrected map to: {output_path}")
    
    return output_path

def handle_null_result(t_stat_map_path: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Handle the null result case when no clusters survive FDR correction.
    
    This function:
    1. Calculates the global t-statistic p-value
    2. Saves an uncorrected map thresholded at p < 0.001
    3. Logs the null result with appropriate metadata
    
    Args:
        t_stat_map_path: Path to the t-statistic map
        output_dir: Directory where output files will be saved
        
    Returns:
        Dictionary containing the null result analysis
    """
    if not t_stat_map_path.exists():
        raise FileNotFoundError(f"T-statistic map not found: {t_stat_map_path}")
    
    logger.warning("NULL RESULT: No clusters survived FDR correction")
    
    # Calculate global p-value
    global_stats = calculate_global_p_value(t_stat_map_path)
    
    # Define output path for uncorrected map
    uncorrected_map_path = output_dir / "uncorrected_map.nii.gz"
    
    # Save uncorrected map
    save_uncorrected_map(t_stat_map_path, uncorrected_map_path, threshold=0.001)
    
    # Prepare result dictionary
    result = {
        'status': 'null_result',
        'message': 'NULL RESULT: No clusters survived FDR',
        'global_statistics': global_stats,
        'uncorrected_map_path': str(uncorrected_map_path),
        'threshold_applied': 0.001,
        'fdr_threshold': 0.05,
        'timestamp': str(Path(t_stat_map_path).parent.name)  # Use subject ID or similar
    }
    
    # Log the complete result
    logger.info(f"Null result handled. Global p-value: {global_stats['global_p']:.6f}")
    logger.info(f"Uncorrected map saved to: {uncorrected_map_path}")
    
    return result

def main():
    """
    Main entry point for handling null results in group analysis.
    
    This script is typically called after FDR correction when no significant
    clusters are found. It calculates global statistics and saves an
    uncorrected map for further inspection.
    
    Usage:
        python code/glm_null_result_handler.py <t_stat_map_path> <output_dir>
    """
    if len(sys.argv) < 3:
        print("Usage: python glm_null_result_handler.py <t_stat_map_path> <output_dir>")
        print("  t_stat_map_path: Path to the t-statistic map (nii.gz)")
        print("  output_dir: Directory to save the uncorrected map")
        sys.exit(1)
    
    t_stat_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    if not t_stat_path.exists():
        logger.error(f"T-statistic map not found: {t_stat_path}")
        sys.exit(1)
    
    try:
        result = handle_null_result(t_stat_path, output_dir)
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error handling null result: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
