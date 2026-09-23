"""
Spatial smoothing module for fMRI ROI data.

Implements spatial smoothing kernels (4mm, 8mm) on preprocessed data.
Generates derived dataset filenames using a pipeline_config_hash.

Primary requirement for FR-002 and US-3.
"""

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import nibabel as nib
import numpy as np
from scipy.ndimage import gaussian_filter

from utils.seed_manager import set_global_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_pipeline_config_hash(
    roi_mask: str,
    kernel_size: float,
    smoothing_type: str = 'spatial'
) -> str:
    """
    Compute a deterministic hash for the pipeline configuration.
    
    Args:
        roi_mask: Path or name of the ROI mask used
        kernel_size: Smoothing kernel size in mm
        smoothing_type: Type of smoothing ('spatial' or 'temporal')
        
    Returns:
        A hexadecimal hash string for the configuration
    """
    config_str = f"{roi_mask}_{kernel_size}_{smoothing_type}"
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]

def load_smoothed_timeseries(input_path: Path) -> np.ndarray:
    """
    Load preprocessed ROI timeseries data.
    
    Args:
        input_path: Path to the input NIfTI file containing ROI data
        
    Returns:
        3D numpy array (x, y, t) or 4D (x, y, z, t)
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    img = nib.load(input_path)
    data = img.get_fdata()
    
    logger.info(f"Loaded data with shape: {data.shape}")
    return data

def apply_spatial_smoothing(
    data: np.ndarray,
    kernel_size_mm: float,
    tr: float = 2.0,
    voxelsize_mm: Tuple[float, float, float] = (2.0, 2.0, 2.0)
) -> np.ndarray:
    """
    Apply Gaussian spatial smoothing to fMRI data.
    
    Converts kernel size from mm to voxels and applies Gaussian filter.
    Boundary handling uses 'reflect' mode as specified.
    
    Args:
        data: 4D numpy array (x, y, z, t) or 3D (x, y, t)
        kernel_size_mm: Full Width at Half Maximum (FWHM) in mm
        tr: Repetition time in seconds (for reference)
        voxelsize_mm: Voxel dimensions in mm (x, y, z)
        
    Returns:
        Smoothed data array with same shape as input
    """
    # Convert FWHM to standard deviation in voxels
    # FWHM = sigma * sqrt(8 * ln(2)) => sigma = FWHM / sqrt(8 * ln(2))
    sigma_voxels = kernel_size_mm / np.sqrt(8 * np.log(2))
    
    # Convert to voxels based on voxel size
    sigma_x = sigma_voxels / voxelsize_mm[0]
    sigma_y = sigma_voxels / voxelsize_mm[1]
    sigma_z = sigma_voxels / voxelsize_mm[2] if len(data.shape) == 4 else 0.0
    
    # Create sigma tuple for gaussian_filter
    # For 4D data: (sigma_x, sigma_y, sigma_z, 0) - no smoothing in time dimension
    if len(data.shape) == 4:
        sigma = (sigma_x, sigma_y, sigma_z, 0.0)
    else:
        # 3D data (x, y, t) - assume no z dimension
        sigma = (sigma_x, sigma_y, 0.0)
    
    # Apply Gaussian filter with reflect boundary handling
    smoothed_data = gaussian_filter(
        data,
        sigma=sigma,
        mode='reflect'
    )
    
    logger.info(f"Applied spatial smoothing with {kernel_size_mm}mm FWHM")
    logger.info(f"Sigma in voxels: {sigma}")
    
    return smoothed_data

def save_smoothed_data(
    smoothed_data: np.ndarray,
    output_path: Path,
    reference_path: Path
) -> None:
    """
    Save smoothed data to NIfTI file, preserving affine and header.
    
    Args:
        smoothed_data: Smoothed numpy array
        output_path: Path to save the output NIfTI file
        reference_path: Path to reference NIfTI file (for affine/header)
    """
    reference_img = nib.load(reference_path)
    affine = reference_img.affine
    header = reference_img.header.copy()
    
    # Create new NIfTI image
    smoothed_img = nib.Nifti1Image(smoothed_data, affine, header)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to disk
    nib.save(smoothed_img, output_path)
    logger.info(f"Saved smoothed data to: {output_path}")

def process_single_roi_file(
    input_path: Path,
    output_dir: Path,
    kernel_size_mm: float,
    roi_mask_name: str,
    voxelsize_mm: Tuple[float, float, float] = (2.0, 2.0, 2.0)
) -> Path:
    """
    Process a single ROI file: load, smooth, and save.
    
    Args:
        input_path: Path to input ROI file
        output_dir: Directory to save output file
        kernel_size_mm: Smoothing kernel size in mm
        roi_mask_name: Name of the ROI mask for hashing
        voxelsize_mm: Voxel dimensions
        
    Returns:
        Path to the output file
    """
    # Compute pipeline config hash
    config_hash = compute_pipeline_config_hash(
        roi_mask=roi_mask_name,
        kernel_size=kernel_size_mm,
        smoothing_type='spatial'
    )
    
    # Generate output filename with hash
    input_stem = input_path.stem
    output_filename = f"{config_hash}_{input_stem}_smoothed.nii.gz"
    output_path = output_dir / output_filename
    
    # Skip if already processed
    if output_path.exists():
        logger.info(f"Output already exists, skipping: {output_path}")
        return output_path
    
    # Load data
    logger.info(f"Loading data from: {input_path}")
    data = load_smoothed_timeseries(input_path)
    
    # Apply spatial smoothing
    smoothed_data = apply_spatial_smoothing(
        data=data,
        kernel_size_mm=kernel_size_mm,
        voxelsize_mm=voxelsize_mm
    )
    
    # Save smoothed data
    save_smoothed_data(
        smoothed_data=smoothed_data,
        output_path=output_path,
        reference_path=input_path
    )
    
    return output_path

def process_roi_directory(
    input_dir: Path,
    output_dir: Path,
    kernel_sizes: List[float],
    roi_mask_name: str,
    voxelsize_mm: Tuple[float, float, float] = (2.0, 2.0, 2.0)
) -> Dict[str, List[Path]]:
    """
    Process all ROI files in a directory with multiple kernel sizes.
    
    Args:
        input_dir: Directory containing input ROI files
        output_dir: Directory to save output files
        kernel_sizes: List of kernel sizes in mm (e.g., [4.0, 8.0])
        roi_mask_name: Name of the ROI mask for hashing
        voxelsize_mm: Voxel dimensions
        
    Returns:
        Dictionary mapping kernel size to list of output paths
    """
    results = {}
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all NIfTI files
    nifti_files = list(input_dir.glob("*.nii.gz")) + list(input_dir.glob("*.nii"))
    
    if not nifti_files:
        logger.warning(f"No NIfTI files found in: {input_dir}")
        return results
    
    logger.info(f"Found {len(nifti_files)} ROI files to process")
    
    for kernel_size in kernel_sizes:
        results[kernel_size] = []
        logger.info(f"Processing with kernel size: {kernel_size}mm")
        
        for input_path in nifti_files:
            output_path = process_single_roi_file(
                input_path=input_path,
                output_dir=output_dir,
                kernel_size_mm=kernel_size,
                roi_mask_name=roi_mask_name,
                voxelsize_mm=voxelsize_mm
            )
            results[kernel_size].append(output_path)
    
    return results

def main():
    """Main entry point for spatial smoothing CLI."""
    parser = argparse.ArgumentParser(
        description="Apply spatial smoothing to preprocessed fMRI ROI data"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing input ROI files"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory to save smoothed ROI files"
    )
    parser.add_argument(
        "--kernels",
        type=float,
        nargs="+",
        default=[4.0, 8.0],
        help="Smoothing kernel sizes in mm (default: 4.0 8.0)"
    )
    parser.add_argument(
        "--roi-mask",
        type=str,
        default="aal_atlas",
        help="Name of ROI mask used (for config hash)"
    )
    parser.add_argument(
        "--voxelsize",
        type=float,
        nargs=3,
        default=(2.0, 2.0, 2.0),
        help="Voxel dimensions in mm (x y z)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    # Set global seed
    set_global_seed(args.seed)
    
    logger.info(f"Spatial smoothing started")
    logger.info(f"Input directory: {args.input_dir}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Kernel sizes: {args.kernels}")
    logger.info(f"ROI mask: {args.roi_mask}")
    
    # Process ROI directory
    results = process_roi_directory(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        kernel_sizes=args.kernels,
        roi_mask_name=args.roi_mask,
        voxelsize_mm=tuple(args.voxelsize)
    )
    
    # Log summary
    total_files = sum(len(paths) for paths in results.values())
    logger.info(f"Processing complete. Processed {total_files} files across {len(results)} kernel sizes")
    
    # Save manifest
    manifest_path = args.output_dir / "spatial_smoothing_manifest.json"
    manifest = {
        "input_dir": str(args.input_dir),
        "output_dir": str(args.output_dir),
        "kernel_sizes": args.kernels,
        "roi_mask": args.roi_mask,
        "voxelsize": args.voxelsize,
        "seed": args.seed,
        "results": {
            str(k): [str(p) for p in paths]
            for k, paths in results.items()
        }
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Manifest saved to: {manifest_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
