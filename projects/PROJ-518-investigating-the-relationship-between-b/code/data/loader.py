import json
import os
import requests
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
import pandas as pd

# Project utilities
from llmxive_toolkit import paths, get_logger
from errors import DataMissingCreativityError
from utils.logging import log_exclusion

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


def validate_caq_availability(behavioral_json: Dict[str, Any]) -> bool:
    """
    Validates that the CAQ field exists and is non‑null in the behavioral data.

    Parameters
    ----------
    behavioral_json : dict
        Parsed JSON dictionary containing behavioral metadata for a subject.

    Returns
    -------
    bool
        True if CAQ is present and non‑null, otherwise raises DataMissingCreativityError.
    """
    caq_value = behavioral_json.get("CAQ")
    if caq_value is None:
        log.error("CAQ field missing or null in behavioral data.")
        raise DataMissingCreativityError("DATA_MISSING_CREATIVITY")
    log.info("CAQ field verified in behavioral data.")
    return True


def _compute_sha256(file_path: Path) -> str:
    """Compute SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_checksums() -> Dict[str, str]:
    """Load existing checksums dictionary from data/checksums.json."""
    checksum_path = Path("data/checksums.json")
    if checksum_path.is_file():
        with open(checksum_path, "r") as f:
            return json.load(f)
    return {}


def _save_checksums(checksums: Dict[str, str]) -> None:
    """Write the checksums dictionary to data/checksums.json."""
    checksum_path = Path("data/checksums.json")
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_path, "w") as f:
        json.dump(checksums, f, indent=2)


def _load_manifest() -> List[str]:
    """Load the manifest (list of subject IDs) from data/raw/manifest.json."""
    manifest_path = Path("data/raw/manifest.json")
    if manifest_path.is_file():
        with open(manifest_path, "r") as f:
            data = json.load(f)
            return data.get("subject_ids", [])
    return []


def _save_manifest(subject_ids: List[str]) -> None:
    """Save the manifest (list of subject IDs) to data/raw/manifest.json."""
    manifest_path = Path("data/raw/manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump({"subject_ids": subject_ids}, f, indent=2)


def fetch_hcp_data(subject_id: str) -> Path:
    """
    Downloads raw fMRI (resting‑state) and behavioral JSON for a specific subject
    from the OpenNeuro HCP S1200 dataset (ds003189). Files are saved under
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

    # Base URL for the OpenNeuro HCP S1200 dataset
    base_url = "https://openneuro.org/crn/datasets/ds003189/files"

    # Expected relative paths inside the BIDS hierarchy
    fmri_rel_path = f"sub-{subject_id}/func/sub-{subject_id}_task-rest_bold.dtseries.nii"
    behav_rel_path = f"sub-{subject_id}/phenotype/sub-{subject_id}_behav.json"

    def _download(url: str, dest: Path) -> None:
        """Download a single file with streaming and raise on HTTP errors."""
        log.info(f"Downloading {url} → {dest}")
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        log.info(f"Finished downloading {dest.name}")

    # Append download query parameter required by OpenNeuro to trigger raw file download
    fmri_url = f"{base_url}/{fmri_rel_path}?download=1"
    behav_url = f"{base_url}/{behav_rel_path}?download=1"

    fmri_dest = target_dir / Path(fmri_rel_path).name
    behav_dest = target_dir / Path(behav_rel_path).name

    # Perform downloads (will raise if HTTP error)
    _download(fmri_url, fmri_dest)
    _download(behav_url, behav_dest)

    # Verify CAQ availability immediately after download
    try:
        with open(behav_dest, "r") as f:
            behav_data = json.load(f)
        validate_caq_availability(behav_data)
    except DataMissingCreativityError:
        # Clean up partially downloaded data to avoid leaving inconsistent state
        log.error("CAQ missing – removing downloaded files.")
        fmri_dest.unlink(missing_ok=True)
        behav_dest.unlink(missing_ok=True)
        raise

    # Record SHA‑256 checksums
    checksums = _load_checksums()
    for file_path in (fmri_dest, behav_dest):
        rel_path = str(file_path.relative_to(Path.cwd()))
        checksums[rel_path] = _compute_sha256(file_path)
    _save_checksums(checksums)

    # Update manifest.json
    manifest_ids = _load_manifest()
    if subject_id not in manifest_ids:
        manifest_ids.append(subject_id)
        _save_manifest(manifest_ids)

    return target_dir


