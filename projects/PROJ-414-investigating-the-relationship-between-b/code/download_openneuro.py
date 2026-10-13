"""Download OpenNeuro fMRI dataset ds000246 and prepare manifest & checksums.

This script follows the authoritative plan.md by using the HuggingFace `datasets` 
library to fetch the verified OpenNeuro mirror of ds000246.

1. Streams the dataset to identify available files.
2. Downloads `participants.tsv` and BOLD NIfTIs for the first 20 subjects 
   who have both 'Improv' and 'Scripted' runs.
3. Builds a `manifest.json` containing subject metadata.
4. Computes SHA-256 checksums for all downloaded NIfTIs and writes them to 
   `data/raw/checksums.json`.
5. Validates subject count and run availability.
"""
import csv
import json
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from datasets import load_dataset
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
    """
    Legacy helper for URL downloads. 
    The main pipeline now uses the HuggingFace datasets library.
    """
    import requests
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

    log.info(f"Loading OpenNeuro dataset {dataset_id} via HuggingFace datasets...")
    try:
        # Use streaming=True to avoid loading the entire dataset into RAM
        ds = load_dataset("openneuro/ds000246", streaming=True, split="train")
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset {dataset_id} from HuggingFace: {e}")

    # ------------------------------------------------------------------
    # 1. First Pass: Scan for available files and metadata
    # ------------------------------------------------------------------
    bold_pattern = re.compile(
        r"sub-(?P<sid>[^_/]+).*task-(?P<task>[^_/]+)_bold\.nii(\.gz)?$", re.IGNORECASE
    )
    
    subject_runs: Dict[str, Dict[str, str]] = {} # sid -> {run_label -> path}
    participants_data: Optional[bytes] = None

    for item in ds:
        path = item['path']
        if path == "participants.tsv":
            participants_data = item['data']
        
        m = bold_pattern.search(path)
        if m:
            sid = f"sub-{m.group('sid')}"
            task_raw = m.group("task")
            run_label = (
                "Improv" if task_raw.lower() in ("improv", "improvisation")
                else "Scripted" if task_raw.lower() in ("scripted", "control")
                else task_raw
            )
            subject_runs.setdefault(sid, {})[run_label] = path

    if participants_data is None:
        raise RuntimeError("participants.tsv not found in the dataset.")

    # Write participants.tsv to disk
    participants_path = raw_dir / "participants.tsv"
    participants_path.write_bytes(participants_data)
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

    # Create a set of paths we actually need to download
    needed_paths: Set[str] = set()
    for sid in selected_subjects:
        needed_paths.add(subject_runs[sid]["Improv"])
        needed_paths.add(subject_runs[sid]["Scripted"])

    # ------------------------------------------------------------------
    # 3. Second Pass: Download and write selected files
    # ------------------------------------------------------------------
    downloaded_paths: List[Path] = []
    
    # We iterate again because it's a streaming dataset
    ds_stream = load_dataset("openneuro/ds000246", streaming=True, split="train")
    for item in ds_stream:
        path = item['path']
        if path in needed_paths:
            dest_path = raw_dir / path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(item['data'])
            downloaded_paths.append(dest_path)
            log.info(f"Saved {path}")

    # ------------------------------------------------------------------
    # 4. Manifest and Checksums
    # ------------------------------------------------------------------
    manifest: List[Dict] = []
    checksums: Dict[str, str] = {}

    for nifti_path in downloaded_paths:
        rel_path = str(nifti_path.relative_to(raw_dir))
        m = bold_pattern.search(rel_path)
        if not m:
            continue
        
        subject_id = f"sub-{m.group('sid')}"
        task_raw = m.group("task")
        run_label = (
            "Improv" if task_raw.lower() in ("improv", "improvisation")
            else "Scripted" if task_raw.lower() in ("scripted", "control")
            else task_raw
        )
        
        meta = subject_meta.get(subject_id, {"age": None, "years_training": None})
        
        # Checksum
        checksum = compute_sha256(nifti_path)
        checksum_key = f"{subject_id}_{run_label}.nii.gz"
        checksums[checksum_key] = checksum

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
