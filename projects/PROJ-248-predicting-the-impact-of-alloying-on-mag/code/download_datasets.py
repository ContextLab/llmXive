"""
download_datasets.py

Script to download the Materials Project magnetic dataset and the OQMD magnetic CSV
using the HuggingFace `datasets` library. The script writes three artefacts:

* `data/raw_mp.jsonl` – filtered JSON‑lines from the Materials Project
  (only entries where `magnetic_type` is not `NM`).
* `data/raw_oqmd.csv` – the raw OQMD CSV file.
* `data/data_sources.yaml` – a manifest containing version identifiers,
  SHA‑256 checksums, and basic download metadata for reproducibility.
"""

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
from datasets import load_dataset
import yaml
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

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

def download_materials_project(raw_mp_path: Path) -> dict:
    """
    Download Materials Project magnetic entries via the HuggingFace ``datasets``
    library. The dataset identifier is ``materialsproject/mp`` with the
    configuration ``2020.10.01``. The function streams the dataset, filters out
    entries where ``magnetic_type`` equals ``NM``, and writes the remaining
    records as JSON‑lines to ``raw_mp_path``.
    Returns a manifest containing a version identifier, SHA‑256 checksum,
    and the number of records written.
    """
    log.info("Loading Materials Project magnetic dataset via ``datasets``")
    # The dataset is publicly hosted; no auth token is required.
    ds = load_dataset(
        "materialsproject/mp",
        "2020.10.01",
        split="train",
        streaming=True,
    )

    raw_mp_path.parent.mkdir(parents=True, exist_ok=True)

    sha256 = hashlib.sha256()
    count = 0
    with raw_mp_path.open("w", encoding="utf-8") as out_f:
        for record in ds:
            # ``record`` is a dict; ensure required key exists.
            if record.get("magnetic_type") == "NM":
                continue
            json_line = json.dumps(record, ensure_ascii=False)
            out_f.write(json_line + "\n")
            sha256.update(json_line.encode("utf-8"))
            count += 1
            if count % 10_000 == 0:
                log.info("Materials Project: %d magnetic records written...", count)

    if count == 0:
        raise RuntimeError(
            "No magnetic records were found after filtering the Materials Project dataset."
        )

    checksum = sha256.hexdigest()
    log.info(
        "Materials Project download complete - %d records written, SHA‑256: %s",
        count,
        checksum,
    )

    version_id = "mp-2020.10.01"
    return {"version": version_id, "sha256": checksum, "records": count}

def download_oqmd(raw_oqmd_path: Path) -> dict:
    """
    Download the OQMD magnetic CSV via the HuggingFace ``datasets`` library.
    The dataset identifier is ``oqmd/oqmd`` with the configuration ``magnetic``.
    The function writes the table to ``raw_oqmd_path`` as a CSV file.
    Returns a manifest containing the source URL, SHA‑256 checksum, and size.
    """
    log.info("Loading OQMD magnetic dataset via ``datasets``")
    ds = load_dataset(
        "oqmd/oqmd",
        "magnetic",
        split="train",
        streaming=False,  # small enough to load in memory
    )

    # Convert to pandas DataFrame for easy CSV export.
    df = pd.DataFrame(ds)

    raw_oqmd_path.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV (UTF‑8, no index)
    df.to_csv(raw_oqmd_path, index=False, encoding="utf-8")

    checksum = _sha256_of_path(raw_oqmd_path)
    total_bytes = raw_oqmd_path.stat().st_size

    log.info(
        "OQMD download complete - %d bytes written, SHA‑256: %s",
        total_bytes,
        checksum,
    )

    # The dataset page can be used as a stable reference URL.
    url = "https://huggingface.co/datasets/oqmd/oqmd/tree/main"

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