"""Download the OpenNeuro ds004510 dataset (FR-001) with FR-012 gates.

Pipeline:
  1. verify_dataset_id() -- FR-012(1) gate runs BEFORE any download; halts on mismatch.
  2. Fetch the full BIDS zip archive from OpenNeuro, extract minimal required files
     (participants.tsv and each subject's events.tsv) into data/raw/.
  3. Record SHA-256 checksums of every extracted file in data/raw/checksums.json.
  4. verify_conditions() -- FR-012(2)/FR-008 gate after metadata is available.
  5. Validate dataset metadata against contracts/dataset.schema.yaml and write
     data/results/dataset_metadata.json.
  6. Update project state file with artifact hashes and timestamp (FR-013).

Usage: python code/download.py --subjects 2
"""

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml
from llmxive_toolkit import paths, get_logger

from verify_references import (
    CANONICAL_DATASET_ID,
    S3_BASE,
    verify_dataset_id,
    verify_conditions,
)

log = get_logger(__name__)

# Path to the dataset schema used for metadata validation
SCHEMA_PATH = (
    paths.root
    / "specs"
    / "001-neural-correlates-of-temporal-prediction"
    / "contracts"
    / "dataset.schema.yaml"
)
STATE_PATH = (
    paths.root
    / "state"
    / "projects"
    / "PROJ-250-neural-correlates-of-temporal-prediction.yaml"
)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _run_cmd(cmd):
    """Run a command via subprocess, raising RuntimeError on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command {' '.join(cmd)} failed with rc={result.returncode}: {result.stderr}"
        )
    return result.stdout

def _download_file(url, dest):
    """Download a file using curl (fallback wget)."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    curl_cmd = ["curl", "-L", "-fSL", "--retry", "3", "-o", str(dest), url]
    try:
        _run_cmd(curl_cmd)
        return
    except RuntimeError as e:
        log.warning("curl failed (%s); trying wget...", e)

    wget_cmd = ["wget", "-q", "--tries=3", "-O", str(dest), url]
    _run_cmd(wget_cmd)

def _record_checksums(root_dir):
    """Record SHA-256 checksums of all files under root_dir into checksums.json."""
    checksums = {}
    for f in sorted(Path(root_dir).rglob("*")):
        if f.is_file():
            rel = str(f.relative_to(root_dir))
            h = hashlib.sha256()
            with open(f, "rb") as fh:
                for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                    h.update(chunk)
            checksums[rel] = h.hexdigest()
            log.info("SHA-256 %s  %s", checksums[rel][:16], rel)

    out_path = Path(root_dir) / "checksums.json"
    out_path.write_text(json.dumps(checksums, indent=2, sort_keys=True), encoding="utf-8")
    log.info("Checksums written to %s", out_path)
    return checksums

def _update_state(root_dir, checksums):
    """Write artifact hashes and an updated timestamp to the project state YAML."""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    state = {}
    if STATE_PATH.is_file():
        try:
            state = yaml.safe_load(STATE_PATH.read_text(encoding="utf-8")) or {}
        except Exception:
            log.warning("Failed to parse existing state file; starting fresh.")
    state["artifact_hashes"] = {str(Path(root_dir) / p): h for p, h in checksums.items()}
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    STATE_PATH.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
    log.info("Project state updated at %s", STATE_PATH)

