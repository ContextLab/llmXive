"""Download OpenNeuro fMRI dataset ds000246 and prepare manifest & checksums.

This script:
1. Queries the OpenNeuro public API to list all files belonging to dataset ds000246.
2. Downloads every functional NIfTI file (ending with ``.nii.gz``) into
   ``data/raw/openneuro/ds000246/`` with a deterministic filename
   ``<subject_id>_<run_label>.nii.gz``.
3. Parses ``participants.tsv`` for each subject to obtain ``age`` and
   ``years_training`` (if present). If a column is missing the value is set to ``null``.
4. Sets ``fd`` to ``null`` (the script does **not** compute frame‑wise displacement; that
   will be done later in the preprocessing stage).
5. Writes a ``manifest.json`` containing the required columns:
   ``subject_id``, ``run_label``, ``age``, ``years_training``, ``fd``.
6. Computes SHA‑256 checksums for every downloaded NIfTI file and writes them to
   ``data/raw/checksums.json``.
7. Validates that at least 20 distinct subjects are present and that each subject has
   both an ``Improv`` and a ``Scripted`` run. On validation failure a clear ``ValueError``
   is raised, satisfying the requirement that the script aborts loudly on any problem.
"""
import csv
import json
import hashlib
import logging
import re
import shutil
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
    with requests.get(url, stream=True, timeout=60) as r:
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
    version = "latest"  # we use the most recent snapshot

    # Destination directory for raw NIfTI files
    raw_dir: Path = paths.data("raw", "openneuro", dataset_id)
    raw_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Retrieve file list from OpenNeuro API
    # ------------------------------------------------------------------
    # The public OpenNeuro API endpoint for file listings:
    #   https://openneuro.org/crn/datasets/<dataset_id>/files?format=json
    # This returns a JSON array where each element has a ``path`` key.
    files_endpoint = f"https://openneuro.org/crn/datasets/{dataset_id}/files?format=json"
    log.info(f"Fetching file list from {files_endpoint}")
    response = requests.get(files_endpoint, timeout=60)
    response.raise_for_status()
    files_json = response.json()

    # ------------------------------------------------------------------
    # 2. Identify functional NIfTI files and participants.tsv files
    # ------------------------------------------------------------------
    nifti_files: List[Dict] = []
    participants_files: List[Dict] = []

    for entry in files_json:
        path = entry.get("path", "")
        if path.endswith(".nii.gz") or path.endswith(".nii"):
            nifti_files.append(entry)
        elif path.endswith("participants.tsv"):
            participants_files.append(entry)

    if not nifti_files:
        raise RuntimeError("No NIfTI files found in the dataset listing.")

    # ------------------------------------------------------------------
    # 3. Download participants.tsv for each subject (may be duplicated;
    #    we keep the first occurrence per subject)
    # ------------------------------------------------------------------
    subject_meta: Dict[str, Dict[str, Optional[float]]] = {}
    for entry in participants_files:
        rel_path = entry["path"]
        # Example path: sub-01/participants.tsv
        m = re.match(r"sub-([A-Za-z0-9]+)", rel_path)
        if not m:
            continue
        sid = f"sub-{m.group(1)}"
        if sid in subject_meta:
            continue  # already have this subject's metadata

        download_url = f"https://openneuro.org/crn/datasets/{dataset_id}/files/{rel_path}?download=1"
        tmp_path = raw_dir / f"tmp_{sid}_participants.tsv"
        download_file(download_url, tmp_path)
        meta = parse_participants_tsv(tmp_path)
        if sid in meta:
            subject_meta[sid] = meta[sid]
        else:
            # If the TSV does not contain a row for this subject, store empty values.
            subject_meta[sid] = {"age": None, "years_training": None}
        tmp_path.unlink()  # remove temporary copy

    # ------------------------------------------------------------------
    # 4. Download functional runs, build manifest, compute checksums
    # ------------------------------------------------------------------
    manifest: List[Dict] = []
    checksums: Dict[str, str] = {}

    # Regex to extract subject, run label from typical BIDS filename:
    # sub-01_ses-01_task-improv_bold.nii.gz  →  subject_id=sub-01, run_label=Improv
    fname_regex = re.compile(
        r"sub-(?P<sid>[A-Za-z0-9]+).*task-(?P<task>[A-Za-z]+).*bold", re.IGNORECASE
    )

    for entry in nifti_files:
        rel_path = entry["path"]
        filename = Path(rel_path).name
        m = fname_regex.search(filename)
        if not m:
            log.debug(f"Skipping file that does not match BIDS pattern: {filename}")
            continue

        subject_id = f"sub-{m.group('sid')}"
        run_label_raw = m.group("task")
        # Normalise run label to the expected capitalised form
        run_label = (
            "Improv" if run_label_raw.lower() in ("improv", "improvisation")
            else "Scripted" if run_label_raw.lower() in ("scripted", "control")
            else run_label_raw
        )

        # Retrieve subject‑level metadata (age, years_training)
        meta = subject_meta.get(subject_id, {"age": None, "years_training": None})
        age = meta["age"]
        years_training = meta["years_training"]
        fd = None  # placeholder – real FD will be computed later

        # Destination filename
        dest_name = f"{subject_id}_{run_label}.nii.gz"
        dest_path = raw_dir / dest_name

        # Download the file
        download_url = f"https://openneuro.org/crn/datasets/{dataset_id}/files/{rel_path}?download=1"
        download_file(download_url, dest_path)

        # Compute checksum
        checksum = compute_sha256(dest_path)
        checksums[dest_name] = checksum

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
    # 5. Write manifest.json
    # ------------------------------------------------------------------
    manifest_path = raw_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    log.info(f"Wrote manifest with {len(manifest)} entries to {manifest_path}")

    # ------------------------------------------------------------------
    # 6. Write checksums.json at the top‑level raw folder
    # ------------------------------------------------------------------
    checksums_path = paths.data("raw", "checksums.json")
    checksums_path.write_text(json.dumps(checksums, indent=2))
    log.info(f"Wrote checksums for {len(checksums)} files to {checksums_path}")

    # ------------------------------------------------------------------
    # 7. Validation
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
