"""
Ingestion script for the Predicting Avian Song Variation project.

This script downloads the verified ``analysis_dataset.parquet`` file from
HuggingFace, records its SHA‑256 checksum, updates ``data/checksums.txt`` and
registers the artifact in the project state file. It also optionally detects
the Coordinate Reference System (CRS) of a user‑supplied climate raster and,
if necessary, reprojects it to EPSG:4326.

Additionally, helper functions required by the test suite are provided:
- ``haversine_distance`` – compute great‑circle distance between two lat/lon
  points.
- ``perform_spatial_join`` – join song records with climate records based on
  a maximum radius (kilometres).
- ``save_processed_data`` – write the joined data to CSV, update the
  checksum file and log the operation.

Usage
-----
``python code/ingestion.py --download-only [--raster /path/to/raster.tif]``

The ``--download-only`` flag is the default behaviour; it can be omitted
when the script is invoked without additional sub‑commands.
"""

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict

import pandas as pd
import requests
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from llmxive_toolkit import paths, get_logger

# Local utilities
from utils import _update_state_file

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DOWNLOAD_URL = (
    "https://huggingface.co/datasets/Onuii/analysis_dataset/resolve/main/data/"
    "train-00000-of-00005.parquet"
)
FILE_NAME = "analysis_dataset.parquet"
CHECKSUMS_FILE = paths.data("checksums.txt")
RAW_DATA_PATH = paths.data("raw", FILE_NAME)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def setup_logging() -> logging.Logger:
    """Configure a module‑level logger."""
    logger = get_logger(__name__, log_file="logs/ingestion.log")
    logger.setLevel(logging.INFO)
    return logger

def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA‑256 hash of *file_path*."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def download_file(url: str, dest: Path, logger: logging.Logger) -> None:
    """Download *url* to *dest* using streaming; raise on failure."""
    logger.info("Downloading %s → %s", url, dest)
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    logger.info("Download completed.")

def append_checksum(
    checksums_path: Path, filename: str, checksum: str, logger: logging.Logger
) -> None:
    """Append a checksum line to ``checksums.txt`` (create file if missing)."""
    logger.info("Recording checksum for %s", filename)
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    line = f"{filename}  {checksum}\n"
    # Avoid duplicate entries
    if checksums_path.is_file():
        with checksums_path.open("r") as f:
            if any(line.strip().startswith(filename) for line in f):
                logger.info("Checksum for %s already recorded.", filename)
                return
    with checksums_path.open("a") as f:
        f.write(line)
    logger.info("Checksum recorded.")

def detect_raster_crs(raster_path: Path, logger: logging.Logger) -> rasterio.crs.CRS:
    """
    Detect and return the CRS of a raster file.

    Parameters
    ----------
    raster_path : Path
        Path to the raster (e.g., a GeoTIFF) supplied by the user.
    logger : logging.Logger
        Logger used for reporting.

    Returns
    -------
    rasterio.crs.CRS
        The CRS object (may be ``None`` if undefined).
    """
    if not raster_path.is_file():
        logger.error("Raster file not found: %s", raster_path)
        raise FileNotFoundError(f"Raster file not found: {raster_path}")

    try:
        with rasterio.open(raster_path) as src:
            crs = src.crs
            if crs:
                logger.info(
                    "Detected CRS for %s: %s", raster_path.name, crs.to_string()
                )
            else:
                logger.warning("Raster %s has no CRS defined.", raster_path.name)
            return crs
    except Exception as exc:
        logger.error("Failed to read raster %s: %s", raster_path, exc)
        raise

def reproject_raster(
    raster_path: Path,
    target_crs: str = "EPSG:4326",
    logger: logging.Logger = None,
) -> Path:
    """
    Reproject a raster to ``target_crs`` (default EPSG:4326).

    The function overwrites the original file with the reprojected version.
    If you need to keep the original, copy it before calling.

    Parameters
    ----------
    raster_path : Path
        Path to the source raster.
    target_crs : str
        Target CRS identifier (e.g., "EPSG:4326").
    logger : logging.Logger, optional
        Logger for status messages.

    Returns
    -------
    Path
        Path to the reprojected raster (same as ``raster_path``).
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.info("Reprojecting %s to %s", raster_path.name, target_crs)

    with rasterio.open(raster_path) as src:
        src_crs = src.crs
        if src_crs is None:
            raise ValueError(f"Source raster {raster_path} has undefined CRS.")

        if src_crs.to_string() == target_crs:
            logger.info("Raster already in target CRS; no reprojection needed.")
            return raster_path

        transform, width, height = calculate_default_transform(
            src_crs, target_crs, src.width, src.height, *src.bounds
        )
        kwargs = src.meta.copy()
        kwargs.update(
            {
                "crs": target_crs,
                "transform": transform,
                "width": width,
                "height": height,
            }
        )

        # Write to a temporary file first to avoid data loss on failure
        tmp_path = raster_path.with_suffix(".tmp.tif")
        with rasterio.open(tmp_path, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src_crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=Resampling.nearest,
                )

        # Replace original file with reprojected version
        tmp_path.replace(raster_path)
        logger.info("Reprojection completed and saved to %s", raster_path)

    return raster_path

def validate_merge(df: pd.DataFrame, logger: logging.Logger) -> None:
    """
    Validate the quality of the pre‑merged dataset.

    Checks the ``match_status`` column (should be ``matched`` for all rows)
    and computes the proportion of matched rows. If more than 5 % of rows
    are mismatched the function raises a RuntimeError.

    The resulting ``match_rate`` (float between 0 and 1) is written to
    ``outputs/merge_validation.json``.
    """
    total_rows = len(df)
    if total_rows == 0:
        logger.error("The analysis dataset is empty.")
        raise RuntimeError("Empty analysis dataset.")

    # Rows where match_status is not 'matched' are considered mismatched.
    mismatched_mask = df.get("match_status") != "matched"
    mismatched_count = int(mismatched_mask.sum())
    match_rate = (total_rows - mismatched_count) / total_rows

    logger.info(
        "Merge validation: %d mismatched rows out of %d total (%.2f%% mismatched).",
        mismatched_count,
        total_rows,
        (mismatched_count / total_rows) * 100,
    )

    if mismatched_count / total_rows > 0.05:
        logger.error(
            "More than 5%% of rows are mismatched (%.2f%%). Aborting.",
            (mismatched_count / total_rows) * 100,
        )
        raise RuntimeError("Merge validation failed: >5% mismatched rows.")

    # Write the match_rate to the designated JSON file.
    out_path = paths.outputs("merge_validation.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump({"match_rate": match_rate}, f, ensure_ascii=False, indent=2)

    logger.info("Merge validation result written to %s", out_path)

# ----------------------------------------------------------------------
# Helper utilities required by the test suite
# ----------------------------------------------------------------------
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute the great‑circle distance between two points on the Earth
    (specified in decimal degrees) using the Haversine formula.
    Returns distance in kilometres.
    """
    # Earth radius in kilometres
    R = 6371.0

    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)

    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

