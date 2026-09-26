"""
Spatial Smoothing Module for fMRI Data (NIfTI).

This module implements spatial smoothing kernels (4mm, 8mm) on 3D/4D NIfTI data.
It is distinct from temporal_smoothing.py (T013) which operates on 1D ROI time-series.
This module operates on the volumetric data directly or on extracted 3D/4D masks.

Dependencies:
  - nibabel: For NIfTI I/O
  - scipy: For Gaussian convolution
  - numpy: For array manipulation
"""

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
import nibabel as nib
from scipy.ndimage import gaussian_filter

# Project imports
from models.simulation_config import SimulationConfig
from utils.seed_manager import set_global_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SpatialSmoothingError(Exception):
    """Custom exception for spatial smoothing failures."""
    pass


def compute_pipeline_config_hash(config: SimulationConfig) -> str:
    """
    Compute a deterministic hash of the pipeline configuration.
    This ensures derived data filenames reflect the exact parameters used.
    """
    config_dict = {
        'smoothing_kernel_mm': getattr(config, 'smoothing_kernel', 4.0),
        'random_seed': config.random_seed,
        'sample_size_target': config.sample_size_target
    }
    json_str = json.dumps(config_dict, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()[:16]


def load_smoothed_timeseries(roi_path: Path) -> Tuple[np.ndarray, nib.Nifti1Image]:
    """
    Load ROI time-series data from a NIfTI file.
    Returns the data array and the affine/header info for reconstruction.
    """
    if not roi_path.exists():
        raise SpatialSmoothingError(f"ROI file not found: {roi_path}")

    try:
        img = nib.load(str(roi_path))
        data = img.get_fdata()
        return data, img
    except Exception as e:
        raise SpatialSmoothingError(f"Failed to load NIfTI {roi_path}: {e}")


def apply_spatial_smoothing(
    data: np.ndarray,
    kernel_mm: float,
    voxel_sizes: Tuple[float, float, float],
    mode: str = 'reflect'
) -> np.ndarray:
    """
    Apply spatial Gaussian smoothing to 3D or 4D NIfTI data.

    Args:
        data: 3D (x, y, z) or 4D (x, y, z, t) numpy array.
        kernel_mm: Full Width at Half Maximum (FWHM) in millimeters.
        voxel_sizes: Tuple (dx, dy, dz) in millimeters.
        mode: Boundary handling mode for scipy.ndimage (default 'reflect').

    Returns:
        Smoothed numpy array of the same shape.
    """
    if data.ndim not in (3, 4):
        raise SpatialSmoothingError(f"Expected 3D or 4D data, got {data.ndim}D")

    if kernel_mm <= 0:
        logger.warning("Kernel size <= 0. Returning unsmoothed data.")
        return data

    # Calculate sigma in voxels: sigma = FWHM / (2 * sqrt(2 * ln(2)))
    # Standard Gaussian conversion: sigma = FWHM / 2.35482
    sigma_factor = 2.35482
    sigma_voxels = kernel_mm / sigma_factor

    # Calculate sigma for each dimension based on voxel size
    # sigma_voxel_dim = sigma_voxels / voxel_size
    sigmas = [sigma_voxels / v for v in voxel_sizes]

    # If 4D, we only smooth the spatial dimensions (0, 1, 2), not time (3)
    if data.ndim == 4:
        # Apply filter to spatial dimensions only
        # scipy.ndimage.gaussian_filter allows specifying axes
        # We need to construct a sigma list where time dimension sigma is 0
        sigmas_4d = list(sigmas) + [0.0]
        smoothed_data = gaussian_filter(data, sigma=sigmas_4d, mode=mode)
    else:
        smoothed_data = gaussian_filter(data, sigma=sigmas, mode=mode)

    return smoothed_data


def save_smoothed_data(
    smoothed_data: np.ndarray,
    original_img: nib.Nifti1Image,
    output_path: Path,
    kernel_mm: float
) -> None:
    """
    Save smoothed data to a new NIfTI file.
    The filename will include the kernel size to distinguish versions.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create new NIfTI image with same affine and header
    smoothed_img = nib.Nifti1Image(smoothed_data, original_img.affine, header=original_img.header)

    try:
        nib.save(smoothed_img, str(output_path))
        logger.info(f"Saved smoothed data to {output_path} (Kernel: {kernel_mm}mm)")
    except Exception as e:
        raise SpatialSmoothingError(f"Failed to save smoothed data to {output_path}: {e}")


def process_single_roi_file(
    input_path: Path,
    output_dir: Path,
    kernel_mm: float,
    voxel_sizes: Optional[Tuple[float, float, float]] = None
) -> Path:
    """
    Process a single ROI NIfTI file: load, smooth, and save.

    Args:
        input_path: Path to input NIfTI file.
        output_dir: Directory to write output.
        kernel_mm: Smoothing kernel FWHM in mm.
        voxel_sizes: Optional override for voxel sizes (otherwise derived from header).

    Returns:
        Path to the saved output file.
    """
    data, img = load_smoothed_timeseries(input_path)

    if voxel_sizes is None:
        # Derive from affine
        affine = img.affine
        # Extract voxel sizes from the upper 3x3 block of affine
        # This is an approximation; for precise values, one might use img.header.get_zooms()
        voxel_sizes = tuple(img.header.get_zooms()[:3])

    logger.info(f"Applying {kernel_mm}mm spatial smoothing to {input_path.name}...")
    smoothed_data = apply_spatial_smoothing(data, kernel_mm, voxel_sizes)

    # Construct output filename: <basename>_smoothed_<kernel>mm.nii.gz
      # Ensure output_dir exists
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem
    output_filename = f"{stem}_smoothed_{kernel_mm}mm.nii.gz"
    output_path = output_dir / output_filename

    save_smoothed_data(smoothed_data, img, output_path, kernel_mm)

    return output_path


def process_roi_directory(
    input_dir: Path,
    output_dir: Path,
    kernel_mm: float,
    config: Optional[SimulationConfig] = None
) -> List[Path]:
    """
    Process all NIfTI files in a directory (e.g., an ROI directory).

    Args:
        input_dir: Directory containing input NIfTI files.
        output_dir: Directory to write output files.
        kernel_mm: Smoothing kernel FWHM in mm.
        config: Optional SimulationConfig to include in metadata.

    Returns:
        List of paths to saved output files.
    """
    if not input_dir.exists():
        raise SpatialSmoothingError(f"Input directory does not exist: {input_dir}")

    # Set seed if config provided
    if config:
        set_global_seed(config.random_seed)

    nifti_files = list(input_dir.glob("*.nii")) + list(input_dir.glob("*.nii.gz"))
    if not nifti_files:
        logger.warning(f"No NIfTI files found in {input_dir}")
        return []

    output_paths = []
    for nifti_file in nifti_files:
        try:
            out_path = process_single_roi_file(nifti_file, output_dir, kernel_mm)
            output_paths.append(out_path)
        except SpatialSmoothingError as e:
            logger.error(f"Skipping {nifti_file} due to error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing {nifti_file}: {e}")

    return output_paths


def main() -> None:
    """
    CLI entry point for spatial smoothing.
    Usage: python -m preprocess.spatial_smoothing --input_dir <path> --output_dir <path> --kernel 4
    """
    parser = argparse.ArgumentParser(
        description="Apply spatial smoothing to fMRI NIfTI data."
    )
    parser.add_argument(
        "--input_dir",
        type=Path,
        required=True,
        help="Directory containing input NIfTI files."
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        required=True,
        help="Directory to write smoothed output files."
    )
    parser.add_argument(
        "--kernel",
        type=float,
        required=True,
        help="Smoothing kernel FWHM in mm (e.g., 4, 8)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )

    args = parser.parse_args()

    # Basic validation
    if args.kernel <= 0:
        logger.error("Kernel size must be positive.")
        sys.exit(1)

    try:
        # Create a minimal config for seed management if needed
        config = SimulationConfig(
            sample_size_target=10,
            smoothing_kernel=args.kernel,
            num_iterations=1,
            random_seed=args.seed
        )

        output_paths = process_roi_directory(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            kernel_mm=args.kernel,
            config=config
        )

        logger.info(f"Completed spatial smoothing. Processed {len(output_paths)} files.")

        # Log results to a JSON manifest if files were produced
        if output_paths:
            manifest_path = args.output_dir / "spatial_smoothing_manifest.json"
            manifest = {
                "kernel_mm": args.kernel,
                "input_dir": str(args.input_dir),
                "output_dir": str(args.output_dir),
                "files": [str(p) for p in output_paths],
                "seed": args.seed
            }
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            logger.info(f"Manifest saved to {manifest_path}")

    except Exception as e:
        logger.error(f"Spatial smoothing pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()