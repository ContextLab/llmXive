"""
Load Harvard-Oxford masks for Left Hippocampus, Right Hippocampus, and DLPFC.
Uses nilearn to fetch atlases. If fetch fails, attempts to generate masks from
coordinates. If ROI cannot be defined, raises a specific error.
"""
import os
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import nibabel as nib
from nilearn import datasets
from nilearn.image import new_img_like
from nilearn.masking import apply_mask
import logging

# Configure logging to match project standards
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Hardcoded coordinates for DLPFC (Brodmann Area 9/46) in MNI space
# Approximate center coordinates for Left and Right DLPFC
DLPFC_COORDS = {
    "left": [-44, 36, 24],
    "right": [44, 36, 24]
}
HIPPOCAMPUS_COORDS = {
    "left": [-24, -12, -18],
    "right": [24, -12, -18]
}
# Standard MNI affine for a 2mm isotropic grid (common default)
DEFAULT_AFFINE = np.eye(4) * 2
DEFAULT_AFFINE[3, 3] = 1.0
DEFAULT_SHAPE = (91, 109, 91)  # Typical MNI152 shape for 2mm

def fetch_harvard_oxford_subcortical():
    """Fetch the Harvard-Oxford Subcortical structural atlas."""
    try:
        atlas_img = datasets.fetch_atlas_harvard_oxford('sub-maxprob-thr0-2mm')
        return atlas_img.filename, atlas_img.maps
    except Exception as e:
        logger.warning(f"Failed to fetch Harvard-Oxford subcortical: {e}")
        return None, None

def fetch_harvard_oxford_cortical():
    """Fetch the Harvard-Oxford Cortical structural atlas."""
    try:
        atlas_img = datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr0-2mm')
        return atlas_img.filename, atlas_img.maps
    except Exception as e:
        logger.warning(f"Failed to fetch Harvard-Oxford cortical: {e}")
        return None, None

def extract_roi_mask(atlas_img, atlas_labels, target_name: str) -> Optional[np.ndarray]:
    """
    Extract a binary mask for a specific ROI name from the atlas.
    Returns the mask as a numpy array or None if not found.
    """
    if atlas_img is None or atlas_labels is None:
        return None

    # Load the atlas image
    img = nib.load(atlas_img)
    data = img.get_fdata()
    labels = atlas_labels

    # Find the index of the target name in labels
    target_idx = None
    for i, label in enumerate(labels):
        if target_name.lower() in label.lower():
            target_idx = i
            break

    if target_idx is None:
        logger.warning(f"ROI '{target_name}' not found in atlas labels: {labels}")
        return None

    # Create binary mask
    mask = (data == target_idx).astype(np.float32)
    return mask

def generate_coordinate_mask(coords: List[int], shape: Tuple[int, int, int], 
                             affine: np.ndarray, radius_mm: float = 10.0) -> np.ndarray:
    """
    Generate a spherical mask around given MNI coordinates.
    """
    mask = np.zeros(shape, dtype=np.float32)
    
    # Convert MNI coordinates to voxel indices
    # affine @ [x, y, z, 1] = voxel_coords
    # We need the inverse to go from MNI to voxel
    inv_affine = np.linalg.inv(affine)
    
    # Create a 4x1 vector for the coordinate
    mni_vec = np.array([coords[0], coords[1], coords[2], 1.0])
    voxel_center = np.dot(inv_affine, mni_vec)[:3]
    
    # Create a grid of voxel indices
    z, y, x = np.ogrid[:shape[0], :shape[1], :shape[2]]
    vox_coords = np.stack([x, y, z], axis=-1).astype(np.float32)
    
    # Calculate distance in mm
    # Distance = sqrt(sum((voxel - center)^2 * (affine_scale)^2))
    # Assuming isotropic scaling for simplicity in this fallback
    # More robust: transform voxel offsets to MNI space
    offsets = vox_coords - voxel_center
    # Transform offset to MNI space using affine
    mni_offsets = np.dot(affine[:3, :3], offsets.T).T
    distances = np.sqrt(np.sum(mni_offsets**2, axis=-1))
    
    mask = (distances <= radius_mm).astype(np.float32)
    return mask

