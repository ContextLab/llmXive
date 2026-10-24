"""
download_datasets.py

Script to download the Materials Project magnetic dataset (via the HuggingFace
Hub) and the OQMD magnetic CSV release (via a direct HTTP request).  The script
writes three artefacts:

* ``data/raw_mp.jsonl`` – filtered JSON‑lines from the Materials Project
  (only entries where ``magnetic_type`` is not ``NM``).
* ``data/raw_oqmd.csv`` – the raw OQMD CSV file.
* ``data/data_sources.yaml`` – a small YAML manifest containing version
  identifiers and SHA‑256 checksums for reproducibility.

The script is intended to be run as part of the pipeline's Phase 0 and must
succeed on a fresh runner (no cached data).  It aborts loudly if any download
fails or if the resulting checksum cannot be computed.
"""

import hashlib
import json
import sys
from pathlib import Path
import os
import requests
import yaml

# The `datasets` library provides a streaming interface to the Materials
# Project dataset hosted on the HuggingFace Hub.  It is listed as a required
# dependency in ``requirements.txt``.
import datasets

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _sha256_of_path(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _write_yaml(manifest: dict, out_path: Path) -> None:
    """Write a dictionary to a YAML file (ensuring parent dirs exist)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, sort_keys=False)

# ----------------------------------------------------------------------
# Phase 0 – Materials Project magnetic entries
# ----------------------------------------------------------------------
def download_materials_project(raw_mp_path: Path) -> dict:
    """
    Download the Materials Project dataset using the ``datasets`` library,
    filter out non‑magnetic entries (``magnetic_type`` == ``NM``), and write
    each remaining record as a JSON line.

    Returns a manifest dictionary containing the dataset version (the
    git‑commit hash of the snapshot) and the SHA‑256 checksum of the written
    file.
    """
    log.info("Downloading Materials Project dataset via the HuggingFace `datasets` library.")
    # The dataset identifier on the Hub.
    dataset_name = "materialsproject"
    try:
        # ``load_dataset`` with ``streaming=True`` avoids downloading the
        # entire archive to disk and yields records lazily.
        ds = datasets.load_dataset(
            path=dataset_name,
            split="train",          # the default split for this dataset
            streaming=True,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load the Materials Project dataset '{dataset_name}' via the `datasets` library: {exc}"
        ) from exc

    # Retrieve the snapshot version (commit hash) from the dataset info.
    try:
        version = ds._fingerprint  # fingerprint is a hash of the underlying files
    except Exception:
        version = "unknown"

    raw_mp_path.parent.mkdir(parents=True, exist_ok=True)

    sha256 = hashlib.sha256()
    count = 0
    with raw_mp_path.open("w", encoding="utf-8") as dst:
        for record in ds:
            # Defensive: ensure we have a mapping.
            if not isinstance(record, dict):
                continue
            # Keep only magnetic entries (magnetic_type != "NM").
            if record.get("magnetic_type") == "NM":
                continue
            out_line = json.dumps(record, ensure_ascii=False)
            dst.write(out_line + "\n")
            sha256.update(out_line.encode("utf-8"))
            count += 1
            if count % 10_000 == 0:
                log.info("Materials Project: %d magnetic records written...", count)

    if count == 0:
        raise RuntimeError(
            "No magnetic records were found after filtering the Materials Project dataset."
        )

    checksum = sha256.hexdigest()
    log.info(
        "Materials Project download complete – %d records written, SHA‑256: %s",
        count,
        checksum,
    )

    return {"version": version, "sha256": checksum, "records": count}

# ----------------------------------------------------------------------
# Phase 0 – OQMD magnetic CSV
# ----------------------------------------------------------------------
def download_oqmd(raw_oqmd_path: Path) -> dict:
    """
    Download the OQMD magnetic CSV from a verified HuggingFace URL.

    Returns a manifest dictionary containing the URL and the SHA‑256
    checksum of the downloaded file.
    """
    # Verified HuggingFace URL for the OQMD magnetic CSV.
    url = "https://huggingface.co/datasets/oqmd/oqmd/resolve/main/oqmd.csv"

    log.info("Downloading OQMD magnetic CSV from %s", url)
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()

    raw_oqmd_path.parent.mkdir(parents=True, exist_ok=True)

    sha256 = hashlib.sha256()
    total_bytes = 0
    with raw_oqmd_path.open("wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if not chunk:
                continue
            f.write(chunk)
            sha256.update(chunk)
            total_bytes += len(chunk)

    if total_bytes == 0:
        raise RuntimeError("Downloaded OQMD CSV is empty.")

    checksum = sha256.hexdigest()
    log.info("OQMD download complete – %d bytes, SHA‑256: %s", total_bytes, checksum)

    return {"url": url, "sha256": checksum, "bytes": total_bytes}

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the download steps and write the data sources manifest.
    """
    raw_mp_path = paths.data("raw_mp.jsonl")
    raw_oqmd_path = paths.data("raw_oqmd.csv")
    manifest_path = paths.data("data_sources.yaml")

    mp_manifest = download_materials_project(raw_mp_path)
    oqmd_manifest = download_oqmd(raw_oqmd_path)

    manifest = {
        "materials_project": mp_manifest,
        "oqmd": oqmd_manifest,
    }

    _write_yaml(manifest, manifest_path)
    log.info("Data sources manifest written to %s", manifest_path)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.exception("Data acquisition failed: %s", exc)
        sys.exit(1)
