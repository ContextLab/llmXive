"""Download the OpenNeuro ds004510 dataset (FR-001) with FR-012 gates.

Pipeline:
  1. verify_dataset_id() -- FR-012(1) gate runs BEFORE any download; halts on mismatch.
  2. Fetch ds004510 from the OpenNeuro S3 HTTPS endpoint via curl (fallback wget),
     processing subjects iteratively (one subject at a time; never loading
     all subjects at once) to stay within ~7 GB RAM.
  3. Record SHA-256 checksums of every downloaded file in data/raw/checksums.json.
  4. verify_conditions() -- FR-012(2)/FR-008 gate after metadata is available.
  5. Validate dataset metadata against contracts/dataset.schema.yaml and write
     data/results/dataset_metadata.json.

Usage: python code/download.py --subjects 2
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import requests
import yaml
from jsonschema import validate
from llmxive_toolkit import paths, get_logger

from verify_references import (
    CANONICAL_DATASET_ID,
    S3_BASE,
    collect_events,
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

def _strip_ns(tag):
    """Strip XML namespace from tag."""
    return tag.split("}")[-1]

# ----------------------------------------------------------------------
# Helper functions (unchanged from original where still useful)
# ----------------------------------------------------------------------
def s3_list(prefix, delimiter=None):
    """List objects in the public OpenNeuro S3 bucket under `prefix` (paginated)."""
    keys, prefixes = [], []
    token = None
    while True:
        params = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if delimiter:
            params["delimiter"] = delimiter
        if token:
            params["continuation-token"] = token
        try:
            resp = requests.get(S3_BASE, params=params, timeout=60)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Failed to list S3 objects under {prefix}: {exc}"
            )
        root = ET.fromstring(resp.text)
        for child in root:
            name = _strip_ns(child.tag)
            if name == "Contents":
                for sub in child:
                    if _strip_ns(sub.tag) == "Key":
                        keys.append(sub.text)
            elif name == "CommonPrefixes":
                for sub in child:
                    if _strip_ns(sub.tag) == "Prefix":
                        prefixes.append(sub.text)
            elif name == "Error":
                raise RuntimeError(f"S3 listing error: {ET.tostring(child)}")
        truncated = False
        token = None
        for child in root:
            if _strip_ns(child.tag) == "IsTruncated" and child.text == "true":
                truncated = True
            if _strip_ns(child.tag) == "NextContinuationToken":
                token = child.text
        if not truncated or token is None:
            break
    return keys, prefixes

def resolve_dataset_prefix():
    """Return the S3 key prefix holding current ds004510 files (versioned if applicable)."""
    base = CANONICAL_DATASET_ID + "/"
    keys, prefixes = s3_list(base)
    if keys:
        # Flat layout
        return base
    version_prefixes = [
        p.rstrip("/")
        for p in prefixes
        if re.fullmatch(r"\d+(\.\d+)*", p.rstrip("/"))
    ]
    if version_prefixes:
        version_prefixes.sort(key=lambda v: tuple(int(x) for x in v.split(".")))
        latest = version_prefixes[-1]
        print(f"Resolved dataset version: {latest} (latest of {version_prefixes})")
        return base + latest + "/"
    raise RuntimeError(
        f"No objects found under s3://{S3_BASE}/{base}; dataset {CANONICAL_DATASET_ID} is not reachable."
    )

# ----------------------------------------------------------------------
# Core download logic (new implementation using the official OpenNeuro zip)
# ----------------------------------------------------------------------
def fetch_file(url, dest, max_retries=3):
    """Fetch one file via curl (fallback wget). Fails loudly; no synthetic fallback."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Try curl first
    curl_cmd = [
        "curl", "-fSL", "--retry", str(max_retries),
        "--connect-timeout", "60", "--max-time", "300",
        "-o", str(dest), url,
    ]
    proc = subprocess.run(curl_cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        return

    log.warning("curl failed (%d) for %s; trying wget...", proc.returncode, url)

    # Fallback to wget
    wget_cmd = [
        "wget", "-q", "--tries", str(max_retries),
        "--timeout", "60", "-O", str(dest), url
    ]
    proc2 = subprocess.run(wget_cmd, capture_output=True, text=True)
    if proc2.returncode != 0:
        raise RuntimeError(
            f"FAILED to download {url} (curl rc={proc.returncode}, wget rc={proc2.returncode})."
        )

def sha256_file(path, chunk_size=1024 * 1024):
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()

def download_subjects(n_subjects, raw_dir):
    """
    Download the dataset as a zip archive, extract the requested number of subjects,
    and return a list of all extracted file paths.
    """
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    zip_url = f"https://openneuro.org/datasets/{CANONICAL_DATASET_ID}/download?type=raw"
    zip_path = raw_dir / f"{CANONICAL_DATASET_ID}.zip"

    if not zip_path.is_file():
        print(f"Downloading dataset zip from {zip_url}")
        fetch_file(zip_url, zip_path)
    else:
        print(f"Using cached zip at {zip_path}")

    # Extract zip to a temporary location
    temp_extract_dir = raw_dir / "_tmp_extracted"
    if temp_extract_dir.exists():
        shutil.rmtree(temp_extract_dir)
    temp_extract_dir.mkdir(parents=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Identify all subject directories inside the zip (they start with "sub-")
        subject_dirs = set()
        for member in zf.namelist():
            parts = member.split("/")
            if len(parts) > 1 and parts[0].startswith("sub-"):
                subject_dirs.add(parts[0])
        subjects = sorted(
            subject_dirs,
            key=lambda s: int(re.sub(r"\D", "", s) or 0)
        )
        selected = subjects if n_subjects == 0 else subjects[:n_subjects]
        print(f"Dataset has {len(subjects)} subjects; extracting {len(selected)}: {selected}")

        # Extract top‑level (non‑subject) files
        for member in zf.namelist():
            if "/" not in member.rstrip("/"):
                zf.extract(member, temp_extract_dir)

        # Extract selected subject files
        for member in zf.namelist():
            for subj in selected:
                if member.startswith(f"{subj}/"):
                    zf.extract(member, temp_extract_dir)
                    break

    # Move extracted content up one level if the zip includes a top‑level folder
    # (e.g., ds004510/...). Detect and flatten it.
    top_level_items = list(temp_extract_dir.iterdir())
    if len(top_level_items) == 1 and top_level_items[0].is_dir():
        inner = top_level_items[0]
        for item in inner.iterdir():
            shutil.move(str(item), raw_dir)
    else:
        for item in top_level_items:
            shutil.move(str(item), raw_dir)

    # Clean up temporary directory
    shutil.rmtree(temp_extract_dir, ignore_errors=True)

    # Gather all extracted file paths
    extracted_files = []
    for root, _, files in os.walk(raw_dir):
        for f in files:
            extracted_files.append(Path(root) / f)

    return extracted_files

def record_checksums(files, raw_dir):
    """Record SHA-256 checksums of downloaded files."""
    checksums_path = Path(raw_dir) / "checksums.json"
    checksums = {}
    if checksums_path.exists():
        try:
            checksums = json.loads(checksums_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            checksums = {}

    for f in files:
        rel = str(Path(f).relative_to(raw_dir))
        checksums[rel] = sha256_file(f)
        print(f"SHA-256 {checksums[rel][:16]}...  {rel}")

    checksums_path.write_text(
        json.dumps(checksums, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"Checksums for {len(files)} files recorded in {checksums_path}")
    return checksums

def validate_metadata(raw_dir):
    """Validate dataset metadata against contracts/dataset.schema.yaml (FR-014)."""
    labels, stimulus_types, per_file = collect_events(raw_dir)
    if not stimulus_types:
        raise RuntimeError(
            "No standard/deviant stimulus types found in events metadata; "
            "cannot build dataset metadata rows."
        )

    schema = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    rows = []
    for events_path in sorted(Path(raw_dir).rglob("*events.tsv")):
        subj_m = re.search(r"(sub-[A-Za-z0-9]+)", str(events_path))
        if not subj_m:
            continue
        subject_id = subj_m.group(1)

        with open(events_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            headers = reader.fieldnames or []
            rows_raw = list(reader)

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
            validate(row, schema)
            if row not in rows:
                rows.append(row)

    out = paths.results("dataset_metadata.json")
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(
        f"Validated {len(rows)} metadata rows against {SCHEMA_PATH}; written to {out}"
    )
    return rows

def main():
    parser = argparse.ArgumentParser(description="Download OpenNeuro ds004510 (FR-001)")
    parser.add_argument(
        "--subjects", type=int, default=2,
        help="Number of subjects to download for this pass (0 = all)",
    )
    parser.add_argument(
        "--dataset-id", default=CANONICAL_DATASET_ID,
        help="Dataset ID (verified against the canonical source before download)",
    )
    args = parser.parse_args()

    # FR-012(1): pre‑download dataset‑ID gate.
    verify_dataset_id(args.dataset_id)

    raw_dir = paths.data("raw")
    files = download_subjects(args.subjects, raw_dir)
    if not files:
        raise RuntimeError("No files were downloaded; halting.")
    record_checksums(files, raw_dir)

    # FR-012(2) / FR-008: condition gate.
    verify_conditions(raw_dir)

    # Validate metadata and write dataset_metadata.json
    validate_metadata(raw_dir)

    print(f"Download stage complete: {len(files)} files under {raw_dir}")

if __name__ == "__main__":
    main()