def perform_spatial_join(
    song_data: List[Dict],
    climate_data: List[Dict],
    max_radius_km: float = 100.0,
) -> List[Dict]:
    """
    Very lightweight spatial join used by the test suite.
    For each song record, the first climate record within ``max_radius_km``
    is merged into the song dict. If none are found, the song record is
    dropped.
    """
    joined = []
    for song in song_data:
        s_lat = float(song["lat"])
        s_lon = float(song["lon"])
        match = None
        for clim in climate_data:
            c_lat = float(clim["lat"])
            c_lon = float(clim["lon"])
            if haversine_distance(s_lat, s_lon, c_lat, c_lon) <= max_radius_km:
                match = clim
                break
        if match:
            merged = {**song, **match}
            joined.append(merged)
    return joined

def save_processed_data(
    data: List[Dict],
    output_path: Path,
    logger: logging.Logger,
) -> None:
    """
    Write ``data`` (a list of dictionaries) to ``output_path`` as CSV,
    compute its SHA‑256 checksum and append the checksum line to the
    checksums file.
    """
    if not data:
        logger.warning("No data to save.")
        return

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    fieldnames = list(data[0].keys())
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    logger.info("Processed data written to %s", output_path)

    # Compute checksum and record it
    checksum = calculate_sha256(output_path)
    append_checksum(CHECKSUMS_FILE, output_path.name, checksum, logger)

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    logger = setup_logging()
    parser = argparse.ArgumentParser(
        description=(
            "Download and register the verified AnalysisDataset, optionally "
            "detect/reproject a user‑supplied climate raster, and validate the "
            "merge quality."
        )
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Only download the dataset and record its checksum.",
    )
    parser.add_argument(
        "--raster",
        type=Path,
        default=None,
        help=(
            "Path to an optional user‑supplied climate raster (e.g., GeoTIFF). "
            "If provided, the script will detect its CRS and reproject to EPSG:4326 "
            "when necessary."
        ),
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Step 1 – download the parquet file
    # ------------------------------------------------------------------
    try:
        download_file(DOWNLOAD_URL, RAW_DATA_PATH, logger)
    except Exception as exc:
        logger.error("Failed to download file: %s", exc)
        raise

    # ------------------------------------------------------------------
    # Step 2 – compute SHA‑256 checksum
    # ------------------------------------------------------------------
    checksum = calculate_sha256(RAW_DATA_PATH)
    logger.info("SHA‑256 checksum: %s", checksum)

    # ------------------------------------------------------------------
    # Step 3 – record checksum
    # ------------------------------------------------------------------
    append_checksum(CHECKSUMS_FILE, FILE_NAME, checksum, logger)

    # ------------------------------------------------------------------
    # Step 4 – update project state (artifact hash tracking)
    # ------------------------------------------------------------------
    try:
        _update_state_file(str(RAW_DATA_PATH))
        logger.info("Project state file updated.")
    except Exception as exc:
        logger.warning("State update failed (non‑critical): %s", exc)

    # ------------------------------------------------------------------
    # Step 5 – load the dataset and validate the merge
    # ------------------------------------------------------------------
    try:
        df = pd.read_parquet(RAW_DATA_PATH)
        logger.info("Loaded analysis dataset with %d rows.", len(df))
    except Exception as exc:
        logger.error("Failed to read parquet file %s: %s", RAW_DATA_PATH, exc)
        raise

    # Perform merge‑validation as required by T018
    validate_merge(df, logger)

    # ------------------------------------------------------------------
    # Step 6 – optional CRS detection & reprojection for a user‑supplied raster
    # ------------------------------------------------------------------
    if args.raster:
        logger.info("User supplied raster detected: %s", args.raster)
        crs = detect_raster_crs(args.raster, logger)
        if crs is None:
            logger.error("Cannot reproject raster without a defined CRS.")
            raise ValueError("Raster has undefined CRS.")
        if crs.to_string() != "EPSG:4326":
            # Reproject and overwrite the original raster
            reproject_raster(args.raster, target_crs="EPSG:4326", logger=logger)
        else:
            logger.info("Raster CRS is already EPSG:4326; no reprojection needed.")
    else:
        logger.info("No user‑supplied raster provided; skipping CRS detection.")

    logger.info("Ingestion step completed successfully.")

if __name__ == "__main__":
    sys.exit(main())
