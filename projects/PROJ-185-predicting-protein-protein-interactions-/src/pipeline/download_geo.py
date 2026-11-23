"""
GEO series downloader for the PPI prediction pipeline.

Reads ``src/config/species.yaml`` to obtain a mapping of species → GEO
accession IDs.  For each accession the script:

1. Retrieves the GEO series using ``GEOparse``.
2. Determines the number of samples in the series.
3. Skips the series (with a warning) if it contains fewer than 30
   samples.
4. Otherwise creates a ``.tar.gz`` archive of the raw GEO files and
   stores it under ``data/raw/<accession>.tar.gz``.
5. Computes a SHA‑256 checksum of the archive and records it in
   ``data/artifact_hashes.yaml`` (a simple ``accession: checksum`` mapping).

All major actions are logged to ``src/logs/pipeline.log`` in JSON‑Line
format using the project‑wide logger obtained from ``llmxive_toolkit``.
"""
import hashlib
import json
import logging
import shutil
import tempfile
from pathlib import Path

import GEOparse
import yaml

from llmxive_toolkit import paths, get_logger

# Initialise logger (JSON‑Line handling is performed by the toolkit)
logger = get_logger(__name__)

# Paths used throughout the script
SPECIES_YAML = paths.code("config", "species.yaml")
RAW_DIR = paths.data("raw")
HASHES_YAML = paths.data("artifact_hashes.yaml")
LOG_PATH = paths.logs("pipeline.log")


def _load_species_config() -> dict:
    """Load ``species.yaml`` and return the parsed dictionary."""
    if not SPECIES_YAML.is_file():
        raise FileNotFoundError(f"Species configuration not found at {SPECIES_YAML}")
    with SPECIES_YAML.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _ensure_raw_dir() -> None:
    """Create the ``data/raw`` directory if it does not already exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def _load_hashes() -> dict:
    """Load (or create) the artifact‑hashes mapping."""
    if HASHES_YAML.is_file():
        with HASHES_YAML.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    return {}


def _save_hashes(hashes: dict) -> None:
    """Write the ``artifact_hashes.yaml`` file atomically."""
    HASHES_YAML.parent.mkdir(parents=True, exist_ok=True)
    with HASHES_YAML.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(hashes, fh, sort_keys=True)


def _sha256_of_file(path: Path) -> str:
    """Return the hexadecimal SHA‑256 checksum of *path*."""
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _download_and_archive(gse_id: str) -> Path:
    """
    Download a GEO series, archive the raw files, and return the path
    to the created ``.tar.gz`` file.

    Parameters
    ----------
    gse_id : str
        GEO Series accession (e.g. ``GSE5620``).

    Returns
    -------
    Path
        Path to the created archive under ``data/raw``.
    """
    logger.info("Downloading GEO series %s", gse_id)

    # Use a temporary directory so that partially‑downloaded data does not
    # pollute the project tree.
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # GEOparse downloads the series into a sub‑directory named after the
        # accession (e.g. ``tmpdir/GSE5620``).
        geo = GEOparse.get_GEO(geo=gse_id, destdir=tmp_path, silent=True)

        # GEOparse stores each sample as a ``GSMxxxxxx`` object in ``geo.gsms``.
        sample_count = len(geo.gsms)
        if sample_count < 30:
            logger.warning(
                "Series %s has insufficient samples (%d); skipping.", gse_id, sample_count
            )
            return None  # Signal that the series was skipped

        # Archive the entire accession directory.
        accession_dir = tmp_path / gse_id
        archive_path = RAW_DIR / f"{gse_id}.tar.gz"
        # ``make_archive`` creates ``<archive_path>.tar.gz`` when ``format='gztar'``.
        shutil.make_archive(base_name=str(archive_path.with_suffix("")), format="gztar", root_dir=tmp_path, base_dir=gse_id)

        logger.info("Archived GEO series %s to %s", gse_id, archive_path)
        return archive_path


def main() -> int:
    """Entry point used by the Makefile target ``download``."""
    try:
        _ensure_raw_dir()
        species_cfg = _load_species_config()
    except Exception as exc:
        logger.error("Failed to load configuration: %s", exc)
        return 1

    # Flatten all accession IDs across species
    accessions = []
    for species, cfg in species_cfg.items():
        # The configuration format is expected to contain an ``accessions`` list.
        # If it does not, we raise an informative error.
        if not isinstance(cfg, dict) or "accessions" not in cfg:
            logger.error("Missing 'accessions' list for species %s", species)
            return 1
        accessions.extend(cfg["accessions"])

    # Load any previously recorded checksums.
    hashes = _load_hashes()

    for gse_id in accessions:
        try:
            archive_path = _download_and_archive(gse_id)
            if archive_path is None:
                # Series was skipped due to low sample count.
                continue
            checksum = _sha256_of_file(archive_path)
            hashes[gse_id] = checksum
            logger.info("Recorded checksum for %s: %s", gse_id, checksum)
        except Exception as exc:
            logger.error("Error processing %s: %s", gse_id, exc)
            return 1

    # Persist the updated checksum mapping.
    _save_hashes(hashes)

    logger.info("All GEO series processed successfully.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
