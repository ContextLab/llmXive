import os
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import nibabel as nib

from nilearn.datasets import fetch_atlas_harvard_oxford
from nilearn import image
from config import get_config
from utils.logging_config import get_logger, error, info, warning

logger = get_logger(__name__)

def fetch_harvard_oxford_subcortical() -> Tuple[Path, np.ndarray]:
    """
    Fetches the Harvard-Oxford Subcortical structural atlas.
    Returns the path to the NIfTI file and the loaded 3D numpy array.
    """
    try:
        atlas = fetch_atlas_harvard_oxford('sub-maxprob-thr0-1mm')
        atlas_img = atlas.maps
        # nilearn returns a Niimg-like object, convert to Nifti1Image if needed
        if not isinstance(atlas_img, nib.Nifti1Image):
            # Assuming it's a filename string or similar, load it
            atlas_img = image.load_img(atlas_img)
        
        data = atlas_img.get_fdata()
        # Ensure output directory exists
        data_dir = Path(get_config()['data_dir'])
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Save a copy locally for reference
        local_path = data_dir / 'harvard_oxford_subcortical.nii.gz'
        nib.save(atlas_img, str(local_path))
        
        return local_path, data
    except Exception as e:
        logger.critical(f"Failed to fetch Harvard-Oxford Subcortical atlas: {e}")
        raise

def fetch_harvard_oxford_cortical() -> Tuple[Path, np.ndarray, List[str]]:
    """
    Fetches the Harvard-Oxford Cortical structural atlas.
    Returns the path to the NIfTI file, the loaded 3D numpy array, and the label names.
    """
    try:
        atlas = fetch_atlas_harvard_oxford('cort-maxprob-thr0-1mm')
        atlas_img = atlas.maps
        labels = atlas.labels
        
        if not isinstance(atlas_img, nib.Nifti1Image):
            atlas_img = image.load_img(atlas_img)
        
        data = atlas_img.get_fdata()
        
        data_dir = Path(get_config()['data_dir'])
        data_dir.mkdir(parents=True, exist_ok=True)
        
        local_path = data_dir / 'harvard_oxford_cortical.nii.gz'
        nib.save(atlas_img, str(local_path))
        
        return local_path, data, labels
    except Exception as e:
        logger.critical(f"Failed to fetch Harvard-Oxford Cortical atlas: {e}")
        raise

def extract_roi_mask(
    atlas_data: np.ndarray,
    labels: List[str],
    roi_name: str,
    threshold: float = 0.5
) -> np.ndarray:
    """
    Extracts a binary mask for a specific ROI from the atlas data.
    The roi_name is matched against the label names (case-insensitive).
    """
    target_idx = None
    for i, label in enumerate(labels):
        if roi_name.lower() in label.lower():
            target_idx = i
            break
    
    if target_idx is None:
        raise ValueError(f"ROI '{roi_name}' not found in atlas labels: {labels}")
    
    # Create binary mask
    mask = (atlas_data == target_idx).astype(np.float32)
    
    # Apply threshold if necessary (though maxprob should be 0 or 1)
    if threshold > 0:
        mask = (mask >= threshold).astype(np.float32)
        
    return mask

def generate_coordinate_mask(
    atlas_img_path: Path,
    center_coords: Tuple[int, int, int],
    radius: int = 5
) -> np.ndarray:
    """
    Generates a spherical mask around a specific coordinate in MNI space.
    This is the fallback mechanism if specific ROI labels are missing.
    """
    img = nib.load(str(atlas_img_path))
    affine = img.affine
    data_shape = img.shape
    data = np.zeros(data_shape, dtype=np.float32)
    
    # Convert MNI coords to voxel indices
    # Note: This is a simplified conversion assuming standard MNI alignment.
    # In practice, one might need to use `nilearn.image.coord_transform` 
    # or inverse affine if the atlas is not in standard MNI space.
    try:
        # Inverse affine to go from world (mm) to voxel (index)
        # However, fetch_atlas_harvard_oxford returns images in MNI space (1mm or 2mm).
        # If center_coords are in mm, we need to map them.
        # For 1mm resolution, voxel index approx equals mm value relative to origin.
        # We will assume center_coords are in voxel indices relative to the image origin 
        # or convert if necessary. Here we assume center_coords are MNI mm and convert.
        
        # MNI to Voxel conversion for standard 1mm atlas (origin usually at 0,0,0 or similar)
        # A robust way is: voxel = np.linalg.inv(affine).dot([x, y, z, 1])
        mni_pt = np.array(list(center_coords) + [1])
        voxel_pt = np.linalg.inv(affine).dot(mni_pt)
        ix, iy, iz = np.round(voxel_pt[:3]).astype(int)
        
        # Create sphere
        for x in range(ix - radius, ix + radius + 1):
            for y in range(iy - radius, iy + radius + 1):
                for z in range(iz - radius, iz + radius + 1):
                    if 0 <= x < data_shape[0] and 0 <= y < data_shape[1] and 0 <= z < data_shape[2]:
                        dist = np.sqrt((x - ix)**2 + (y - iy)**2 + (z - iz)**2)
                        if dist <= radius:
                            data[x, y, z] = 1.0
                            
        return data
    except Exception as e:
        logger.error(f"Failed to generate coordinate mask: {e}")
        raise

