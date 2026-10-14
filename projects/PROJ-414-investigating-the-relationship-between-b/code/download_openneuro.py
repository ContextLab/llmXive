"""Download OpenNeuro fMRI dataset ds000246 and prepare manifest & checksums.

This script uses the OpenNeuro API to fetch the verified dataset ds000246.
It identifies subjects with both 'Improv' and 'Scripted' runs, downloads
the BOLD NIfTIs for the first 20 such subjects, and generates a manifest
and checksum file for verification.
"""
import csv
import json
import hashlib
import re
import requests
from pathlib import Path
from typing import Dict, List, Optional, Set

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Return the SHA-256 checksum of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def download_file(url: str, dest: Path) -> None:
    """Download a file from a URL to a destination path."""
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
            if not sid.lower().startswith("sub-"):
                sid = f"sub-{sid}"
            
            age = row.get("age")
            years = row.get("years_training")
            try:
                age_val = float(age) if age not in (None, "", "n/a") else None
            except (ValueError, TypeError):
                age_val = None
            try:
                years_val = float(years) if years not in (None, "", "n/a") else None
            except (ValueError, TypeError):
                years_val = None
            mapping[sid] = {"age": age_val, "years_training": years_val}
    return mapping

def main() -> None:
    dataset_id = "ds000246"
    raw_dir: Path = paths.data("raw", "openneuro", dataset_id)
    raw_dir.mkdir(parents=True, exist_ok=True)

    log.info(f"Fetching file list for OpenNeuro dataset {dataset_id}...")
    api_url = f"https://openneuro.org/api/datasets/{dataset_id}/files"
    try:
        response = requests.get(api_url, timeout=60)
        response.raise_for_status()
        files_list = response.json()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch file list from OpenNeuro API: {e}")

    # ------------------------------------------------------------------
    # 1. Scan for available files and metadata
    # ------------------------------------------------------------------
    bold_pattern = re.compile(
        r"sub-(?P<sid>[^_/]+).*task-(?P<task>[^_/]+)_bold\.nii(\.gz)?$", re.IGNORECASE
    )
    
    subject_runs: Dict[str, Dict[str, str]] = {} # sid -> {run_label -> url}
    participants_url: Optional[str] = None

    for item in files_list:
        path = item['path']
        url = item['url']
        
        if path == "participants.tsv":
            participants_url = url
        
        m = bold_pattern.search(path)
        if m:
            sid = f"sub-{m.group('sid')}"
            task_raw = m.group("task")
            run_label = (
                "Improv" if task_raw.lower() in ("improv", "improvisation")
                else "Scripted" if task_raw.lower() in ("scripted", "control")
                else task_raw
            )
            subject_runs.setdefault(sid, {})[run_label] = url

    if participants_url is None:
        raise RuntimeError("participants.tsv not found in the dataset file list.")

    # Download and parse participants.tsv
    participants_path = raw_dir / "participants.tsv"
    download_file(participants_url, participants_path)
    subject_meta = parse_participants_tsv(participants_path)

    # ------------------------------------------------------------------
    # 2. Select 20 subjects with both Improv and Scripted runs
    # ------------------------------------------------------------------
    eligible_subjects = [
        sid for sid, runs in subject_runs.items() 
        if {"Improv", "Scripted"}.issubset(runs.keys())
    ]
    
    if len(eligible_subjects) < 20:
        raise ValueError(
            f"Only {len(eligible_subjects)} subjects found with both runs; 20 required."
        )
    
    selected_subjects = sorted(eligible_subjects)[:20]
    log.info(f"Selected subjects: {selected_subjects}")

    # ------------------------------------------------------------------
    # 3. Download selected BOLD files
    # ------------------------------------------------------------------
    downloaded_files: List[Path] = []
    for sid in selected_subjects:
        for run_label in ["Improv", "Scripted"]:
            url = subject_runs[sid][run_label]
            # Construct a local path that mimics the dataset structure
            # e.g., data/raw/openneuro/ds000246/sub-01/func/sub-01_task-Improv_bold.nii.gz
            # We can extract the path from the URL or use a simplified one
            # For the test, we need the files to exist and match the manifest.
            # We'll use a simplified structure: sub-XX_run_label.nii.gz
            filename = f"{sid}_{run_label}.nii.gz"
            dest_path = raw_dir / filename
            download_file(url, dest_path)
            downloaded_files.append(dest_path)

    # ------------------------------------------------------------------
    # 4. Manifest and Checksums
    # ------------------------------------------------------------------
    manifest: List[Dict] = []
    checksums: Dict[str, str] = {}

    for nifti_path in downloaded_files:
        # filename is like sub-01_Improv.nii.gz
        filename = nifti_path.name
        m = re.match(r"(sub-[^/]+)_(Improv|Scripted)\.nii\.gz", filename)
        if not m:
            continue
        
        subject_id = m.group(1)
        run_label = m.group(2)
        
        meta = subject_meta.get(subject_id, {"age": None, "years_training": None})
        
        # Checksum
        checksum = compute_sha256(nifti_path)
        checksums[filename] = checksum

        manifest.append({
            "subject_id": subject_id,
            "run_label": run_label,
            "age": meta["age"],
            "years_training": meta["years_training"],
            "fd": None, # Placeholder for later preprocessing
        })

    # Write manifest.json in dataset folder
    manifest_path = raw_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    
    # Write checksums.json in data/raw/
    checksums_path = paths.data("raw", "checksums.json")
    checksums_path.write_text(json.dumps(checksums, indent=2))
    
    log.info(f"Successfully downloaded {len(selected_subjects)} subjects.")
    log.info(f"Manifest: {manifest_path}, Checksums: {checksums_path}")

if __name__ == "__main__":
    main()
