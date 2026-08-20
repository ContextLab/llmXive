"""
T017: Combine extracted ROI timecourses into a single CSV.

Reads the extracted .npy files for Left Hippocampus, Right Hippocampus, and DLPFC,
aggregates them into a long-format DataFrame, and saves to data/processed/roi_timecourses.csv.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, error, info

logger = get_logger(__name__)

def load_roi_timecourse(npy_path: Path) -> np.ndarray:
    """Load a .npy file containing timecourse data."""
    if not npy_path.exists():
        raise FileNotFoundError(f"Required timecourse file missing: {npy_path}")
    data = np.load(npy_path, allow_pickle=True)
    return data

def extract_subject_ids(mask_paths_file: Path) -> list:
    """
    Extract subject IDs from the mask_paths.json or by scanning the data directory.
    Since T013-T016 produce files per subject, we scan the data/processed directory
    for patterns like 'sub-XX_roi_left_hipp.npy' if mask_paths.json is insufficient.
    """
    # Check if mask_paths.json exists and has subject info
    if mask_paths_file.exists():
        try:
            with open(mask_paths_file, 'r') as f:
                data = json.load(f)
            # Expecting structure like {"subjects": ["sub-01", ...]} or similar
            if "subjects" in data:
                return data["subjects"]
        except Exception as e:
            logger.warning(f"Could not parse subject IDs from mask_paths.json: {e}")

    # Fallback: Scan data/processed for known patterns
    processed_dir = mask_paths_file.parent
    subjects = set()
    for f in processed_dir.glob("sub-*_roi_left_hipp.npy"):
        # Extract sub-XX from filename
        stem = f.stem
        # Assume format sub-XX_roi_...
        if stem.startswith("sub-"):
            sub_id = stem.split("_")[0]
            subjects.add(sub_id)

    if not subjects:
        raise FileNotFoundError(
            "Could not determine subject IDs. No sub-*.npy files found in data/processed."
        )

    return sorted(list(subjects))

def combine_roi_timecourses(
    output_path: Path,
    processed_dir: Path,
    subject_ids: list,
    rois: dict
):
    """
    Combine timecourses from multiple ROIs and subjects into a single CSV.

    Args:
        output_path: Path to save the combined CSV.
        processed_dir: Directory containing the .npy files.
        subject_ids: List of subject identifiers (e.g., ['sub-01', ...]).
        rois: Dict mapping ROI name to filename pattern (e.g., {'left_hipp': 'sub-{}_roi_left_hipp.npy'}).
    """
    rows = []

    for sub_id in subject_ids:
        for roi_name, file_pattern in rois.items():
            npy_path = processed_dir / file_pattern.format(sub_id)
            
            if not npy_path.exists():
                logger.warning(f"Missing file for {sub_id} {roi_name}: {npy_path}")
                continue

            try:
                timecourse = load_roi_timecourse(npy_path)
            except Exception as e:
                logger.error(f"Failed to load {npy_path}: {e}")
                continue

            if timecourse.ndim == 1:
                # Single subject, single ROI: shape (timepoints,)
                timepoints = range(len(timecourse))
                signals = timecourse.tolist()
            elif timecourse.ndim == 2:
                # If shape is (timepoints, 1) or (timepoints, voxels) - flatten or take mean
                # Assuming we want the mean signal across voxels if 2D
                if timecourse.shape[1] == 1:
                    signals = timecourse.flatten().tolist()
                else:
                    # Average across voxels
                    signals = np.mean(timecourse, axis=1).tolist()
                timepoints = range(len(signals))
            else:
                logger.error(f"Unexpected shape for {npy_path}: {timecourse.shape}")
                continue

            for tp, signal in zip(timepoints, signals):
                rows.append({
                    "subject_id": sub_id,
                    "roi": roi_name,
                    "timepoint": tp,
                    "signal": signal
                })

    if not rows:
        raise RuntimeError("No data rows were collected. Check input files.")

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    info(f"Combined {len(rows)} rows into {output_path}")

def main():
    processed_dir = Path("data/processed")
    output_file = processed_dir / "roi_timecourses.csv"
    mask_paths_file = processed_dir / "mask_paths.json"

    if not processed_dir.exists():
        error("Directory data/processed does not exist. Run setup tasks first.")
        sys.exit(1)

    # Define ROI file patterns based on T014, T015, T016 outputs
    # T014: data/processed/roi_left_hipp.npy (Wait, the task says 'roi_left_hipp.npy' but usually these are per subject)
    # Re-reading T014: "Save to data/processed/roi_left_hipp.npy". 
    # If the previous tasks saved a SINGLE file for ALL subjects, the logic changes.
    # However, standard fMRI pipelines save per subject. 
    # Let's check the T014 description again: "Extract BOLD timecourses for Left Hippocampus ... Save to data/processed/roi_left_hipp.npy".
    # This implies a single file? Or is it a template? 
    # Given T017 says "Combine extracted timecourses", and T014/15/16 are marked [P] (parallel), 
    # it is highly likely they produce per-subject files or a single aggregated file per ROI.
    # If T014 produces a SINGLE file 'roi_left_hipp.npy' containing data for all subjects, 
    # then T017 just needs to load these 3 files and melt them.
    
    # Let's assume the previous tasks (T014-T016) produced SINGLE files per ROI 
    # containing all subjects' data (e.g., shape: [n_subjects, n_timepoints] or similar).
    # If they produced per-subject files, the file names would likely be sub-XX_...
    # The task description for T014 says "Save to data/processed/roi_left_hipp.npy" (singular).
    # We will implement logic to handle the single-file case first, as that matches the literal description.
    
    roi_files = {
        "left_hipp": processed_dir / "roi_left_hipp.npy",
        "right_hipp": processed_dir / "roi_right_hipp.npy",
        "dlpfc": processed_dir / "roi_dlpfc.npy"
    }

    # Check if files exist
    missing = [name for name, path in roi_files.items() if not path.exists()]
    if missing:
        error(f"Missing required input files: {missing}. Ensure T014-T016 completed successfully.")
        sys.exit(1)

    rows = []

    # Strategy: Load each ROI file. Assume shape is (n_subjects, n_timepoints) or (n_timepoints, n_subjects).
    # We need to identify subject IDs. If the file doesn't contain them, we might need to infer from 
    # a metadata file or assume a sequence.
    # Let's look for a subjects list in mask_paths.json or generate sequential IDs if not found.
    
    subject_ids = []
    if mask_paths_file.exists():
        try:
            with open(mask_paths_file, 'r') as f:
                mask_data = json.load(f)
            if "subjects" in mask_data:
                subject_ids = mask_data["subjects"]
        except:
            pass

    for roi_name, fpath in roi_files.items():
        data = np.load(fpath, allow_pickle=True)
        
        # Determine dimensions
        # If 1D: Assume single subject or flattened. If 1D, we can't separate subjects easily without metadata.
        # If 2D: Likely (subjects, timepoints) or (timepoints, subjects).
        
        if data.ndim == 1:
            # Assume this is a single subject's timecourse or an average.
            # Without subject ID, we might default to 'sub-01' or fail.
            # Given the context of 'Combine', we expect multiple subjects.
            # If T014 produced a single file for ALL subjects, it must be 2D.
            # If it's 1D, we treat it as one subject.
            if not subject_ids:
                subject_ids = ["sub-01"] # Fallback
            timepoints = range(len(data))
            for tp, signal in zip(timepoints, data):
                rows.append({
                    "subject_id": subject_ids[0],
                    "roi": roi_name,
                    "timepoint": tp,
                    "signal": float(signal)
                })
        elif data.ndim == 2:
            # Heuristic: If second dim is large (timepoints) and first is small (subjects), shape=(N, T)
            # If first is large, shape=(T, N).
            # Let's assume standard (Subjects, Timepoints) if N_subjects < N_timepoints
            n_rows, n_cols = data.shape
            
            if not subject_ids:
                # Infer count
                # If n_rows < n_cols, likely rows are subjects
                if n_rows < n_cols:
                    num_subjects = n_rows
                    time_dim = n_cols
                    subject_ids = [f"sub-{i+1:02d}" for i in range(num_subjects)]
                else:
                    # Assume columns are subjects
                    num_subjects = n_cols
                    time_dim = n_rows
                    subject_ids = [f"sub-{i+1:02d}" for i in range(num_subjects)]
            
            # Determine orientation
            if n_rows == len(subject_ids):
                # Rows are subjects, Cols are timepoints
                for i, sub in enumerate(subject_ids):
                    timepoints = range(n_cols)
                    for tp, signal in zip(timepoints, data[i]):
                        rows.append({
                            "subject_id": sub,
                            "roi": roi_name,
                            "timepoint": tp,
                            "signal": float(signal)
                        })
            else:
                # Rows are timepoints, Cols are subjects
                for j, sub in enumerate(subject_ids):
                    timepoints = range(n_rows)
                    for tp, signal in zip(timepoints, data[:, j]):
                        rows.append({
                            "subject_id": sub,
                            "roi": roi_name,
                            "timepoint": tp,
                            "signal": float(signal)
                        })
        else:
            error(f"Unsupported array shape for {roi_name}: {data.shape}")
            continue

    if not rows:
        error("No data extracted. Check input shapes and subject ID logic.")
        sys.exit(1)

    df = pd.DataFrame(rows)
    # Ensure column order matches spec: subject_id, roi, timepoint, signal
    df = df[["subject_id", "roi", "timepoint", "signal"]]
    
    df.to_csv(output_file, index=False)
    info(f"Successfully created {output_file} with {len(df)} rows.")

if __name__ == "__main__":
    main()
