"""
Data loading utilities for HCP OpenNeuro dataset (ds000224).

This module provides helper functions used throughout the pipeline to
locate raw data files, validate their presence, and load diffusion MRI
(dMRI) and functional MRI (fMRI) data into NumPy arrays.

The implementation follows the expectations of the unit tests in
``tests/unit/test_loader.py`` and serves as the public API for other
pipeline components (e.g., tractography sensitivity analysis).
"""

import os
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any

import numpy as np
import nibabel as nib

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def _get_raw_data_dir() -> Path:
    """
    Return the absolute path to the project's ``data/raw`` directory.

    The function is deliberately simple so that tests can patch it
    (see ``tests/unit/test_loader.py``). By default it resolves the
    repository root relative to this file's location.

    Returns
    -------
    Path
        Path object pointing to ``<project_root>/data/raw``.
    """
    # ``loader.py`` lives in ``code/preprocess/``; two parents up is the
    # project root.
    project_root = Path(__file__).resolve().parents[2]
    return project_root / "data" / "raw"


def _validate_data_existence(root_dir: Path) -> bool:
    """
    Check whether the given directory appears to contain any subject
    sub‑directories or files.

    Parameters
    ----------
    root_dir : Path
        Directory that should contain raw HCP subject folders.

    Returns
    -------
    bool
        ``True`` if at least one entry (file or folder) exists, otherwise
        ``False``.
    """
    if not root_dir.is_dir():
        return False
    # Any entry (file or directory) inside signals that data is present.
    return any(entry for entry in root_dir.iterdir())


# ----------------------------------------------------------------------
# Core loading functions
# ----------------------------------------------------------------------


def load_hcp_dmri(
    subject_id: str,
    return_confidence: bool = False,
    raw_dir: Optional[Path] = None,
) -> Tuple[np.ndarray, np.ndarray] | Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Load diffusion MRI (dMRI) data for a given subject.

    The function expects the BIDS‑style naming convention used in the
    test fixtures:

    - Diffusion image: ``{subject_id}_dMRI.nii.gz``
    - b‑values file: ``{subject_id}_dMRI.bval``

    If ``return_confidence`` is ``True`` the loader also attempts to read a
    confidence matrix stored as ``{subject_id}_confidence.npy``.  This
    auxiliary file is optional; when absent a ``FileNotFoundError`` is
    raised.

    Parameters
    ----------
    subject_id : str
        Subject identifier (e.g., ``"100307"`` or ``"sub-100307"``).
    return_confidence : bool, optional
        Whether to also return a confidence matrix.  Default is ``False``.
    raw_dir : Path, optional
        Override the default raw data directory (useful for tests).

    Returns
    -------
    Tuple[np.ndarray, np.ndarray] or Tuple[None, None]
        If ``return_confidence`` is ``False`` a tuple ``(dmri_data,
        bvals)`` is returned.  ``dmri_data`` is a 4‑D NumPy array with the
        diffusion volumes as the last dimension; ``bvals`` is a 1‑D array
        of b‑values.  When ``return_confidence`` is ``True`` a tuple
        ``(dmri_data, confidence_matrix)`` is returned; the ``bvals`` are
        omitted in this mode.

    Raises
    ------
    FileNotFoundError
        If the expected files cannot be located.
    ValueError
        If the loaded NIfTI image does not have four dimensions.
    """
    raw_root = raw_dir or _get_raw_data_dir()
    subject_dir = raw_root / subject_id
    if not subject_dir.is_dir():
        raise FileNotFoundError(f"Subject directory not found: {subject_dir}")

    # ------------------------------------------------------------------
    # Load diffusion image
    # ------------------------------------------------------------------
    dmri_path = subject_dir / f"{subject_id}_dMRI.nii.gz"
    if not dmri_path.is_file():
        raise FileNotFoundError(f"dMRI NIfTI file not found: {dmri_path}")

    dmri_img = nib.load(str(dmri_path))
    dmri_data = dmri_img.get_fdata()
    if dmri_data.ndim != 4:
        raise ValueError(
            f"dMRI data for {subject_id} must be 4‑D (X,Y,Z,volumes); got shape {dmri_data.shape}"
        )
    dmri_data = dmri_data.astype(np.float32)

    # ------------------------------------------------------------------
    # Load b‑values (used by downstream tractography steps)
    # ------------------------------------------------------------------
    bval_path = subject_dir / f"{subject_id}_dMRI.bval"
    if not bval_path.is_file():
        raise FileNotFoundError(f"bval file not found: {bval_path}")

    # ``np.loadtxt`` works for both space‑ and newline‑separated b‑values.
    bvals = np.loadtxt(str(bval_path), dtype=np.float32)

    if return_confidence:
        # Confidence matrix is optional but required when the caller asks
        # for it (e.g., tractography sensitivity analysis).
        conf_path = subject_dir / f"{subject_id}_confidence.npy"
        if not conf_path.is_file():
            raise FileNotFoundError(
                f"Confidence matrix not found for {subject_id}: {conf_path}"
            )
        confidence = np.load(str(conf_path))
        return dmri_data, confidence

    return dmri_data, bvals


def load_hcp_fmri(
    subject_id: str,
    raw_dir: Optional[Path] = None,
) -> np.ndarray:
    """
    Load resting‑state functional MRI (fMRI) data for a given subject.

    The expected filename follows the pattern used in the test suite:

    ``{subject_id}_rfMRI_REST1_LR.nii.gz``

    Parameters
    ----------
    subject_id : str
        Subject identifier.
    raw_dir : Path, optional
        Override the default raw data directory.

    Returns
    -------
    np.ndarray
        4‑D fMRI data array (X, Y, Z, time).

    Raises
    ------
    FileNotFoundError
        If the fMRI file cannot be found.
    ValueError
        If the loaded NIfTI image is not 4‑D.
    """
    raw_root = raw_dir or _get_raw_data_dir()
    subject_dir = raw_root / subject_id
    if not subject_dir.is_dir():
        raise FileNotFoundError(f"Subject directory not found: {subject_dir}")

    fmri_path = subject_dir / f"{subject_id}_rfMRI_REST1_LR.nii.gz"
    if not fmri_path.is_file():
        raise FileNotFoundError(f"fMRI NIfTI file not found: {fmri_path}")

    fmri_img = nib.load(str(fmri_path))
    fmri_data = fmri_img.get_fdata()
    if fmri_data.ndim != 4:
        raise ValueError(
            f"fMRI data for {subject_id} must be 4‑D; got shape {fmri_data.shape}"
        )
    return fmri_data.astype(np.float32)


# ----------------------------------------------------------------------
# Public API (re‑export for convenience)
# ----------------------------------------------------------------------
__all__ = [
    "_get_raw_data_dir",
    "_validate_data_existence",
    "load_hcp_dmri",
    "load_hcp_fmri",
]
