"""
extract_archive.py
------------------
Implements Task **T004c-extract**: given a downloaded file (potentially a
compressed archive) from the Zenodo record, extract its contents, locate the
relevant ``*.csv`` file, and return the absolute path to that CSV.

The script is deliberately lightweight – it does **not** rename or move the
CSV to the canonical location ``data/raw/barrier_dataset.csv``. That step
belongs to the subsequent *normalize* task (T004c‑normalize).  The function
can be used programmatically or via the simple CLI provided at the bottom
of the file.

The implementation mirrors the extraction logic already present in
``code/fetch_data.py`` to guarantee consistent behaviour across the
pipeline.
"""

import argparse
import logging
import sys
import tarfile
import zipfile
import shutil
from pathlib import Path
from typing import List

# ----------------------------------------------------------------------
# Helper functions (mirrored from ``fetch_data.py``)
# ----------------------------------------------------------------------


def _setup_logger(log_file: Path) -> logging.Logger:
    """Create a logger that writes to *log_file* and also echoes to stdout."""
    logger = logging.getLogger("extract_archive")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # File handler
    fh = logging.FileHandler(log_file, mode="a")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Stream handler (stdout)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    return logger


def _extract_tarball(tar_path: Path, dest_dir: Path, logger: logging.Logger) -> List[Path]:
    """Extract a ``.tar`` / ``.tar.gz`` / ``.tgz`` archive."""
    logger.info(f"Extracting tarball: {tar_path}")
    extracted: List[Path] = []
    with tarfile.open(tar_path, "r:*") as tar:
        tar.extractall(path=dest_dir)
        for member in tar.getmembers():
            if not member.isdir():
                extracted.append(dest_dir / member.name)
    logger.info(f"Extracted {len(extracted)} files from tarball.")
    return extracted


def _extract_zipball(zip_path: Path, dest_dir: Path, logger: logging.Logger) -> List[Path]:
    """Extract a ``.zip`` archive."""
    logger.info(f"Extracting zipball: {zip_path}")
    extracted: List[Path] = []
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(dest_dir)
        for info in zip_ref.infolist():
            if not info.is_dir():
                extracted.append(dest_dir / info.filename)
    logger.info(f"Extracted {len(extracted)} files from zipball.")
    return extracted


def _select_csv_from_directory(search_dir: Path, logger: logging.Logger) -> Path:
    """
    Locate the CSV that contains the experimental barrier data.

    Preference order:
    1. Any ``*barrier*.csv`` (case‑insensitive) – the largest one if several.
    2. Otherwise the largest ``*.csv`` file.
    """
    csv_files = list(search_dir.rglob("*.csv"))
    if not csv_files:
        raise FileNotFoundError("No CSV files found after extraction.")

    # Prefer files whose name contains the word “barrier”
    barrier_matches = [p for p in csv_files if "barrier" in p.name.lower()]
    if barrier_matches:
        chosen = max(barrier_matches, key=lambda p: p.stat().st_size)
        logger.info(f"Selected CSV (pattern match): {chosen.name}")
        return chosen

    # Fallback: the largest CSV file
    chosen = max(csv_files, key=lambda p: p.stat().st_size)
    logger.info(f"No pattern match – selected largest CSV: {chosen.name}")
    return chosen


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def extract_archive(archive_path: Path, logger: logging.Logger) -> Path:
    """
    Extract *archive_path* (which may be an archive or a plain CSV) and
    return the absolute path to the selected CSV file.

    The function creates a temporary directory, extracts the archive (if
    needed), locates the appropriate CSV using the same rules as the
    original ``fetch_data`` implementation, and finally returns the CSV
    path.  The temporary directory is cleaned up automatically on exit.

    Parameters
    ----------
    archive_path: Path
        Path to the downloaded file (could be ``.zip``, ``.tar.gz``, ``.gz``,
        ``.tar`` or an already‑uncompressed ``.csv``).
    logger: logging.Logger
        Logger used for status messages.

    Returns
    -------
    Path
        Absolute path to the CSV file that contains the barrier dataset.
    """
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    # If the file is already a CSV we can skip extraction entirely.
    if archive_path.suffix.lower() == ".csv":
        logger.info(f"Provided file is a CSV – no extraction needed: {archive_path.name}")
        return archive_path.resolve()

    # Otherwise we need to extract.
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        if archive_path.suffix.lower() == ".zip":
            extracted = _extract_zipball(archive_path, tmp_path, logger)
        elif archive_path.suffixes[-2:] == [".tar", ".gz"] or archive_path.suffix.lower() == ".tgz":
            extracted = _extract_tarball(archive_path, tmp_path, logger)
        elif archive_path.suffix.lower() == ".gz":
            # ``gzip`` files that are not tarballs are handled by the tarfile
            # module in “r:gz” mode – it will raise if the file isn’t a tar.
            extracted = _extract_tarball(archive_path, tmp_path, logger)
        else:
            raise ValueError(f"Unsupported archive type: {archive_path}")

        # Locate the CSV inside the temporary extraction directory.
        selected_csv = _select_csv_from_directory(tmp_path, logger)

        # Return the absolute path (the temporary directory will still exist
        # until the context manager exits, but callers typically copy the file
        # immediately after receiving the path).
        return selected_csv.resolve()


# ----------------------------------------------------------------------
# CLI entry point (convenient for manual debugging)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract a Zenodo archive and locate the barrier CSV."
    )
    parser.add_argument(
        "archive",
        type=Path,
        help="Path to the downloaded archive (or CSV).",
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=Path("logs") / "extract_archive.log",
        help="Path to the log file.",
    )

    args = parser.parse_args()

    # Ensure the log directory exists
    args.log.parent.mkdir(parents=True, exist_ok=True)
    log = _setup_logger(args.log)

    try:
        csv_path = extract_archive(args.archive, log)
        log.info(f"Extraction complete – CSV located at: {csv_path}")
        print(csv_path)  # Echo to stdout for easy piping
    except Exception as exc:
        log.error(f"Extraction failed: {exc}")
        sys.exit(1)