"""
T012: Data Curation Pipeline for US1
Downloads Sentinel-2 imagery (via Microsoft Planetary Computer) and LiDAR data
(via OpenTopography), aligns them, filters by alignment error (< 2 m), and
writes manifests describing the raw downloads and the final aligned pairs.

The script can be run directly or imported. By default it attempts to collect
5 valid samples (useful for quick CI runs) but the target can be increased
with the ``--target-samples`` CLI argument (e.g. 500 for the full experiment).
"""

import argparse
import json
import logging
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from pyproj import Transformer

# External libraries – added to ``code/requirements.txt`` by this task
import planetary_computer
import rasterio
from pystac_client import Client
import laspy

# Project‑relative imports (the project already provides these utilities)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.alignment import (
    AlignmentError,
    calculate_alignment_error,
    validate_alignment_threshold,
    create_transformer,
    get_utm_zone,
    geo_to_utm,
)
from lib.config import load_environment_config, get_config
from lib.logging_config import setup_logging, get_logger
from lib.models import GroundTruthLiDAR, DegradedScene

# ----------------------------------------------------------------------
# Constants (can be overridden via CLI)
# ----------------------------------------------------------------------
DEFAULT_TARGET_SAMPLES = 5          # small default for CI; set to 500 for full run
ALIGNMENT_THRESHOLD_METERS = 2.0
BATCH_SIZE = 10
MAX_RETRIES_PER_BATCH = 3

