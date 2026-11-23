"""
Data loading utilities for the HCP OpenNeuro dataset (ds000224).

This module provides:
* `download_hcp_dataset` – downloads the full OpenNeuro HCP dataset
  into a user‑specified directory using the 🤗 datasets library.
* `load_dmri` – loads a subject's diffusion MRI (dMRI) NIfTI file as a
  NumPy array.
* `load_fmri` – loads a subject's resting‑state fMRI NIfTI file as a
  NumPy array.
* `get_subject_paths` – helper that returns the absolute paths of the
  dMRI and fMRI files for a given subject inside the downloaded BIDS
  hierarchy.

All functions raise informative exceptions if the requested data cannot
be found, ensuring that failures are loud rather than silently falling
back to synthetic placeholders.
"""

import os
import json
from pathlib import Path
from typing import Tuple, Optional

import numpy as np
import nibabel as nib

# The 🤗 datasets library is not part of the standard environment.
# It is declared in ``requirements.txt`` and will be installed by the
# project’s setup step.
from datasets import load_dataset, DownloadConfig

# ----------------------------------------------------------------------
# Configuration constants – these mirror the values defined in
# ``code/config.py`` where possible.
# ----------------------------------------------------------------------
DEFAULT_DATASET_NAME = "openneuro"
DEFAULT_DATASET_ID = "ds000224"
DEFAULT_DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "raw"

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
__all__ = [
    "download_hcp_dataset",
    "load_dmri",
    "load_fmri",
    "get_subject_paths",
]

def download_hcp_dataset(
    dest_dir: Optional[Path] = None,
    force_download: bool = False,
) -> Path:
    """
    Download the HCP OpenNeuro dataset (ds000224) into ``dest_dir``.

    Parameters
    ----------
    dest_dir : pathlib.Path or None
        Destination directory for the BIDS hierarchy. If ``None``,
        ``DEFAULT_DATA_ROOT`` (``<project>/data/raw``) is used.
    force_download : bool
        If ``True`` the dataset is re‑downloaded even if a cached copy
        exists.

    Returns
    -------
    pathlib.Path
        The path to the directory that now contains the downloaded BIDS
        structure.

    Notes
    -----
    The 🤗 datasets library stores the raw files in its own cache.
    This function copies the relevant files into ``dest_dir`` preserving
    the original BIDS layout (subject folders, ``sub-XXX``).
    """
    if dest_dir is None:
        dest_dir = DEFAULT_DATA_ROOT

    dest_dir = Path(dest_dir).expanduser().resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    # ``load_dataset`` with ``streaming=False`` downloads the whole dataset
    # into the HuggingFace cache.  We then copy the files we need.
    download_cfg = DownloadConfig(
        # ``force_download`` forces a fresh download; otherwise reuse cache.
        force_download=force_download,
        # The dataset is fairly large; we keep the default cache dir.
    )

    # Load the dataset – this will download all files into the HF cache.
    # The OpenNeuro loader returns a dictionary with a ``file`` column that
    # points to the local cached file.
    ds = load_dataset(
        DEFAULT_DATASET_NAME,
        DEFAULT_DATASET_ID,
        download_mode="reuse_cache_if_exists",
        download_config=download_cfg,
    )

    # The dataset contains many splits (e.g. ``train``).  For the HCP
    # OpenNeuro collection the default split already contains all subjects.
    # We iterate over the rows and copy each file into the destination
    # preserving its relative path inside the BIDS structure.
    for record in ds["train"]:  # type: ignore[index]
        # ``record`` is a dict with keys like ``file`` and ``filename``.
        src_path = Path(record["file"])
        # The BIDS relative path is stored in ``filename`` (e.g.
        # ``sub-100307/dwi/sub-100307_dwi.nii.gz``).  We replicate that.
        rel_path = Path(record["filename"])
        target_path = dest_dir / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        # Copy only if the file does not already exist or if forced.
        if force_download or not target_path.exists():
            target_path.write_bytes(src_path.read_bytes())

    return dest_dir

