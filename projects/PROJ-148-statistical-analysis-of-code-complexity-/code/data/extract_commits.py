"""Extract Java source files and commit‑like metadata from downloaded archives.

This script is part of the US1 data acquisition pipeline. It looks for
archive files (ZIP or TAR.GZ) in ``data/raw/`` (the output directory of
``code/data/download_gh.py``), extracts them to a temporary location,
walks the extracted tree for ``*.java`` source files and creates a CSV
``data/commits.csv`` containing:

- ``project``: name of the original archive (without extension)
- ``file_path``: path of the Java file relative to the extracted project root
- ``commit_hash``: SHA‑256 hash of the file contents (used as a stand‑in for a VCS hash)
- ``file_size``: size of the file in bytes
- ``modified_time``: ISO‑8601 timestamp of the file's last modification time
"""
from __future__ import annotations

import csv
import hashlib
import logging
import os
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

import pandas as pd

# Local utilities
from utils.logging import get_logger

logger = get_logger(__name__)

SUPPORTED_ARCHIVE_SUFFIXES = {".zip", ".tar.gz", ".tgz"}

def _hash_file(path: Path) -> str:
    """Return a SHA‑256 hex digest of the file contents."""
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def _iter_archive_paths(root: Path) -> Iterable[Path]:
    """Yield archive files under *root* that have a supported suffix."""
    for entry in root.iterdir():
        if entry.is_file() and any(entry.name.lower().endswith(s) for s in SUPPORTED_ARCHIVE_SUFFIXES):
            yield entry

def _extract_archive(archive_path: Path, destination: Path) -> None:
    """Extract *archive_path* into *destination*.

    Currently only ZIP archives are supported; other formats raise a
    ``RuntimeError`` so that the pipeline can fail fast.
    """
    if archive_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(destination)
    else:
        raise RuntimeError(f"Unsupported archive format: {archive_path}")

def _collect_java_files(project_root: Path) -> List[Path]:
    """Return a list of all ``*.java`` files under *project_root*."""
    return [p for p in project_root.rglob("*.java") if p.is_file()]

def _record_file_metadata(
    project_name: str,
    file_path: Path,
    project_root: Path,
) -> dict:
    """Create a metadata dictionary for a single Java file."""
    rel_path = file_path.relative_to(project_root).as_posix()
    stat = file_path.stat()
    modified_dt = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
    return {
        "project": project_name,
        "file_path": rel_path,
        "commit_hash": _hash_file(file_path),
        "file_size": stat.st_size,
        "modified_time": modified_dt.isoformat(),
    }

def extract_commits(
    raw_dir: Path = Path("data/raw"),
    output_csv: Path = Path("data/commits.csv"),
    keep_extracted: bool = False,
) -> pd.DataFrame:
    """Extract Java files from archives and write a CSV of metadata.

    Parameters
    ----------
    raw_dir: Path
        Directory containing downloaded project archives.
    output_csv: Path
        Destination CSV file that will contain the collected metadata.
    keep_extracted: bool, default ``False``
        If ``True``, the extracted project directories are left on disk
        under ``data/extracted/``; otherwise they are removed after processing.

    Returns
    -------
    pandas.DataFrame
        Dataframe with one row per discovered Java source file.
    """
    raw_dir = Path(raw_dir)
    output_csv = Path(output_csv)

    if not raw_dir.is_dir():
        logger.error("Raw data directory %s does not exist.", raw_dir)
        raise FileNotFoundError(raw_dir)

    logger.info("Scanning %s for archives …", raw_dir)
    records: List[dict] = []

    # Temporary directory for extraction (or a persistent one if requested)
    base_extracted_dir = Path("data/extracted")
    base_extracted_dir.mkdir(parents=True, exist_ok=True)

    for archive_path in _iter_archive_paths(raw_dir):
        project_name = archive_path.stem
        logger.info("Processing archive %s (project: %s)", archive_path.name, project_name)

        # Choose extraction destination
        if keep_extracted:
            extract_dir = base_extracted_dir / project_name
            extract_dir.mkdir(parents=True, exist_ok=True)
        else:
            extract_dir = Path(tempfile.mkdtemp(prefix=f"{project_name}_"))

        try:
            _extract_archive(archive_path, extract_dir)
        except Exception as exc:
            logger.warning("Failed to extract %s: %s – skipping.", archive_path, exc)
            continue

        java_files = _collect_java_files(extract_dir)
        logger.debug("Found %d Java files in project %s.", len(java_files), project_name)

        for jf in java_files:
            records.append(_record_file_metadata(project_name, jf, extract_dir))

        # Clean up temporary extraction directory unless the user asked to keep it
        if not keep_extracted:
            shutil.rmtree(extract_dir, ignore_errors=True)

    if not records:
        logger.warning("No Java files were discovered in any archive.")
        df = pd.DataFrame(columns=[
            "project", "file_path", "commit_hash", "file_size", "modified_time"
        ])
    else:
        df = pd.DataFrame.from_records(records)

    # Ensure output directory exists
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    logger.info("Wrote %d records to %s.", len(df), output_csv)

    return df

def _setup_logging() -> None:
    """Configure a basic console logger if the root logger has no handlers."""
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s – %(message)s",
            stream=sys.stderr,
        )

def main() -> None:
    _setup_logging()
    # Default locations follow the conventions used by other pipeline steps.
    extract_commits()

if __name__ == "__main__":
    main()
