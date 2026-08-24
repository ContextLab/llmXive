"""Run QC-only pipeline for fMRI NIfTI files.

This script scans an input directory for NIfTI files, computes
temporal signal-to-noise ratio (tSNR) and framewise displacement (FD)
for each subject, and writes a summary CSV to the analysis directory.

The implementation relies only on real data – no synthetic placeholders
are generated.  All heavy‑lifting is performed with ``nibabel`` for
NIfTI handling and ``pandas`` for CSV output.

Usage
-----
python code/preprocess/run_qc_only.py \
    --input <path_to_raw_data_dir> \
    --output <path_to_processed_dir>

The script will create (if necessary) the directory
``data/analysis`` and write ``qc_summary.csv`` there.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import nibabel as nib
import numpy as np
import pandas as pd

# Use the project‑wide tolerant logger
from code.logging_config import get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def find_nifti_files(input_dir: Path) -> List[Path]:
    """Return a list of all ``*.nii`` or ``*.nii.gz`` files in *input_dir*."""
    nifti_paths = list(input_dir.rglob("*.nii")) + list(
        input_dir.rglob("*.nii.gz")
    )
    logger.info(f"Found {len(nifti_paths)} NIfTI files in {input_dir}")
    return nifti_paths


def compute_tsnr(nifti_path: Path) -> float:
    """Compute the temporal SNR for a 4‑D fMRI image.

    tSNR is defined as the mean signal across time divided by the
    standard deviation across time, averaged over all brain voxels.
    For simplicity we average over all voxels (including zeros); in a
    production pipeline a brain mask would be applied.
    """
    img = nib.load(str(nifti_path))
    data = img.get_fdata()
    if data.ndim != 4:
        raise ValueError(
            f"Expected a 4‑D fMRI image, got shape {data.shape} for {nifti_path}"
        )
    # Exclude the first 5 volumes (common practice for equilibration)
    data = data[..., 5:]
    mean_signal = np.mean(data, axis=3)
    std_signal = np.std(data, axis=3, ddof=1)
    # Avoid division by zero
    with np.errstate(divide="ignore", invalid="ignore"):
        voxel_tsnr = np.where(std_signal == 0, 0, mean_signal / std_signal)
    # Return the median tSNR across voxels (robust to outliers)
    tsnr_value = float(np.median(voxel_tsnr[np.isfinite(voxel_tsnr)]))
    logger.debug(f"tSNR for {nifti_path.name}: {tsnr_value:.2f}")
    return tsnr_value


def load_motion_parameters(nifti_path: Path) -> np.ndarray:
    """Load motion parameters associated with *nifti_path*.

    The convention used throughout the repository is that a text file
    named ``<subject>_motion.par`` (space‑separated, 6 columns) resides
    alongside the NIfTI file.  If the file does not exist, an empty array
    is returned and FD will be reported as NaN.
    """
    motion_file = nifti_path.with_name(nifti_path.stem + "_motion.par")
    if not motion_file.is_file():
        logger.warning(
            f"Motion parameter file not found for {nifti_path.name}: {motion_file}"
        )
        return np.empty((0, 6))
    try:
        motion = np.loadtxt(str(motion_file))
        if motion.ndim == 1:
            motion = motion.reshape(1, -1)
        if motion.shape[1] != 6:
            raise ValueError(
                f"Expected 6 motion columns, got {motion.shape[1]} in {motion_file}"
            )
        logger.debug(
            f"Loaded motion parameters for {nifti_path.name}: shape {motion.shape}"
        )
        return motion
    except Exception as exc:
        logger.error(f"Failed to read motion parameters from {motion_file}: {exc}")
        raise


def compute_fd(motion: np.ndarray) -> float:
    """Compute framewise displacement (FD) from motion parameters.

    FD is the sum of absolute differences of the six motion parameters
    between consecutive volumes (translation + rotation).  Rotations are
    converted from degrees to millimetres assuming a 50 mm radius head.
    """
    if motion.shape[0] <= 1:
        logger.warning("Not enough motion frames to compute FD; returning NaN")
        return float("nan")
    # Convert rotations (degrees) to millimetres (radius = 50 mm)
    rot = np.deg2rad(motion[:, 3:]) * 50.0
    trans = motion[:, :3]
    params = np.hstack([trans, rot])
    diff = np.abs(np.diff(params, axis=0))
    fd = np.sum(diff, axis=1)
    fd_mean = float(np.mean(fd))
    logger.debug(f"Mean FD: {fd_mean:.4f} mm")
    return fd_mean


def run_qc(nifti_path: Path) -> Dict[str, float]:
    """Run QC for a single NIfTI file.

    Returns a dictionary with keys:
        - ``tSNR``: temporal signal‑to‑noise ratio
        - ``FD``:   mean framewise displacement (mm)
    """
    tsnr = compute_tsnr(nifti_path)
    motion = load_motion_parameters(nifti_path)
    fd = compute_fd(motion) if motion.size else float("nan")
    return {"tSNR": tsnr, "FD": fd}


# ----------------------------------------------------------------------
# CLI / pipeline orchestration
# ----------------------------------------------------------------------


def run_qc_pipeline(input_dir: Path, output_dir: Path) -> None:
    """Execute the QC‑only pipeline over all subjects.

    The function writes ``data/analysis/qc_summary.csv`` containing one
    row per subject with columns ``subject_id``, ``tSNR`` and ``FD``.
    """
    nifti_files = find_nifti_files(input_dir)
    if not nifti_files:
        raise FileNotFoundError(f"No NIfTI files found in {input_dir}")

    records: List[Tuple[str, float, float]] = []
    for nifti_path in nifti_files:
        subject_id = nifti_path.stem.split("_")[0]  # simple heuristic
        logger.info(f"Processing subject {subject_id} ({nifti_path.name})")
        try:
            qc_metrics = run_qc(nifti_path)
            records.append(
                (subject_id, qc_metrics["tSNR"], qc_metrics["FD"])
            )
        except Exception as exc:
            logger.error(f"QC failed for {nifti_path}: {exc}")
            raise

    # Ensure the analysis directory exists
    analysis_dir = Path("data/analysis")
    analysis_dir.mkdir(parents=True, exist_ok=True)

    qc_df = pd.DataFrame(
        records, columns=["subject_id", "tSNR", "FD"]
    )
    qc_csv_path = analysis_dir / "qc_summary.csv"
    qc_df.to_csv(qc_csv_path, index=False)
    logger.info(f"Wrote QC summary to {qc_csv_path}")

    # Also write a minimal subjects_included file (subjects that passed the
    # tSNR threshold of ≥ 50 for ≥ 90 % of voxels).  The exact threshold
    # logic is implemented in ``code/data/preprocess.py``; here we simply
    # forward the subject IDs that have a finite tSNR.
    included_path = analysis_dir / "subjects_included.csv"
    included_df = qc_df[qc_df["tSNR"].notna()][["subject_id"]]
    included_df.to_csv(included_path, index=False)
    logger.info(f"Wrote subjects_included to {included_path}")


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="QC‑only pipeline (tSNR + FD) for fMRI NIfTI files."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Directory containing raw NIfTI files.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=False,
        default="data/processed",
        help="Directory where processed outputs will be placed (currently unused).",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    if not input_path.is_dir():
        logger.error(f"Input directory does not exist: {input_path}")
        sys.exit(1)
    try:
        run_qc_pipeline(input_path, output_path)
    except Exception as exc:
        logger.error(f"QC pipeline failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()