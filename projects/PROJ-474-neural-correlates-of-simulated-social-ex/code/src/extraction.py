"""
ROI Time-Series Extraction Module.

Implements FR-003: Extract BOLD time-series from PCC, mPFC, and Angular Gyrus
using the AAL/Harvard-Oxford atlas.

Memory Constraint: Processes subjects one-by-one to ensure < 7GB RAM usage.
"""
import os
import json
import logging
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from nilearn import image, masking
from nilearn.datasets import fetch_atlas_harvard_oxford, fetch_atlas_aal
from nilearn.image import get_data

from src.config import load_config
from src.utils import get_logger, PipelineError

# Constants for ROI names based on standard atlases
# Using Harvard-Oxford Subcortical/Cortical as primary, with AAL as fallback if needed.
# PCC: Posterior Cingulate Cortex
# mPFC: Medial Prefrontal Cortex
# Angular: Angular Gyrus
ROI_NAMES = {
    "PCC": ["Posterior Cingulate Cortex"],
    "mPFC": ["Medial Prefrontal Cortex"],
    "Angular": ["Angular Gyrus"]
}

def load_atlas(atlas_type: str = "harvard_oxford") -> Tuple[Any, Dict[str, int]]:
    """
    Fetches the specified atlas and returns the image and a mapping of ROI names to indices.
    
    Args:
        atlas_type: 'harvard_oxford' or 'aal'
        
    Returns:
        Tuple of (atlas_img, name_to_index_map)
    """
    logger = get_logger(__name__)
    
    if atlas_type == "harvard_oxford":
        # Harvard-Oxford Cortical Structural Atlas
        # Note: Probabilistic atlases are common; we use the structural (max prob) version
        try:
            atlas = fetch_atlas_harvard_oxford("cort-maxprob-thr0-1mm")
            atlas_img = atlas.maps
            # The labels list usually starts with an empty string for background (index 0)
            labels = atlas.labels
            name_to_idx = {name: idx for idx, name in enumerate(labels) if idx > 0}
            logger.info(f"Loaded Harvard-Oxford Cortical Atlas. Found {len(name_to_idx)} regions.")
            return atlas_img, name_to_idx
        except Exception as e:
            logger.error(f"Failed to load Harvard-Oxford atlas: {e}")
            raise PipelineError(f"Atlas loading failed: {e}")
            
    elif atlas_type == "aal":
        try:
            atlas = fetch_atlas_aal()
            atlas_img = atlas.maps
            labels = atlas.labels
            # AAL labels often include 'Background' at index 0
            name_to_idx = {name: idx for idx, name in enumerate(labels) if idx > 0}
            logger.info(f"Loaded AAL Atlas. Found {len(name_to_idx)} regions.")
            return atlas_img, name_to_idx
        except Exception as e:
            logger.error(f"Failed to load AAL atlas: {e}")
            raise PipelineError(f"Atlas loading failed: {e}")
    
    else:
        raise ValueError(f"Unsupported atlas type: {atlas_type}")

def get_roi_mask_indices(roi_name: str, name_to_idx: Dict[str, int], atlas_img: Any) -> Optional[np.ndarray]:
    """
    Identifies voxel indices for a specific ROI name.
    Handles potential name variations (e.g., "Left Angular Gyrus" vs "Angular Gyrus").
    
    Returns:
        Boolean mask array or None if not found.
    """
    # Exact match first
    if roi_name in name_to_idx:
        idx = name_to_idx[roi_name]
        data = get_data(atlas_img)
        return data == idx
    
    # Fuzzy match: look for substrings in labels
    # e.g., searching "Angular Gyrus" might find "Left Angular Gyrus"
    # We will combine all matching ROIs if multiple exist (e.g., Left + Right)
    matching_indices = []
    found_labels = []
    
    for label, idx in name_to_idx.items():
        if roi_name.lower() in label.lower():
            matching_indices.append(idx)
            found_labels.append(label)
    
    if not matching_indices:
        return None
    
    # Combine masks for all matching labels (e.g. Left + Right)
    data = get_data(atlas_img)
    combined_mask = np.isin(data, matching_indices)
    return combined_mask

