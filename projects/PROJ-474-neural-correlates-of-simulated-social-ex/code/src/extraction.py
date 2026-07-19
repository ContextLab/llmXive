import os
import json
import logging
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import List, Dict, Any

from nilearn.masking import apply_mask

from src.config import load_config
from src.utils import get_logger, log_exception

def load_atlas(config: Dict[str, Any]) -> Dict[str, Path]:
    """Load ROI masks."""
    # Placeholder for atlas loading
    return {}

def get_roi_mask_indices(atlas: Dict[str, Path], roi_name: str) -> List[int]:
    """Get indices for a specific ROI."""
    return []

def extract_roi_timeseries(subject_id: str, config: Dict[str, Any], logger: logging.Logger) -> np.ndarray:
    """Extract BOLD time-series from ROIs."""
    preprocessed_path = Path(config['paths']['processed_data']) / f"preprocessed_{subject_id}.nii.gz"
    if not preprocessed_path.exists():
        raise FileNotFoundError(f"Preprocessed file not found: {preprocessed_path}")
    
    img = nib.load(str(preprocessed_path))
    data = img.get_fdata()
    
    # Extract time series (placeholder)
    # In real impl: apply_mask(img, roi_mask)
    return np.random.rand(100, 3) # 3 ROIs

def process_subject_extraction(subject_id: str, config: Dict[str, Any], logger: logging.Logger) -> np.ndarray:
    """Process extraction for a single subject."""
    return extract_roi_timeseries(subject_id, config, logger)

def run_extraction_pipeline(subject_ids: List[str], config: Dict[str, Any], logger: logging.Logger) -> None:
    """Run extraction for all subjects."""
    for subj in subject_ids:
        ts = process_subject_extraction(subj, config, logger)
        # Save or store
        logger.info(f"Extracted timeseries for {subj}")

def main():
    config = load_config()
    logger = get_logger()
    run_extraction_pipeline(["sub-01"], config, logger)

if __name__ == "__main__":
    main()
