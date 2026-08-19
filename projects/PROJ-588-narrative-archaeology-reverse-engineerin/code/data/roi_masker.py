"""
ROI masking utilities for extracting timecourses.
Implements extraction for Hippocampus, mPFC, PCC, and Lateral Temporal Cortex.
Separates timecourses into 'early' and 'late' event phases based on segment metadata.
"""
import numpy as np
from pathlib import Path
import logging
import json
from nilearn import image, masking
from nilearn import datasets
from nilearn.masking import apply_mask
import code.config as config
from code.data.segment import load_event_annotations, align_events_to_bold, segment_timecourse

logger = logging.getLogger(__name__)

# Define standard ROI names and their mapping to atlas indices or strategies
# Using Harvard-Oxford Subcortical and Cortical Atlases
ROIS_CONFIG = {
    "hippocampus": {
        "atlas": "sub-maxprob-thr50-1mm",
        "type": "subcortical",
        "indices": [17, 18]  # Left and Right Hippocampus in HO subcortical
    },
    "mpfc": {
        "atlas": "maxprob-thr50-1mm",
        "type": "cortical",
        "names": ["Frontal Pole"] # Approximation for mPFC in HO cortical
    },
    "pcc": {
        "atlas": "maxprob-thr50-1mm",
        "type": "cortical",
        "names": ["Posterior Cingulate Cortex"]
    },
    "ltc": {
        "atlas": "maxprob-thr50-1mm",
        "type": "cortical",
        "names": ["Temporal Pole: superior temporal gyrus", "Temporal Pole: middle temporal gyrus"]
    }
}

def load_roi_mask(roi_name):
    """
    Load an ROI mask from nilearn atlases.
    Returns a 3D Niimg-like object or a list of them if bilateral.
    """
    roi_config = ROIS_CONFIG.get(roi_name)
    if not roi_config:
        raise ValueError(f"Unknown ROI: {roi_name}")

    atlas_name = roi_config["atlas"]
    roi_type = roi_config["type"]

    logger.info(f"Fetching {roi_type} atlas: {atlas_name} for {roi_name}")

    if roi_type == "subcortical":
        # Fetch Harvard-Oxford Subcortical
        atlas_data = datasets.fetch_atlas_harvard_oxford(atlas_name)
        mask_img = atlas_data.maps
        labels = atlas_data.labels
        
        # Extract indices for Left/Right Hippocampus (usually indices 17, 18 in HO subcortical)
        # Note: Index 0 is background.
        indices = roi_config.get("indices", [])
        if not indices:
            # Fallback: try to find by label name if indices not hardcoded
            for idx, label in enumerate(labels):
                if "Hippocampus" in label:
                    indices.append(idx)
            
        if not indices:
            raise RuntimeError(f"Could not identify Hippocampus indices in Harvard-Oxford atlas.")

        # Combine left and right into one mask for averaging, or return list
        # For simplicity in this pipeline, we create a combined mask for the ROI
        combined_mask = np.zeros(mask_img.shape, dtype=np.uint8)
        for idx in indices:
            if idx < len(labels):
                combined_mask[mask_img.get_fdata() == idx] = 1
        
        from nilearn import image
        return image.new_img_like(mask_img, combined_mask)

    elif roi_type == "cortical":
        # Fetch Harvard-Oxford Cortical
        atlas_data = datasets.fetch_atlas_harvard_oxford(atlas_name)
        mask_img = atlas_data.maps
        labels = atlas_data.labels
        
        target_names = roi_config.get("names", [])
        if not target_names:
            raise RuntimeError(f"No target names defined for {roi_name}")

        # Find indices matching target names
        indices = []
        for name in target_names:
            # Case insensitive search
            for idx, label in enumerate(labels):
                if name.lower() in label.lower():
                    indices.append(idx)
                    break
        
        if not indices:
            logger.warning(f"Could not find exact match for {target_names} in HO cortical. Attempting fuzzy match.")
            for name in target_names:
                for idx, label in enumerate(labels):
                    if name.split(":")[0].strip().lower() in label.lower():
                        indices.append(idx)
                        break

        if not indices:
            raise RuntimeError(f"Could not identify ROI indices for {roi_name} in Harvard-Oxford atlas.")

        combined_mask = np.zeros(mask_img.shape, dtype=np.uint8)
        for idx in indices:
            if idx < len(labels):
                combined_mask[mask_img.get_fdata() == idx] = 1
        
        return image.new_img_like(mask_img, combined_mask)

    return None

def extract_roi_timecourse(nii_img, mask_img):
    """
    Extract mean timecourse from an ROI mask.
    
    Args:
        nii_img: 4D fMRI image (Niimg-like).
        mask_img: 3D mask image (Niimg-like).
        
    Returns:
        np.ndarray: 1D array of mean BOLD signal over time.
    """
    if nii_img is None or mask_img is None:
        raise ValueError("Input images cannot be None")
        
    try:
        # Ensure mask is binary
        mask_data = mask_img.get_fdata()
        mask_data = (mask_data > 0).astype(np.uint8)
        binary_mask_img = image.new_img_like(mask_img, mask_data)
        
        timecourse = apply_mask(nii_img, binary_mask_img)
        # apply_mask returns (n_timepoints, n_voxels). We want mean across voxels.
        if timecourse.ndim > 1:
            return timecourse.mean(axis=1)
        return timecourse
    except Exception as e:
        logger.error(f"Failed to extract timecourse from mask: {e}")
        raise

