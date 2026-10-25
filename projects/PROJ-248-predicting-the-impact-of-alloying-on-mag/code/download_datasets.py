"""
download_datasets.py

Script to download the Materials Project magnetic dataset (via the HuggingFace
`datasets` library) and the OQMD magnetic CSV release (via a direct HTTP
request). The script writes three artefacts:

* `data/raw_mp.jsonl` – filtered JSON-lines from the Materials Project
  (only entries where `magnetic_type` is not `NM`).
* `data/raw_oqmd.csv` – the raw OQMD CSV file.
* `data/data_sources.yaml` – a small YAML manifest containing version
  identifiers and SHA-256 checksums for reproducibility.
"""

import hashlib
import json
import sys
from pathlib import Path

import requests
import yaml
from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _sha256_of_path(file_path: Path) -> str:
    """Compute the SHA-256 checksum of a file."""
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

def download_materials_project(raw_mp_path: Path) -> dict:
    """
    Download Materials Project magnetic entries using a publicly available
    HuggingFace dataset. The dataset ``materialsproject/mp-2020.10.01`` is
    a snapshot of the Materials Project bulk archive and does not require
    an API key.

    The function streams the dataset, filters out entries where
    ``magnetic_type`` equals ``NM`` (non‑magnetic), and writes each
    remaining record as a JSON line to ``raw_mp_path``. It returns a
    manifest containing a version identifier, the SHA‑256 checksum of the
    written file and the number of records written.
    """
    log.info("Loading Materials Project dataset via `datasets` (streaming).")
    try:
        ds = load_dataset(
            "materialsproject/mp-2020.10.01",
            split="train",
            streaming=True,
            trust_remote_code=True,
        )
    except Exception as e:
        log.error("Failed to load Materials Project dataset: %s", e)
        raise RuntimeError(f"Materials Project dataset not accessible: {e}")

    # Keep only magnetic entries (exclude non‑magnetic)
    ds = ds.filter(lambda x: x.get("magnetic_type") != "NM")

    # Attempt to capture a version/revision identifier
    version_id = "unknown"
    if hasattr(ds, "info") and getattr(ds, "info", None):
        version_id = getattr(ds.info, "revision", "unknown")

    raw_mp_path.parent.mkdir(parents=True, exist_ok=True)

    sha256 = hashlib.sha256()
    count = 0
    with raw_mp_path.open("w", encoding="utf-8") as dst:
        for record in ds:
            line = json.dumps(record, ensure_ascii=False)
            dst.write(line + "\n")
            sha256.update(line.encode("utf-8"))
            count += 1
            if count % 10_000 == 0:
                log.info("Materials Project: %d magnetic records written...", count)

    if count == 0:
        raise RuntimeError(
            "No magnetic records were found after filtering the Materials Project dataset."
        )

    checksum = sha256.hexdigest()
    log.info(
        "Materials Project download complete - %d records written, SHA-256: %s",
        count,
        checksum,
    )

    return {"version": str(version_id), "sha256": checksum, "records": count}

def download_oqmd(raw_oqmd_path: Path) -> dict:
    """
    Download the OQMD magnetic CSV from a verified HuggingFace URL.
    """
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
    log.info("OQMD download complete - %d bytes, SHA-256: %s", total_bytes, checksum)

    return {"url": url, "sha256": checksum, "bytes": total_bytes}

def main() -> None:
    """
    Execute the download steps and write the data sources manifest.
    """
    raw_mp_path = paths.data("raw_mp.jsonl")
    raw_oqmd_path = paths.data("raw_oqmd.csv")
    manifest_path = paths.data("data_sources.yaml")

    # Perform downloads
    mp_manifest = download_materials_project(raw_mp_path)
    oqmd_manifest = download_oqmd(raw_oqmd_path)

    # Build and write manifest
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