def save_mask_and_record(mask: np.ndarray, output_path: Path, 
                         affine: np.ndarray = None, shape: Tuple = None):
    """Save mask as NIfTI and record path."""
    if affine is None:
        affine = DEFAULT_AFFINE
    if shape is None:
        shape = DEFAULT_SHAPE
    
    # Create NIfTI image
    img = nib.Nifti1Image(mask, affine)
    nib.save(img, str(output_path))
    logger.info(f"Saved mask to {output_path}")

def main():
    """
    Main entry point to load masks for Left Hippocampus, Right Hippocampus, and DLPFC.
    Saves paths to data/processed/mask_paths.json.
    """
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    mask_paths = {}
    roi_definitions = {
        "left_hipp": ("Left Hippocampus", "subcortical", HIPPOCAMPUS_COORDS["left"]),
        "right_hipp": ("Right Hippocampus", "subcortical", HIPPOCAMPUS_COORDS["right"]),
        "dlpfc": ("Frontal Pole", "cortical", DLPFC_COORDS["left"]) # Fallback name, will refine
    }

    # Attempt to fetch atlases
    subcortical_path, subcortical_maps = fetch_harvard_oxford_subcortical()
    cortical_path, cortical_maps = fetch_harvard_oxford_cortical()
    
    # Fallback to coordinate generation if fetch fails
    use_coords = (subcortical_path is None or cortical_path is None)
    
    if use_coords:
        logger.warning("Harvard-Oxford fetch failed or incomplete. Using coordinate-based masks.")
    
    # Process each ROI
    for key, (name, atlas_type, coords) in roi_definitions.items():
        mask_data = None
        success = False
        
        # Try atlas extraction first
        if not use_coords:
            if atlas_type == "subcortical" and subcortical_path:
                mask_data = extract_roi_mask(subcortical_path, subcortical_maps, name)
            elif atlas_type == "cortical" and cortical_path:
                # DLPFC is cortical, but "Frontal Pole" might not be exact. 
                # We might need to search for "Middle Frontal Gyrus" or similar.
                # Let's try a few variations for DLPFC
                variations = ["Middle Frontal Gyrus", "Frontal Pole", "Superior Frontal Gyrus"]
                for var in variations:
                    mask_data = extract_roi_mask(cortical_path, cortical_maps, var)
                    if mask_data is not None:
                        break
        
        # Fallback to coordinate generation
        if mask_data is None:
            logger.info(f"Generating mask for {key} using coordinates: {coords}")
            mask_data = generate_coordinate_mask(coords, DEFAULT_SHAPE, DEFAULT_AFFINE)
            if mask_data is not None:
                success = True
            else:
                logger.error(f"Failed to generate coordinate mask for {key}")
        else:
            success = True

        if success:
            out_path = output_dir / f"mask_{key}.nii.gz"
            save_mask_and_record(mask_data, out_path)
            mask_paths[key] = str(out_path)
        else:
            logger.error(f"Could not define ROI for {key}")

    # Final check
    required_keys = ["left_hipp", "right_hipp", "dlpfc"]
    missing = [k for k in required_keys if k not in mask_paths]
    
    if missing:
        raise RuntimeError(f"ROI definition failed: neither precomputed mask nor Harvard-Oxford coordinates available for: {missing}")
    
    # Save mask paths to JSON
    json_path = output_dir / "mask_paths.json"
    with open(json_path, 'w') as f:
        json.dump(mask_paths, f, indent=2)
    
    logger.info(f"Mask paths saved to {json_path}")
    return mask_paths

if __name__ == "__main__":
    main()
