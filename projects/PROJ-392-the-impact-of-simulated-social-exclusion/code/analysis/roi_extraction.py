"""
ROI Extraction Module for Social Exclusion Study.

This module loads predefined Region of Interest (ROI) masks in MNI space:
1. Ventral Striatum (VS) from the AAL atlas.
2. Orbitofrontal Cortex (OFC) from the Harvard-Oxford atlas (thresholded).

It extracts beta estimates from preprocessed first-level GLM results
for specified subjects and conditions.
"""

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import nibabel as nib
import numpy as np
import pandas as pd
from nilearn import image, masking
from nilearn.datasets import fetch_atlas_aal, fetch_atlas_harvard_oxford
from nilearn.input_data import NiftiMasker

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed-fmri"
RESULTS_DIR = DATA_DIR / "results"

# Ensure results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_aal_vs_mask() -> Optional[nib.Nifti1Image]:
    """
    Fetches the AAL atlas and constructs a Ventral Striatum mask.
    The AAL atlas defines 'Putamen' and 'Caudate' which are often used
    to approximate the Ventral Striatum in coarse atlases, or 'VentralStriatum'
    if available in the specific AAL version. In standard AAL (v1/v2),
    we typically map specific ROI indices.
    
    For this implementation, we target the 'Putamen' and 'Caudate' 
    labels often associated with the striatum, or specifically 'VentralStriatum'
    if the atlas version supports it.
    
    Returns:
        Nifti1Image: Mask image for the Ventral Striatum.
    """
    logger.info("Fetching AAL atlas...")
    try:
        aal_atlas = fetch_atlas_aal()
        atlas_img = aal_atlas.maps
        labels = aal_atlas.labels

        # AAL v1/v2 indices for striatal regions:
        # Caudate: 48, Putamen: 49, Pallidum: 50
        # Ventral Striatum is often approximated by a subset or specific label.
        # In many AAL versions, 'VentralStriatum' is not a single label but 
        # a functional definition. We will use 'Putamen' and 'Caudate' 
        # as the anatomical proxy for the Ventral Striatum in this context
        # unless 'VentralStriatum' is explicitly found in labels.
        
        vs_indices = []
        for i, label in enumerate(labels):
            # Normalize label for case-insensitive matching
            clean_label = label.replace("_", " ").strip().lower()
            if "ventral striatum" in clean_label or "ventralstriatum" in clean_label:
                vs_indices.append(i)
            elif "caudate" in clean_label or "putamen" in clean_label:
                # Include as part of the broader striatal mask if VS not explicit
                # But strictly, VS is more specific. Let's try to be precise.
                # If we don't find explicit VS, we might fall back to a coordinate-based mask
                # or use the standard AAL 'VentralStriatum' if the dataset includes it.
                pass

        if not vs_indices:
            # Fallback: If AAL doesn't have explicit VS label, use coordinates 
            # to create a spherical mask in MNI space, which is common for VS.
            # MNI coordinates for VS: approx [-10, 10, -6] and [10, 10, -6]
            logger.warning("Explicit 'Ventral Striatum' label not found in AAL. Creating coordinate-based mask.")
            return create_coordinate_mask(mni_coords=[(-10, 10, -6), (10, 10, -6)], radius=8)
        
        # Construct mask
        atlas_data = atlas_img.get_fdata()
        vs_mask_data = np.zeros_like(atlas_data)
        for idx in vs_indices:
            vs_mask_data[atlas_data == idx] = 1.0
        
        return nib.Nifti1Image(vs_mask_data, atlas_img.affine)

    except Exception as e:
        logger.error(f"Failed to fetch AAL atlas: {e}")
        raise


