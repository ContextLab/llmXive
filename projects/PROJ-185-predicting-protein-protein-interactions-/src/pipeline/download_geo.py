"""
download_geo.py
----------------
Implements the GEO series download step for the PPI prediction pipeline.

- Reads ``src/config/species.yaml`` to obtain a mapping of species to GEO
  accession IDs.
- For each GEO series:
  * Retrieves the series metadata using ``GEOparse`` to obtain the sample
    count.
  * Skips the series (logs a warning) if it contains fewer than 30 samples.
  * Downloads the raw ``.tar`` archive (or, if unavailable, the series
    matrix) from the NCBI GEO FTP site.
  * Writes the downloaded archive to ``data/raw/``.
  * Computes a SHA‑256 checksum of the file and records it in
    ``data/artifact_hashes.yaml``.
- All major actions are logged to the JSON‑Line pipeline log via the
  shared logger obtained from ``llmxive_toolkit``.
- The script can be invoked directly (``python -m src.pipeline.download_geo``)
  or via the Makefile target ``download``.
"""

import argparse
import hashlib
import logging
import os
import tempfile
from pathlib import Path

import requests
import yaml
import GEOparse

from llmxive_toolkit import paths, get_logger

# Initialise a logger that writes to the central pipeline log.
log = get_logger(__name__)

def _load_species_config(config_path: Path) -> dict:
    """Load ``species.yaml`` and return the parsed dictionary."""
    if not config_path.is_file():
        raise FileNotFoundError(f"Species configuration not found: {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}

def _compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 checksum of *file_path*."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def _record_checksum(file_name: str, checksum: str) -> None:
    """
    Record ``file_name`` → ``checksum`` mapping in ``data/artifact_hashes.yaml``.
    The file is created if it does not exist; existing entries are preserved.
    """
    hash_path = paths.data("artifact_hashes.yaml")
    if hash_path.is_file():
        with open(hash_path, "r") as fh:
            data = yaml.safe_load(fh) or {}
    else:
        data = {}

    data[file_name] = checksum

    with open(hash_path, "w") as fh:
        yaml.safe_dump(data, fh)

    log.info(f"Recorded checksum for {file_name}: {checksum}")

def _sample_count(gse_id: str) -> int:
    """
    Retrieve the GEO series using ``GEOparse`` (download only the soft file)
    and return the number of samples contained in the series.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            gse = GEOparse.get_GEO(geo=gse_id, destdir=tmpdir, silent=True)
        except Exception as exc:
            log.error(f"Failed to fetch GEO metadata for {gse_id}: {exc}")
            raise
    # ``gse.gsms`` is a dict of Sample objects.
    return len(gse.gsms)

def _download_raw_archive(gse_id: str, dest_dir: Path) -> Path:
    """
    Download the raw ``.tar`` archive for *gse_id* from the GEO FTP site.
    If the raw archive is not present, fall back to the series‑matrix file.
    Returns the path to the downloaded file.
    """
    # GEO series numbers are zero‑padded six‑digit identifiers.
    numeric = int(gse_id.replace("GSE", ""))
    base = (numeric // 1000) * 1000
    folder = f"GSE{base:06d}"
    # Preferred raw archive location.
    raw_url = (
        f"https://ftp.ncbi.nlm.nih.gov/geo/series/{folder}/{gse_id}/suppl/"
        f"{gse_id}_RAW.tar"
    )
    response = requests.get(raw_url, stream=True, timeout=30)
    if response.status_code == 200:
        file_name = f"{gse_id}_RAW.tar"
    else:
        # Fallback to the series‑matrix file (gzipped).
        raw_url = (
            f"https://ftp.ncbi.nlm.nih.gov/geo/series/{folder}/{gse_id}/matrix/"
            f"{gse_id}_series_matrix.txt.gz"
        )
        response = requests.get(raw_url, stream=True, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"Unable to download raw data for {gse_id}")
        file_name = f"{gse_id}_series_matrix.txt.gz"

    out_path = dest_dir / file_name
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "wb") as out_f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                out_f.write(chunk)

    log.info(f"Downloaded {gse_id} → {out_path}")
    return out_path

def _process_series(gse_id: str, raw_dir: Path) -> None:
    """
    Process a single GEO series:
    1. Determine sample count.
    2. Skip and log a warning if <30 samples.
    3. Download the raw archive.
    4. Compute and record its SHA‑256 checksum.
    """
    try:
        count = _sample_count(gse_id)
    except Exception:
        # The helper already logs the error; re‑raise to abort this series.
        raise

    if count < 30:
        log.warning(
            f"Series {gse_id} has insufficient samples ({count}); skipping."
        )
        return

    downloaded_path = _download_raw_archive(gse_id, raw_dir)
    checksum = _compute_sha256(downloaded_path)
    _record_checksum(downloaded_path.name, checksum)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download GEO series defined in src/config/species.yaml"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(paths.path("src", "config", "species.yaml")),
        help="Path to the species configuration YAML file.",
    )
    return parser

def main() -> int:
    """
    Entry point used by the Makefile target ``download``.
    Returns 0 on success, non‑zero on failure.
    """
    parser = build_parser()
    args = parser.parse_args()

    config_path = Path(args.config)
    try:
        cfg = _load_species_config(config_path)
    except Exception as exc:
        log.error(f"Failed to load species configuration: {exc}")
        return 1

    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # ``species.yaml`` may map a species name to a list of accession IDs
    # or to a dict containing an ``accessions`` key.  Both formats are
    # supported for flexibility.
    for species, spec in cfg.items():
        if isinstance(spec, dict):
            series_ids = spec.get("accessions", [])
        else:
            series_ids = spec
        if not series_ids:
            log.info(f"No GEO series listed for species '{species}'.")
            continue

        for gse_id in series_ids:
            try:
                _process_series(gse_id, raw_dir)
            except Exception as exc:
                log.error(f"Error processing {gse_id}: {exc}")
                return 1

    log.info("All GEO series processed successfully.")
    return 0

if __name__ == "__main__":
    exit_code = main()
    raise SystemExit(exit_code)
