"""
Sensitivity Analysis: ROI Mask Probability Thresholds

This module implements the logic to iterate over ROI mask probability thresholds
to generate corresponding masks for sensitivity analysis.

It satisfies FR-008 by using concrete probability threshold values:
- Low threshold: 0.30 (30% probability)
- High threshold: 0.60 (60% probability)

This allows testing the robustness of findings across different ROI definitions.
"""
import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import nibabel as nib
from nilearn import image
from nilearn.maskers import NiftiMasker
from nilearn.input_data import NiftiLabelsMasker

# Import from existing API surface
from config.loader import get_config, get_roi_definition, get_roi_atlas
from utils.provenance import generate_provenance_sidecar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Concrete threshold values for sensitivity analysis (FR-008)
PROBABILITY_THRESHOLDS = [0.30, 0.60]

def get_mask_file_path(roi_name: str, threshold: float, output_dir: Path) -> Path:
    """
    Generate the file path for a thresholded ROI mask.
    
    Args:
        roi_name: Name of the ROI (e.g., 'VS', 'OFC')
        threshold: Probability threshold (0.0 to 1.0)
        output_dir: Directory to save the mask
        
    Returns:
        Path to the mask file
    """
    safe_roi_name = roi_name.replace(' ', '_').lower()
    mask_filename = f"roi_{safe_roi_name}_prob_{threshold:.2f}.nii.gz"
    return output_dir / mask_filename

def load_atlas_roi(atlas_name: str, atlas_label: str, threshold: float) -> nib.Nifti1Image:
    """
    Load an ROI mask from an atlas and apply probability thresholding.
    
    Args:
        atlas_name: Name of the atlas file (e.g., 'AAL.nii', 'HarvardOxford-cort-prob.nii')
        atlas_label: Label of the ROI within the atlas
        threshold: Probability threshold to apply
        
    Returns:
        Thresholded NIfTI image of the ROI
    """
    config = get_config()
    atlas_dir = Path(config['paths']['atlas_dir'])
    atlas_path = atlas_dir / atlas_name
    
    if not atlas_path.exists():
        raise FileNotFoundError(f"Atlas file not found: {atlas_path}")
    
    logger.info(f"Loading atlas: {atlas_path}")
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata()
    
    # Find the index/label for the ROI
    # This depends on the atlas format (AAL uses integer labels, HO uses probabilistic)
    roi_idx = None
    
    if 'AAL' in atlas_name:
        # AAL atlas: look up label index from config or use known mapping
        # For VS (Ventral Striatum), typically label 11 in AAL
        # For OFC, typically label 10-11 in AAL (varies by version)
        aal_mapping = config.get('atlases', {}).get('aal', {}).get('labels', {})
        roi_idx = aal_mapping.get(atlas_label)
        
        if roi_idx is None:
            raise ValueError(f"ROI label '{atlas_label}' not found in AAL mapping")
        
        # Create binary mask
        mask_data = (atlas_data == roi_idx).astype(np.float32)
        
    elif 'HarvardOxford' in atlas_name:
        # Harvard-Oxford probabilistic atlas
        # Need to find the label index for the ROI name
        ho_labels = config.get('atlases', {}).get('harvard_oxford', {}).get('labels', {})
        roi_idx = ho_labels.get(atlas_label)
        
        if roi_idx is None:
            # Fallback: try to find by scanning labels if available
            # For now, raise error
            raise ValueError(f"ROI label '{atlas_label}' not found in Harvard-Oxford mapping")
        
        # Extract probability map for this ROI
        # In HO, each ROI has its own probability map (or we use the max probability approach)
        # Assuming we have a single 3D probability map where values represent probability
        mask_data = atlas_data.copy()
        
    else:
        raise ValueError(f"Unsupported atlas type: {atlas_name}")
    
    # Apply probability threshold
    mask_data = (mask_data >= threshold).astype(np.float32)
    
    # Create new NIfTI image
    thresholded_img = nib.Nifti1Image(mask_data, atlas_img.affine, atlas_img.header)
    
    # Ensure we have some voxels
    if np.sum(mask_data) == 0:
        logger.warning(f"No voxels found for {atlas_label} at threshold {threshold}")
        # Return empty mask (will be handled downstream)
    
    return thresholded_img

