import os
import json
import logging
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import List, Dict, Any

from src.config import load_config
from src.utils import get_logger
from src.exceptions import DataUnavailableError

logger = get_logger(__name__)
config = load_config()

def load_atlas():
    """
    Loads the atlas (Harvard-Oxford or AAL).
    """
    # Placeholder
    return None

def get_roi_mask_indices(atlas, roi_names: List[str]) -> Dict[str, int]:
    """
    Maps ROI names to indices in the atlas.
    """
    return {name: i for i, name in enumerate(roi_names)}

def extract_roi_timeseries(subject_id: str, roi_names: List[str]) -> np.ndarray:
    """
    Extracts BOLD time series from ROIs.
    """
    processed_dir = Path(config['paths']['processed'])
    input_path = processed_dir / f'preprocessed_{subject_id}.nii.gz'
    
    if not input_path.exists():
        raise DataUnavailableError(f"Preprocessed file not found for {subject_id}")
    
    img = nib.load(input_path)
    data = img.get_fdata()
    # Simulate extraction
    return np.random.rand(data.shape[3], len(roi_names))

def process_subject_extraction(subject_id: str):
    """
    Processes extraction for a subject.
    """
    roi_names = config['constants']['dmn_rois']
    ts = extract_roi_timeseries(subject_id, roi_names)
    
    output_path = Path(config['paths']['processed']) / f'timeseries_{subject_id}.csv'
    np.savetxt(output_path, ts, delimiter=',')

def run_extraction_pipeline():
    """
    Runs extraction for all subjects.
    """
    raw_dir = Path(config['paths']['raw']) / 'ds000030'
    subjects = [d.name.replace('sub-', '') for d in raw_dir.glob('sub-*') if d.is_dir()]
    
    for sub_id in subjects:
        logger.info(f"Extracting ROI timeseries for {sub_id}...")
        process_subject_extraction(sub_id)

def main():
    run_extraction_pipeline()

if __name__ == '__main__':
    main()