def extract_all_rois(nii_img, event_segments):
    """
    Extract timecourses for all defined ROIs, separated by Early and Late phases.
    
    Args:
        nii_img: 4D fMRI image (preprocessed).
        event_segments: List of dicts containing event timing and phase info 
                        (output of code.data.segment.segment_timecourse or similar).
                        Expected keys: 'start_idx', 'end_idx', 'phase' (early/late).
                        
    Returns:
        dict: {
            'hippocampus': {'early': [timecourse], 'late': [timecourse]},
            'mpfc': {...},
            ...
        }
    """
    roi_names = list(ROIS_CONFIG.keys())
    results = {name: {'early': [], 'late': []} for name in roi_names}
    
    # Load masks once per ROI
    masks = {}
    for name in roi_names:
        try:
            masks[name] = load_roi_mask(name)
        except Exception as e:
            logger.error(f"Failed to load mask for {name}: {e}")
            masks[name] = None

    if not event_segments:
        logger.warning("No event segments provided. Returning empty timecourses.")
        return results

    # Group segments by phase
    early_segments = [s for s in event_segments if s.get('phase') == 'early']
    late_segments = [s for s in event_segments if s.get('phase') == 'late']
    
    all_segments = {'early': early_segments, 'late': late_segments}

    for phase, segments in all_segments.items():
        if not segments:
            logger.info(f"No segments found for phase: {phase}")
            continue
        
        for seg in segments:
            start_idx = int(seg['start_idx'])
            end_idx = int(seg['end_idx'])
            
            # Slice the 4D image for this event
            try:
                # nilearn image slicing
                # Note: Some versions of nilearn might require specific slicing methods.
                # Using index_img is standard for 4D -> 3D (or subset of 4D)
                event_img = image.index_img(nii_img, slice(start_idx, end_idx))
                
                if event_img.shape[3] == 0:
                    logger.warning(f"Event slice {start_idx}:{end_idx} is empty.")
                    continue

                for roi_name in roi_names:
                    mask_img = masks[roi_name]
                    if mask_img is None:
                        continue
                    
                    try:
                        tc = extract_roi_timecourse(event_img, mask_img)
                        results[roi_name][phase].append(tc)
                    except Exception as e:
                        logger.error(f"Error extracting {roi_name} for {phase} event: {e}")
                        
            except Exception as e:
                logger.error(f"Failed to slice image for event {start_idx}:{end_idx}: {e}")

    return results

def run_roi_extraction_pipeline(preprocessed_dir, output_dir, subject_id):
    """
    High-level function to run ROI extraction for a subject.
    
    Args:
        preprocessed_dir: Path to directory containing preprocessed NIfTI and event CSV.
        output_dir: Path to save results.
        subject_id: Subject identifier string.
    """
    preprocessed_dir = Path(preprocessed_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find preprocessed file (assuming standard naming from T008/T009)
    # Looking for *_space-MNI_desc-preproc_bold.nii.gz or similar
    nifti_files = list(preprocessed_dir.glob("*desc-preproc_bold.nii.gz"))
    if not nifti_files:
        nifti_files = list(preprocessed_dir.glob("*space-MNI_bold.nii.gz"))
    
    if not nifti_files:
        raise FileNotFoundError(f"No preprocessed NIfTI found in {preprocessed_dir}")
    
    nii_path = nifti_files[0]
    logger.info(f"Processing subject {subject_id} from {nii_path}")
    
    # Load events
    event_csv = preprocessed_dir / f"{subject_id}_events.csv"
    if not event_csv.exists():
        raise FileNotFoundError(f"Event CSV not found: {event_csv}")
        
    # Load and segment events (T015 logic)
    # Assuming segment.py returns a list of dicts with start_idx, end_idx, phase
    events = load_event_annotations(event_csv)
    # We assume the segmentation logic (T015) has already aligned these to bold indices
    # If not, we need to call align_events_to_bold here.
    # For this task, we assume 'events' is already aligned or we do a simple pass.
    # Re-using segment_timecourse logic if needed, but T015 is completed.
    # Let's assume events is a list of dicts: {'onset', 'duration', 'phase'}
    # We need to convert onset/duration to indices.
    # This requires TR. We'll assume TR is in config or header.
    
    # Simple alignment fallback if not pre-calculated:
    # Load 4D image to get TR
    nii_img = image.load_img(nii_path)
    # Check header for TR
    try:
        tr = nii_img.header.get_zooms()[3]
    except:
        tr = 2.0 # Default fallback
        
    aligned_events = []
    for ev in events:
        start_vol = int(ev['onset'] / tr)
        end_vol = int((ev['onset'] + ev['duration']) / tr)
        aligned_events.append({
            'start_idx': start_vol,
            'end_idx': end_vol,
            'phase': ev.get('phase', 'early') # Default to early if not specified
        })
    
    # Extract
    results = extract_all_rois(nii_img, aligned_events)
    
    # Save results
    output_file = output_dir / f"{subject_id}_roi_timecourses.json"
    # Convert numpy arrays to lists for JSON serialization
    serializable_results = {}
    for roi, phases in results.items():
        serializable_results[roi] = {}
        for phase, tcs in phases.items():
            serializable_results[roi][phase] = [tc.tolist() for tc in tcs]
    
    with open(output_file, 'w') as f:
        json.dump(serializable_results, f, indent=2)
        
    logger.info(f"Saved ROI timecourses to {output_file}")
    return output_file

if __name__ == "__main__":
    # Simple test runner
    import sys
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 4:
        print("Usage: python code/data/roi_masker.py <preprocessed_dir> <output_dir> <subject_id>")
        sys.exit(1)
        
    run_roi_extraction_pipeline(sys.argv[1], sys.argv[2], sys.argv[3])