def create_roi_mask(roi_name: str, threshold: float, output_dir: Path) -> Path:
    """
    Create a thresholded ROI mask for sensitivity analysis.
    
    Args:
        roi_name: Name of the ROI (e.g., 'VS', 'OFC')
        threshold: Probability threshold to apply
        output_dir: Directory to save the mask
        
    Returns:
        Path to the created mask file
    """
    config = get_config()
    roi_def = get_roi_definition(roi_name)
    
    if roi_def is None:
        raise ValueError(f"ROI definition not found: {roi_name}")
    
    atlas_name = roi_def.get('atlas', 'AAL')
    atlas_label = roi_def.get('label', roi_name)
    
    logger.info(f"Creating mask for {roi_name} at threshold {threshold:.2f}")
    
    # Load and threshold the atlas ROI
    mask_img = load_atlas_roi(atlas_name, atlas_label, threshold)
    
    # Save the mask
    mask_path = get_mask_file_path(roi_name, threshold, output_dir)
    nib.save(mask_img, str(mask_path))
    
    logger.info(f"Saved mask to: {mask_path}")
    
    # Generate provenance sidecar
    generate_provenance_sidecar(
        input_files=[str(Path(config['paths']['atlas_dir']) / atlas_name)],
        output_file=str(mask_path),
        parameters={
            'roi_name': roi_name,
            'threshold': threshold,
            'atlas_name': atlas_name,
            'atlas_label': atlas_label
        },
        software_versions={'nilearn': 'unknown', 'nibabel': 'unknown'}
    )
    
    return mask_path

def iterate_mask_thresholds(
    roi_names: List[str],
    thresholds: List[float],
    output_dir: Path
) -> Dict[str, Dict[float, Path]]:
    """
    Iterate over ROI names and probability thresholds to generate all masks.
    
    Args:
        roi_names: List of ROI names to process
        thresholds: List of probability thresholds to apply
        output_dir: Directory to save generated masks
        
    Returns:
        Dictionary mapping ROI names to threshold->path mappings
    """
    results = {}
    
    for roi_name in roi_names:
        results[roi_name] = {}
        logger.info(f"Processing ROI: {roi_name}")
        
        for threshold in thresholds:
            try:
                mask_path = create_roi_mask(roi_name, threshold, output_dir)
                results[roi_name][threshold] = mask_path
                logger.info(f"  Created mask for threshold {threshold:.2f}: {mask_path}")
            except Exception as e:
                logger.error(f"  Failed to create mask for {roi_name} at {threshold}: {e}")
                results[roi_name][threshold] = None
    
    return results

def validate_mask_volume(mask_path: Path, min_voxels: int = 10) -> bool:
    """
    Validate that a mask has sufficient volume for analysis.
    
    Args:
        mask_path: Path to the mask file
        min_voxels: Minimum number of voxels required
        
    Returns:
        True if mask is valid, False otherwise
    """
    if not mask_path.exists():
        return False
    
    mask_img = nib.load(str(mask_path))
    mask_data = mask_img.get_fdata()
    voxel_count = np.sum(mask_data > 0)
    
    return voxel_count >= min_voxels

