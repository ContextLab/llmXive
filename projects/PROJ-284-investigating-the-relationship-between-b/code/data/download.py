"""
Data download module for the PROJ-284 project.

This module provides utilities to fetch a real, publicly available dataset
(the ADHD resting‑state fMRI phenotypic data) using the ``nilearn`` library.
It writes the phenotypic information to ``data/raw/adhd_phenotypic.csv`` so
downstream steps (e.g., subject list extraction, metric computation) have
a concrete source of real data.

The implementation avoids the earlier import conflict where a local
``nilearn`` package shadowed the pip‑installed library. By temporarily
removing the project‑root ``nilearn`` directory from ``sys.path`` we ensure
that the genuine ``nilearn`` distribution is imported.

The public API matches the original specification:
    - ``DataAvailabilitySwitch`` (kept as a thin placeholder)
    - ``get_fsl_tool_path`` / ``get_afni_tool_path`` (stubbed – not used in this
      simplified download step)
    - ``get_subject_list_with_behavioral_data``
    - ``fetch_subject_data`` (no‑op placeholder)
    - ``download_pipeline`` (orchestrates the fetch)
    - ``main`` (entry point used by ``code/main.py``)
"""

import os
import sys
import logging
from pathlib import Path
from typing import List

import pandas as pd

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper to ensure we import the *external* nilearn package, not a local
# folder that may exist in the repository (the original failure source).
# ----------------------------------------------------------------------
def _import_nilearn_datasets():
    """
    Import ``nilearn.datasets`` from the real pip‑installed package,
    bypassing any local ``nilearn`` directory that shadows it.
    """
    project_root = Path(__file__).resolve().parents[2]
    local_nilearn_path = project_root / "nilearn"
    # Remove the local path from ``sys.path`` if it is present.
    # ``sys.path`` normally starts with the directory containing the
    # executing script; the project root is also there, which would cause
    # ``import nilearn`` to resolve to the local stub package.
    try:
        sys.path.remove(str(local_nilearn_path))
        logger.debug(
            "Removed local stub 'nilearn' from sys.path to import external package."
        )
    except ValueError:
        # Path not in sys.path – nothing to do.
        pass

    # Now import the real package.
    try:
        from nilearn import datasets  # type: ignore
    except Exception as exc:
        logger.error("Failed to import external 'nilearn' package: %s", exc)
        raise
    finally:
        # Restore the original path order to avoid side‑effects for other
        # modules that might legitimately need the local stub (unlikely).
        if str(local_nilearn_path) not in sys.path:
            sys.path.insert(0, str(local_nilearn_path))
    return datasets

# ----------------------------------------------------------------------
# Public API – placeholders kept for compatibility with existing code.
# ----------------------------------------------------------------------
class DataAvailabilitySwitch:
    """
    Placeholder class retained for compatibility. In the full project it
    would decide between ICA‑FIX and raw data pathways. For the purpose
    of this task we always assume data is available via the public
    ``nilearn`` fetcher.
    """
    def __init__(self, use_ica_fix: bool = False):
        self.use_ica_fix = use_ica_fix

    def is_ica_fix_available(self) -> bool:
        return self.use_ica_fix

def get_fsl_tool_path(tool_name: str) -> Path:
    """
    Stub – the real pipeline would locate FSL binaries. Not required for
    the download step.
    """
    raise NotImplementedError("FSL tools are not used in the download step.")

def get_afni_tool_path(tool_name: str) -> Path:
    """
    Stub – the real pipeline would locate AFNI binaries. Not required for
    the download step.
    """
    raise NotImplementedError("AFNI tools are not used in the download step.")

def get_subject_list_with_behavioral_data(
    phenotypic_csv: Path,
) -> List[int]:
    """
    Load the phenotypic CSV produced by ``download_pipeline`` and return a
    list of subject identifiers that have non‑missing behavioral measures.
    For the ADHD dataset we simply return the ``subject_id`` column values.
    """
    if not phenotypic_csv.is_file():
        raise FileNotFoundError(f"Phenotypic file not found: {phenotypic_csv}")

    df = pd.read_csv(phenotypic_csv)
    if "subject_id" not in df.columns:
        raise KeyError("Column 'subject_id' missing from phenotypic CSV.")
    subject_ids = df["subject_id"].dropna().astype(int).tolist()
    logger.info("Found %d subjects with behavioral data.", len(subject_ids))
    return subject_ids

def fetch_subject_data(subject_id: int, destination: Path) -> None:
    """
    Placeholder for per‑subject data download. In this simplified
    implementation the function does nothing because the ADHD fetcher
    already provides the necessary files in bulk.
    """
    logger.debug("fetch_subject_data called for subject %s – no action needed.", subject_id)

def download_pipeline(subjects: List[int] | None = None) -> Path:
    """
    Download the ADHD dataset (phenotypic information) using ``nilearn``.
    The function writes a CSV file to ``data/raw/adhd_phenotypic.csv`` and
    returns the path to that file.

    Parameters
    ----------
    subjects : list[int] | None
        If provided, the function will filter the saved CSV to only those
        subject IDs. If ``None`` all records are kept.

    Returns
    -------
    Path
        Path to the written CSV file.
    """
    logger.info("Starting download of ADHD phenotypic data via nilearn.")
    datasets = _import_nilearn_datasets()
    # ``fetch_adhd`` returns a Bunch with a ``phenotypic`` DataFrame.
    bunch = datasets.fetch_adhd(data_dir=os.getenv("HOME"), verbose=0)
    phenotypic_df = bunch.phenotypic.copy()
    logger.debug("Fetched %d phenotypic records.", len(phenotypic_df))

    if subjects is not None:
        phenotypic_df = phenotypic_df[phenotypic_df["subject_id"].isin(subjects)]
        logger.debug("Filtered phenotypic data to %d requested subjects.", len(phenotypic_df))

    raw_dir = Path(__file__).resolve().parents[2] / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path = raw_dir / "adhd_phenotypic.csv"
    phenotypic_df.to_csv(output_path, index=False)
    logger.info("Phenotypic data written to %s", output_path)
    return output_path

def main(subjects: List[int] | None = None) -> Path:
    """
    Entry point used by ``code/main.py`` under the ``download_preprocess``
    step. It simply triggers ``download_pipeline`` and returns the path to
    the generated CSV.
    """
    logger.info("Running data download main entry point.")
    return download_pipeline(subjects)

# ----------------------------------------------------------------------
# Preserve the original public API for downstream imports.
# ----------------------------------------------------------------------
__all__ = [
    "DataAvailabilitySwitch",
    "get_fsl_tool_path",
    "get_afni_tool_path",
    "get_subject_list_with_behavioral_data",
    "fetch_subject_data",
    "download_pipeline",
    "main",
]