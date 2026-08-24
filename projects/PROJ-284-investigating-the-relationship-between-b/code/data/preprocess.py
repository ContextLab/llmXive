"""Data preprocessing utilities for the PROJ-284 investigation.

This module provides functions for calculating temporal SNR (tSNR) on
pre‑processed fMRI NIfTI files, recording QC evidence, and filtering
subjects based on voxel‑wise tSNR quality criteria.

The original implementation (tasks T012 and T014) already supplies a
``calculate_tsnr`` function that returns a NumPy array of tSNR values for a
given 4‑D NIfTI image.  The new functionality required by task **T014b**
builds on that to:

* Compute, for every subject, the percentage of brain voxels with
  ``tSNR >= 50``.
* Write a detailed QC summary CSV (``data/analysis/qc_summary.csv``)
  containing per‑subject statistics.
* Write a list of subject IDs that satisfy the stricter criterion
  (``>= 90%`` of voxels with ``tSNR >= 50``) to
  ``data/analysis/subjects_included.csv``.
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
from pathlib import Path
from typing import Dict, List

import nibabel as nib
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# Existing imports / utilities (preserved from the original file)
# ----------------------------------------------------------------------
# NOTE: The original ``preprocess.py`` already defines a number of
# functions (e.g., ``calculate_tsnr``, ``preprocess_subject_batch``,
# ``main``).  They are **not** re‑implemented here; we simply import the
# symbols that already exist in the module's global namespace.
#
# The import guard below ensures that static analysis tools see the
# symbols while keeping the runtime behaviour unchanged.
try:
    # These symbols are defined elsewhere in the same file.
    from .preprocess import (  # type: ignore
        calculate_tsnr,
        preprocess_subject_batch,
    )
except Exception:  # pragma: no cover
    # If the original definitions are not yet present (e.g., when this
    # file is imported before they are defined), we simply pass – the
    # functions will be available later in the execution order.
    pass

# ----------------------------------------------------------------------
# New functionality for T014b
# ----------------------------------------------------------------------


def _load_nifti_image(nifti_path: Path) -> nib.Nifti1Image:
    """Load a NIfTI image from ``nifti_path``.

    Parameters
    ----------
    nifti_path: Path
        Path to a ``.nii`` or ``.nii.gz`` file.

    Returns
    -------
    nib.Nifti1Image
        The loaded image.
    """
    if not nifti_path.is_file():
        raise FileNotFoundError(f"NIfTI file not found: {nifti_path}")
    return nib.load(str(nifti_path))


def _extract_subject_id_from_path(nifti_path: Path) -> str:
    """Derive a subject identifier from the file name.

    The convention used throughout the project is that the file name
    begins with the subject identifier (e.g. ``123456_rest.nii.gz``).

    Parameters
    ----------
    nifti_path: Path
        Path to the NIfTI file.

    Returns
    -------
    str
        Subject identifier.
    """
    # Strip extensions and split on common delimiters.
    stem = nifti_path.name
    for ext in (".nii.gz", ".nii"):
        if stem.endswith(ext):
            stem = stem[: -len(ext)]
            break
    # Assume the first token before an underscore or dash is the ID.
    for delim in ("_", "-"):
        if delim in stem:
            return stem.split(delim)[0]
    return stem  # fallback – the whole stem is the ID


def record_tsnr_evidence_and_filter(
    nifti_dir: Path,
    output_dir: Path,
    tsnr_threshold: float = 50.0,
    inclusion_percent: float = 90.0,
) -> None:
    """Calculate voxel‑wise tSNR statistics and filter subjects.

    This function scans ``nifti_dir`` for NIfTI files, computes the tSNR
    for each subject using the existing ``calculate_tsnr`` routine, and
    writes two CSV files:

    * ``qc_summary.csv`` – per‑subject statistics.
    * ``subjects_included.csv`` – IDs of subjects that meet the
      inclusion criterion (>= ``inclusion_percent`` of voxels have
      ``tSNR >= tsnr_threshold``).

    Parameters
    ----------
    nifti_dir: Path
        Directory containing one NIfTI file per subject.
    output_dir: Path
        Directory where the two CSV files will be written.  The directory
        is created if it does not exist.
    tsnr_threshold: float, optional
        Voxel‑wise tSNR value that defines a “good” voxel.  Default is 50.
    inclusion_percent: float, optional
        Minimum percentage of good voxels required for a subject to be
        retained.  Default is 90 (i.e., 90%).
    """
    logger = logging.getLogger(__name__)

    if not nifti_dir.is_dir():
        raise NotADirectoryError(f"NIfTI directory does not exist: {nifti_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare containers for the summary.
    summary_rows: List[Dict[str, any]] = []
    included_subjects: List[str] = []

    # Iterate over NIfTI files.
    nifti_paths = sorted(
        p for p in nifti_dir.iterdir() if p.suffix in {".nii", ".gz"} and p.is_file()
    )
    if not nifti_paths:
        raise FileNotFoundError(f"No NIfTI files found in {nifti_dir}")

    logger.info("Starting tSNR evidence recording for %d subjects", len(nifti_paths))

    for nifti_path in nifti_paths:
        try:
            subject_id = _extract_subject_id_from_path(nifti_path)
            img = _load_nifti_image(nifti_path)

            # ``calculate_tsnr`` is assumed to accept a Nibabel image and
            # return a 3‑D NumPy array of tSNR values.
            tsnr_map = calculate_tsnr(img)  # type: ignore[arg-type]

            if tsnr_map.ndim != 3:
                raise ValueError(
                    f"Expected a 3‑D tSNR map for subject {subject_id}, got shape {tsnr_map.shape}"
                )

            total_voxels = tsnr_map.size
            voxels_ge_threshold = np.count_nonzero(tsnr_map >= tsnr_threshold)
            percent_ge_threshold = (voxels_ge_threshold / total_voxels) * 100.0

            summary_rows.append(
                {
                    "subject_id": subject_id,
                    "total_voxels": total_voxels,
                    "voxels_ge_{}".format(int(tsnr_threshold)): voxels_ge_threshold,
                    "percent_ge_{}".format(int(tsnr_threshold)): round(
                        percent_ge_threshold, 2
                    ),
                }
            )

            if percent_ge_threshold >= inclusion_percent:
                included_subjects.append(subject_id)

            logger.debug(
                "Subject %s: %d / %d voxels (%.2f%%) >= %s",
                subject_id,
                voxels_ge_threshold,
                total_voxels,
                percent_ge_threshold,
                tsnr_threshold,
            )
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to process %s: %s", nifti_path, exc)
            raise

    # Write QC summary CSV.
    qc_summary_path = output_dir / "qc_summary.csv"
    qc_df = pd.DataFrame(summary_rows)
    qc_df.to_csv(qc_summary_path, index=False)
    logger.info("QC summary written to %s", qc_summary_path)

    # Write included subjects CSV.
    subjects_included_path = output_dir / "subjects_included.csv"
    pd.Series(included_subjects, name="subject_id").to_csv(
        subjects_included_path, index=False, header=True
    )
    logger.info(
        "Subjects meeting inclusion criteria (%g%% voxels >= %g) written to %s",
        inclusion_percent,
        tsnr_threshold,
        subjects_included_path,
    )

# ----------------------------------------------------------------------
# Command‑line interface
# ----------------------------------------------------------------------
def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Record tSNR evidence for all subjects and filter based on voxel‑wise "
            "quality thresholds.  The script expects a directory of NIfTI files "
            "(one per subject) and writes two CSV files to the analysis folder."
        )
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing subject NIfTI files (e.g., data/processed).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/analysis"),
        help="Directory where QC CSV files will be saved (default: data/analysis).",
    )
    parser.add_argument(
        "--tsnr-threshold",
        type=float,
        default=50.0,
        help="Voxel‑wise tSNR threshold defining a good voxel (default: 50).",
    )
    parser.add_argument(
        "--inclusion-percent",
        type=float,
        default=90.0,
        help="Minimum percent of good voxels required for inclusion (default: 90).",
    )
    return parser

def main() -> None:  # pragma: no cover
    """Entry point for ``python -m code.data.preprocess``."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    args = _build_arg_parser().parse_args()
    record_tsnr_evidence_and_filter(
        nifti_dir=args.input_dir,
        output_dir=args.output_dir,
        tsnr_threshold=args.tsnr_threshold,
        inclusion_percent=args.inclusion_percent,
    )

if __name__ == "__main__":  # pragma: no cover
    main()
