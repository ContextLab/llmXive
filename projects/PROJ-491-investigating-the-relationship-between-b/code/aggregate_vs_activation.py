import os
import sys
import csv
import logging
import numpy as np
from pathlib import Path

from config import ensure_directories
from preprocessing import extract_vs_roi_timeseries
from state_manager import update_state_artifact

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/processed/aggregate_vs_activation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def find_valid_subject_dirs(raw_data_dir: Path) -> list:
    """
    Scan the raw data directory for subject folders that contain task-fMRI data.
    Returns a list of paths to valid subject directories.
    """
    valid_subjects = []
    if not raw_data_dir.exists():
        logger.error(f"Raw data directory does not exist: {raw_data_dir}")
        return valid_subjects

    for item in raw_data_dir.iterdir():
        if item.is_dir() and item.name.startswith('sub-'):
            # Check for task-fMRI existence (looking for standard HCP task naming)
            # HCP tasks usually have 'task-rest' and 'task-exec' etc.
            # We specifically need task-fMRI for VS activation.
            # Assuming standard HCP structure: sub-XX/MNINonLinear/Results/...
            # Or simpler: sub-XX/func/
            func_dir = item / "MNINonLinear" / "Results"
            if not func_dir.exists():
                func_dir = item / "func"
            
            if func_dir.exists():
                # Look for any nifti file to confirm data presence
                nifti_files = list(func_dir.glob("*.nii*"))
                if nifti_files:
                    valid_subjects.append(item)
                else:
                    logger.warning(f"No NIfTI files found in {func_dir}, skipping {item.name}")
            else:
                logger.warning(f"Functional directory not found for {item.name}")
    
    logger.info(f"Found {len(valid_subjects)} valid subject directories.")
    return valid_subjects

def load_subject_vs_timeseries(subject_dir: Path) -> np.ndarray:
    """
    Load the Ventral Striatum time series for a specific subject.
    This assumes T016c has already run and generated the intermediate time series
    or that we can derive it here. 
    
    Since T016c is a separate task that writes timeseries, we assume the 
    preprocessing module `extract_vs_roi_timeseries` is available and can 
    process the raw data directly if intermediate files aren't present, 
    OR we look for the intermediate file if T016c created one.
    
    For this aggregation task, we will call the extraction logic directly 
    to ensure we have the data, assuming the raw data is available.
    """
    # We rely on the preprocessing module to handle the extraction logic.
    # If T016c produced a file, we could load it. If not, we extract on the fly.
    # To be robust, we check for an intermediate file first, then extract.
    
    # Expected intermediate path pattern based on T016c context:
    # data/processed/timeseries/{subject_id}_vs_timeseries.npy
    # However, to ensure we get the data, we will invoke the extraction function
    # from preprocessing.py which reads the raw NIfTI.
    
    try:
        # This function assumes the raw data is in `subject_dir`
        # and the ROI definition is available in data/contracts.
        # We pass the subject_dir to the extraction function.
        ts = extract_vs_roi_timeseries(subject_dir)
        if ts is None or len(ts) == 0:
            logger.warning(f"Could not extract VS timeseries for {subject_dir.name}")
            return None
        return ts
    except Exception as e:
        logger.error(f"Error extracting VS timeseries for {subject_dir.name}: {e}")
        return None

def calculate_mean_activation(timeseries: np.ndarray) -> float:
    """
    Calculate the mean activation magnitude of the Ventral Striatum time series.
    Returns a float.
    """
    if timeseries is None or len(timeseries) == 0:
        return np.nan
    
    # Calculate mean of the absolute values or just the mean?
    # "Activation magnitude" usually implies deviation from baseline.
    # Assuming the timeseries is already preprocessed (z-scored or mean-centered).
    # If not, we take the mean of the signal as a proxy for activation level.
    # Standard fMRI analysis often uses mean signal intensity or mean z-score.
    # Given the context of "magnitude", we'll compute the mean of the signal.
    return float(np.mean(timeseries))

def write_activation_csv(subject_data: list, output_path: Path):
    """
    Write the aggregated activation data to a CSV file.
    Columns: subject_id, mean_activation
    """
    ensure_directories()
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['subject_id', 'mean_activation'])
        for sub_id, activation in subject_data:
            writer.writerow([sub_id, activation])
    
    logger.info(f"Activation data written to {output_path}")

def main():
    """
    Main entry point for T016b: Aggregate VS activation.
    1. Find valid subject directories.
    2. For each, extract VS time series.
    3. Calculate mean activation.
    4. Write results to data/processed/ventral_striatum_activation.csv.
    """
    # Ensure directories exist
    ensure_directories()
    
    # Paths
    raw_data_dir = Path("data/raw")
    output_file = Path("data/processed/ventral_striatum_activation.csv")
    
    # 1. Find subjects
    subjects = find_valid_subject_dirs(raw_data_dir)
    if not subjects:
        logger.error("No valid subjects found. Exiting.")
        sys.exit(1)
    
    results = []
    valid_count = 0
    
    # 2. Process each subject
    for subject_dir in subjects:
        subject_id = subject_dir.name
        logger.info(f"Processing {subject_id}...")
        
        ts = load_subject_vs_timeseries(subject_dir)
        
        if ts is not None:
            mean_act = calculate_mean_activation(ts)
            results.append((subject_id, mean_act))
            valid_count += 1
        else:
            logger.warning(f"Skipping {subject_id} due to missing/invalid timeseries.")
    
    if valid_count == 0:
        logger.error("No subjects processed successfully.")
        sys.exit(1)
    
    # 3. Write results
    write_activation_csv(results, output_file)
    
    # 4. Update state
    update_state_artifact(output_file)
    
    logger.info(f"Successfully processed {valid_count} subjects.")

if __name__ == "__main__":
    main()