def _validate_metadata(raw_dir):
    """Validate dataset metadata against contracts/dataset.schema.yaml (FR-014)."""
    # Import inside function to avoid circular import issues
    from verify_references import collect_events, CONDITION_ALIASES, STIMULUS_ALIASES

    labels, stimulus_types, per_file = collect_events(raw_dir)
    if not stimulus_types:
        raise RuntimeError(
            "No standard/deviant stimulus types found in events metadata; "
            "cannot build dataset metadata rows."
        )

    schema = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    rows = []
    for events_path in sorted(Path(raw_dir).rglob("*events.tsv")):
        subj_match = re.search(r"(sub-[A-Za-z0-9]+)", str(events_path))
        if not subj_match:
            continue
        subject_id = subj_match.group(1)

        with open(events_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            headers = reader.fieldnames or []
            rows_raw = list(reader)

        # Determine condition and stimulus columns (same logic as in verify_references)
        cond_col = "condition_label" if "condition_label" in headers else None
        if cond_col is None:
            for h in headers:
                vals = {str(r.get(h) or "").strip().lower() for r in rows_raw}
                if vals & set(CONDITION_ALIASES):
                    cond_col = h
                    break

        stim_col = "stimulus_type" if "stimulus_type" in headers else None
        if stim_col is None:
            for h in headers:
                vals = {str(r.get(h) or "").strip().lower() for r in rows_raw}
                if vals & set(STIMULUS_ALIASES):
                    stim_col = h
                    break

        if cond_col is None or stim_col is None:
            continue

        for r in rows_raw:
            c = CONDITION_ALIASES.get(str(r.get(cond_col) or "").strip().lower())
            s = STIMULUS_ALIASES.get(str(r.get(stim_col) or "").strip().lower())
            if c is None or s is None:
                continue
            row = {
                "subject_id": subject_id,
                "condition_label": c,
                "stimulus_type": s,
                "is_valid": True,
                "artifact_rejection_rate": 0.0,
            }
            # Validate against the schema; will raise if invalid
            from jsonschema import validate  # Imported here to avoid top‑level dependency loop
            validate(row, schema)
            if row not in rows:
                rows.append(row)

    out = paths.results("dataset_metadata.json")
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    log.info(
        "Validated %d metadata rows against %s; written to %s",
        len(rows),
        SCHEMA_PATH,
        out,
    )
    return rows

# ----------------------------------------------------------------------
# Core download logic (full BIDS zip)
# ----------------------------------------------------------------------
def _download_full_zip(dataset_id, dest_dir):
    """Download the full BIDS zip archive from OpenNeuro and extract it."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    zip_url = f"https://openneuro.org/crn/datasets/{dataset_id}/download?format=zip"
    log.info("Downloading full BIDS zip from %s", zip_url)

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / f"{dataset_id}.zip"
        _download_file(zip_url, zip_path)

        log.info("Extracting zip archive %s", zip_path)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(dest_dir)

    log.info("Extraction complete into %s", dest_dir)
    return dest_dir

def prune_subjects(raw_dir, n_subjects):
    """Keep only the first n_subjects (sorted) under raw_dir; delete others."""
    raw_dir = Path(raw_dir)
    subject_dirs = sorted(
        [p for p in raw_dir.iterdir() if p.is_dir() and p.name.startswith("sub-")]
    )
    if n_subjects == 0:
        log.info("Keeping all %d subjects.", len(subject_dirs))
        return
    keep = set(subject_dirs[:n_subjects])
    log.info("Keeping subjects: %s", [p.name for p in keep])
    for p in subject_dirs:
        if p not in keep:
            log.info("Removing extra subject directory %s", p)
            shutil.rmtree(p)

def main():
    parser = argparse.ArgumentParser(description="Download OpenNeuro ds004510 (FR-001)")
    parser.add_argument(
        "--subjects",
        type=int,
        default=2,
        help="Number of subjects to keep for this pass (0 = all).",
    )
    parser.add_argument(
        "--dataset-id",
        default=CANONICAL_DATASET_ID,
        help="Dataset ID (verified against the canonical source before download)",
    )
    args = parser.parse_args()

    # FR-012(1): pre‑download dataset‑ID gate.
    verify_dataset_id(args.dataset_id)

    raw_dir = paths.data("raw")
    # Download the full BIDS zip and extract
    _download_full_zip(args.dataset_id, raw_dir)

    # Prune to the requested number of subjects
    prune_subjects(raw_dir, args.subjects)

    # Record checksums for all extracted files
    checksums = _record_checksums(raw_dir)

    # Update project state with hashes and timestamp (FR-013)
    _update_state(raw_dir, checksums)

    # FR-012(2) / FR-008: condition gate.
    verify_conditions(raw_dir)

    # Validate metadata and write dataset_metadata.json
    _validate_metadata(raw_dir)

    log.info(
        "Download stage complete for %d subjects under %s",
        args.subjects,
        raw_dir,
    )

if __name__ == "__main__":
    main()