# ----------------------------------------------------------------------
# Helper classes
# ----------------------------------------------------------------------
class DataDownloader:
    """
    Handles real download of Sentinel‑2 imagery and OpenTopography LiDAR.

    The implementation uses the Microsoft Planetary Computer STAC API for
    Sentinel‑2 and the OpenTopography API (exposed as a STAC catalog) for
    LiDAR point clouds.
    """

    SENTINEL_COLLECTION = "sentinel-2-l2a"
    LIDAR_COLLECTION = "opentopography"

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        # Planetary Computer client
        self.stac = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
        # OpenTopography STAC endpoint (public)
        self.lidar_stac = Client.open("https://opentopography.org/api/stac/v1")

    # ------------------------------------------------------------------
    # Sentinel‑2
    # ------------------------------------------------------------------
    def search_sentinel_tile(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Search for the most recent cloud‑free Sentinel‑2 tile that covers
        the supplied latitude/longitude. Returns the first matching STAC
        item dictionary or ``None`` if nothing is found.
        """
        try:
            # Simple 0.01 deg bounding box around the point
            bbox = [lon - 0.01, lat - 0.01, lon + 0.01, lat + 0.01]
            items = self.stac.search(
                collections=[self.SENTINEL_COLLECTION],
                bbox=bbox,
                datetime="2022-01-01/2023-12-31",
                limit=1,
            ).items()
            item = next(items, None)
            if item is None:
                self.logger.debug(f"No Sentinel‑2 item found for ({lat:.4f},{lon:.4f})")
                return None
            # Use planetarycomputer signing
            signed_item = planetary_computer.sign(item)
            return signed_item.to_dict()
        except Exception as e:
            self.logger.error(f"Sentinel‑2 search failed: {e}")
            return None

    def download_sentinel_asset(self, item: Dict, output_dir: Path) -> Path:
        """
        Downloads the ``B01`` (coastal aerosol) band (10 m resolution) as a
        GeoTIFF. Returns the path to the downloaded file.
        """
        asset = item["assets"]["B01"]
        href = asset["href"]
        out_path = output_dir / f"{item['id']}_B01.tif"
        self.logger.info(f"Downloading Sentinel‑2 asset to {out_path}")
        # rasterio can read directly from the signed URL
        with rasterio.open(href) as src:
            data = src.read()
            profile = src.profile
            profile.update(driver="GTiff")
            with rasterio.open(out_path, "w", **profile) as dst:
                dst.write(data)
        return out_path

    # ------------------------------------------------------------------
    # LiDAR
    # ------------------------------------------------------------------
    def search_lidar_tile(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Searches OpenTopography for a LiDAR tile that covers the point.
        Returns the first matching STAC item dictionary or ``None``.
        """
        try:
            bbox = [lon - 0.01, lat - 0.01, lon + 0.01, lat + 0.01]
            items = self.lidar_stac.search(
                collections=[self.LIDAR_COLLECTION],
                bbox=bbox,
                limit=1,
            ).items()
            item = next(items, None)
            if item is None:
                self.logger.debug(f"No LiDAR item found for ({lat:.4f},{lon:.4f})")
                return None
            signed_item = planetary_computer.sign(item)
            return signed_item.to_dict()
        except Exception as e:
            self.logger.error(f"LiDAR search failed: {e}")
            return None

    def download_lidar_asset(self, item: Dict, output_dir: Path) -> Path:
        """
        Downloads the point‑cloud asset (usually a .laz file) and returns
        the local path.
        """
        # The asset key varies across OpenTopography collections; we look
        # for the first asset with a ``.laz`` or ``.las`` extension.
        asset_key = None
        for key, asset in item["assets"].items():
            href = asset["href"]
            if href.lower().endswith((".laz", ".las")):
                asset_key = key
                break
        if asset_key is None:
            raise RuntimeError("No LiDAR point‑cloud asset found in item.")

        asset = item["assets"][asset_key]
        href = asset["href"]
        out_path = output_dir / f"{item['id']}{Path(href).suffix}"
        self.logger.info(f"Downloading LiDAR asset to {out_path}")
        # Use rasterio for remote read is not appropriate for .laz;
        # we stream via requests (built‑in in planetary_computer.sign)
        import requests

        with requests.get(href, stream=True) as r:
            r.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return out_path

# ----------------------------------------------------------------------
# Alignment helper
# ----------------------------------------------------------------------
class DataAligner:
    """
    Aligns a Sentinel‑2 tile and a LiDAR point cloud using their geographic
    centroids. The heavy‑lifting (e.g., ICP) is omitted – we only compute
    the residual distance between the two centroids after projecting both
    into a common UTM zone.
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def align_pair(
        self,
        sentinel_path: Path,
        lidar_path: Path,
        sentinel_meta: Dict,
    ) -> Tuple[bool, float, Dict]:
        """
        Returns ``(is_valid, residual_m, metadata)``.

        * ``is_valid`` – ``True`` if ``residual_m`` < ``ALIGNMENT_THRESHOLD_METERS``.
        * ``residual_m`` – Euclidean distance (in metres) between the two centroids.
        * ``metadata`` – dictionary with auxiliary information for the manifest.
        """
        try:
            # Extract geographic centre of the Sentinel tile from its geotransform
            with rasterio.open(sentinel_path) as src:
                transform = src.transform
                width, height = src.width, src.height
                # centre pixel coordinates
                cx = width / 2
                cy = height / 2
                lon, lat = transform * (cx, cy)

            # Load LiDAR points (LAS/LAZ) and compute centroid
            with laspy.open(lidar_path) as laz:
                points = laz.read().points
                xs = points["X"] * laz.header.x_scale + laz.header.x_offset
                ys = points["Y"] * laz.header.y_scale + laz.header.y_offset
                zs = points["Z"] * laz.header.z_scale + laz.header.z_offset
                lidar_centroid = np.array([xs.mean(), ys.mean(), zs.mean()])

            # Determine UTM zone from Sentinel centre
            utm_zone = get_utm_zone(lat, lon)
            crs_utm = f"EPSG:{32600 + utm_zone}"
            transformer = create_transformer("EPSG:4326", crs_utm)

            # Convert both centroids to UTM
            s_x, s_y = geo_to_utm(lat, lon, transformer)
            l_x, l_y = lidar_centroid[0], lidar_centroid[1]  # already in UTM
            residual = np.sqrt((s_x - l_x) ** 2 + (s_y - l_y) ** 2)

            is_valid = residual < ALIGNMENT_THRESHOLD_METERS
            meta = {
                "utm_zone": utm_zone,
                "sentinel_lat": lat,
                "sentinel_lon": lon,
                "lidar_centroid_x": l_x,
                "lidar_centroid_y": l_y,
                "centroid_offset_m": np.sqrt((s_x - l_x) ** 2 + (s_y - l_y) ** 2),
                "final_residual_m": residual,
                "sentinel_id": sentinel_meta["id"],
                "lidar_id": Path(lidar_path).stem,
            }
            return is_valid, residual, meta
        except Exception as e:
            self.logger.error(f"Alignment error: {e}")
            return False, float("inf"), {}

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main():
    """
    Entry point for the data‑curation pipeline.

    The script:
    1. Generates random urban coordinates (NYC, London, Tokyo).
    2. Downloads Sentinel‑2 imagery and LiDAR point clouds.
    3. Aligns them and keeps only pairs with residual < 2 m.
    4. Persists three CSV manifests:
         * ``raw_manifest.csv`` – every successful download.
         * ``aligned_pairs.csv`` – only the validated pairs.
         * ``alignment_report.csv`` – diagnostic information for *all* attempts.
    """
    parser = argparse.ArgumentParser(
        description="Data curation for US1 – download Sentinel‑2 and LiDAR, align, filter."
    )
    parser.add_argument(
        "--target-samples",
        type=int,
        default=DEFAULT_TARGET_SAMPLES,
        help="Number of valid aligned pairs to collect (default: %(default)s).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help="How many coordinate locations to try per loop iteration.",
    )
    parser.add_argument(
        "--max-retries-per-batch",
        type=int,
        default=MAX_RETRIES_PER_BATCH,
        help="Maximum consecutive empty batches before aborting.",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    config = load_environment_config()
    setup_logging()
    logger = get_logger("DataCuration")
    logger.info("Starting T012 – Data Curation Pipeline")

    downloader = DataDownloader(logger)
    aligner = DataAligner(logger)

    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    raw_manifest_path = processed_dir / "raw_manifest.csv"
    aligned_pairs_path = processed_dir / "aligned_pairs.csv"
    alignment_report_path = processed_dir / "alignment_report.csv"

    # ------------------------------------------------------------------
    # Containers for CSV rows
    # ------------------------------------------------------------------
    raw_manifest: List[Dict] = []
    aligned_pairs: List[Dict] = []
    alignment_report: List[Dict] = []

    valid_count = 0
    total_downloaded = 0
    retry_attempts = 0

    logger.info(
        f"Targeting {args.target_samples} valid samples (threshold {ALIGNMENT_THRESHOLD_METERS} m)."
    )

    # ------------------------------------------------------------------
    # Main retry loop
    # ------------------------------------------------------------------
    while valid_count < args.target_samples:
        batch_valid = 0
        logger.debug(
            f"Batch start – currently have {valid_count}/{args.target_samples} valid samples."
        )

        # Randomly chosen urban centres – small jitter added each iteration
        urban_coords = [
            (
                40.7128 + random.uniform(-0.05, 0.05),
                -74.0060 + random.uniform(-0.05, 0.05),
            ),  # NYC
            (
                51.5074 + random.uniform(-0.05, 0.05),
                -0.1278 + random.uniform(-0.05, 0.05),
            ),  # London
            (
                35.6762 + random.uniform(-0.05, 0.05),
                139.6503 + random.uniform(-0.05, 0.05),
            ),  # Tokyo
        ]

        for lat, lon in urban_coords:
            if valid_count >= args.target_samples:
                break

            # -----------------------------------------------------------
            # Sentinel‑2 download
            # -----------------------------------------------------------
            sentinel_item = downloader.search_sentinel_tile(lat, lon)
            if sentinel_item is None:
                logger.warning(f"No Sentinel‑2 tile for ({lat:.4f},{lon:.4f})")
                continue

            try:
                sentinel_path = downloader.download_sentinel_asset(
                    sentinel_item, raw_dir
                )
            except Exception as e:
                logger.error(f"Failed to download Sentinel‑2 asset: {e}")
                continue

            # -----------------------------------------------------------
            # LiDAR download
            # -----------------------------------------------------------
            lidar_item = downloader.search_lidar_tile(lat, lon)
            if lidar_item is None:
                logger.warning(f"No LiDAR tile for ({lat:.4f},{lon:.4f})")
                # Clean up the Sentinel file to avoid orphaned data
                sentinel_path.unlink(missing_ok=True)
                continue

            try:
                lidar_path = downloader.download_lidar_asset(lidar_item, raw_dir)
            except Exception as e:
                logger.error(f"Failed to download LiDAR asset: {e}")
                sentinel_path.unlink(missing_ok=True)
                continue

            total_downloaded += 1

            # -----------------------------------------------------------
            # Record raw manifest entry
            # -----------------------------------------------------------
            raw_manifest.append(
                {
                    "sentinel_id": sentinel_item["id"],
                    "lidar_id": Path(lidar_path).stem,
                    "lat": lat,
                    "lon": lon,
                    "sentinel_path": str(sentinel_path),
                    "lidar_path": str(lidar_path),
                    "status": "downloaded",
                }
            )

            # -----------------------------------------------------------
            # Alignment & validation
            # -----------------------------------------------------------
            is_valid, residual, meta = aligner.align_pair(
                sentinel_path, lidar_path, sentinel_item
            )

            if is_valid:
                valid_count += 1
                batch_valid += 1
                status = "aligned_valid"
                aligned_pairs.append(
                    {
                        "sentinel_id": sentinel_item["id"],
                        "lidar_id": Path(lidar_path).stem,
                        "lat": lat,
                        "lon": lon,
                        "sentinel_path": str(sentinel_path),
                        "lidar_path": str(lidar_path),
                        "utm_zone": meta["utm_zone"],
                        "residual_m": residual,
                    }
                )
            else:
                status = "aligned_invalid"

            alignment_report.append(
                {
                    "sentinel_id": sentinel_item["id"],
                    "lidar_id": Path(lidar_path).stem,
                    "lat": lat,
                    "lon": lon,
                    "sentinel_path": str(sentinel_path),
                    "lidar_path": str(lidar_path),
                    "status": status,
                    "residual_m": residual,
                    "utm_zone": meta.get("utm_zone", "N/A"),
                }
            )

            logger.debug(
                f"Processed {sentinel_item['id']}: {status} (residual {residual:.2f} m)."
            )

        # ---------------------------------------------------------------
        # Retry logic handling
        # ---------------------------------------------------------------
        if batch_valid == 0 and total_downloaded > 0:
            retry_attempts += 1
            logger.warning(
                f"Batch yielded 0 valid samples – retry attempt {retry_attempts}."
            )
            if retry_attempts > args.max_retries_per_batch:
                logger.critical(
                    "Maximum consecutive empty batches exceeded – aborting."
                )
                break
            time.sleep(1)  # back‑off before next batch
        else:
            retry_attempts = 0

        # Safety guard – prevents infinite loops during CI runs
        if total_downloaded > 5000 and valid_count == 0:
            logger.error(
                "Unable to obtain any valid samples after 5 000 attempts – exiting."
            )
            break

    # ------------------------------------------------------------------
    # Persist CSV manifests
    # ------------------------------------------------------------------
    logger.info(
        f"Curation finished – {valid_count} valid pairs out of {total_downloaded} downloads."
    )

    if raw_manifest:
        pd.DataFrame(raw_manifest).to_csv(raw_manifest_path, index=False)
        logger.info(f"Wrote raw manifest to {raw_manifest_path}")

    if aligned_pairs:
        pd.DataFrame(aligned_pairs).to_csv(aligned_pairs_path, index=False)
        logger.info(f"Wrote aligned pairs to {aligned_pairs_path}")

    if alignment_report:
        pd.DataFrame(alignment_report).to_csv(alignment_report_path, index=False)
        logger.info(f"Wrote alignment report to {alignment_report_path}")

    # ------------------------------------------------------------------
    # Summary JSON (useful for downstream steps)
    # ------------------------------------------------------------------
    summary = {
        "total_downloaded": total_downloaded,
        "valid_samples": valid_count,
        "target_samples": args.target_samples,
        "alignment_threshold_m": ALIGNMENT_THRESHOLD_METERS,
    }
    logger.info("Run summary: " + json.dumps(summary))

    # Exit with non‑zero status if we failed to meet the target – CI can catch this.
    if valid_count < args.target_samples:
        logger.error(
            f"Failed to reach target of {args.target_samples} valid samples."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
