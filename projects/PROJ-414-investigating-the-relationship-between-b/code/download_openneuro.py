"""Download OpenNeuro fMRI dataset ds000246 and prepare manifest & checksums.

This script:
1. Queries the OpenNeuro API for the file list of ds000246 (version 1.0.0).
2. Downloads ``participants.tsv`` and the functional BOLD NIfTI files for the
   first 20 subjects that have **both** an ``Improv`` and a ``Scripted`` run.
3. Builds a ``manifest.json`` containing ``subject_id``, ``run_label``,
   ``age``, ``years_training``, ``fd`` (placeholder).
4. Computes SHA‑256 checksums for every downloaded NIfTI file and writes them
   to ``data/raw/checksums.json`` using the key format
   ``<subject_id>_<run_label>.nii.gz``.
5. Validates that at least 20 subjects are present and that each has both
   required runs; on validation failure a clear ``ValueError`` is raised.
"""
import csv
import json
import hashlib
import logging
import re
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

import requests
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 checksum of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def download_file(url: str, dest: Path) -> None:
    """Stream‑download ``url`` to ``dest``."""
    log.info(f"Downloading {url} → {dest}")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def parse_participants_tsv(tsv_path: Path) -> Dict[str, Dict[str, Optional[float]]]:
    """
    Parse ``participants.tsv`` and return a mapping:

        subject_id → { "age": float|None, "years_training": float|None }

    Missing columns are recorded as ``None``.
    """
    mapping: Dict[str, Dict[str, Optional[float]]] = {}
    if not tsv_path.is_file():
        log.warning(f"participants.tsv not found at {tsv_path}")
        return mapping

    with tsv_path.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            sid = (
                row.get("participant_id")
                or row.get("subject_id")
                or row.get("sub")
            )
            if not sid:
                continue
            # Ensure BIDS style prefix
            if not sid.lower().startswith("sub-"):
                sid = f"sub-{sid}"
            age = row.get("age")
            years = row.get("years_training")
            try:
                age_val = float(age) if age not in (None, "", "n/a") else None
            except ValueError:
                age_val = None
            try:
                years_val = (
                    float(years) if years not in (None, "", "n/a") else None
                )
            except ValueError:
                years_val = None
            mapping[sid] = {"age": age_val, "years_training": years_val}
    return mapping


# ----------------------------------------------------------------------
# Core download / manifest logic
# ----------------------------------------------------------------------
def _extract_archive(archive_path: Path, dest_dir: Path) -> None:
    """Extract ``tar.gz`` or ``zip`` archives safely into ``dest_dir``."""
    if archive_path.suffixes[-2:] == [".tar", ".gz"]:
        log.info(f"Extracting tar.gz archive {archive_path}")
        with tarfile.open(archive_path, "r:gz") as tar:
            def is_within_directory(directory: Path, target: Path) -> bool:
                abs_directory = directory.resolve()
                abs_target = target.resolve()
                return str(abs_target).startswith(str(abs_directory))

            for member in tar.getmembers():
                member_path = dest_dir / member.name
                if not is_within_directory(dest_dir, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
            tar.extractall(path=dest_dir)
    elif archive_path.suffix == ".zip":
        log.info(f"Extracting zip archive {archive_path}")
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            for member in zip_ref.namelist():
                member_path = dest_dir / member
                if not str(member_path.resolve()).startswith(str(dest_dir.resolve())):
                    raise Exception("Attempted Path Traversal in Zip File")
            zip_ref.extractall(path=dest_dir)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path}")


def _list_openneuro_files(dataset_id: str, version: str) -> List[Dict]:
    """
    Query the OpenNeuro API for the file list of a specific dataset version.
    Returns a list of dicts, each containing at least a ``filename`` key.
    """
    api_url = f"https://openneuro.org/crn/datasets/{dataset_id}/versions/{version}/files"
    log.info(f"Requesting OpenNeuro file list from {api_url}")
    resp = requests.get(api_url, timeout=120)
    resp.raise_for_status()
    return resp.json()


def _download_openneuro_file(dataset_id: str, version: str, filename: str, dest: Path) -> None:
    """
    Download a single file from OpenNeuro.
    ``filename`` is the path relative to the dataset root (e.g. ``sub-01/...``).
    The actual download URL appends ``?download=1`` to trigger raw file delivery.
    """
    url = f"https://openneuro.org/crn/datasets/{dataset_id}/versions/{version}/files/{filename}?download=1"
    download_file(url, dest)


