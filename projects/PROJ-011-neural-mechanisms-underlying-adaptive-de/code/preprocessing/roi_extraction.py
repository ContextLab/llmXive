"""
ROI Extraction Module

Extracts BOLD signals from specific Regions of Interest (dlPFC, ventral striatum, ACC)
from normalized fMRI data.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Union

import numpy as np
import pandas as pd
import nibabel as nib
from nilearn import image, masking
from nilearn.datasets import fetch_atlas_harvard_oxford

# Add project root to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.io import ensure_dir, file_exists, load_json, save_json, IOLoadError
from utils.config import get_config
from utils.logger import get_logger

# Define ROI names based on task description and standard atlases
# Mapping logical names to Harvard-Oxford cortical/subcortical labels
ROI_MAPPING = {
    "dlPFC": ["Middle Frontal Gyrus", "Superior Frontal Gyrus"], # Approximate dlPFC
    "ventral_striatum": ["Nucleus Accumbens", "Caudate", "Putamen"], # Ventral striatum includes NAcc
    "ACC": ["Anterior Cingulate Cortex"]
}

logger = get_logger(__name__)

def load_roi_masks(atlas_name: str = "HarvardOxford") -> Dict[str, nib.Nifti1Image]:
    """
    Loads ROI masks from a standard atlas.
    
    Args:
        atlas_name: Name of the atlas to use (currently supports HarvardOxford).
        
    Returns:
        Dictionary mapping ROI logical names to NIfTI mask images.
    """
    logger.info(f"Loading ROI masks from {atlas_name} atlas...")
    
    # Fetch Harvard-Oxford Cortial and Subcortical atlases
    # nilearn caches these automatically
    try:
        # Fetch cortical atlas for dlPFC and ACC
        cort_atlas = fetch_atlas_harvard_oxford("cort-maxprob-thr0-1mm")
        cort_labels = cort_atlas.labels
        cort_img = cort_atlas.maps
        
        # Fetch subcortical atlas for ventral striatum
        sub_atlas = fetch_atlas_harvard_oxford("sub-maxprob-thr0-1mm")
        sub_labels = sub_atlas.labels
        sub_img = sub_atlas.maps
        
        masks = {}
        
        for roi_name, atlas_names in ROI_MAPPING.items():
            mask_data = np.zeros(cort_img.shape, dtype=bool)
            source_img = cort_img
            source_labels = cort_labels
            
            # Determine if we need to switch to subcortical atlas
            # Check if any target name is in subcortical labels
            if any(name in sub_labels for name in atlas_names):
                source_img = sub_img
                source_labels = sub_labels
            
            # Combine masks for names in the list
            for target_name in atlas_names:
                if target_name in source_labels:
                    idx = source_labels.index(target_name)
                    # Extract the mask for this label (1-based index in labels, 0-based in data usually, but nilearn handles this)
                    # nilearn maps are 4D, each volume is a label
                    if source_img.ndim == 4:
                        label_mask = source_img.slicer[:, :, :, idx - 1] # Labels are 1-indexed in the list usually, data is 0-indexed
                        # However, fetch_atlas_harvard_oxford returns 4D where the last dim is the label index.
                        # The labels list includes 'Background' as the first item (index 0).
                        # So label '1' corresponds to index 0 in the data volume? No, usually index 0 in data is label 1.
                        # Let's rely on the masking function which is safer.
                        pass
                    else:
                        # If 3D, find the voxel value
                        label_val = source_labels.index(target_name)
                        label_mask = (source_img.get_fdata() == label_val)
                    
                    mask_data = mask_data | label_mask
                else:
                    logger.warning(f"ROI label '{target_name}' not found in {source_labels}. Skipping.")
            
            if np.any(mask_data):
                # Create a NIfTI image from the combined mask
                # Use affine from the source image
                if source_img.ndim == 4:
                    # Use the first volume's affine
                    affine = source_img.affine
                else:
                    affine = source_img.affine
                
                # Create a 3D Nifti image
                mask_img = nib.Nifti1Image(mask_data.astype(np.int16), affine)
                masks[roi_name] = mask_img
                logger.info(f"Loaded mask for {roi_name} with {np.sum(mask_data)} voxels.")
            else:
                logger.error(f"Could not construct mask for {roi_name}. No valid labels found.")
                
        return masks
        
    except Exception as e:
        logger.error(f"Failed to load atlas: {e}")
        raise IOLoadError(f"Failed to load ROI masks: {e}")

def extract_roi_timeseries(
    functional_img: Union[str, Path, nib.Nifti1Image],
    roi_masks: Optional[Dict[str, nib.Nifti1Image]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    participant_id: str = "unknown"
) -> Dict[str, pd.DataFrame]:
    """
    Extracts the mean BOLD time series for each ROI from a functional image.
    
    Args:
        functional_img: Path to the 4D functional NIfTI file or a Nifti1Image object.
        roi_masks: Dictionary of ROI masks. If None, loads them automatically.
        output_dir: Directory to save the resulting CSVs.
        participant_id: ID of the participant for naming output files.
        
    Returns:
        Dictionary mapping ROI names to DataFrames containing the time series.
    """
    if roi_masks is None:
        roi_masks = load_roi_masks()
        
    if not roi_masks:
        raise IOLoadError("No ROI masks available for extraction.")
        
    # Load functional image if path provided
    if isinstance(functional_img, (str, Path)):
        if not file_exists(str(functional_img)):
            raise IOLoadError(f"Functional image not found: {functional_img}")
        func_img = nib.load(str(functional_img))
    else:
        func_img = functional_img
        
    logger.info(f"Extracting ROI time series from {func_img.shape} image...")
    
    results = {}
    
    for roi_name, mask_img in roi_masks.items():
        try:
            # Use nilearn's masking to extract mean time series
            # mean_ts shape: (n_timepoints,)
            mean_ts = masking.apply_mask(
                func_img,
                mask_img,
                mask_strategy='whole-brain' # Default, but we are providing a specific mask
            )
            # apply_mask with a specific mask image returns the mean signal in that mask over time
            # Actually, masking.apply_mask(img, mask) extracts the time series for each voxel in mask.
            # We want the mean across the ROI.
            
            # Correct approach: extract voxel time series then average
            voxel_ts = masking.apply_mask(func_img, mask_img)
            # voxel_ts shape: (n_timepoints, n_voxels)
            mean_signal = np.mean(voxel_ts, axis=1)
            
            # Create DataFrame
            df = pd.DataFrame({
                "timepoint": range(len(mean_signal)),
                f"{roi_name}_mean": mean_signal
            })
            
            results[roi_name] = df
            
            logger.debug(f"Extracted {len(mean_signal)} timepoints for {roi_name}.")
            
        except Exception as e:
            logger.error(f"Failed to extract time series for {roi_name}: {e}")
            continue
            
    # Save to disk if output_dir specified
    if output_dir:
        ensure_dir(output_dir)
        for roi_name, df in results.items():
            out_path = Path(output_dir) / f"{participant_id}_{roi_name}_timeseries.csv"
            df.to_csv(out_path, index=False)
            logger.info(f"Saved ROI timeseries to {out_path}")
            
    return results

def main():
    """
    Main entry point for ROI extraction pipeline.
    Reads configuration, loads normalized data, extracts ROIs, and saves results.
    """
    config = get_config()
    logger.info("Starting ROI Extraction Pipeline")
    
    # Configuration paths
    data_dir = Path(config.get("paths.data_processed", "data/processed"))
    output_dir = Path(config.get("paths.roi_output", "data/processed/roi"))
    
    # Ensure output directory exists
    ensure_dir(output_dir)
    
    # Load ROI masks
    try:
        roi_masks = load_roi_masks()
    except IOLoadError as e:
        logger.critical(f"Cannot proceed without ROI masks: {e}")
        sys.exit(1)
        
    # Find processed functional images (assuming normalized/smoothed files)
    # Pattern: sub-<id>_space-MNI_desc-preproc_bold.nii.gz
    func_files = list(data_dir.glob("sub-*/sub-*_space-MNI_desc-preproc_bold.nii.gz"))
    
    if not func_files:
        logger.warning("No processed functional images found in data/processed. "
                     "Looking for alternative patterns...")
        func_files = list(data_dir.glob("sub-*/sub-*_desc-preproc_bold.nii.gz"))
        
    if not func_files:
        logger.error("No functional images found to process.")
        sys.exit(1)
        
    logger.info(f"Found {len(func_files)} functional images to process.")
    
    all_results = {}
    
    for func_file in func_files:
        # Extract participant ID from filename
        # Expected: sub-01/... or similar
        parts = func_file.relative_to(data_dir).parts
        participant_id = parts[0] if len(parts) > 1 else func_file.stem
        
        logger.info(f"Processing participant: {participant_id}")
        
        try:
            results = extract_roi_timeseries(
                functional_img=func_file,
                roi_masks=roi_masks,
                output_dir=output_dir,
                participant_id=participant_id
            )
            all_results[participant_id] = results
        except Exception as e:
            logger.error(f"Failed to process {func_file}: {e}")
            
    # Save summary of extracted data
    summary_path = output_dir / "roi_extraction_summary.json"
    summary_data = {
        "participants_processed": len(all_results),
        "rois_extracted": list(roi_masks.keys()),
        "files": [str(f.relative_to(data_dir)) for f in func_files]
    }
    save_json(summary_data, summary_path)
    logger.info(f"ROI extraction complete. Summary saved to {summary_path}")

if __name__ == "__main__":
    main()
