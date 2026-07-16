"""
Spatial mapping and overlap analysis module.

Implements functions to align parcellations using binary masks and strict
voxel containment checks to derive majority-vote overlap maps.
"""
import os
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from utils.logger import get_logger, ProcessingError
from config import get_path

logger = get_logger(__name__)


def load_atlas_mask(atlas_name: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load an atlas mask from disk.
    
    Args:
        atlas_name: Name of the atlas (e.g., 'aal', 'schaefer_400').
    
    Returns:
        Tuple of (mask_array, affine).
    """
    # Map logical names to expected file paths
    # These should match the filenames used in T013, T014, T015
    if atlas_name == 'aal':
        # AAL3 atlas is typically downloaded or provided; we assume it's in data/raw/atlas/
        # or downloaded during T012/T016 process. For this task, we assume it exists.
        mask_path = get_path('data/raw/atlas/AAL3.nii')
    elif atlas_name == 'schaefer_400':
        mask_path = get_path('data/raw/atlas/Schaefer2018_400Parcels_7Networks_order_FSLMNI152_2mm.nii')
    elif atlas_name == 'schaefer_200':
        mask_path = get_path('data/raw/atlas/Schaefer2018_200Parcels_7Networks_order_FSLMNI152_2mm.nii')
    else:
        raise ProcessingError(f"Unknown atlas: {atlas_name}")
    
    if not os.path.exists(mask_path):
        raise ProcessingError(f"Atlas file not found: {mask_path}")
    
    img = nib.load(mask_path)
    data = img.get_fdata().astype(np.int32)
    return data, img.affine


def create_strict_containment_map(
    high_res_mask: np.ndarray,
    low_res_mask: np.ndarray,
    high_res_label: int,
    low_res_labels: List[int]
) -> Dict[int, int]:
    """
    Create a mapping from a single high-resolution node to a low-resolution node
    based on strict voxel containment (majority vote).
    
    Args:
        high_res_mask: 3D array of high-res atlas labels.
        low_res_mask: 3D array of low-res atlas labels.
        high_res_label: The specific label in the high-res mask to map.
        low_res_labels: List of valid labels in the low-res mask.
    
    Returns:
        Dict mapping high_res_label -> low_res_label (the majority vote target).
    """
    # Get voxels belonging to the high-res node
    high_res_voxels = np.where(high_res_mask == high_res_label)
    
    if len(high_res_voxels[0]) == 0:
        logger.warning(f"No voxels found for high-res label {high_res_label}")
        return {}
    
    # Check which low-res labels these voxels fall into
    corresponding_low_res = low_res_mask[high_res_voxels]
    
    # Filter out background (0)
    valid_corresponding = corresponding_low_res[corresponding_low_res > 0]
    
    if len(valid_corresponding) == 0:
        logger.warning(f"No overlap found for high-res label {high_res_label}")
        return {}
    
    # Majority vote
    unique, counts = np.unique(valid_corresponding, return_counts=True)
    majority_label = unique[np.argmax(counts)]
    
    return {high_res_label: int(majority_label)}


def generate_schaefer_to_aal_mapping(
    schaefer_labels: List[int],
    aal_labels: List[int],
    schaefer_mask: np.ndarray,
    aal_mask: np.ndarray
) -> np.ndarray:
    """
    Generate a lookup table mapping Schaefer node indices to AAL node indices.
    
    Args:
        schaefer_labels: List of valid Schaefer labels.
        aal_labels: List of valid AAL labels.
        schaefer_mask: 3D array of Schaefer atlas.
        aal_mask: 3D array of AAL atlas.
    
    Returns:
        1D numpy array where index i maps to the AAL label for Schaefer label i.
        If no mapping is found, the value is -1.
    """
    max_schaefer = max(schaefer_labels) if schaefer_labels else 0
    # Initialize mapping array with -1 (no mapping)
    mapping = np.full(max_schaefer + 1, -1, dtype=np.int32)
    
    logger.info(f"Generating mapping for {len(schaefer_labels)} Schaefer nodes to {len(aal_labels)} AAL nodes")
    
    for label in schaefer_labels:
        if label == 0:
            continue
        
        result = create_strict_containment_map(
            schaefer_mask,
            aal_mask,
            label,
            aal_labels
        )
        
        if result:
            mapped_aal = result[label]
            mapping[label] = mapped_aal
            logger.debug(f"Schaefer {label} -> AAL {mapped_aal}")
        else:
            logger.warning(f"No mapping found for Schaefer label {label}")
    
    return mapping


def main():
    """
    Main function to generate the spatial mapping from Schaefer-400 to AAL-90.
    
    Output:
        data/processed/mapping_schaefer_to_aal.npy
        Format: 1D array where index i is the AAL label for Schaefer label i.
    """
    logger.info("Starting spatial mapping generation: Schaefer-400 to AAL-90")
    
    # Load atlases
    try:
        logger.info("Loading AAL3 atlas...")
        aal_mask, aal_affine = load_atlas_mask('aal')
        
        logger.info("Loading Schaefer-400 atlas...")
        schaefer_mask, schaefer_affine = load_atlas_mask('schaefer_400')
    except ProcessingError as e:
        logger.error(f"Failed to load atlas: {e}")
        raise
    
    # Verify affine alignment (strict check)
    if not np.allclose(aal_affine, schaefer_affine):
        logger.warning("Affines do not match exactly. This may cause misalignment.")
        # In a real pipeline, we might resample, but per FR-009 we use strict containment
        # We proceed assuming they are in the same space (MNI152 2mm)
    
    # Get unique labels (excluding background 0)
    aal_labels = sorted(list(np.unique(aal_mask)))
    aal_labels = [l for l in aal_labels if l > 0]
    
    schaefer_labels = sorted(list(np.unique(schaefer_mask)))
    schaefer_labels = [l for l in schaefer_labels if l > 0]
    
    logger.info(f"AAL labels: {len(aal_labels)} (range: {min(aal_labels)}-{max(aal_labels)})")
    logger.info(f"Schaefer labels: {len(schaefer_labels)} (range: {min(schaefer_labels)}-{max(schaefer_labels)})")
    
    # Generate mapping
    mapping = generate_schaefer_to_aal_mapping(
        schaefer_labels,
        aal_labels,
        schaefer_mask,
        aal_mask
    )
    
    # Save output
    output_path = get_path('data/processed/mapping_schaefer_to_aal.npy')
    logger.info(f"Saving mapping to {output_path}")
    
    np.save(output_path, mapping)
    
    # Verify output
    if os.path.exists(output_path):
        loaded = np.load(output_path)
        logger.info(f"Saved mapping shape: {loaded.shape}, dtype: {loaded.dtype}")
        logger.info(f"Successfully generated {output_path}")
    else:
        raise ProcessingError(f"Failed to write output file: {output_path}")
    
    return mapping


if __name__ == '__main__':
    main()
