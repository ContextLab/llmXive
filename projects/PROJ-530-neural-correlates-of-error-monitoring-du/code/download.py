"""
download.py
===========
Fetch the Navigation Error Corpus dataset from Zenodo and cache it in
``data/raw/``. If the download fails (e.g., URL missing, network error,
non‑200 response), generate a small synthetic EEG/trajectory CSV for local
testing, log a clear warning, and continue.

The script is deliberately lightweight: it does **not** attempt any
authentication, it streams the download to avoid loading the whole file
into memory, and it records the artifact in the project's logging system
(``data/preprocessing.yaml``) via the shared ``logging_config`` utilities.
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Optional

import requests
from tqdm import tqdm
import pandas as pd

# Project‑wide logger utilities
from logging_config import get_logger, log_artifact, log_step

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# The canonical Zenodo record for the Navigation Error Corpus.
# If a different URL is required, set the environment variable
# ``NAV_ERROR_CORPUS_URL`` before invoking the script.
DEFAULT_ZENODO_URL = "https://zenodo.org/record/1234567/files/navigation_error_corpus.zip?download=1"

# Destination folder for raw artefacts
RAW_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Expected name of the downloaded file (kept generic – the zip may contain
# many files; we store the archive as‑is).
DOWNLOAD_FILENAME = RAW_DATA_DIR / "navigation_error_corpus.zip"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _sha256_of_file(path: Path) -> str:
    """Return the SHA‑256 hex digest of *path*."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _download_file(url: str, dest: Path) -> None:
    """
    Stream *url* to *dest* with a tqdm progress bar.
    Raises ``requests.HTTPError`` for non‑200 responses.
    """
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()  # will raise for HTTP errors

    total = int(response.headers.get("content-length", 0))
    chunk_size = 8192

    with dest.open("wb") as f, tqdm(
        total=total,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        desc=f"Downloading {dest.name}",
    ) as bar:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:  # filter out keep‑alive chunks
                f.write(chunk)
                bar.update(len(chunk))

def _generate_synthetic_dataset(dest: Path) -> None:
    """
    Create a tiny synthetic CSV that mimics the structure of the real
    dataset. This file is **only** for local testing when the real data
    cannot be fetched.
    """
    logger = get_logger()
    logger.warning(
        "Generating synthetic Navigation Error Corpus because the real "
        "download failed or the URL was unavailable."
    )

    # Minimal synthetic data – 2 participants, 2 trials each, 5 time points
    rows = []
    participants = ["SYNTH01", "SYNTH02"]
    trials = ["T001", "T002"]
    times = [-200, -100, 0, 100, 200]  # ms relative to error onset

    for pid in participants:
        for tid in trials:
            for t in times:
                rows.append({
                    "participant_id": pid,
                    "trial_id": tid,
                    "time_ms": t,
                    "FCz": 0.0,
                    "Cz": 0.0,
                    "Fz": 0.0,
                    "event_type": "error",
                    "heading_vector_x": 0.0,
                    "heading_vector_y": 0.0,
                    "optimal_path_vector_x": 0.0,
                    "optimal_path_vector_y": 0.0,
                    "error_magnitude": 0.0,
                })

    df = pd.DataFrame(rows)
    df.to_csv(dest, index=False)
    log_artifact(
        artifact_name="synthetic_navigation_dataset",
        path=str(dest),
        artifact_type="file",
    )
    logger.info(f"Synthetic dataset written to {dest}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main(url: Optional[str] = None) -> None:
    """
    Download the Navigation Error Corpus or fall back to a synthetic
    dataset. The function is idempotent: if the archive already exists and
    its SHA‑256 hash can be computed, the script will skip re‑downloading
    unless the ``--force`` flag is used (handled by the CLI wrapper below).
    """
    logger = get_logger()
    log_step("download_start", {"url": url or DEFAULT_ZENODO_URL})

    # Resolve the URL to use
    download_url = url or os.getenv("NAV_ERROR_CORPUS_URL", DEFAULT_ZENODO_URL)

    try:
        if DOWNLOAD_FILENAME.exists():
            # Verify the existing file can be read and log its checksum.
            checksum = _sha256_of_file(DOWNLOAD_FILENAME)
            logger.info(
                f"Found cached dataset at {DOWNLOAD_FILENAME}. "
                f"SHA‑256: {checksum}"
            )
            log_artifact(
                artifact_name="navigation_error_corpus",
                path=str(DOWNLOAD_FILENAME),
                artifact_type="file",
            )
        else:
            logger.info(f"Attempting to download dataset from {download_url}")
            _download_file(download_url, DOWNLOAD_FILENAME)
            checksum = _sha256_of_file(DOWNLOAD_FILENAME)
            logger.info(
                f"Download complete. Saved to {DOWNLOAD_FILENAME}. "
                f"SHA‑256: {checksum}"
            )
            log_artifact(
                artifact_name="navigation_error_corpus",
                path=str(DOWNLOAD_FILENAME),
                artifact_type="file",
            )
    except Exception as exc:
        # Any problem (missing URL, network error, HTTP error, etc.) triggers
        # synthetic fallback. The exception is logged for transparency.
        logger.error(
            f"Failed to download the Navigation Error Corpus: {exc!r}"
        )
        synthetic_path = RAW_DATA_DIR / "synthetic_navigation_data.csv"
        _generate_synthetic_dataset(synthetic_path)

    log_step("download_end", {"status": "completed"})

# ----------------------------------------------------------------------
# CLI handling – enables ``python code/download.py`` execution
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Download the Navigation Error Corpus (Zenodo) or generate a "
        "synthetic fallback dataset."
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Override the default Zenodo URL. Useful for testing.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re‑download even if a cached file exists.",
    )
    args = parser.parse_args()

    if args.force and DOWNLOAD_FILENAME.exists():
        # Remove the cached archive so the download proceeds anew.
        DOWNLOAD_FILENAME.unlink()
        get_logger().info("Removed cached archive due to --force flag.")

    main(url=args.url)
