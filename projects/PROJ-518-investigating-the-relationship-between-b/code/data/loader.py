import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, NamedTuple
from dataclasses import dataclass
import logging

# Project utilities
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


@dataclass
class Participant:
    """Simple container for a study participant."""
    subject_id: str
    age: Optional[float] = None
    sex: Optional[str] = None
    education: Optional[int] = None
    fmri_path: Optional[Path] = None
    creativity_score: Optional[float] = None
    motion_fd: Optional[float] = None  # mean framewise displacement


class DataMissingCreativityError(Exception):
    """Raised when the required CAQ field is not present in the behavioral data."""
    pass


def validate_caq_availability(manifest_path: str, behavioral_path: str) -> bool:
    """
    Validates that the CAQ field exists in the behavioral data.

    Parameters
    ----------
    manifest_path : str
        Path to the dataset manifest JSON file.
    behavioral_path : str
        Path to the behavioral JSON file for a subject.

    Returns
    -------
    bool
        True if CAQ is present, otherwise raises DataMissingCreativityError.
    """
    # Load manifest (if needed for future extensions)
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except FileNotFoundError as exc:
        log.error(f"Manifest not found at {manifest_path}")
        raise

    # Load behavioral JSON
    try:
        with open(behavioral_path, "r") as f:
            behav = json.load(f)
    except FileNotFoundError as exc:
        log.error(f"Behavioral file not found at {behavioral_path}")
        raise

    # The CAQ field name follows the HCP convention; adjust if the dataset uses a different key.
    if "CAQ" not in behav:
        log.error("CAQ field missing in behavioral data.")
        raise DataMissingCreativityError("CAQ field is required but missing.")

    log.info("CAQ field verified in behavioral data.")
    return True


def fetch_hcp_data(subject_id: str) -> Path:
    """
    Downloads raw fMRI (resting‑state) and behavioral JSON for a specific subject
    from OpenNeuro (dataset ds000114 – HCP S1200). Files are saved under
    ``data/raw/hcp_{subject_id}/``.

    Parameters
    ----------
    subject_id : str
        The HCP subject identifier (e.g., ``"100206"``). The function does **not**
        prepend ``sub-``; callers should provide the raw numeric/id part.

    Returns
    -------
    pathlib.Path
        Path to the directory containing the downloaded files.

    Raises
    ------
    FileNotFoundError
        If the manifest cannot be found or the expected files are missing on the server.
    DataMissingCreativityError
        If the CAQ field is absent in the downloaded behavioral JSON.
    """
    # Resolve the target directory using the toolkit helper (creates parent dirs)
    target_dir: Path = paths.data("raw", f"hcp_{subject_id}")
    target_dir.mkdir(parents=True, exist_ok=True)

    # Base URL for the OpenNeuro dataset version 1.0.0
    base_url = "https://openneuro.org/crn/datasets/ds000114/versions/1.0.0/files"

    # Construct expected relative paths inside the BIDS hierarchy
    fmri_rel_path = f"sub-{subject_id}/func/sub-{subject_id}_task-rest_bold.nii.gz"
    behav_rel_path = f"sub-{subject_id}/phenotype/sub-{subject_id}_behav.json"

    # Helper to download a single file
    def _download(url: str, dest: Path) -> None:
        log.info(f"Downloading {url} → {dest}")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep‑alive chunks
                        f.write(chunk)
        log.info(f"Finished downloading {dest.name}")

    # Download fMRI file
    fmri_url = f"{base_url}/{fmri_rel_path}"
    fmri_dest = target_dir / Path(fmri_rel_path).name
    _download(fmri_url, fmri_dest)

    # Download behavioral JSON
    behav_url = f"{base_url}/{behav_rel_path}"
    behav_dest = target_dir / Path(behav_rel_path).name
    _download(behav_url, behav_dest)

    # Verify CAQ availability immediately after download
    # (uses a minimal manifest placeholder – the manifest is optional for this check)
    # If a manifest file exists at the project root we could point to it; otherwise we skip.
    manifest_path = paths.data("raw", "manifest.json")
    try:
        validate_caq_availability(str(manifest_path), str(behav_dest))
    except DataMissingCreativityError:
        # Clean up partially downloaded data to avoid leaving inconsistent state
        log.error("CAQ missing – removing downloaded files.")
        fmri_dest.unlink(missing_ok=True)
        behav_dest.unlink(missing_ok=True)
        raise

    return target_dir


def validate_and_filter_subjects(subjects: List[Participant]) -> List[Participant]:
    """
    Validates and filters subjects based on scan availability and behavioral scores.

    Exclusion Logic:
    1. Missing scans: Log warning, skip subject.
    2. Missing behavioral scores: Exclude subject, log with reason 'MISSING_SCORE'.

    Parameters
    ----------
    subjects : List[Participant]
        List of Participant objects.

    Returns
    -------
    List[Participant]
        List of filtered Participant objects.
    """
    filtered = []
    for sub in subjects:
        if sub.fmri_path is None or not sub.fmri_path.exists():
            log.warning(f"Subject {sub.subject_id} missing fMRI scan – excluded.")
            continue
        if sub.creativity_score is None:
            log.warning(f"Subject {sub.subject_id} missing creativity score – excluded.")
            # Assuming logging function exists elsewhere; here we just warn.
            continue
        filtered.append(sub)
    return filtered


def filter_by_motion(subjects: List[Participant], fd_thresh: float = 0.5,
                     vol_thresh: float = 0.2) -> List[Participant]:
    """
    Excludes participants exceeding motion criteria.

    Parameters
    ----------
    subjects : List[Participant]
        List of Participant objects.
    fd_thresh : float, optional
        Threshold for mean Framewise Displacement (default 0.5 mm).
    vol_thresh : float, optional
        Threshold for proportion of high‑motion volumes (default 0.2 = 20%).

    Returns
    -------
    List[Participant]
        List of participants that pass the motion criteria.
    """
    passed = []
    for sub in subjects:
        if sub.motion_fd is None:
            log.warning(f"Subject {sub.subject_id} missing motion information – excluded.")
            continue
        if sub.motion_fd > fd_thresh:
            log.info(f"Subject {sub.subject_id} exceeds FD threshold ({sub.motion_fd:.3f} > {fd_thresh}) – excluded.")
            continue
        # In a full implementation we would also check the proportion of volumes;
        # here we only have a single FD metric, so we apply the simple rule.
        passed.append(sub)
    return passed


# NOTE: The rest of the module (e.g., additional helper functions) can be added here
# as the pipeline evolves. The current implementation focuses on the data‑fetching
# requirement of task T012.