def extract_roi_timeseries(
    subject_preprocessed_path: Path,
    atlas_img: Any,
    name_to_idx: Dict[str, int],
    rois: List[str]
) -> Dict[str, np.ndarray]:
    """
    Extracts time-series for specified ROIs from a preprocessed NIfTI file.
    
    Args:
        subject_preprocessed_path: Path to the preprocessed subject NIfTI file.
        atlas_img: Atlas image object.
        name_to_idx: Mapping of ROI names to atlas indices.
        rois: List of ROI keys (e.g., ["PCC", "mPFC", "Angular"]) to extract.
        
    Returns:
        Dictionary mapping ROI keys to 1D numpy arrays (time-series).
    """
    logger = get_logger(__name__)
    
    if not subject_preprocessed_path.exists():
        raise FileNotFoundError(f"Preprocessed file not found: {subject_preprocessed_path}")
    
    # Load subject image (memory mapped)
    try:
        subject_img = nib.load(str(subject_preprocessed_path))
    except Exception as e:
        raise PipelineError(f"Failed to load subject image {subject_preprocessed_path}: {e}")
    
    # Ensure atlas and subject are in same space/resolution for masking
    # Nilearn masking functions handle resampling automatically if needed, 
    # but it's safer to ensure they are loaded correctly.
    
    results = {}
    
    for roi_key in rois:
        roi_name = ROI_NAMES.get(roi_key, [roi_key])[0]
        mask = get_roi_mask_indices(roi_name, name_to_idx, atlas_img)
        
        if mask is None:
            logger.warning(f"ROI '{roi_key}' (searching '{roi_name}') not found in atlas. Skipping.")
            # Create empty array or raise? Spec says extract, so we skip but log.
            # To maintain structure, we could return empty, but let's skip to avoid bad data.
            results[roi_key] = None
            continue
        
        try:
            # Use apply_mask to extract time series
            # This returns shape (n_timepoints, n_voxels)
            ts = masking.apply_mask(subject_img, mask)
            
            # Average across voxels within the ROI to get a single time-series
            # Shape becomes (n_timepoints,)
            mean_ts = np.mean(ts, axis=1)
            results[roi_key] = mean_ts
            
        except Exception as e:
            logger.error(f"Failed to extract time-series for {roi_key}: {e}")
            results[roi_key] = None
            
    return results

