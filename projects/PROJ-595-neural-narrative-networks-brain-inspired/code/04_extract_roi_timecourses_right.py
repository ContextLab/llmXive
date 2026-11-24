"""
T015 – Extract right hippocampus BOLD timecourses.

This script mirrors `04_extract_roi_timecourses.py` but operates on the
right‑hippocampus mask. The output files are:
  * data/processed/roi_right_hipp.npy
  * data/processed/roi_right_hipp.ids.json  (subject identifiers)
"""

import os
import sys
import glob
import json
import numpy as np
import nibabel as nib
from pathlib import Path

# Project‑relative paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "openneuro_ds001495"
MASK_PATHS_FILE = PROJECT_ROOT / "data" / "processed" / "mask_paths.json"
OUTPUT_NPY = PROJECT_ROOT / "data" / "processed" / "roi_right_hipp.npy"

# Error codes (matching logging_config expectations)
ERROR_E001 = "E001"
ERROR_E002 = "E002"

def log_error(code: str, message: str):
    sys.stderr.write(f"{code}: {message}\\n")
    sys.stderr.flush()
    sys.exit(1)

def natural_sort_key(s: str):
    import re
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'([0-9]+)', s)]

def load_mask_from_json() -> Path:
    if not MASK_PATHS_FILE.exists():
        log_error(ERROR_E001, f"Mask paths file not found: {MASK_PATHS_FILE}")

    with open(MASK_PATHS_FILE, "r") as f:
        mask_data = json.load(f)

    if "right_hipp" not in mask_data:
        log_error(ERROR_E001, "Right hippocampus mask path missing in mask_paths.json")

    mask_path = PROJECT_ROOT / mask_data["right_hipp"]
    if not mask_path.exists():
        log_error(ERROR_E001, f"Right hippocampus mask file not found: {mask_path}")

    return mask_path

def find_functional_runs(subject_dir: Path) -> list:
    pattern = subject_dir / "func" / "*task-narratives_bold.nii.gz"
    files = sorted(glob.glob(str(pattern)))
    return files

def extract_roi_timecourse(nifti_path: Path, mask_path: Path) -> np.ndarray:
    img = nib.load(str(nifti_path))
    mask = nib.load(str(mask_path))

    data = img.get_fdata()
    mask_data = mask.get_fdata()

    if data.shape[:3] != mask_data.shape[:3]:
        log_error(ERROR_E001,
                  f"Shape mismatch between image {data.shape[:3]} and mask {mask_data.shape[:3]}")

    # Flatten spatial dimensions
    voxels = np.prod(data.shape[:3])
    timepoints = data.shape[3]
    data_flat = data.reshape(voxels, timepoints)
    mask_flat = mask_data.flatten()
    valid = mask_flat > 0
    if not np.any(valid):
        log_error(ERROR_E002, f"No valid voxels in mask for {nifti_path}")

    # Mean across valid voxels for each timepoint
    roi_signal = data_flat[valid, :].mean(axis=0)
    return roi_signal

def process_subject(subject_dir: Path, mask_path: Path) -> tuple:
    subject_id = subject_dir.name
    runs = find_functional_runs(subject_dir)
    if not runs:
        log_error(ERROR_E002, f"No functional runs found for subject {subject_id}")

    timecourses = []
    for run in runs:
        ts = extract_roi_timecourse(Path(run), mask_path)
        timecourses.append(ts)

    combined = np.concatenate(timecourses)
    return subject_id, combined

def main() -> int:
    # Verify raw data directory
    if not DATA_RAW_DIR.exists():
        log_error(ERROR_E001, f"Raw data directory missing: {DATA_RAW_DIR}")

    # Load mask
    mask_path = load_mask_from_json()

    # Discover subjects
    subject_pattern = DATA_RAW_DIR / "sub-*"
    subject_dirs = sorted(glob.glob(str(subject_pattern)), key=lambda x: natural_sort_key(os.path.basename(x)))
    if not subject_dirs:
        log_error(ERROR_E001, f"No subject directories found under {DATA_RAW_DIR}")

    results = []
    for subj_dir in subject_dirs:
        subj_path = Path(subj_dir)
        sid, ts = process_subject(subj_path, mask_path)
        results.append((sid, ts))

    if not results:
        log_error(ERROR_E002, "No timecourses extracted for any subject.")

    # Pad to max length
    max_len = max(len(ts) for _, ts in results)
    matrix = np.full((len(results), max_len), np.nan, dtype=np.float32)
    subject_ids = []
    for i, (sid, ts) in enumerate(results):
        matrix[i, :len(ts)] = ts.astype(np.float32)
        subject_ids.append(sid)

    # Ensure output directory exists
    OUTPUT_NPY.parent.mkdir(parents=True, exist_ok=True)

    np.save(OUTPUT_NPY, matrix)
    ids_path = OUTPUT_NPY.with_suffix('.ids.json')
    with open(ids_path, "w") as f:
        json.dump(subject_ids, f)

    print(f"Right hippocampus timecourses saved to {OUTPUT_NPY}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