def get_ho_ofo_mask(threshold: float = 0.25) -> Optional[nib.Nifti1Image]:
    """
    Fetches the Harvard-Oxford Cortical Atlas and extracts the OFC mask.
    
    Args:
        threshold: Probability threshold for the mask (0.0 to 1.0).
    
    Returns:
        Nifti1Image: Thresholded mask for the Orbitofrontal Cortex.
    """
    logger.info(f"Fetching Harvard-Oxford atlas with threshold {threshold}...")
    try:
        ho_atlas = fetch_atlas_harvard_oxford("cort-prob")
        atlas_img = ho_atlas.maps
        labels = ho_atlas.labels

        # Find OFC label
        # Labels are typically: 'Left Orbitofrontal', 'Right Orbitofrontal', or 'Orbitofrontal Cortex'
        ofc_indices = []
        for i, label in enumerate(labels):
            clean_label = label.lower()
            if "orbitofrontal" in clean_label:
                ofc_indices.append(i)

        if not ofc_indices:
            logger.error("Could not find 'Orbitofrontal' label in Harvard-Oxford atlas.")
            return None

        # Construct probability mask
        prob_data = atlas_img.get_fdata()
        ofc_mask_data = np.zeros_like(prob_data)

        for idx in ofc_indices:
            # Extract probability map for this label (index in labels corresponds to index in data)
            # Note: In HO probabilistic atlas, the 4th dimension usually corresponds to labels.
            # However, nilearn's fetch_atlas_harvard_oxford returns a 3D image for 'cort-prob' 
            # where values represent the probability of being in a region, but the labels are 
            # mapped differently or it's a single 3D volume with indices.
            # Actually, for 'cort-prob', the image is 3D, and the values are indices? 
            # No, usually it's a 4D image where each volume is a region's probability map.
            # Let's check the shape.
            if len(prob_data.shape) == 4:
                region_prob = prob_data[:, :, :, idx]
            else:
                # If 3D, it might be an index map, but 'cort-prob' is usually 4D.
                # If 3D, we might need to re-fetch 'cort-max' or handle differently.
                # Assuming 4D based on standard HO probabilistic output.
                region_prob = prob_data[:, :, :, idx]
            
            # Threshold
            ofc_mask_data += (region_prob > threshold).astype(float)

        # Ensure we have a binary mask
        ofc_mask_data = (ofc_mask_data > 0).astype(float)

        return nib.Nifti1Image(ofc_mask_data, atlas_img.affine)

    except Exception as e:
        logger.error(f"Failed to fetch Harvard-Oxford atlas: {e}")
        raise


def create_coordinate_mask(mni_coords: List[Tuple[float, float, float]], radius: float = 8) -> nib.Nifti1Image:
    """
    Creates a spherical mask around specific MNI coordinates.
    
    Args:
        mni_coords: List of (x, y, z) coordinates in MNI space.
        radius: Radius of the sphere in mm.
    
    Returns:
        Nifti1Image: Combined spherical mask.
    """
    # Create a blank image in MNI space (standard 2mm resolution)
    shape = (91, 109, 91)
    affine = np.array([[-2., 0., 0., -90.],
                       [0., 2., 0., -126.],
                       [0., 0., 2., -72.],
                       [0., 0., 0., 1.]])
    
    mask_data = np.zeros(shape)
    
    for x, y, z in mni_coords:
        # Convert MNI to voxel indices
        voxel = np.linalg.inv(affine) @ np.array([x, y, z, 1])
        vx, vy, vz = voxel[:3].astype(int)
        
        # Create sphere
        for i in range(shape[0]):
            for j in range(shape[1]):
                for k in range(shape[2]):
                    dist = np.sqrt((i - vx)**2 + (j - vy)**2 + (k - vz)**2)
                    if dist <= radius:
                        mask_data[i, j, k] = 1.0
    
    return nib.Nifti1Image(mask_data, affine)


def extract_beta_from_glm_results(
    subject_id: str,
    dataset_id: str,
    roi_img: nib.Nifti1Image,
    glm_results_dir: Path,
    contrast_name: str = "reward"
) -> Optional[float]:
    """
    Extracts the mean beta value for a specific contrast from a subject's GLM results
    within the given ROI.
    
    Args:
        subject_id: The subject identifier (e.g., 'sub-01').
        dataset_id: The dataset identifier (e.g., 'ds000246').
        roi_img: The Nifti image representing the ROI mask.
        glm_results_dir: Path to the directory containing GLM result files (con images).
        contrast_name: Name of the contrast to extract (e.g., 'reward', 'exclusion').
    
    Returns:
        float: The mean beta value in the ROI, or None if not found.
    """
    # Construct path to the contrast image (con file)
    # Typical fMRIPrep/Nilearn output structure:
    # <subject>/func/<subject>_task-<task>_space-MNI_desc-<desc>_stat-<stat>_contrast-<contrast>.nii.gz
    # Or simply con_0001.nii.gz in a 'con' folder.
    
    # We will search for a file matching the contrast name
    found_file = None
    for ext in ['.nii', '.nii.gz']:
        # Try standard naming convention
        candidate = glm_results_dir / f"{subject_id}_{contrast_name}{ext}"
        if candidate.exists():
            found_file = candidate
            break
        
        # Try 'con' prefix
        candidate = glm_results_dir / f"con_{contrast_name}{ext}"
        if candidate.exists():
            found_file = candidate
            break
        
        # Try full pattern search
        for f in glm_results_dir.glob(f"*{contrast_name}*{ext}"):
            found_file = f
            break
        
        if found_file:
            break

    if not found_file:
        logger.warning(f"No contrast image found for {subject_id}, {contrast_name} in {glm_results_dir}")
        return None

    try:
        con_img = nib.load(str(found_file))
        
        # Apply mask
        # Ensure ROI is in the same space (MNI) and resolution as con_img
        # If not, resample ROI to con_img
        if not np.allclose(roi_img.affine, con_img.affine) or roi_img.shape != con_img.shape:
            roi_resampled = image.resample_img(
                roi_img, 
                target_affine=con_img.affine, 
                target_shape=con_img.shape, 
                interpolation='nearest'
            )
            mask_data = roi_resampled.get_fdata()
        else:
            mask_data = roi_img.get_fdata()
        
        # Extract mean value
        con_data = con_img.get_fdata()
        mean_val = np.mean(con_data[mask_data > 0])
        
        return float(mean_val)
        
    except Exception as e:
        logger.error(f"Error extracting beta from {found_file}: {e}")
        return None