def process_subject_extraction(
    subject_id: str,
    config: Dict[str, Any],
    qc_list_path: Path
) -> Dict[str, Any]:
    """
    Processes a single subject for ROI extraction.
    Implements memory-efficient single-subject processing.
    
    Args:
        subject_id: The subject identifier.
        config: Configuration dictionary.
        qc_list_path: Path to the subject QC list JSON to find input file.
        
    Returns:
        Dictionary containing extraction results for this subject.
    """
    logger = get_logger(__name__)
    logger.info(f"Processing extraction for subject: {subject_id}")
    
    # 1. Load Config
    data_dir = Path(config["paths"]["data_dir"])
    processed_dir = Path(config["paths"]["processed_dir"])
    output_dir = Path(config["paths"]["results_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Locate Input File
    # Expected path: data/processed/preprocessed_{subject_id}.nii.gz
    input_file = processed_dir / f"preprocessed_{subject_id}.nii.gz"
    
    if not input_file.exists():
        logger.error(f"Input file missing for {subject_id}: {input_file}")
        return {"subject_id": subject_id, "status": "failed", "error": "Input file missing"}
    
    # 3. Load Atlas (Cached globally or re-loaded? Re-load for simplicity in this function, 
    #    but in production, pass atlas objects to avoid repeated I/O. 
    #    Given the constraint of <7GB, loading a standard atlas is fine (~50MB-100MB).)
    atlas_type = config.get("atlas", {}).get("type", "harvard_oxford")
    atlas_img, name_to_idx = load_atlas(atlas_type)
    
    # 4. Extract Time-Series
    try:
        timeseries_data = extract_roi_timeseries(
            subject_preprocessed_path=input_file,
            atlas_img=atlas_img,
            name_to_idx=name_to_idx,
            rois=["PCC", "mPFC", "Angular"]
        )
        
        # Validate extraction
        if any(v is None for v in timeseries_data.values()):
            logger.warning(f"Partial extraction failure for {subject_id}")
            # Still return what we have, but mark status
        
        # Save individual subject results
        subject_output_path = output_dir / f"timeseries_{subject_id}.json"
        
        # Convert numpy arrays to lists for JSON serialization
        serializable_data = {
            key: value.tolist() if value is not None else None
            for key, value in timeseries_data.items()
        }
        
        with open(subject_output_path, 'w') as f:
            json.dump({
                "subject_id": subject_id,
                "roi_timeseries": serializable_data,
                "n_timepoints": len(timeseries_data.get("PCC", [])) if timeseries_data.get("PCC") else 0
            }, f, indent=2)
        
        logger.info(f"Saved extraction results for {subject_id} to {subject_output_path}")
        
        return {
            "subject_id": subject_id,
            "status": "success",
            "output_file": str(subject_output_path),
            "n_timepoints": len(timeseries_data.get("PCC", [])) if timeseries_data.get("PCC") else 0
        }
        
    except Exception as e:
        logger.error(f"Extraction failed for {subject_id}: {e}")
        return {"subject_id": subject_id, "status": "failed", "error": str(e)}

def run_extraction_pipeline(config_path: str = "code/config.yaml") -> List[Dict[str, Any]]:
    """
    Orchestrates the extraction pipeline for all retained subjects.
    Reads subject list from data/processed/subject_qc_list.json.
    
    Args:
        config_path: Path to config.yaml
        
    Returns:
        List of results dictionaries for each subject.
    """
    logger = get_logger(__name__)
    logger.info("Starting ROI Extraction Pipeline (T024)")
    
    # Load Config
    config = load_config(config_path)
    
    # Load QC List to determine which subjects to process
    qc_list_path = Path(config["paths"]["processed_dir"]) / "subject_qc_list.json"
    
    if not qc_list_path.exists():
        raise FileNotFoundError(f"Subject QC list not found: {qc_list_path}. Run T014 first.")
    
    with open(qc_list_path, 'r') as f:
        qc_data = json.load(f)
    
    # Filter for retained subjects
    retained_subjects = [
        item["subject_id"] for item in qc_data 
        if item.get("retained", False)
    ]
    
    if not retained_subjects:
        logger.warning("No retained subjects found in QC list. Aborting extraction.")
        return []
    
    logger.info(f"Processing {len(retained_subjects)} retained subjects.")
    
    results = []
    for subj_id in retained_subjects:
        # Process one by one to stay within memory limits
        res = process_subject_extraction(subj_id, config, qc_list_path)
        results.append(res)
        
        # Optional: Log progress
        if res["status"] == "failed":
            logger.warning(f"Skipped {subj_id} due to failure.")
    
    # Save summary
    summary_path = Path(config["paths"]["results_dir"]) / "extraction_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Extraction pipeline complete. Summary saved to {summary_path}")
    return results

def main():
    """Entry point for script execution."""
    import sys
    from src.utils import setup_logging
    
    setup_logging()
    logger = get_logger(__name__)
    
    try:
        results = run_extraction_pipeline()
        success_count = sum(1 for r in results if r["status"] == "success")
        logger.info(f"Pipeline finished. Success: {success_count}/{len(results)}")
        
        if success_count == 0 and len(results) > 0:
            sys.exit(1)
            
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
