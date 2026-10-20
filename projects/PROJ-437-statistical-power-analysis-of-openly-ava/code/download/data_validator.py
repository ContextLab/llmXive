"""
Data Validator
---------------
Performs a lightweight sanity‑check on the BIDS directory produced by
``openneuro_fetcher``.  The validator walks the directory tree and
confirms that at least one NIfTI file (``*.nii`` or ``*.nii.gz``)
exists for each subject.  If the check fails, a ``FileNotFoundError`` is
raised – this implements the “fail loudly” policy required by the
specification.
"""

import logging
import sys
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def _find_subject_dirs(bids_root: Path) -> List[Path]:
    """Return a list of subject directories (``sub-XX``) under ``bids_root``."""
    return [p for p in bids_root.rglob("*") if p.is_dir() and p.name.startswith("sub-")]


def validate_bids_structure(bids_root: Path) -> None:
    """
    Validate that each subject directory contains at least one functional
    NIfTI file.  Raises ``FileNotFoundError`` if the check fails.
    """
    if not bids_root.is_dir():
        raise FileNotFoundError(f"BIDS root directory does not exist: {bids_root}")

    subject_dirs = _find_subject_dirs(bids_root)
    if not subject_dirs:
        raise FileNotFoundError(f"No subject directories found under {bids_root}")

    for sub_dir in subject_dirs:
        nifti_files = list(sub_dir.rglob("*.nii")) + list(sub_dir.rglob("*.nii.gz"))
        if not nifti_files:
            raise FileNotFoundError(f"No NIfTI files found for subject {sub_dir.name}")

    logger.info(f"Validated BIDS structure under {bids_root}: {len(subject_dirs)} subjects found.")
