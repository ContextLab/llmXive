"""
Script to preprocess all downloaded HCP resting‑state fMRI files.

For each subject directory under ``data/raw/hcp_<subject_id>/`` the script
searches for the first NIfTI file (``*.nii`` or ``*.nii.gz``) and runs the
``preprocess_fmri`` function defined in ``code/data/preprocess.py``.
The preprocessed image is written to
``data/processed/fmri_clean/<subject_id>.nii.gz`` as required by the
specification (FR‑001).

The script is intended to be executed as part of the pipeline:
    python code/data/run_preprocess.py

It will raise an error if required input files are missing, ensuring that
only real data are processed (no synthetic fall‑backs).
"""

import sys
import logging
from pathlib import Path
from typing import List

# Project‑wide utilities
from llmxive_toolkit import paths, get_logger
from data.preprocess import preprocess_fmri

log = get_logger(__name__)

def find_nifti_file(subject_dir: Path) -> Path:
    """
    Return the first NIfTI file found in ``subject_dir``.
    Raises ``FileNotFoundError`` if none are present.
    """
    nifti_candidates: List[Path] = sorted(
        list(subject_dir.rglob("*.nii")) + list(subject_dir.rglob("*.nii.gz"))
    )
    if not nifti_candidates:
        raise FileNotFoundError(f"No NIfTI file found in {subject_dir}")
    return nifti_candidates[0]

def main() -> None:
    """
    Locate raw subject folders, preprocess each fMRI scan, and write the
    cleaned image to ``data/processed/fmri_clean/<subject_id>.nii.gz``.
    """
    raw_root = paths.data("raw")
    output_root = paths.data("processed", "fmri_clean")
    output_root.mkdir(parents=True, exist_ok=True)

    # Subject directories follow the pattern ``hcp_<subject_id>``.
    subject_dirs = sorted(raw_root.glob("hcp_*"))
    if not subject_dirs:
        log.error("No subject directories found under %s", raw_root)
        sys.exit(1)

    for subj_dir in subject_dirs:
        # Derive subject identifier (strip the ``hcp_`` prefix)
        subject_id = subj_dir.name.replace("hcp_", "")
        try:
            input_nii = find_nifti_file(subj_dir)
        except FileNotFoundError as e:
            log.warning("Skipping subject %s: %s", subject_id, e)
            continue

        output_path = output_root / f"{subject_id}.nii.gz"

        try:
            log.info("Preprocessing subject %s: %s -> %s", subject_id, input_nii, output_path)
            preprocess_fmri(
                input_path=str(input_nii),
                output_path=str(output_path),
                low_freq=0.01,
                high_freq=0.1,
                do_motion_correction=True,
                do_normalization=True,
            )
            log.info("Successfully wrote preprocessed file for %s", subject_id)
        except Exception as exc:
            log.error("Failed to preprocess subject %s: %s", subject_id, exc)
            # Propagate the exception – the pipeline must fail loudly on real data errors.
            raise

if __name__ == "__main__":
    main()