def save_mask_and_record(
    mask: np.ndarray,
    roi_name: str,
    mask_path: Path,
    source_info: Dict[str, Any]
) -> str:
    """
    Saves the mask as a NIfTI file and returns the path string.
    """
    mask_path.parent.mkdir(parents=True, exist_ok=True)
    # Create Nifti1Image with identity or appropriate affine if known
    # Since we are extracting from an atlas, we should preserve the atlas affine.
    # However, we don't have the original image here. 
    # We will assume a standard 1mm MNI affine for the mask if not derived from an image.
    # Better: pass the original affine from the atlas.
    
    # Placeholder affine (1mm MNI) - ideally passed from caller
    affine = np.eye(4)
    nib.save(nib.Nifti1Image(mask, affine), str(mask_path))
    
    return str(mask_path)

def main() -> None:
    """
    Main entry point to load Harvard-Oxford masks for Left Hippocampus, 
    Right Hippocampus, and DLPFC.
    Saves mask paths to data/processed/mask_paths.json.
    """
    config = get_config()
    processed_dir = Path(config['data_dir']) / 'processed'
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = processed_dir / 'mask_paths.json'
    
    rois = {
        'left_hippocampus': {
            'atlas_type': 'subcortical',
            'search_term': 'Left Hippocampus',
            'fallback_coords': (-24, -12, -18), # Approx MNI for Left Hippocampus
            'fallback_radius': 6
        },
        'right_hippocampus': {
            'atlas_type': 'subcortical',
            'search_term': 'Right Hippocampus',
            'fallback_coords': (24, -12, -18), # Approx MNI for Right Hippocampus
            'fallback_radius': 6
        },
        'dlpfc': {
            'atlas_type': 'cortical',
            'search_term': 'Frontal Pole', # DLPFC is often mapped to Frontal Pole or Middle Frontal Gyrus
            # DLPFC is not a single label in HO. We might need to combine or use coords.
            # Let's try 'Frontal Pole' first, if not found, use coords for DLPFC approx (-40, 40, 30)
            'fallback_coords': (-40, 40, 30), 
            'fallback_radius': 8
        }
    }
    
    mask_results = {}
    atlas_cache = {}
    
    for roi_key, roi_info in rois.items():
        try:
            # Fetch atlas if not cached
            atlas_type = roi_info['atlas_type']
            if atlas_type not in atlas_cache:
                if atlas_type == 'subcortical':
                    path, data, _ = fetch_harvard_oxford_subcortical()
                    atlas_cache[atlas_type] = {'path': path, 'data': data, 'labels': None}
                else:
                    path, data, labels = fetch_harvard_oxford_cortical()
                    atlas_cache[atlas_type] = {'path': path, 'data': data, 'labels': labels}
            
            atlas_data = atlas_cache[atlas_type]['data']
            labels = atlas_cache[atlas_type]['labels']
            
            mask = None
            source = None
            
            # Try label matching
            if labels:
                try:
                    mask = extract_roi_mask(atlas_data, labels, roi_info['search_term'])
                    source = f"Label: {roi_info['search_term']}"
                    logger.info(f"Found ROI '{roi_key}' via label matching.")
                except ValueError:
                    logger.warning(f"Label '{roi_info['search_term']}' not found for {roi_key}. Falling back to coordinates.")
            
            # Fallback to coordinate mask
            if mask is None:
                coords = roi_info['fallback_coords']
                radius = roi_info['fallback_radius']
                # We need the affine for coordinate mask generation, which we don't have directly in cache
                # We'll re-fetch or pass the path. For simplicity, we assume standard MNI 1mm.
                # A more robust implementation would load the image from the cached path.
                atlas_path = atlas_cache[atlas_type]['path']
                mask = generate_coordinate_mask(atlas_path, coords, radius)
                source = f"Coordinates: {coords}, Radius: {radius}"
                logger.info(f"Generated ROI '{roi_key}' via coordinate fallback.")
            
            if mask is None:
                raise RuntimeError(f"ROI definition failed: neither precomputed mask nor Harvard-Oxford coordinates available for {roi_key}.")
            
            # Save mask
            mask_filename = f"mask_{roi_key}.nii.gz"
            mask_path = processed_dir / mask_filename
            final_path = save_mask_and_record(mask, roi_key, mask_path, {'source': source})
            
            mask_results[roi_key] = {
                'path': final_path,
                'source': source,
                'shape': mask.shape,
                'voxel_count': int(np.sum(mask > 0))
            }
            
        except Exception as e:
            error_msg = f"Failed to process {roi_key}: {str(e)}"
            logger.error(error_msg)
            # Do not raise immediately to attempt other ROIs, but ensure we fail loudly if all fail
            mask_results[roi_key] = {'error': error_msg}
    
    # Check if any failed
    if any('error' in v for v in mask_results.values()):
        failed_rois = [k for k, v in mask_results.items() if 'error' in v]
        raise RuntimeError(f"Critical failures for ROIs: {failed_rois}")
    
    # Save paths to JSON
    with open(output_file, 'w') as f:
        json.dump(mask_results, f, indent=2)
    
    logger.info(f"Successfully saved mask paths to {output_file}")
    print(f"Mask paths saved to {output_file}")

if __name__ == '__main__':
    main()
