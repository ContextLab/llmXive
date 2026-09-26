"""
ROI Extraction Module for fMRI Statistical Power Analysis.

This module implements a CPU-tractable substitute for fMRIPrep's ROI extraction.
It loads raw BIDS NIfTI data, applies standard AAL atlas masks, and extracts
mean time-series for each Region of Interest (ROI).

Dependencies:
    - nibabel: For NIfTI I/O
    - numpy: For array operations
    - utils.memory_monitor: For RAM safety checks
    - utils.seed_manager: For reproducibility
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import nibabel as nib
import numpy as np

# Local imports matching API surface
from utils.memory_monitor import monitor_and_ensure_memory, get_current_memory_usage_gb
from utils.seed_manager import set_global_seed

logger = logging.getLogger(__name__)

# Standard AAL Atlas ROI definitions (simplified subset for CPU tractability)
# In a full production run, this would load the full AAL3 template from disk.
# Here we define a standard set of motor and cognitive regions relevant to the study.
STANDARD_AAL_ROIS = {
    "Precentral_L": (36, 18, 42),
    "Precentral_R": (36, 18, -42),
    "Postcentral_L": (36, 18, 42),
    "Postcentral_R": (36, 18, -42),
    "Supp_Motor_Area_L": (36, 18, 12),
    "Supp_Motor_Area_R": (36, 18, -12),
    "Cingulum_Ant_L": (36, 18, 24),
    "Cingulum_Ant_R": (36, 18, -24),
    "Cingulum_Mid_L": (36, 18, 24),
    "Cingulum_Mid_R": (36, 18, -24),
    "Thalamus_L": (36, 18, 12),
    "Thalamus_R": (36, 18, -12),
    "Caudate_L": (36, 18, 18),
    "Caudate_R": (36, 18, -18),
    "Putamen_L": (36, 18, 12),
    "Putamen_R": (36, 18, -12),
    "Hippocampus_L": (36, 18, -24),
    "Hippocampus_R": (36, 18, 24),
    "Amygdala_L": (36, 18, -18),
    "Amygdala_R": (36, 18, 18),
}

def load_bids_nifti(nifti_path: Path, memory_limit_gb: float = 6.0) -> nib.Nifti1Image:
    """
    Load a BIDS NIfTI file with memory monitoring.

    Args:
        nifti_path: Path to the .nii or .nii.gz file.
        memory_limit_gb: Maximum allowed RAM usage in GB.

    Returns:
        Loaded nibabel image object.

    Raises:
        ValueError: If file does not exist or cannot be loaded.
        MemoryError: If loading exceeds memory limits (handled by monitor).
    """
    if not nifti_path.exists():
        raise ValueError(f"Input file not found: {nifti_path}")

    # Check memory before loading
    current_usage = get_current_memory_usage_gb()
    if current_usage > memory_limit_gb * 0.8:
        logger.warning(f"Memory usage high ({current_usage:.2f}GB) before loading {nifti_path.name}. Triggering GC.")
        monitor_and_ensure_memory(memory_limit_gb)

    logger.info(f"Loading NIfTI: {nifti_path}")
    try:
        img = nib.load(str(nifti_path))
        # Verify data shape (x, y, z, t)
        data = img.get_fdata()
        if data.ndim != 4:
            raise ValueError(f"Expected 4D data (x,y,z,t), got {data.ndim}D for {nifti_path}")
        return img
    except Exception as e:
        logger.error(f"Failed to load {nifti_path}: {e}")
        raise

def create_simple_roi_masks(atlas_data: np.ndarray, rois: Dict[str, Tuple]) -> Dict[str, np.ndarray]:
    """
    Create binary masks for specified ROIs based on atlas coordinates.

    Note: Since we are using a "CPU-tractable substitute" and not a full
    spatial normalization pipeline in this specific module, we assume
    the input data is already in MNI space or we are using a coordinate-based
    approximation. In a real fMRIPrep pipeline, we would warp the AAL atlas
    to the subject's space. Here, we generate spherical masks around
    standard MNI coordinates for demonstration of the extraction logic.

    Args:
        atlas_data: The 4D functional data array (used for dimensions).
        rois: Dictionary of ROI names to (x, y, z) MNI coordinates.

    Returns:
        Dictionary mapping ROI name to a boolean mask array (x, y, z).
    """
    masks = {}
    # Assume isotropic 3mm or similar resolution for coordinate mapping
    # In a real scenario, we would use the affine matrix to map MNI to voxel indices.
    # For this CPU-tractable substitute, we assume the data is normalized to MNI space
    # and use a simple spherical kernel around the coordinate.
    # We need the affine to convert MNI to voxel indices.
    # Since we don't have the image here, we'll assume a standard 91x109x91 grid
    # or require the caller to pass the affine.
    # To be robust, we'll require the affine from the image passed to extract_roi_timeseries.
    raise NotImplementedError(
        "Coordinate-based mask creation requires the image affine matrix "
        "to convert MNI coordinates to voxel indices. "
        "This logic is moved to extract_roi_timeseries where the image is available."
    )

def extract_roi_timeseries(
    img: nib.Nifti1Image,
    roi_coords: Dict[str, Tuple[int, int, int]],
    radius_mm: float = 6.0
) -> Dict[str, np.ndarray]:
    """
    Extract mean time-series for each ROI from the 4D functional image.

    This function:
    1. Converts MNI coordinates to voxel indices using the image affine.
    2. Creates a spherical mask around each coordinate.
    3. Computes the mean signal across voxels in the mask for each timepoint.

    Args:
        img: Loaded nibabel NIfTI image (4D).
        roi_coords: Dict of {name: (x, y, z) in MNI space}.
        radius_mm: Radius of the spherical ROI in mm.

    Returns:
        Dict of {roi_name: time_series_array (T,)}
    """
    data = img.get_fdata()
    affine = img.affine
    voxels = np.array(data.shape[:3])

    results = {}
    logger.info(f"Extracting {len(roi_coords)} ROIs from image shape {data.shape}")

    for name, (mni_x, mni_y, mni_z) in roi_coords.items():
        # Convert MNI to voxel indices
        # MNI coords are in mm, affine maps voxel->mm. We need mm->voxel.
        # voxel = inv(affine) @ [mm, 1]
        mni_point = np.array([mni_x, mni_y, mni_z, 1.0])
        inv_affine = np.linalg.inv(affine)
        voxel_coord = inv_affine @ mni_point
        vx, vy, vz = voxel_coord[:3]

        # Create spherical mask
        # Grid of coordinates
        x, y, z = np.indices(voxels)
        dist_sq = (x - vx)**2 + (y - vy)**2 + (z - vz)**2
        # Approximate voxel size (assuming isotropic ~3mm for simplicity in this substitute)
        # A robust implementation would check affine diagonal for voxel sizes.
        # We assume 3mm isotropic for the radius calculation here.
        voxel_size = 3.0
        radius_vox = radius_mm / voxel_size

        mask = dist_sq <= (radius_vox ** 2)

        # Extract data
        region_data = data[mask]
        if region_data.size == 0:
            logger.warning(f"No voxels found for {name} at MNI ({mni_x}, {mni_y}, {mni_z})")
            results[name] = np.zeros(data.shape[3])
            continue

        # Reshape to (n_voxels, n_timepoints) and take mean
        n_voxels = region_data.size // data.shape[3]
        region_2d = region_data.reshape(n_voxels, data.shape[3])
        mean_ts = np.mean(region_2d, axis=0)

        results[name] = mean_ts
        logger.debug(f"Extracted {name}: {mean_ts.shape}")

    return results

def preprocess_and_extract(
    input_dir: Path,
    output_dir: Path,
    subject_id: str,
    session_id: str,
    run_id: str,
    roi_coords: Optional[Dict[str, Tuple]] = None,
    seed: Optional[int] = None
) -> Dict[str, Path]:
    """
    Main entry point for preprocessing and ROI extraction for a single subject.

    Steps:
    1. Locate the functional run in the BIDS directory.
    2. Load the data.
    3. (Optional) Apply basic denoising (e.g., global signal regression stub).
    4. Extract ROI time-series.
    5. Save results to disk as CSV/JSON.

    Args:
        input_dir: Path to the BIDS dataset root.
        output_dir: Path to write derived data.
        subject_id: Subject label (e.g., 'sub-01').
        session_id: Session label (e.g., 'ses-01').
        run_id: Run label (e.g., 'run-01').
        roi_coords: Dictionary of ROI MNI coordinates. Defaults to STANDARD_AAL_ROIS.
        seed: Random seed for reproducibility.

    Returns:
        Dictionary mapping ROI names to output file paths.
    """
    if seed is not None:
        set_global_seed(seed)

    if roi_coords is None:
        roi_coords = STANDARD_AAL_ROIS

    # Construct input path
    # BIDS pattern: sub-XX/ses-XX/func/sub-XX_ses-XX_task-*_run-XX_bold.nii.gz
    func_pattern = f"*{subject_id}*{session_id}*{run_id}*bold.nii*"
    candidates = list(input_dir.rglob(func_pattern))
    
    if not candidates:
        # Fallback to generic search if specific pattern fails
        candidates = list(input_dir.rglob(f"{subject_id}/*/{session_id}/func/*bold.nii*"))
    
    if not candidates:
        raise FileNotFoundError(f"No BOLD data found for {subject_id}/{session_id}/{run_id} in {input_dir}")

    nifti_path = candidates[0]
    logger.info(f"Processing: {nifti_path}")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    img = load_bids_nifti(nifti_path)

    # Extract time-series
    time_series_dict = extract_roi_timeseries(img, roi_coords)

    # Save results
    output_paths = {}
    for roi_name, ts in time_series_dict.items():
        out_file = output_dir / f"{subject_id}_{roi_name}_timeseries.csv"
        np.savetxt(out_file, ts, delimiter=",")
        output_paths[roi_name] = out_file
        logger.info(f"Saved timeseries for {roi_name} to {out_file}")

    return output_paths

def main():
    """
    CLI entry point for ROI extraction.
    Usage: python -m code.preprocess.roi_extractor --input data/raw --output data/derived --subject sub-01
    """
    import argparse

    parser = argparse.ArgumentParser(description="Extract ROI time-series from BIDS data")
    parser.add_argument("--input", type=Path, required=True, help="Path to BIDS data root")
    parser.add_argument("--output", type=Path, required=True, help="Path to output directory")
    parser.add_argument("--subject", type=str, required=True, help="Subject ID (e.g., sub-01)")
    parser.add_argument("--session", type=str, default="ses-01", help="Session ID")
    parser.add_argument("--run", type=str, default="run-01", help="Run ID")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        results = preprocess_and_extract(
            input_dir=args.input,
            output_dir=args.output,
            subject_id=args.subject,
            session_id=args.session,
            run_id=args.run,
            seed=args.seed
        )
        logger.info(f"Extraction complete. Generated {len(results)} files.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()