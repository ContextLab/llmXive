"""
ROI Masking utilities for Hippocampus, mPFC, PCC, Lateral Temporal Cortex.
"""
import numpy as np
from pathlib import Path
import logging
from nilearn import image, masking
from nilearn import datasets
import code.config as config

logger = logging.getLogger(__name__)

# Define ROIs based on standard atlases (Harvard-Oxford or similar)
ROI_LABELS = {
    'hippocampus': 'Left-Hippocampus', # Simplified mapping
    'mpfc': 'Frontal-Mid',
    'pcc': 'Post-Cingulate-Cortex',
    'ltc': 'Temporal-Sup'
}

def load_roi_mask(roi_name, template='MNI152'):
    """
    Load an ROI mask. In a real pipeline, this loads from a specific atlas file.
    """
    logger.info(f"Loading mask for {roi_name}")
    # Placeholder for actual atlas loading logic
    return None

def extract_roi_timecourse(nifti_img, mask_img):
    """
    Extract mean timecourse from an ROI mask.
    """
    return masking.apply_mask(nifti_img, mask_img).mean(axis=1)

def extract_all_rois(nifti_img, rois=None):
    """
    Extract timecourses for all defined ROIs.
    Returns a dict: {roi_name: timecourse_array}
    """
    if rois is None:
        rois = ROI_LABELS.keys()
    
    results = {}
    for roi in rois:
        # Simulate extraction
        results[roi] = np.random.rand(100) # Placeholder for real extraction
    return results
