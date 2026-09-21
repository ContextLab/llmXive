"""
ROI Extractor Module.

Extracts Region of Interest (ROI) time-series from raw BIDS fMRI data.
This serves as a CPU-tractable substitute for full fMRIPrep preprocessing,
focusing on extracting mean time-series from predefined anatomical ROIs.

Must support real data input only. No synthetic fallbacks.
"""
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import nibabel as nib
import numpy as np
import pandas as pd
from nilearn import image, masking

# Import seed manager for reproducibility
from utils.seed_manager import set_global_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default ROI masks (simplified AAL-like regions for demonstration)
# In a real scenario, these would be loaded from standard MNI space atlases
DEFAULT_ROI_NAMES = [
    'motor_cortex',
    'visual_cortex',
    'prefrontal_cortex',
    'parietal_cortex',
    'temporal_cortex'
]

def load_bids_nifti(subject_data_path: Path, task_label: str) -> nib.Nifti1Image:
    """
    Load a BIDS-compliant NIfTI file for a specific task.

    Args:
        subject_data_path: Path to the subject's directory in BIDS format.
        task_label: The task label (e.g., 'rest', 'nback').

    Returns:
        Loaded NIfTI image object.

    Raises:
        FileNotFoundError: If no matching NIfTI file is found.
        ValueError: If multiple matching files are found (ambiguous).
    """
    # Construct search pattern for BIDS functional data
    # Pattern: sub-<label>_task-<task_label>_bold.nii[.gz]
    search_pattern = f"sub-*_task-{task_label}_bold.nii*"
    matches = list(subject_data_path.rglob(search_pattern))

    if not matches:
        raise FileNotFoundError(
            f"No BIDS functional data found for task '{task_label}' in {subject_data_path}"
        )

    if len(matches) > 1:
        logger.warning(
            f"Multiple files found for task '{task_label}': {matches}. "
            f"Using the first one."
        )

    nii_path = matches[0]
    logger.info(f"Loading functional data from: {nii_path}")

    try:
        img = nib.load(str(nii_path))
    except Exception as e:
        raise RuntimeError(f"Failed to load NIfTI file {nii_path}: {e}")

    return img

def create_simple_roi_masks(img_shape: Tuple[int, int, int, int], 
                            mask_dir: Path) -> Dict[str, np.ndarray]:
    """
    Create simple anatomical ROI masks based on MNI-like coordinates.
    
    This is a simplified approach for demonstration. In a production environment,
    you would load standard atlases (e.g., AAL, Harvard-Oxford) from MNI space
    and resample them to the subject's functional space.

    Args:
        img_shape: Shape of the functional image (x, y, z, t).
        mask_dir: Directory to save the generated mask files.

    Returns:
        Dictionary mapping ROI names to boolean masks.
    """
    mask_dir.mkdir(parents=True, exist_ok=True)
    masks = {}
    
    # Define rough MNI-like coordinates for demonstration
    # These are approximations and would be replaced by real atlas masks in production
    roi_definitions = {
        'motor_cortex': {'center': (30, 30, 30), 'radius': 10},
        'visual_cortex': {'center': (30, 30, 70), 'radius': 8},
        'prefrontal_cortex': {'center': (30, 60, 40), 'radius': 12},
        'parietal_cortex': {'center': (30, 40, 60), 'radius': 9},
        'temporal_cortex': {'center': (30, 20, 50), 'radius': 8}
    }

    for name, params in roi_definitions.items():
        # Create a spherical mask in functional space
        mask = np.zeros(img_shape[:3], dtype=bool)
        center = np.array(params['center'])
        radius = params['radius']
        
        # Generate coordinate grid
        x, y, z = np.ogrid[:img_shape[0], :img_shape[1], :img_shape[2]]
        dist = np.sqrt((x - center[0])**2 + (y - center[1])**2 + (z - center[2])**2)
        mask = dist <= radius
        
        masks[name] = mask
        
        # Save mask for traceability
        mask_path = mask_dir / f"{name}_mask.nii.gz"
        mask_img = nib.Nifti1Image(mask.astype(np.uint8), np.eye(4))
        nib.save(mask_img, str(mask_path))
        logger.info(f"Saved ROI mask: {mask_path}")

    return masks

def extract_roi_timeseries(img: nib.Nifti1Image, 
                           masks: Dict[str, np.ndarray]) -> pd.DataFrame:
    """
    Extract mean time-series from each ROI mask.

    Args:
        img: Loaded NIfTI image.
        masks: Dictionary of ROI masks.

    Returns:
        DataFrame with time-series for each ROI.
    """
    data = img.get_fdata()
    time_points = data.shape[3]
    
    roi_data = {}
    for roi_name, mask in masks.items():
        # Ensure mask shape matches spatial dimensions of data
        if mask.shape != data.shape[:3]:
            raise ValueError(
                f"Mask shape {mask.shape} does not match data spatial shape {data.shape[:3]}"
            )
        
        # Extract mean time-series for this ROI
        roi_values = data[mask]
        mean_ts = np.mean(roi_values, axis=1)
        roi_data[roi_name] = mean_ts

    # Create DataFrame
    df = pd.DataFrame(roi_data)
    return df

def preprocess_and_extract(subject_dir: Path, 
                           task_label: str, 
                           output_dir: Path,
                           seed: Optional[int] = None) -> Path:
    """
    Main pipeline to preprocess (load) and extract ROI time-series from a subject.

    Args:
        subject_dir: Path to the subject's BIDS directory.
        task_label: The task label to process.
        output_dir: Directory to save the extracted time-series.
        seed: Random seed for reproducibility (if needed for future steps).

    Returns:
        Path to the saved CSV file containing the time-series.
    """
    if seed is not None:
        set_global_seed(seed)
    
    logger.info(f"Processing subject: {subject_dir.name} for task: {task_label}")
    
    # 1. Load BIDS data
    img = load_bids_nifti(subject_dir, task_label)
    
    # 2. Create ROI masks
    mask_dir = output_dir / "masks"
    masks = create_simple_roi_masks(img.shape, mask_dir)
    
    # 3. Extract time-series
    timeseries_df = extract_roi_timeseries(img, masks)
    
    # 4. Save results
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{subject_dir.name}_{task_label}_roi_timeseries.csv"
    timeseries_df.to_csv(output_file, index=False)
    
    logger.info(f"Saved ROI time-series to: {output_file}")
    
    return output_file

def main():
    """
    Command-line entry point for ROI extraction.
    
    Usage:
        python -m preprocess.roi_extractor --subject <path> --task <label> --output <path>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Extract ROI time-series from BIDS data")
    parser.add_argument("--subject", type=str, required=True, 
                        help="Path to subject BIDS directory")
    parser.add_argument("--task", type=str, required=True, 
                        help="Task label (e.g., 'rest', 'nback')")
    parser.add_argument("--output", type=str, required=True, 
                        help="Output directory for results")
    parser.add_argument("--seed", type=int, default=None, 
                        help="Random seed for reproducibility")

    args = parser.parse_args()

    subject_path = Path(args.subject)
    if not subject_path.exists():
        logger.error(f"Subject path does not exist: {subject_path}")
        sys.exit(1)

    output_path = Path(args.output)
    
    try:
        result_file = preprocess_and_extract(
            subject_dir=subject_path,
            task_label=args.task,
            output_dir=output_path,
            seed=args.seed
        )
        print(f"Success: {result_file}")
    except Exception as e:
        logger.error(f"Failed to process subject: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()