def get_subject_paths(
    subject_id: str,
    data_root: Optional[Path] = None,
) -> Tuple[Path, Path]:
    """
    Return the absolute paths of the dMRI and resting‑state fMRI files for a
    given ``subject_id``.

    Parameters
    ----------
    subject_id : str
        The HCP subject identifier (e.g. ``"100307"`` or ``"sub-100307"``).
    data_root : pathlib.Path or None
        Root of the downloaded BIDS hierarchy. If ``None``, the default
        ``data/raw`` directory is used.

    Returns
    -------
    tuple(Path, Path)
        ``(dmri_path, fmri_path)`` – paths to the diffusion and functional
        NIfTI files respectively.

    Raises
    ------
    FileNotFoundError
        If either the dMRI or fMRI file cannot be located.
    """
    if data_root is None:
        data_root = DEFAULT_DATA_ROOT
    data_root = Path(data_root).expanduser().resolve()

    # Normalise the subject identifier – the BIDS layout uses the ``sub-`` prefix.
    sub_prefix = subject_id if subject_id.startswith("sub-") else f"sub-{subject_id}"

    # Typical OpenNeuro HCP file naming (subject‑specific):
    #   dMRI:   <sub>/dwi/<sub>_dwi.nii.gz  (or *_dwi.nii.gz)
    #   fMRI:   <sub>/func/<sub>_task-rest_bold.nii.gz
    # The exact filenames can vary; we perform a simple glob search.
    dmri_candidates = list(
        (data_root / sub_prefix / "dwi").glob(f"{sub_prefix}_*dwi*.nii*")
    )
    fmri_candidates = list(
        (data_root / sub_prefix / "func").glob(f"{sub_prefix}_*bold*.nii*")
    )

    if not dmri_candidates:
        raise FileNotFoundError(
            f"dMRI file not found for subject '{subject_id}' under {data_root}"
        )
    if not fmri_candidates:
        raise FileNotFoundError(
            f"fMRI file not found for subject '{subject_id}' under {data_root}"
        )

    # Pick the first match – in a well‑formed BIDS tree there should be only one.
    dmri_path = dmri_candidates[0].resolve()
    fmri_path = fmri_candidates[0].resolve()
    return dmri_path, fmri_path

def _load_nifti_image(path: Path) -> np.ndarray:
    """
    Load a NIfTI image and return the data as a NumPy array.

    Parameters
    ----------
    path : pathlib.Path
        Path to the NIfTI file.

    Returns
    -------
    np.ndarray
        Image data (4‑D for functional, 3‑D/4‑D for diffusion).

    Raises
    ------
    IOError
        If the file cannot be read.
    """
    try:
        img = nib.load(str(path))
        data = img.get_fdata()
        return np.asarray(data, dtype=np.float32)
    except Exception as exc:
        raise IOError(f"Failed to load NIfTI file '{path}': {exc}") from exc

def load_dmri(subject_id: str, data_root: Optional[Path] = None) -> np.ndarray:
    """
    Load the diffusion MRI data for ``subject_id`` as a NumPy array.

    Parameters
    ----------
    subject_id : str
        HCP subject identifier.
    data_root : pathlib.Path or None
        Root of the BIDS hierarchy (defaults to ``data/raw``).

    Returns
    -------
    np.ndarray
        The raw dMRI volume data (typically 4‑D: X×Y×Z×directions).

    Raises
    ------
    FileNotFoundError
        If the dMRI file cannot be located.
    """
    dmri_path, _ = get_subject_paths(subject_id, data_root)
    return _load_nifti_image(dmri_path)

def load_fmri(subject_id: str, data_root: Optional[Path] = None) -> np.ndarray:
    """
    Load the resting‑state fMRI data for ``subject_id`` as a NumPy array.

    Parameters
    ----------
    subject_id : str
        HCP subject identifier.
    data_root : pathlib.Path or None
        Root of the BIDS hierarchy (defaults to ``data/raw``).

    Returns
    -------
    np.ndarray
        The fMRI time‑series data (4‑D: X×Y×Z×time).

    Raises
    ------
    FileNotFoundError
        If the fMRI file cannot be located.
    """
    _, fmri_path = get_subject_paths(subject_id, data_root)
    return _load_nifti_image(fmri_path)