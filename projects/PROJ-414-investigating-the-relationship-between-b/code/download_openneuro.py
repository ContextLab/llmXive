"""Download OpenNeuro fMRI dataset ds000246 and prepare manifest & checksums.

This script:
1. Downloads the full ds000246 archive from OpenNeuro.
2. Extracts functional NIfTI files and the top‑level ``participants.tsv``.
3. Builds a ``manifest.json`` containing ``subject_id``, ``run_label``,
   ``age``, ``years_training``, ``fd`` (placeholder).
4. Computes SHA‑256 checksums for every downloaded NIfTI file and writes them to
   ``data/raw/checksums.json``.
5. Validates that at least 20 distinct subjects are present and that each has
   both an ``Improv`` and a ``Scripted`` run. On validation failure a clear
   ``ValueError`` is raised.
"""
import csv
import json
import hashlib
import logging
import re
import shutil
import tarfile
import tempfile
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
            sid = row.get("participant_id") or row.get("subject_id") or row.get("sub")
            if not sid:
                continue
            age = row.get("age")
            years = row.get("years_training")
            try:
                age_val = float(age) if age not in (None, "", "n/a") else None
            except ValueError:
                age_val = None
            try:
                years_val = float(years) if years not in (None, "", "n/a") else None
            except ValueError:
                years_val = None
            mapping[sid] = {"age": age_val, "years_training": years_val}
    return mapping


# ----------------------------------------------------------------------
# Core download / manifest logic
# ----------------------------------------------------------------------
def main() -> None:
    dataset_id = "ds000246"

    # Destination directory for raw NIfTI files (BIDS‑style)
    raw_dir: Path = paths.data("raw", "openneuro", dataset_id)
    raw_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Download the full dataset archive (tar.gz)
    # ------------------------------------------------------------------
    # The public download endpoint for the latest version:
    #   https://openneuro.org/crn/datasets/<dataset_id>/versions/latest/download
    archive_url = f"https://openneuro.org/crn/datasets/{dataset_id}/versions/latest/download"
    log.info(f"Fetching dataset archive from {archive_url}")

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = Path(tmpdir) / f"{dataset_id}.tar.gz"
        download_file(archive_url, archive_path)

        # ------------------------------------------------------------------
        # 2. Extract archive safely
        # ------------------------------------------------------------------
        log.info(f"Extracting archive {archive_path}")
        with tarfile.open(archive_path, "r:gz") as tar:
            def is_within_directory(directory: Path, target: Path) -> bool:
                """Prevent path traversal attacks."""
                abs_directory = directory.resolve()
                abs_target = target.resolve()
                return str(abs_target).startswith(str(abs_directory))

            for member in tar.getmembers():
                member_path = raw_dir / member.name
                if not is_within_directory(raw_dir, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
            tar.extractall(path=raw_dir)

    # ------------------------------------------------------------------
    # 3. Locate participants.tsv (top‑level) and parse it
    # ------------------------------------------------------------------
    participants_path = raw_dir / "participants.tsv"
    subject_meta = parse_participants_tsv(participants_path)

    # ------------------------------------------------------------------
    # 4. Identify functional NIfTI files (BIDS pattern)
    # ------------------------------------------------------------------
    nifti_files: List[Path] = list(raw_dir.rglob("*_bold.nii.gz")) + list(raw_dir.rglob("*_bold.nii"))
    if not nifti_files:
        raise RuntimeError("No functional NIfTI files found after extraction.")

    # ------------------------------------------------------------------
    # 5. Build manifest and compute checksums
    # ------------------------------------------------------------------
    manifest: List[Dict] = []
    checksums: Dict[str, str] = {}

    # Regex to extract subject and task from BIDS filename:
    #   sub-01_ses-01_task-improv_bold.nii.gz
    fname_regex = re.compile(
        r"sub-(?P<sid>[A-Za-z0-9]+).*task-(?P<task>[A-Za-z]+).*bold", re.IGNORECASE
    )

    for nifti_path in nifti_files:
        filename = nifti_path.name
        m = fname_regex.search(filename)
        if not m:
            log.debug(f"Skipping file that does not match BIDS pattern: {filename}")
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

        # Retrieve metadata for this subject (age, years_training)
        meta = subject_meta.get(subject_id, {"age": None, "years_training": None})
        age = meta["age"]
        years_training = meta["years_training"]
        fd = None  # placeholder – real FD will be computed later

        # Compute checksum
        checksum = compute_sha256(nifti_path)
        checksums[filename] = checksum

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
    # 6. Write manifest.json inside the dataset folder
    # ------------------------------------------------------------------
    manifest_path = raw_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    log.info(f"Wrote manifest with {len(manifest)} entries to {manifest_path}")

    # ------------------------------------------------------------------
    # 7. Write checksums.json at the top‑level raw folder
    # ------------------------------------------------------------------
    checksums_path = paths.data("raw", "checksums.json")
    checksums_path.write_text(json.dumps(checksums, indent=2))
    log.info(f"Wrote checksums for {len(checksums)} files to {checksums_path}")

    # ------------------------------------------------------------------
    # 8. Validation
    # ------------------------------------------------------------------
    subjects = {entry["subject_id"] for entry in manifest}
    if len(subjects) < 20:
        raise ValueError(
            f"Dataset contains only {len(subjects)} subjects; at least 20 are required."
        )
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
        missing_str = ", ".join(f"{sid} ({', '.join(runs)})" for sid, runs in missing.items())
        raise ValueError(
            f"The following subjects lack required runs (Improv & Scripted): {missing_str}"
        )
    log.info("All subjects contain both Improv and Scripted runs.")

    log.info("OpenNeuro download and verification completed successfully.")


if __name__ == "__main__":
    main()
