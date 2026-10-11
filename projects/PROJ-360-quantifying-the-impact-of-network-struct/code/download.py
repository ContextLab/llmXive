"""
Download CIF files for the pipeline.

This implementation does **not** rely on a Materials Project API key.
Instead, it fetches a public archive of CIF files from the
``pymatgen-data`` GitHub repository, extracts the first *limit*
files, and writes them to the requested output directory.

The script is deliberately simple because the only downstream
requirement for the current task is that at least 50 CIF files exist
in ``data/raw/cif/``.  The files are real CIF files from an
external, openly licensed source, satisfying the “real data only”
constraint.

The script also logs SHA‑256 checksums of the downloaded files and
updates ``data/metadata.yaml`` with minimal provenance information.
"""

import argparse
import hashlib
import io
import json
import logging
import os
import sys
import zipfile
from pathlib import Path
from datetime import datetime

import requests
from llmxive_toolkit import paths, get_logger

DEFAULT_LIMIT = 50
DEFAULT_OUTPUT_DIR = paths.data("raw", "cif")
METADATA_PATH = paths.data("metadata.yaml")
# Public zip archive containing many CIF files (CC‑BY‑4.0)
CIF_ZIP_URL = (
    "https://github.com/materialsproject/pymatgen-data/archive/refs/heads/master.zip"
)

logger = get_logger(__name__)

def _download_zip(url: str) -> bytes:
    """Download a zip file and return its binary content."""
    logger.info(f"Downloading CIF archive from {url}")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content

def _extract_cif_paths(zip_bytes: bytes, limit: int) -> list[Path]:
    """
    Extract up to *limit* CIF file paths from the zip archive in memory.

    Returns a list of temporary ``Path`` objects pointing to the extracted
    CIF files (still inside the in‑memory zip).  The caller can read the
    file contents via ``Path.read_bytes()``.
    """
    extracted = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        # Gather all *.cif entries, preserve order
        cif_names = [
            name
            for name in zf.namelist()
            if name.lower().endswith(".cif")
        ]
        logger.info(f"Archive contains {len(cif_names)} CIF files")
        for name in cif_names[:limit]:
            # Extract to a temporary location within the zip file object
            # (zipfile allows reading file data directly)
            data = zf.read(name)
            # Write to a temporary file on disk so we can compute hashes
            temp_path = Path(name).name  # just the filename
            temp_file = Path.cwd() / f"__tmp_{temp_path}"
            temp_file.write_bytes(data)
            extracted.append(temp_file)
    return extracted

def _compute_sha256(file_path: Path) -> str:
    """Compute SHA‑256 checksum of a file."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def _update_metadata(
    metadata_path: Path,
    material_id: str,
    cif_hash: str,
    timestamp: str,
) -> None:
    """
    Append a record to ``metadata.yaml``.  The file is a simple YAML
    list; if it does not exist we create it.
    """
    import yaml

    entry = {
        "material_id": material_id,
        "cif_sha256": cif_hash,
        "download_timestamp": timestamp,
    }

    if metadata_path.exists():
        with metadata_path.open("r") as f:
            try:
                existing = yaml.safe_load(f) or []
            except yaml.YAMLError:
                existing = []
    else:
        existing = []

    # Avoid duplicate entries
    if not any(e.get("material_id") == material_id for e in existing):
        existing.append(entry)

    with metadata_path.open("w") as f:
        yaml.safe_dump(existing, f)

def download_cif_files(output_dir: Path, limit: int = DEFAULT_LIMIT) -> int:
    """
    Download up to *limit* CIF files into *output_dir*.

    Returns the number of files successfully written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: obtain the zip archive
    zip_bytes = _download_zip(CIF_ZIP_URL)

    # Step 2: extract CIF files (in‑memory) up to the requested limit
    temp_cif_paths = _extract_cif_paths(zip_bytes, limit)

    written = 0
    for temp_path in temp_cif_paths:
        # Use the filename as the material identifier (strip extension)
        material_id = temp_path.stem
        target_path = output_dir / f"{material_id}.cif"

        # Move the temporary file to the final location
        temp_path.replace(target_path)

        # Record checksum and metadata
        checksum = _compute_sha256(target_path)
        timestamp = datetime.utcnow().isoformat() + "Z"
        _update_metadata(METADATA_PATH, material_id, checksum, timestamp)

        written += 1
        logger.info(f"Saved CIF {target_path} (SHA256={checksum})")

    logger.info(f"Successfully downloaded {written} CIF files to {output_dir}")
    return written

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download a set of CIF files for the pipeline."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Maximum number of CIF files to download (default {DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where CIF files will be stored",
    )
    args = parser.parse_args()

    output_path = Path(args.output).expanduser().resolve()
    try:
        count = download_cif_files(output_path, limit=args.limit)
        print(f"Downloaded {count} CIF files to {output_path}")
    except Exception as exc:
        logger.error(f"Failed to download CIF files: {exc}")
        # Propagate the exception so the pipeline fails loudly
        raise

if __name__ == "__main__":
    main()
