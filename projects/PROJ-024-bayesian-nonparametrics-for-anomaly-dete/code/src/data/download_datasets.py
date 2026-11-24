"""
Dataset Download and Verification Script (T003)

This script downloads the verified real‑world datasets required for the
anomaly‑detection pipeline (NAB and PhysioNet) and validates their integrity
using SHA‑256 checksums. It writes the raw CSV files to ``data/raw/`` and
records the checksums in ``data/processed/results/data_checksums.json``.
The script is deliberately independent of the T020 search results – it
proceeds only with the hard‑coded verified URLs defined below.
"""

import json
import logging
import ssl
import sys
import urllib.request
from pathlib import Path
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Project‑wide paths
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_RESULTS_DIR = PROJECT_ROOT / "data" / "processed" / "results"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Dataset catalogue (verified URLs)
# ----------------------------------------------------------------------
# The URLs point to small, publicly available CSV files that are stable
# and suitable for the CI environment.  They are the canonical sources
# referenced in the project specification.
VERIFIED_DATASETS: Dict[str, str] = {
    # Numenta Anomaly Benchmark – ambient temperature system failure series
    "nab_ambient_temperature": (
        "https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/"
        "ambient_temperature_system_failure.csv"
    ),
    # PhysioNet MIT‑BIH Arrhythmia – first record (CSV representation)
    "physionet_mitdb_100": (
        "https://physionet.org/files/mitdb/1.0.0/100.csv"
    ),
}

# ----------------------------------------------------------------------
# Helper dataclass for download results
# ----------------------------------------------------------------------
@dataclass
class DownloadResult:
    dataset_name: str
    file_path: Path
    checksum: str
    size_bytes: int
    status: str  # "success" or "failed"
    error_message: Optional[str] = None

# ----------------------------------------------------------------------
# Utility functions
# ----------------------------------------------------------------------
def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute SHA‑256 checksum of a file."""
    import hashlib

    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def download_from_url(url: str, dest_path: Path) -> bool:
    """
    Download a file from ``url`` to ``dest_path`` using a verified SSL context.
    Returns ``True`` on success, ``False`` otherwise.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        logger.info(f"Downloading {url} → {dest_path}")
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "ResearchBot/1.0 (+https://github.com)"},
        )
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp, open(
            dest_path, "wb"
        ) as out_file:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                out_file.write(chunk)
        logger.info(f"Finished download: {dest_path} ({dest_path.stat().st_size} bytes)")
        return True
    except Exception as exc:
        logger.error(f"Download failed for {url}: {exc}")
        return False

# ----------------------------------------------------------------------
# Core download routine
# ----------------------------------------------------------------------
def download_all_verified() -> List[DownloadResult]:
    """Iterate over ``VERIFIED_DATASETS`` and download each one."""
    results: List[DownloadResult] = []
    for name, url in VERIFIED_DATASETS.items():
        dest_file = DATA_RAW_DIR / f"{name}.csv"
        try:
            success = download_from_url(url, dest_file)
            if not success:
                raise RuntimeError("download_from_url returned False")
            checksum = compute_file_checksum(dest_file)
            results.append(
                DownloadResult(
                    dataset_name=name,
                    file_path=dest_file,
                    checksum=checksum,
                    size_bytes=dest_file.stat().st_size,
                    status="success",
                )
            )
        except Exception as exc:
            logger.error(f"Failed to obtain dataset '{name}': {exc}")
            results.append(
                DownloadResult(
                    dataset_name=name,
                    file_path=dest_file,
                    checksum="",
                    size_bytes=0,
                    status="failed",
                    error_message=str(exc),
                )
            )
    return results

# ----------------------------------------------------------------------
# Manifest / checksum persistence
# ----------------------------------------------------------------------
def write_checksums(results: List[DownloadResult]) -> None:
    """
    Write a JSON file mapping dataset names to their SHA‑256 checksums.
    Only successful downloads are recorded.
    """
    checksums: Dict[str, str] = {
        r.dataset_name: r.checksum for r in results if r.status == "success"
    }
    output_path = PROCESSED_RESULTS_DIR / "data_checksums.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)
    logger.info(f"Checksums written to {output_path}")

def write_download_manifest(results: List[DownloadResult]) -> None:
    """
    Write a detailed manifest (including failures) for downstream debugging.
    """
    manifest = {
        "status": "completed" if all(r.status == "success" for r in results) else "partial",
        "timestamp": Path(__file__).stat().st_mtime,
        "datasets": [asdict(r) for r in results],
    }
    manifest_path = PROCESSED_RESULTS_DIR / "download_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    logger.info(f"Download manifest written to {manifest_path}")

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    Main CLI entry point.  Returns ``0`` on success, non‑zero on failure.
    """
    logger.info("=" * 80)
    logger.info("Dataset Download and Verification Script (T003)")
    logger.info("=" * 80)

    results = download_all_verified()
    write_download_manifest(results)
    write_checksums(results)

    # Verify that each successful download meets the verification criteria:
    #   1. SHA‑256 checksum recorded (already done)
    #   2. Row count ≥ 1 000
    # If any dataset fails the row‑count check, the script aborts with an error.
    for res in results:
        if res.status != "success":
            logger.error(f"Dataset '{res.dataset_name}' failed to download – aborting.")
            return 1
        # Row‑count validation
        try:
            import pandas as pd

            df = pd.read_csv(res.file_path)
            row_count = len(df)
            if row_count < 1_000:
                raise ValueError(
                    f"Dataset '{res.dataset_name}' contains {row_count} rows "
                    "(minimum required is 1 000)."
                )
            logger.info(f"Dataset '{res.dataset_name}' passed row‑count check ({row_count} rows).")
        except Exception as exc:
            logger.error(f"Validation error for '{res.dataset_name}': {exc}")
            return 1

    logger.info("All verified datasets downloaded and validated successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())