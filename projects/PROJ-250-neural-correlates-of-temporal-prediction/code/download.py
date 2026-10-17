"""Download the OpenNeuro ds004510 dataset (FR-001) with FR-012 gates.

Pipeline:
  1. verify_dataset_id() -- FR-012(1) gate runs BEFORE any download; halts on mismatch.
  2. Fetch ds004510 from the OpenNeuro S3 HTTPS endpoint via curl (fallback wget),
     processing subjects iteratively (one subject's files at a time; never loading
     all subjects at once) to stay within ~7 GB RAM.
  3. Record SHA-256 checksums of every downloaded file in data/raw/checksums.json.
  4. verify_conditions() -- FR-012(2)/FR-008 gate after metadata is available.
  5. Validate dataset metadata against contracts/dataset.schema.yaml and write
     data/results/dataset_metadata.json.

The loader fails loudly on any fetch error -- there are NO synthetic or mock fallbacks.

Usage: python code/download.py --subjects 2
"""

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
import yaml
from jsonschema import validate
from llmxive_toolkit import paths

from verify_references import (
    CANONICAL_DATASET_ID,
    S3_BASE,
    collect_events,
    verify_dataset_id,
)

SCHEMA_PATH = (
    paths.root
    / "specs"
    / "001-neural-correlates-of-temporal-prediction"
    / "contracts"
    / "dataset.schema.yaml"
)


def _strip_ns(tag):
    return tag.split("}")[-1]


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
        resp = requests.get(S3_BASE, params=params, timeout=60)
        resp.raise_for_status()
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
                raise RuntimeError("S3 listing error: %s" % ET.tostring(child))
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
    """Return the S3 key prefix holding current ds004510 files (versioned if applicable).

    ds004510 is stored FLAT under ds004510/ in the OpenNeuro S3 bucket (its
    CommonPrefixes are subject directories like ds004510/sub-UTS01/, NOT version
    directories). Only descend into a sub-directory when it is a genuine
    semantic-version directory (e.g. '1.2.0') and the dataset has no files at
    the top level.
    """
    base = CANONICAL_DATASET_ID + "/"
    keys, prefixes = s3_list(base)
    if keys:
        # Files exist directly under ds004510/ -> flat layout; use it as-is.
        return base
    version_prefixes = [
        p.rstrip("/")
        for p in prefixes
        if re.fullmatch(r"\d+(\.\d+)*", p.rstrip("/"))
    ]
    if version_prefixes:
        version_prefixes.sort(
            key=lambda v: tuple(int(x) for x in v.split("."))
        )
        latest = version_prefixes[-1]
        print("Resolved dataset version: %s (latest of %s)"
              % (latest, version_prefixes))
        return base + latest + "/"
    raise RuntimeError(
        "No objects found under s3://%s/%s; dataset %s is not reachable."
        % (S3_BASE, base, CANONICAL_DATASET_ID)
    )


def fetch_file(url, dest):
    """Fetch one file via curl (fallback wget). Fails loudly; no synthetic fallback."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    curl_cmd = [
        "curl", "-fSL", "--retry", "3", "--connect-timeout", "30",
        "-o", str(dest), url,
    ]
    proc = subprocess.run(curl_cmd)
    if proc.returncode == 0:
        return
    print("curl failed (%d) for %s; trying wget..." % (proc.returncode, url), file=sys.stderr)
    wget_cmd = ["wget", "-q", "--tries", "3", "--timeout", "60", "-O", str(dest), url]
    proc2 = subprocess.run(wget_cmd)
    if proc2.returncode != 0:
        raise RuntimeError(
            "FAILED to download %s (curl rc=%d, wget rc=%d). No fallback data "
            "will be generated; halting." % (url, proc.returncode, proc2.returncode)
        )


def sha256_file(path, chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def download_subjects(n_subjects, raw_dir):
    prefix = resolve_dataset_prefix()
    keys, _ = s3_list(prefix)
    if not keys:
        raise RuntimeError("No files found under S3 prefix %s" % prefix)

    root_files = []
    subject_files = {}
    for key in keys:
        remainder = key[len(prefix):]
        if not remainder or remainder.endswith("/"):
            continue
        m = re.match(r"(sub-[^\t/]+)/", remainder)
        if m:
            subject_files.setdefault(m.group(1), []).append(key)
        else:
            root_files.append(key)

    subjects = sorted(
        subject_files.keys(), key=lambda s: int(re.sub(r"\D", "", s) or 0)
    )
    if n_subjects > 0:
        selected = subjects[:n_subjects]
    else:
        selected = subjects
    print("Dataset has %d subjects; downloading %d: %s"
          % (len(subjects), len(selected), selected))

    downloaded = []
    # Root BIDS metadata files first (participants.tsv, dataset_description.json, ...).
    for key in root_files:
        remainder = key[len(prefix):]
        dest = raw_dir / remainder
        url = "%s/%s" % (S3_BASE, key)
        print("Downloading %s" % remainder)
        fetch_file(url, dest)
        downloaded.append(dest)
    # Then subject files, one subject at a time (iterative; bounded memory).
    for subj in selected:
        for key in sorted(subject_files[subj]):
            remainder = key[len(prefix):]
            dest = raw_dir / remainder
            url = "%s/%s" % (S3_BASE, key)
            print("Downloading %s" % remainder)
            fetch_file(url, dest)
            downloaded.append(dest)
    return downloaded


def record_checksums(files, raw_dir):
    checksums_path = raw_dir / "checksums.json"
    checksums = {}
    if checksums_path.exists():
        try:
            checksums = json.loads(checksums_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            checksums = {}
    for f in files:
        rel = str(f.relative_to(raw_dir))
        checksums[rel] = sha256_file(f)
        print("SHA-256 %s  %s" % (checksums[rel][:16] + "...", rel))
    checksums_path.write_text(
        json.dumps(checksums, indent=2, sort_keys=True), encoding="utf-8"
    )
    print("Checksums for %d files recorded in %s" % (len(files), checksums_path))
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
    alias_c = {"simple": "simple", "complex": "complex"}
    alias_s = {
        "standard": "standard", "std": "standard",
        "deviant": "deviant", "dev": "deviant",
    }
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
                if vals & set(alias_c):
                    cond_col = h
                    break
        stim_col = "stimulus_type" if "stimulus_type" in headers else None
        if stim_col is None:
            for h in headers:
                vals = {str(r.get(h) or "").strip().lower() for r in rows_raw}
                if vals & set(alias_s):
                    stim_col = h
                    break
        if cond_col is None or stim_col is None:
            continue
        for r in rows_raw:
            c = alias_c.get(str(r.get(cond_col) or "").strip().lower())
            s = alias_s.get(str(r.get(stim_col) or "").strip().lower())
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
        "Validated %d metadata rows against %s; written to %s"
        % (len(rows), SCHEMA_PATH, out)
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

    # FR-012(1): pre-download dataset-ID gate. Halts on mismatch.
    verify_dataset_id(args.dataset_id)

    raw_dir = paths.data("raw")
    files = download_subjects(args.subjects, raw_dir)
    if not files:
        raise RuntimeError("No files were downloaded; halting.")
    record_checksums(files, raw_dir)

    # FR-012(2) / FR-008: pre-analysis condition gate (halts with the exact
    # FR-008 message if 'complex' is missing).
    from verify_references import verify_conditions
    verify_conditions(raw_dir)

    validate_metadata(raw_dir)
    print("Download stage complete: %d files under %s" % (len(files), raw_dir))


if __name__ == "__main__":
    main()
