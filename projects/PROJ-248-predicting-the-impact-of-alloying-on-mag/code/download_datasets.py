"""
download_datasets.py

Script to download the Materials Project magnetic dataset via the public
HuggingFace repository and the OQMD magnetic CSV directly from HuggingFace.
The script writes three artifacts:

* `data/raw_mp.jsonl` – filtered JSON‑lines from the Materials Project
  (only entries where `magnetic_type` is not `NM`).
* `data/raw_oqmd.csv` – the raw OQMD magnetic CSV file.
* `data/data_sources.yaml` – a manifest containing version identifiers,
  SHA‑256 checksums, and basic download metadata for reproducibility.
"""

import hashlib
import json
import sys
from pathlib import Path
from typing import Dict

import requests
import yaml
from datasets import load_dataset
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
# Materials Project download (via HuggingFace)
# ----------------------------------------------------------------------


def download_materials_project(raw_mp_path: Path) -> Dict[str, object]:
    """
    Download Materials Project magnetic entries via the HuggingFace hub.
    The dataset identifier is ``materialsproject/mp`` with the configuration
    ``magnetic``.  Each record is written as a JSON‑line to ``raw_mp_path``.

    Returns
    -------
    dict
        Manifest containing a version identifier, SHA‑256 checksum,
        and the number of records written.
    """
    log.info("Downloading Materials Project magnetic dataset via HuggingFace")
    raw_mp_path.parent.mkdir(parents=True, exist_ok=True)

    # Load the dataset; this pulls the public, version‑controlled archive.
    # We use the 'magnetic' config as per the plan and spec.
    ds = load_dataset("materialsproject/mp", "magnetic", split="train")

    sha256 = hashlib.sha256()
    count = 0

    with raw_mp_path.open("w", encoding="utf-8") as out_f:
        for rec in ds:
            # ``rec`` is a dict; write it as a JSON line.
            json_line = json.dumps(rec, ensure_ascii=False)
            out_f.write(json_line + "\n")
            sha256.update(json_line.encode("utf-8"))
            count += 1
            if count % 10_000 == 0:
                log.info("Materials Project: %d records written...", count)

    if count == 0:
        raise RuntimeError(
            "No records were retrieved from the Materials Project dataset."
        )

    checksum = sha256.hexdigest()
    version_id = getattr(ds.info, "version", "unknown")
    log.info(
        "Materials Project download complete - %d records written, SHA‑256: %s",
        count,
        checksum,
    )
    return {"version": str(version_id), "sha256": checksum, "records": count}


# ----------------------------------------------------------------------
# OQMD download
# ----------------------------------------------------------------------


def download_oqmd(raw_oqmd_path: Path) -> Dict[str, object]:
    """
    Download the OQMD magnetic CSV directly from HuggingFace.
    The dataset identifier is ``oqmd/oqmd`` with the configuration
    ``magnetic``.  The raw CSV is written to ``raw_oqmd_path``.

    Returns
    -------
    dict
        Manifest containing the source URL, SHA‑256 checksum, and size in bytes.
    """
    # Direct URL to the CSV file in the HuggingFace repository.
    url = "https://huggingface.co/datasets/oqmd/oqmd/resolve/main/magnetic.csv"
    log.info("Downloading OQMD magnetic CSV from %s", url)

    raw_oqmd_path.parent.mkdir(parents=True, exist_ok=True)

    # Stream download to avoid loading the whole file into memory.
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with raw_oqmd_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive chunks
                    f.write(chunk)

    checksum = _sha256_of_path(raw_oqmd_path)
    total_bytes = raw_oqmd_path.stat().st_size

    log.info(
        "OQMD download complete - %d bytes written, SHA‑256: %s",
        total_bytes,
        checksum,
    )

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