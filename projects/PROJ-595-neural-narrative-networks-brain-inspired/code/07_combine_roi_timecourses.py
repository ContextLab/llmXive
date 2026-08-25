"""
T017: Combine extracted timecourses into a single CSV.

Reads ROI timecourses from:
  - data/processed/roi_left_hipp.npy
  - data/processed/roi_right_hipp.npy
  - data/processed/roi_dlpfc.npy

Produces:
  - data/processed/roi_timecourses.csv

Columns: subject_id, roi, timepoint, signal
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"

# Input files (produced by T014, T015, T016)
INPUT_FILES = {
    "left_hipp": PROCESSED_DIR / "roi_left_hipp.npy",
    "right_hipp": PROCESSED_DIR / "roi_right_hipp.npy",
    "dlpfc": PROCESSED_DIR / "roi_dlpfc.npy",
}

OUTPUT_FILE = PROCESSED_DIR / "roi_timecourses.csv"

# ROI display names
ROI_LABELS = {
    "left_hipp": "left_hippocampus",
    "right_hipp": "right_hippocampus",
    "dlpfc": "dlpfc",
}

def load_roi_timecourse(path: Path) -> np.ndarray:
    """
    Load a .npy file containing timecourses.
    
    Expected shape: (n_subjects, n_timepoints, n_voxels)
    or (n_subjects, n_timepoints) if already averaged over voxels.
    
    Returns:
        np.ndarray of shape (n_subjects, n_timepoints)
    """
    if not path.exists():
        raise FileNotFoundError(f"Required input file missing: {path}")
    
    data = np.load(path, allow_pickle=False)
    
    # Handle case where data might be 2D (subjects, timepoints)
    if data.ndim == 2:
        return data
    
    # If 3D (subjects, timepoints, voxels), average over voxels
    if data.ndim == 3:
        return np.mean(data, axis=2)
    
    raise ValueError(f"Unexpected array shape for {path}: {data.shape}")

def extract_subject_ids(data: np.ndarray) -> list:
    """
    Generate subject IDs based on the number of subjects in the data.
    Format: sub-001, sub-002, etc.
    """
    n_subjects = data.shape[0]
    return [f"sub-{str(i+1).zfill(3)}" for i in range(n_subjects)]

def combine_roi_timecourses() -> pd.DataFrame:
    """
    Combine all ROI timecourses into a single DataFrame.
    
    Returns:
        pd.DataFrame with columns: subject_id, roi, timepoint, signal
    """
    rows = []
    
    for roi_key, path in INPUT_FILES.items():
        if not path.exists():
            raise FileNotFoundError(
                f"Missing required input for {roi_key}: {path}. "
                "Ensure T014, T015, T016 have completed successfully."
            )
        
        data = load_roi_timecourse(path)
        subject_ids = extract_subject_ids(data)
        n_timepoints = data.shape[1]
        
        for subj_idx, subj_id in enumerate(subject_ids):
            for t_idx in range(n_timepoints):
                signal_val = float(data[subj_idx, t_idx])
                rows.append({
                    "subject_id": subj_id,
                    "roi": ROI_LABELS[roi_key],
                    "timepoint": t_idx,
                    "signal": signal_val,
                })
    
    df = pd.DataFrame(rows, columns=["subject_id", "roi", "timepoint", "signal"])
    return df

def main():
    """Main entry point for T017."""
    print(f"Starting T017: Combining ROI timecourses...")
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        df = combine_roi_timecourses()
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"Successfully wrote {len(df)} rows to {OUTPUT_FILE}")
        print(f"Columns: {list(df.columns)}")
        print(f"ROIs included: {df['roi'].unique()}")
        print(f"Subjects: {df['subject_id'].nunique()}")
        print(f"Timepoints per subject: {df['timepoint'].max() + 1}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR during combination: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()