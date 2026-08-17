import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Ensure project root is in path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, info, error, warning
from config import get_config

logger = get_logger(__name__)

def load_roi_timecourse(file_path: Path) -> np.ndarray:
    """
    Load a single ROI timecourse .npy file.
    Expects shape: (n_subjects, n_timepoints) or (n_timepoints,) for single subject.
    Returns a 2D array (n_subjects, n_timepoints).
    """
    if not file_path.exists():
        raise FileNotFoundError(f"ROI timecourse file not found: {file_path}")
    
    try:
        data = np.load(file_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load {file_path}: {e}")
    
    # Normalize to 2D: (subjects, timepoints)
    if data.ndim == 1:
        # Assume single subject, reshape to (1, timepoints)
        data = data.reshape(1, -1)
    elif data.ndim != 2:
        raise ValueError(f"Unexpected shape {data.shape} for {file_path}. Expected 1D or 2D.")
    
    return data

def extract_subject_ids(base_path: Path, roi_name: str) -> list:
    """
    Extract subject IDs from the filenames in the data directory.
    Assumes filenames follow pattern: roi_<name>_<subject_id>.npy or similar.
    For this implementation, we assume the input .npy files are pre-aggregated
    by ROI as per T014-T016 outputs (roi_left_hipp.npy, etc.), which contain
    all subjects. We will generate generic subject IDs if not embedded in filename.
    
    However, looking at the task description: "Combine extracted timecourses...
    with columns: subject_id, roi, timepoint, signal".
    
    Since T014-T016 output files are named `roi_left_hipp.npy`, etc., and likely
    contain stacked data for all subjects, we need to know the subject count.
    If the file is (n_subjects, n_timepoints), we generate subject IDs.
    If the file is (n_timepoints,) it's a single subject (unlikely for a pipeline).
    
    We will assume the files from T014-T016 are shaped (N_subjects, N_timepoints).
    We will generate subject IDs as "sub-001", "sub-002", etc., based on the first dimension.
    """
    # We don't actually have the subject list from the previous steps in the file names
    # because T014-016 output aggregated files. We will infer count from data shape.
    # In a real scenario, we might load a manifest. Here we generate sequential IDs.
    return [] 

def combine_roi_timecourses(
    input_dir: Path,
    output_path: Path,
    roi_files: dict
) -> None:
    """
    Combine ROI timecourses from multiple .npy files into a single CSV.
    
    Args:
        input_dir: Directory containing the .npy files.
        output_path: Path for the output CSV.
        roi_files: Dict mapping ROI name to filename (e.g., {"Left Hippocampus": "roi_left_hipp.npy"}).
    """
    all_rows = []
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    for roi_name, filename in roi_files.items():
        file_path = input_dir / filename
        
        if not file_path.exists():
            error(f"Required input file missing for {roi_name}: {file_path}")
            raise FileNotFoundError(f"Missing {filename} for {roi_name}")
        
        logger.info(f"Loading {roi_name} from {file_path}")
        data = load_roi_timecourse(file_path)
        n_subjects, n_timepoints = data.shape
        
        # Generate subject IDs if not available. 
        # In a real pipeline, we would parse these from the raw data or a manifest.
        # For now, we use generic IDs.
        subject_ids = [f"sub-{i+1:03d}" for i in range(n_subjects)]
        
        for subj_idx, subj_id in enumerate(subject_ids):
            for t in range(n_timepoints):
                signal_val = float(data[subj_idx, t])
                all_rows.append({
                    "subject_id": subj_id,
                    "roi": roi_name,
                    "timepoint": t,
                    "signal": signal_val
                })
    
    if not all_rows:
        error("No data rows collected. Check input files.")
        raise ValueError("No data collected to write to CSV.")
    
    df = pd.DataFrame(all_rows)
    # Ensure column order matches spec: subject_id, roi, timepoint, signal
    df = df[["subject_id", "roi", "timepoint", "signal"]]
    
    df.to_csv(output_path, index=False)
    info(f"Successfully wrote combined timecourses to {output_path} with {len(df)} rows.")

def main():
    config = get_config()
    input_dir = Path("data/processed")
    output_file = Path("data/processed/roi_timecourses.csv")
    
    # Mapping of ROI names to the expected filenames from T014-T016
    roi_files = {
        "Left Hippocampus": "roi_left_hipp.npy",
        "Right Hippocampus": "roi_right_hipp.npy",
        "DLPFC": "roi_dlpfc.npy"
    }
    
    try:
        combine_roi_timecourses(input_dir, output_file, roi_files)
        logger.info("Task T017 completed successfully.")
    except Exception as e:
        logger.critical(f"Task T017 failed: {e}")
        raise

if __name__ == "__main__":
    main()