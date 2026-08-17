import os
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import nibabel as nib

from nilearn.datasets import fetch_atlas_harvard_oxford
from config import get_config
from utils.logging_config import get_logger, info, error, warning

logger = get_logger(__name__)

def fetch_harvard_oxford_subcortical() -> Tuple[nib.Nifti1Image, List[str]]:
    """
    Fetch the Harvard-Oxford Subcortical Structural Atlas.
    Returns the image object and the list of region labels.
    """
    logger.info("Fetching Harvard-Oxford Subcortical Atlas...")
    atlas_img = fetch_atlas_harvard_oxford('subcortical')
    # The labels in nilearn are 1-indexed, index 0 is 'Background'
    labels = list(atlas_img.labels)
    return atlas_img, labels

def fetch_harvard_oxford_cortical() -> Tuple[nib.Nifti1Image, List[str]]:
    """
    Fetch the Harvard-Oxford Cortical Structural Atlas.
    Returns the image object and the list of region labels.
    """
    logger.info("Fetching Harvard-Oxford Cortical Atlas...")
    atlas_img = fetch_atlas_harvard_oxford('cortical-prob')
    labels = list(atlas_img.labels)
    return atlas_img, labels

def generate_coordinate_mask(
    atlas_img: nib.Nifti1Image,
    label_name: str,
    labels: List[str]
) -> Optional[np.ndarray]:
    """
    Generate a boolean mask array for a specific label from the atlas.
    """
    if label_name not in labels:
        logger.error(f"Label '{label_name}' not found in atlas labels.")
        return None

    # Find the index of the label (labels are 1-indexed in the data array)
    # The 'labels' list usually includes 'Background' at index 0.
    # We need to find the integer value associated with the label name.
    label_idx = labels.index(label_name)
    
    data = atlas_img.get_fdata()
    mask = (data == label_idx).astype(np.uint8)
    return mask

def extract_roi_mask(
    atlas_img: nib.Nifti1Image,
    labels: List[str],
    roi_name: str,
    fallback_labels: Optional[List[str]] = None
) -> Optional[np.ndarray]:
    """
    Extract a mask for a specific ROI, attempting fallback labels if primary fails.
    """
    # Try primary name
    mask = generate_coordinate_mask(atlas_img, roi_name, labels)
    if mask is not None:
        logger.info(f"Successfully extracted mask for '{roi_name}'")
        return mask

    # Try fallbacks
    if fallback_labels:
        for alt_name in fallback_labels:
            mask = generate_coordinate_mask(atlas_img, alt_name, labels)
            if mask is not None:
                logger.warning(f"Primary '{roi_name}' failed. Used fallback '{alt_name}'.")
                return mask

    raise ValueError(f"Could not extract mask for ROI '{roi_name}' or its fallbacks.")

def save_mask_and_record(
    mask: np.ndarray,
    atlas_img: nib.Nifti1Image,
    output_path: Path,
    roi_name: str
) -> str:
    """
    Save the mask as a NIfTI file and return the relative path string.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a new NIfTI image with the mask data, using the affine from the atlas
    mask_img = nib.Nifti1Image(mask, atlas_img.affine, header=atlas_img.header)
    nib.save(mask_img, str(output_path))
    
    rel_path = str(output_path.relative_to(Path.cwd()))
    logger.info(f"Saved mask to {rel_path}")
    return rel_path

def main() -> None:
    """
    Main entry point to load Harvard-Oxford masks for Left Hippocampus, 
    Right Hippocampus, and DLPFC, and save their paths to a JSON file.
    """
    config = get_config()
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Define ROIs and their likely names in the atlas
    # Subcortical: Hippocampus (Left/Right)
    # Cortical: DLPFC (often mapped to Middle Frontal Gyrus or specific Brodmann areas)
    # We will fetch subcortical first for Hippocampus
    
    subcortical_img, sub_labels = fetch_harvard_oxford_subcortical()
    cortical_img, cort_labels = fetch_harvard_oxford_cortical()

    mask_records = {}
    failed_rois = []

    # 1. Left Hippocampus (Subcortical)
    # Common label: 'Left Hippocampus' or 'Left-Hippocampus'
    try:
        mask = extract_roi_mask(subcortical_img, sub_labels, "Left Hippocampus")
        out_path = processed_dir / "mask_left_hipp.nii.gz"
        path_str = save_mask_and_record(mask, subcortical_img, out_path, "Left Hippocampus")
        mask_records["left_hippocampus"] = path_str
    except Exception as e:
        logger.error(f"Failed to extract Left Hippocampus: {e}")
        failed_rois.append("left_hippocampus")

    # 2. Right Hippocampus (Subcortical)
    try:
        mask = extract_roi_mask(subcortical_img, sub_labels, "Right Hippocampus")
        out_path = processed_dir / "mask_right_hipp.nii.gz"
        path_str = save_mask_and_record(mask, subcortical_img, out_path, "Right Hippocampus")
        mask_records["right_hippocampus"] = path_str
    except Exception as e:
        logger.error(f"Failed to extract Right Hippocampus: {e}")
        failed_rois.append("right_hippocampus")

    # 3. DLPFC (Dorsolateral Prefrontal Cortex)
    # DLPFC is not a single label in Harvard-Oxford. It is typically approximated by 
    # the Middle Frontal Gyrus (MFG) or a combination of MFG and Superior Frontal Gyrus.
    # We will attempt 'Middle Frontal Gyrus' first, with a fallback to 'Left Middle Frontal Gyrus' / 'Right Middle Frontal Gyrus'.
    # Since DLPFC is bilateral, we might need to combine or pick a representative.
    # For this task, we will attempt to find a "Middle Frontal" label.
    
    dlpf_candidates = [
        "Middle Frontal Gyrus",
        "Left Middle Frontal Gyrus",
        "Right Middle Frontal Gyrus",
        "Frontal Pole" # Fallback if MFG fails
    ]
    
    dlpf_mask = None
    dlpf_label_name = None
    
    for candidate in dlpf_candidates:
        try:
            # Try cortical first
            dlpf_mask = extract_roi_mask(cortical_img, cort_labels, candidate)
            dlpf_label_name = candidate
            break
        except ValueError:
            continue
    
    if dlpf_mask is not None:
        out_path = processed_dir / "mask_dlpfc.nii.gz"
        path_str = save_mask_and_record(dlpf_mask, cortical_img, out_path, dlpf_label_name)
        mask_records["dlpfc"] = path_str
        logger.info(f"Using '{dlpf_label_name}' as DLPFC proxy.")
    else:
        logger.error("Could not identify DLPFC mask in Harvard-Oxford atlas.")
        failed_rois.append("dlpfc")

    # Save the mask paths to JSON
    output_json = processed_dir / "mask_paths.json"
    with open(output_json, 'w') as f:
        json.dump(mask_records, f, indent=2)
    
    logger.info(f"Saved mask paths to {output_json}")
    
    if failed_rois:
        logger.warning(f"Failed to extract masks for: {failed_rois}")
        # Raise to fail loudly as per constraint
        raise RuntimeError(f"Mask extraction failed for: {failed_rois}")

if __name__ == "__main__":
    main()
