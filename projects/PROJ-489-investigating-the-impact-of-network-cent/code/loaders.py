"""
Data loading utilities for the Network Centrality Sleep Synchrony project.

Provides functions to load raw EDF files and sleep stage annotations,
handling the distinction between 'data/raw' and 'data/processed' directories.
"""

import os
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

import mne
import numpy as np
import pandas as pd


def _resolve_path(base_dir: str, filename: str, is_processed: bool = False) -> Path:
    """
    Resolve the full path for a data file based on the directory structure.

    Args:
        base_dir: The root directory of the project.
        filename: The name of the file (e.g., 'ST717BJ-0.edf').
        is_processed: If True, look in 'data/processed', else 'data/raw'.

    Returns:
        The resolved Path object.
    """
    data_type = "processed" if is_processed else "raw"
    data_root = Path(base_dir) / "data" / data_type
    return data_root / filename


def load_raw_edf(
    base_dir: str,
    filename: str,
    is_processed: bool = False,
    preload: bool = True
) -> mne.io.Raw:
    """
    Load an EDF file from the specified data directory.

    This function handles loading from either 'data/raw' or 'data/processed'
    based on the `is_processed` flag. It uses MNE-Python to read the EDF file.

    Args:
        base_dir: The root directory of the project (e.g., '/path/to/PROJ-489').
        filename: The name of the EDF file to load.
        is_processed: If True, loads from 'data/processed'; otherwise 'data/raw'.
        preload: If True, preloads the data into memory (required for many MNE operations).

    Returns:
        An mne.io.Raw object containing the EEG data and metadata.

    Raises:
        FileNotFoundError: If the specified file does not exist at the resolved path.
        RuntimeError: If MNE fails to read the file.
    """
    file_path = _resolve_path(base_dir, filename, is_processed)

    if not file_path.exists():
        raise FileNotFoundError(f"EDF file not found at: {file_path}")

    try:
        raw = mne.io.read_raw_edf(
            file_path,
            preload=preload,
            verbose=False
        )
        return raw
    except Exception as e:
        raise RuntimeError(f"Failed to load EDF file {file_path}: {e}") from e


def load_annotations(
    base_dir: str,
    subject_id: str,
    night_id: int = 1,
    is_processed: bool = False
) -> Optional[mne.Annotations]:
    """
    Load sleep stage annotations for a specific subject and night.

    Sleep-EDF dataset annotations are typically stored in .annot files
    or embedded within the EDF file. This function attempts to locate
    and load the annotations.

    Args:
        base_dir: The root directory of the project.
        subject_id: The subject identifier (e.g., 'ST717BJ').
        night_id: The night number (1 or 2).
        is_processed: If True, looks in 'data/processed', else 'data/raw'.

    Returns:
        An mne.Annotations object if found, otherwise None.
    """
    # Construct the expected annotation filename
    # Sleep-EDF annotations usually follow the pattern: <subject>-<night>.annot
    # or are embedded in the EDF file. We first try to find a dedicated .annot file.
    annot_filename = f"{subject_id}-{night_id}.annot"
    annot_path = _resolve_path(base_dir, annot_filename, is_processed)

    if annot_path.exists():
        try:
            # MNE can read .annot files directly
            annotations = mne.read_annotations(annot_path)
            return annotations
        except Exception:
            pass  # Fall back to embedded annotations if file read fails

    # If no dedicated .annot file, try to load the corresponding EDF and extract annotations
    # Assuming the EDF filename matches the pattern: <subject>-0.edf or <subject>-1.edf
    edf_filename = f"{subject_id}-{night_id - 1}.edf" # EDF files are 0-indexed in Sleep-EDF naming usually (0=night1, 1=night2)
    # However, the task description implies we might just need to load from the EDF if available.
    # Let's try the standard Sleep-EDF mapping: Night 1 -> -0.edf, Night 2 -> -1.edf
    edf_path = _resolve_path(base_dir, edf_filename, is_processed)

    if edf_path.exists():
        try:
            raw = mne.io.read_raw_edf(edf_path, preload=False, verbose=False)
            if raw.annotations:
                return raw.annotations
        except Exception:
            pass

    # Fallback: Try the exact filename provided in other contexts if subject_id includes night info
    # e.g., if filename is passed differently, but here we rely on standard conventions.
    return None


def load_subject_data(
    base_dir: str,
    subject_id: str,
    night_id: int = 1,
    preload: bool = True
) -> Tuple[mne.io.Raw, Optional[mne.Annotations]]:
    """
    Convenience function to load both raw data and annotations for a subject.

    Args:
        base_dir: The root directory of the project.
        subject_id: The subject identifier.
        night_id: The night number (1 or 2).
        preload: Whether to preload the raw data.

    Returns:
        A tuple of (raw_data, annotations).
    """
    raw = load_raw_edf(base_dir, f"{subject_id}-{night_id - 1}.edf", preload=preload)
    annotations = load_annotations(base_dir, subject_id, night_id)
    return raw, annotations