def validate_and_filter_subjects(subjects: List[Participant]) -> List[Participant]:
    """
    Validates and filters subjects based on scan availability and behavioral scores.
    """
    filtered = []
    for sub in subjects:
        if sub.fmri_path is None or not sub.fmri_path.exists():
            log.warning(f"Subject {sub.subject_id} missing fMRI scan – excluded.")
            continue
        if sub.creativity_score is None:
            log.warning(f"Subject {sub.subject_id} missing creativity score – excluded.")
            continue
        filtered.append(sub)
    return filtered


def filter_by_motion(
    subjects: List[Participant],
    fd_thresh: float = 0.5,
    vol_thresh: float = 0.2,
) -> List[Participant]:
    """
    Excludes participants exceeding motion criteria.
    """
    passed = []
    for sub in subjects:
        if sub.motion_fd is None:
            log.warning(f"Subject {sub.subject_id} missing motion information – excluded.")
            continue
        if sub.motion_fd > fd_thresh:
            log.info(
                f"Subject {sub.subject_id} exceeds FD threshold ({sub.motion_fd:.3f} > {fd_thresh}) – excluded."
            )
            continue
        passed.append(sub)
    return passed


def filter_subjects(manifest: List[str], behavioral: Dict[str, Dict[str, Any]]) -> List[Participant]:
    """
    Implements subject filtering with standardized exclusion logging.
    """
    included_participants: List[Participant] = []

    inclusion_csv_path = paths.data("interim", "included_subjects.csv")
    inclusion_csv_path.parent.mkdir(parents=True, exist_ok=True)

    csv_rows = []

    for subj_id in manifest:
        fmri_path = paths.data(
            "raw",
            f"hcp_{subj_id}",
            f"sub-{subj_id}_task-rest_bold.dtseries.nii"
        )

        if not fmri_path.is_file():
            log_exclusion(reason="MISSING_SCAN", subject_id=subj_id)
            continue

        behav = behavioral.get(subj_id, {})
        creativity_score = behav.get("CAQ")
        if creativity_score is None:
            log_exclusion(reason="MISSING_SCORE", subject_id=subj_id)
            continue

        age = behav.get("age")
        sex = behav.get("sex")
        education = behav.get("education")

        motion_fd = behav.get("motion_fd")
        motion_vol_prop = behav.get("motion_vol_proportion")

        high_motion = False
        if motion_fd is not None and motion_fd > 0.5:
            high_motion = True
        if motion_vol_prop is not None and motion_vol_prop > 0.2:
            high_motion = True

        if high_motion:
            log_exclusion(reason="HIGH_MOTION", subject_id=subj_id)
            continue

        participant = Participant(
            subject_id=subj_id,
            age=age,
            sex=sex,
            education=education,
            fmri_path=fmri_path,
            creativity_score=creativity_score,
            motion_fd=motion_fd
        )
        included_participants.append(participant)

        csv_rows.append({
            "subject_id": subj_id,
            "age": age,
            "sex": sex,
            "education": education,
            "creativity_score": creativity_score,
            "rest_fmri_path": str(fmri_path)
        })

    df = pd.DataFrame(csv_rows, columns=[
        "subject_id",
        "age",
        "sex",
        "education",
        "creativity_score",
        "rest_fmri_path"
    ])
    df.to_csv(inclusion_csv_path, index=False)

    return included_participants