def generate_threshold_summary(
    results: Dict[str, Dict[float, Path]],
    output_dir: Path
) -> Path:
    """
    Generate a summary file of all thresholded masks.
    
    Args:
        results: Dictionary of ROI->threshold->path mappings
        output_dir: Directory to save the summary
        
    Returns:
        Path to the summary file
    """
    summary_path = output_dir / "mask_threshold_summary.json"
    
    summary_data = {
        'thresholds_used': PROBABILITY_THRESHOLDS,
        'rois_processed': list(results.keys()),
        'masks': {}
    }
    
    for roi_name, threshold_paths in results.items():
        summary_data['masks'][roi_name] = {}
        for threshold, mask_path in threshold_paths.items():
            if mask_path and mask_path.exists():
                # Validate mask volume
                is_valid = validate_mask_volume(mask_path)
                mask_img = nib.load(str(mask_path))
                voxel_count = np.sum(mask_img.get_fdata() > 0)
                
                summary_data['masks'][roi_name][f"{threshold:.2f}"] = {
                    'path': str(mask_path),
                    'voxel_count': int(voxel_count),
                    'is_valid': is_valid
                }
            else:
                summary_data['masks'][roi_name][f"{threshold:.2f}"] = {
                    'path': None,
                    'voxel_count': 0,
                    'is_valid': False,
                    'error': 'Mask creation failed or file not found'
                }
    
    import json
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    logger.info(f"Saved threshold summary to: {summary_path}")
    return summary_path

def run_sensitivity_mask_thresholds(
    roi_names: List[str] = None,
    thresholds: List[float] = None,
    output_dir: Path = None
) -> Dict[str, Dict[float, Path]]:
    """
    Main entry point for sensitivity analysis mask generation.
    
    Args:
        roi_names: List of ROI names (defaults to config)
        thresholds: List of probability thresholds (defaults to PROBABILITY_THRESHOLDS)
        output_dir: Output directory (defaults to config)
        
    Returns:
        Dictionary of ROI->threshold->path mappings
    """
    config = get_config()
    
    if roi_names is None:
        roi_names = config.get('analysis', {}).get('rois', ['VS', 'OFC'])
    
    if thresholds is None:
        thresholds = PROBABILITY_THRESHOLDS
    
    if output_dir is None:
        output_dir = Path(config['paths']['results_dir']) / 'sensitivity_masks'
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting sensitivity analysis for mask thresholds")
    logger.info(f"  ROIs: {roi_names}")
    logger.info(f"  Thresholds: {thresholds}")
    logger.info(f"  Output directory: {output_dir}")
    
    # Generate all masks
    results = iterate_mask_thresholds(roi_names, thresholds, output_dir)
    
    # Generate summary
    generate_threshold_summary(results, output_dir)
    
    # Log results
    valid_count = 0
    total_count = 0
    for roi_name, threshold_paths in results.items():
        for threshold, mask_path in threshold_paths.items():
            total_count += 1
            if mask_path and mask_path.exists():
                valid_count += 1
    
    logger.info(f"Sensitivity mask generation complete: {valid_count}/{total_count} masks valid")
    
    return results

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate thresholded ROI masks for sensitivity analysis'
    )
    parser.add_argument(
        '--rois',
        nargs='+',
        default=None,
        help='ROI names to process (default: from config)'
    )
    parser.add_argument(
        '--thresholds',
        nargs='+',
        type=float,
        default=None,
        help='Probability thresholds (default: 0.30 0.60)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory (default: from config)'
    )
    
    args = parser.parse_args()
    
    try:
        results = run_sensitivity_mask_thresholds(
            roi_names=args.rois,
            thresholds=args.thresholds,
            output_dir=Path(args.output_dir) if args.output_dir else None
        )
        
        # Print summary
        print("\nThreshold Summary:")
        for roi_name, threshold_paths in results.items():
            print(f"\n{roi_name}:")
            for threshold, mask_path in threshold_paths.items():
                if mask_path and mask_path.exists():
                    mask_img = nib.load(str(mask_path))
                    voxels = np.sum(mask_img.get_fdata() > 0)
                    print(f"  {threshold:.2f}: {mask_path} ({voxels} voxels)")
                else:
                    print(f"  {threshold:.2f}: FAILED")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in sensitivity mask threshold generation: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())