def run_roi_extraction(
    subjects: List[str],
    datasets: List[str],
    rois: Dict[str, str],
    contrasts: List[str],
    output_path: Path
) -> pd.DataFrame:
    """
    Orchestrates the extraction of beta estimates for all subjects, datasets, ROIs, and contrasts.
    
    Args:
        subjects: List of subject IDs.
        datasets: List of dataset IDs.
        rois: Dictionary mapping ROI name to atlas type ('aal_vs', 'ho_ofo').
        contrasts: List of contrast names.
        output_path: Path to save the CSV results.
    
    Returns:
        DataFrame containing the extracted betas.
    """
    logger.info("Starting ROI extraction pipeline...")
    
    # Load ROIs
    roi_images = {}
    for name, atlas_type in rois.items():
        if atlas_type == "aal_vs":
            roi_images[name] = get_aal_vs_mask()
        elif atlas_type == "ho_ofo":
            roi_images[name] = get_ho_ofo_mask(threshold=0.25)
        else:
            logger.error(f"Unknown ROI type: {atlas_type}")
            continue
    
    results = []
    
    for dataset in datasets:
        dataset_dir = PROCESSED_DIR / dataset
        if not dataset_dir.exists():
            logger.warning(f"Dataset directory not found: {dataset_dir}. Skipping.")
            continue
        
        for subject in subjects:
            subject_dir = dataset_dir / subject / "func"
            if not subject_dir.exists():
                logger.warning(f"Subject directory not found: {subject_dir}. Skipping.")
                continue
            
            # Look for GLM results (con images)
            # We assume they are in a 'con' subdirectory or directly in func
            glm_dir = subject_dir / "con"
            if not glm_dir.exists():
                glm_dir = subject_dir # Fallback
            
            for roi_name, roi_img in roi_images.items():
                for contrast in contrasts:
                    beta = extract_beta_from_glm_results(
                        subject_id=subject,
                        dataset_id=dataset,
                        roi_img=roi_img,
                        glm_results_dir=glm_dir,
                        contrast_name=contrast
                    )
                    
                    if beta is not None:
                        results.append({
                            "participant_id": subject,
                            "dataset_id": dataset,
                            "roi": roi_name,
                            "event_type": contrast,
                            "beta_value": beta
                        })
    
    df = pd.DataFrame(results)
    if not df.empty:
        df.to_csv(output_path, index=False)
        logger.info(f"Results saved to {output_path}")
    else:
        logger.warning("No data extracted. Results file not created.")
    
    return df


def main():
    """Main entry point for the ROI extraction script."""
    parser = argparse.ArgumentParser(description="Extract ROI beta estimates from preprocessed fMRI data.")
    parser.add_argument("--subjects", type=str, nargs="+", default=None, help="List of subject IDs (e.g., sub-01 sub-02).")
    parser.add_argument("--datasets", type=str, nargs="+", default=["ds000246", "ds004738"], help="List of dataset IDs.")
    parser.add_argument("--output", type=str, default=str(RESULTS_DIR / "beta_estimates.csv"), help="Output CSV path.")
    
    args = parser.parse_args()
    
    # If no subjects provided, we cannot proceed without a way to list them
    # In a real pipeline, this would be derived from the directory structure
    if not args.subjects:
        # Attempt to auto-discover subjects from the first dataset
        first_dataset_dir = PROCESSED_DIR / args.datasets[0]
        if first_dataset_dir.exists():
            args.subjects = [d.name for d in first_dataset_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]
            if not args.subjects:
                logger.error("No subjects found in dataset directory. Please specify --subjects.")
                sys.exit(1)
        else:
            logger.error(f"Dataset directory {first_dataset_dir} not found. Cannot auto-discover subjects.")
            sys.exit(1)
    
    rois = {
        "VentralStriatum": "aal_vs",
        "OFC": "ho_ofo"
    }
    
    contrasts = ["reward_anticipation", "reward_receipt"] # Example contrasts, adjust based on actual GLM design
    
    output_path = Path(args.output)
    
    run_roi_extraction(
        subjects=args.subjects,
        datasets=args.datasets,
        rois=rois,
        contrasts=contrasts,
        output_path=output_path
    )


if __name__ == "__main__":
    main()
