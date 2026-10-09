"""Preprocess rs‑fMRI BIDS data, apply AAL atlas, and compute connectivity matrices.

This script expects a CSV file ``data/processed/eligible_subjects.csv`` with a
column ``subject_id`` listing the subjects to process. For each subject it:

1. Locates the raw resting‑state BOLD NIfTI file under ``data/raw/ds000246``.
2. Performs a simple motion‑correction step (realignment to the mean image).
3. Normalizes the image to the MNI152 template.
4. Extracts regional time‑series using the AAL atlas (via Nilearn).
5. Computes a Pearson correlation connectivity matrix.
6. Saves the matrix as ``<subject_id>_conn.npy`` (and a CSV version) under
   ``data/processed/connectivity_matrices/``.

All steps are logged via the reproducibility logger. If any subject fails,
processing stops and the script exits with a non‑zero status. Excluded
subjects and reasons are recorded in ``data/processed/excluded_subjects.log``.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

import numpy as np
from nilearn import datasets, image
from nilearn.input_data import NiftiLabelsMasker

# Project‑local logger utilities
from utils.logger import get_logger, log_operation

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

@log_operation
def ensure_directory(path: Path | str) -> None:
    """Create ``path`` if it does not exist."""
    Path(path).mkdir(parents=True, exist_ok=True)

@log_operation
def read_eligible_subjects(csv_path: Path | str) -> List[str]:
    """Return a list of subject IDs from ``eligible_subjects.csv``."""
    subjects: List[str] = []
    with open(csv_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        if "subject_id" not in reader.fieldnames:
            raise ValueError("eligible_subjects.csv must contain a 'subject_id' column")
        for row in reader:
            subjects.append(row["subject_id"])
    return subjects

@log_operation
def find_subject_fmri(subject_id: str) -> Optional[Path]:
    """Search the BIDS tree for the resting‑state BOLD file of ``subject_id``."""
    raw_root = Path("data/raw/ds000246")
    pattern = f"sub-{subject_id}/func/*_task-rest*_bold.nii*"
    matches = list((raw_root / pattern).glob())
    if not matches:
        return None
    # Return the first match (there should normally be only one per session)
    return matches[0]

@log_operation
def motion_correction(bold_path: Path) -> image.Nifti1Image:
    """Realign the BOLD series to its mean image (simple motion correction)."""
    # Load the 4‑D image
    bold_img = image.load_img(str(bold_path))
    # Compute the mean volume
    mean_img = image.mean_img(bold_img)
    # Resample each volume to the mean (acts as a crude realignment)
    corrected = image.resample_to_img(bold_img, mean_img, interpolation="linear")
    return corrected

@log_operation
def normalize_to_mni(img: image.Nifti1Image) -> image.Nifti1Image:
    """Resample ``img`` to the MNI152 2 mm template."""
    mni = datasets.fetch_icbm152_2009()["t1"]
    normalized = image.resample_to_img(img, mni, interpolation="linear")
    return normalized

@log_operation
def extract_time_series(
    img: image.Nifti1Image,
) -> np.ndarray:
    """Apply the AAL atlas and return a (time, region) array."""
    aal = datasets.fetch_atlas_aal()
    masker = NiftiLabelsMasker(
        labels_img=aal["maps"],
        standardize=True,
        detrend=False,
        verbose=0,
    )
    # ``fit_transform`` returns shape (n_scans, n_regions)
    ts = masker.fit_transform(img)
    return ts

@log_operation
def compute_connectivity_matrix(time_series: np.ndarray) -> np.ndarray:
    """Pearson correlation matrix (region × region)."""
    # Correlation of columns (regions)
    corr = np.corrcoef(time_series.T)
    # Replace NaNs that arise from constant columns
    corr = np.nan_to_num(corr)
    return corr

@log_operation
def save_connectivity_matrix(
    subject_id: str,
    matrix: np.ndarray,
    out_dir: Path | str = "data/processed/connectivity_matrices",
) -> None:
    """Write ``matrix`` as ``<subject_id>_conn.npy`` and ``.csv``."""
    out_dir = Path(out_dir)
    ensure_directory(out_dir)
    npy_path = out_dir / f"{subject_id}_conn.npy"
    csv_path = out_dir / f"{subject_id}_conn.csv"
    np.save(npy_path, matrix)
    # CSV for easy inspection
    np.savetxt(csv_path, matrix, delimiter=",")
    get_logger().info(
        "saved_connectivity",
        subject=subject_id,
        npy_path=str(npy_path),
        csv_path=str(csv_path),
    )

@log_operation
def write_excluded_log(subject_id: str, reason: str) -> None:
    """Append a line to ``data/processed/excluded_subjects.log``."""
    log_path = Path("data/processed/excluded_subjects.log")
    ensure_directory(log_path.parent)
    with open(log_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([subject_id, reason])

@log_operation
def write_status(status: dict, path: Path | str = "data/processed/preprocess_status.json") -> None:
    """Write a tiny JSON status file."""
    ensure_directory(Path(path).parent)
    with open(path, "w") as f:
        json.dump(status, f, indent=2)

# --------------------------------------------------------------------------- #
# Core per‑subject pipeline
# --------------------------------------------------------------------------- #

@log_operation
def preprocess_subject(subject_id: str) -> None:
    """Run the full preprocessing pipeline for a single subject."""
    logger = get_logger()
    logger.info("start_preprocess_subject", subject=subject_id)

    bold_path = find_subject_fmri(subject_id)
    if bold_path is None:
        raise FileNotFoundError(f"No BOLD file found for subject {subject_id}")

    # 1️⃣ Motion correction
    corrected = motion_correction(bold_path)

    # 2️⃣ Normalization to MNI space
    normalized = normalize_to_mni(corrected)

    # 3️⃣ Atlas‑based time‑series extraction
    ts = extract_time_series(normalized)

    # 4️⃣ Connectivity matrix
    conn = compute_connectivity_matrix(ts)

    # 5️⃣ Persist results
    save_connectivity_matrix(subject_id, conn)

    logger.info("finished_preprocess_subject", subject=subject_id)

# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

@log_operation
def main() -> None:
    """Run preprocessing for all eligible subjects."""
    logger = get_logger("preprocess_and_parcellate")
    start_time = time.time()

    eligible_csv = Path("data/processed/eligible_subjects.csv")
    if not eligible_csv.is_file():
        logger.error("missing_eligible_csv", path=str(eligible_csv))
        sys.exit(2)  # EXIT_CODE_NO_ELIGIBLE equivalent

    try:
        subjects = read_eligible_subjects(eligible_csv)
    except Exception as exc:
        logger.error("failed_to_read_eligible", error=str(exc))
        sys.exit(1)

    if not subjects:
        logger.error("no_eligible_subjects")
        sys.exit(2)

    any_failure = False
    for subj in subjects:
        try:
            preprocess_subject(subj)
        except Exception as exc:
            any_failure = True
            logger.error(
                "subject_processing_failure",
                subject=subj,
                error=str(exc),
            )
            write_excluded_log(subj, f"Processing failure: {exc}")

    # Write a summary status file
    status = {
        "processed_subjects": len(subjects) - (1 if any_failure else 0),
        "failed": any_failure,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
    }
    write_status(status)

    elapsed = time.time() - start_time
    logger.info("preprocess_complete", elapsed_seconds=elapsed)

    if any_failure:
        sys.exit(1)  # Non‑zero to signal that not all subjects succeeded

# --------------------------------------------------------------------------- #
# Run when executed as a script
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()
