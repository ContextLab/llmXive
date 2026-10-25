"""
download_datasets.py

Script to download the Materials Project magnetic dataset via its public REST API
and the OQMD magnetic CSV directly from the HuggingFace repository.
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
from typing import Dict, Iterable

import requests
import yaml
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
# Materials Project download
# ----------------------------------------------------------------------


def _stream_mp_records(
    base_url: str = "https://materialsproject.org/rest/v2/materials/search",
    page_size: int = 1000,
) -> Iterable[dict]:
    """
    Generator that yields records from the Materials Project public REST API.
    The API endpoint returns paginated JSON. We request ``has_magnetic_properties=true``
    and iterate using ``skip``/``limit`` parameters until no more records are returned.

    Parameters
    ----------
    base_url: str
        The base endpoint URL.
    page_size: int
        Number of records per request (the API max is typically 1000).

    Yields
    ------
    dict
        A single material record.
    """
    session = requests.Session()
    skip = 0
    while True:
        params = {
            "has_magnetic_properties": "true",
            "limit": page_size,
            "skip": skip,
        }
        log.info("Requesting Materials Project page: skip=%d limit=%d", skip, page_size)
        response = session.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        # The API wraps results under ``response`` → ``docs`` (as of v2026).
        # Guard against structural changes.
        records = data.get("response", {}).get("docs", [])
        if not records:
            log.info("No more records returned; terminating pagination.")
            break

        for rec in records:
            yield rec

        # Increment for next page
        skip += page_size

def download_materials_project(raw_mp_path: Path) -> Dict[str, object]:
    """
    Download Materials Project magnetic entries via the public REST API.
    Records with ``magnetic_type`` equal to ``NM`` are filtered out.
    The remaining records are written as JSON‑lines to ``raw_mp_path``.

    Returns
    -------
    dict
        Manifest containing a version identifier, SHA‑256 checksum,
        and the number of records written.
    """
    log.info("Starting Materials Project download via public REST API")
    raw_mp_path.parent.mkdir(parents=True, exist_ok=True)

    sha256 = hashlib.sha256()
    count = 0

    with raw_mp_path.open("w", encoding="utf-8") as out_f:
        for record in _stream_mp_records():
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

    version_id = "mp-public-api-2026.10"
    return {"version": version_id, "sha256": checksum, "records": count}


# ----------------------------------------------------------------------
# OQMD download
# ----------------------------------------------------------------------


def download_oqmd(raw_oqmd_path: Path) -> Dict[str, object]:
    """
    Download the OQMD magnetic CSV directly from HuggingFace.
    The dataset identifier is ``oqmd/oqmd`` with the configuration ``magnetic``.
    The raw CSV is written to ``raw_oqmd_path``.

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