def main() -> None:
    dataset_id = "ds000246"
    version = "1.0.0"  # known public release

    # Destination directory for raw BIDS‑style files
    raw_dir: Path = paths.data("raw", "openneuro", dataset_id)
    raw_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Retrieve full file list from the OpenNeuro API
    # ------------------------------------------------------------------
    try:
        file_list = _list_openneuro_files(dataset_id, version)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to retrieve file list for dataset {dataset_id} version {version}: {exc}"
        ) from exc

    # ------------------------------------------------------------------
    # 2. Identify and download participants.tsv first
    # ------------------------------------------------------------------
    participants_entry = next(
        (f for f in file_list if f.get("filename", "").endswith("participants.tsv")),
        None,
    )
    if participants_entry is None:
        raise RuntimeError("participants.tsv not found in the dataset file list.")
    participants_path = raw_dir / "participants.tsv"
    _download_openneuro_file(
        dataset_id, version, participants_entry["filename"], participants_path
    )
    log.info(f"Downloaded participants.tsv to {participants_path}")

    # Parse participant metadata
    subject_meta = parse_participants_tsv(participants_path)

    # ------------------------------------------------------------------
    # 3. Gather functional BOLD files (Improv and Scripted) per subject
    # ------------------------------------------------------------------
    bold_pattern = re.compile(
        r"sub-(?P<sid>[^_/]+).*task-(?P<task>[^_/]+)_bold\.nii(\.gz)?$", re.IGNORECASE
    )
    # Map subject -> {run_label -> file_entry}
    subject_runs: Dict[str, Dict[str, Dict]] = {}

    for entry in file_list:
        filename = entry.get("filename", "")
        m = bold_pattern.search(filename)
        if not m:
            continue
        sid = f"sub-{m.group('sid')}"
        task_raw = m.group("task")
        run_label = (
            "Improv"
            if task_raw.lower() in ("improv", "improvisation")
            else "Scripted"
            if task_raw.lower() in ("scripted", "control")
            else task_raw
        )
        subject_runs.setdefault(sid, {})[run_label] = entry

    # ------------------------------------------------------------------
    # 4. Select subjects that have **both** Improv and Scripted runs
    # ------------------------------------------------------------------
    eligible_subjects = [
        sid for sid, runs in subject_runs.items() if {"Improv", "Scripted"}.issubset(runs)
    ]
    if len(eligible_subjects) < 20:
        raise ValueError(
            f"Only {len(eligible_subjects)} subjects have both Improv and Scripted runs; "
            "at least 20 are required."
        )
    selected_subjects = sorted(eligible_subjects)[:20]

    # ------------------------------------------------------------------
    # 5. Download the selected BOLD files
    # ------------------------------------------------------------------
    nifti_paths: List[Path] = []
    for sid in selected_subjects:
        runs = subject_runs[sid]
        for run_label in ("Improv", "Scripted"):
            entry = runs[run_label]
            rel_path = entry["filename"]
            dest_path = raw_dir / rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            _download_openneuro_file(dataset_id, version, rel_path, dest_path)
            nifti_paths.append(dest_path)
            log.info(f"Downloaded {run_label} BOLD for {sid} → {dest_path}")

    # ------------------------------------------------------------------
    # 6. Build manifest and compute checksums
    # ------------------------------------------------------------------
    manifest: List[Dict] = []
    checksums: Dict[str, str] = {}

    for nifti_path in nifti_paths:
        filename = nifti_path.name
        # Re‑use the same regex to extract subject and task
        m = bold_pattern.search(str(nifti_path.relative_to(raw_dir)))
        if not m:
            continue
        subject_id = f"sub-{m.group('sid')}"
        run_label_raw = m.group("task")
        run_label = (
            "Improv"
            if run_label_raw.lower() in ("improv", "improvisation")
            else "Scripted"
            if run_label_raw.lower() in ("scripted", "control")
            else run_label_raw
        )
        meta = subject_meta.get(subject_id, {"age": None, "years_training": None})
        age = meta["age"]
        years_training = meta["years_training"]
        fd = None  # placeholder – real FD will be computed later

        checksum = compute_sha256(nifti_path)
        checksum_key = f"{subject_id}_{run_label}.nii.gz"
        checksums[checksum_key] = checksum

        manifest.append(
            {
                "subject_id": subject_id,
                "run_label": run_label,
                "age": age,
                "years_training": years_training,
                "fd": fd,
            }
        )

    # ------------------------------------------------------------------
    # 7. Write manifest.json inside the dataset folder
    # ------------------------------------------------------------------
    manifest_path = raw_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    log.info(f"Wrote manifest with {len(manifest)} entries to {manifest_path}")

    # ------------------------------------------------------------------
    # 8. Write checksums.json at the top‑level raw folder
    # ------------------------------------------------------------------
    checksums_path = paths.data("raw", "checksums.json")
    checksums_path.write_text(json.dumps(checksums, indent=2))
    log.info(f"Wrote checksums for {len(checksums)} files to {checksums_path}")

    # ------------------------------------------------------------------
    # 9. Validation (subjects count already ensured)
    # ------------------------------------------------------------------
    subjects = {entry["subject_id"] for entry in manifest}
    log.info(f"Found {len(subjects)} unique subjects (>=20 required).")
    runs_by_subject: Dict[str, set] = {}
    for entry in manifest:
        runs_by_subject.setdefault(entry["subject_id"], set()).add(entry["run_label"])
    missing = {
        sid: runs
        for sid, runs in runs_by_subject.items()
        if not {"Improv", "Scripted"}.issubset(runs)
    }
    if missing:
        missing_str = ", ".join(
            f"{sid} ({', '.join(runs)})" for sid, runs in missing.items()
        )
        raise ValueError(
            f"The following subjects lack required runs (Improv & Scripted): {missing_str}"
        )
    log.info("All selected subjects contain both Improv and Scripted runs.")
    log.info("OpenNeuro download and verification completed successfully.")


if __name__ == "__main__":
    main()
