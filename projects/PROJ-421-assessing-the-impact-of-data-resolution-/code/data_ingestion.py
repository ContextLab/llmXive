"""
Data Ingestion Module for NLCD Colorado Subset.

Downloads the 30 m NLCD raster (national file) from a verified public URL,
extracts the GeoTIFF, and writes it to ``data/raw/`` along with a JSON
metadata file conforming to ``dataset.schema.yaml``.
"""
import sys
import logging
import zipfile
from pathlib import Path
import shutil

import requests
from tqdm import tqdm

# Import configuration and utilities from the project
from config import (
    NLCD_URL,
    NLCD_OUTPUT_FILENAME,
    NLCD_METADATA_FILENAME,
    DATA_RAW_DIR,
    NLCD_EXPECTED_CHECKSUM,
    LOG_LEVEL,
)
from utils import (
    get_logger,
    setup_logging,
    checksum_file,
    retry_with_backoff,
    RetryError,
)

logger = get_logger(__name__)

CHUNK_SIZE = 1024 * 1024  # 1 MiB
TIMEOUT = 60  # seconds per request

def download_with_progress(url: str, dest_path: Path, filename: str) -> Path:
    """
    Download a file with a tqdm progress bar.

    Returns the full path to the downloaded file.
    """
    dest_path.mkdir(parents=True, exist_ok=True)
    target_file = dest_path / filename

    logger.info(f"Starting download of {filename} from {url}")

    with requests.get(url, stream=True, timeout=TIMEOUT) as response:
        response.raise_for_status()
        total = int(response.headers.get('content-length', 0))
        with open(target_file, 'wb') as f, tqdm(
            total=total,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            desc=filename,
        ) as bar:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))

    logger.info(f"Download completed: {target_file}")
    return target_file

def _extract_tif_from_zip(zip_path: Path, dest_path: Path, target_name: str) -> Path:
    """
    Extract the first .tif file found inside the zip archive and place it at ``dest_path / target_name``.
    """
    logger.info(f"Extracting TIFF from {zip_path}")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Find a .tif entry (case‑insensitive)
        tif_members = [m for m in zf.namelist() if m.lower().endswith('.tif')]
        if not tif_members:
            raise FileNotFoundError("No .tif file found inside the zip archive")
        # Extract the first matching member to a temporary location
        temp_extracted = zf.extract(tif_members[0], path=dest_path)
        temp_path = Path(temp_extracted)
        final_path = dest_path / target_name
        shutil.move(str(temp_path), str(final_path))
    logger.info(f"Extracted TIFF to {final_path}")
    return final_path

def verify_download(filepath: Path, expected_checksum: str) -> bool:
    """
    Verify the downloaded file against a SHA‑256 checksum.

    If ``expected_checksum`` is falsy, the function returns ``True`` (checksum
    verification is optional for this task).
    """
    if not filepath.exists():
        logger.error(f"File not found for verification: {filepath}")
        return False

    if not expected_checksum:
        logger.info("No expected checksum supplied – skipping verification.")
        return True

    actual = checksum_file(str(filepath))
    if actual == expected_checksum:
        logger.info("Checksum verification passed.")
        return True
    else:
        logger.error(
            f"Checksum mismatch for {filepath.name}.\n"
            f"Expected: {expected_checksum}\n"
            f"Actual:   {actual}"
        )
        return False

@retry_with_backoff(max_retries=3, backoff_factor=2)
def run_ingestion() -> Path:
    """
    Orchestrates the download, optional verification and metadata creation.

    Returns:
        Path to the verified raster file.
    """
    # 1️⃣ Download (may be a zip)
    downloaded_path = download_with_progress(NLCD_URL, Path(DATA_RAW_DIR), NLCD_OUTPUT_FILENAME + ".zip")

    # 2️⃣ If a zip archive was downloaded, extract the GeoTIFF
    if downloaded_path.suffix.lower() == ".zip":
        raster_path = _extract_tif_from_zip(downloaded_path, Path(DATA_RAW_DIR), NLCD_OUTPUT_FILENAME)
    else:
        raster_path = downloaded_path

    # 3️⃣ Verify (optional)
    if not verify_download(raster_path, NLCD_EXPECTED_CHECKSUM):
        logger.warning("Verification failed – removing corrupted file and retrying.")
        raster_path.unlink(missing_ok=True)
        raise RetryError("Checksum verification failed")

    # 4️⃣ Write metadata JSON
    _write_metadata(raster_path)

    return raster_path

def _write_metadata(raster_path: Path) -> None:
    """
    Extract raster metadata (CRS, pixel size, dtype, class list, SHA‑256)
    and write it to ``data/raw/<metadata_filename>``.
    """
    import json
    import rasterio

    meta_path = raster_path.parent / NLCD_METADATA_FILENAME

    with rasterio.open(str(raster_path)) as src:
        crs = src.crs.to_string() if src.crs else None
        transform = src.transform
        pixel_size = (abs(transform.a), abs(transform.e))  # (xres, yres)
        dtype = src.dtypes[0]
        # Read unique class values (categorical land‑cover codes)
        # Use a windowed read to avoid loading the full raster into memory
        class_vals = set()
        for window in src.block_windows(1):
            data = src.read(1, window=window)
            class_vals.update(int(v) for v in data.flatten() if v != src.nodata)

    metadata = {
        "source_url": NLCD_URL,
        "crs": crs,
        "pixel_size_m": pixel_size,
        "dtype": dtype,
        "class_list": sorted(class_vals),
        "sha256": checksum_file(str(raster_path)),
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Metadata written to {meta_path}")

def main() -> None:
    """CLI entry point."""
    setup_logging()
    logger.setLevel(LOG_LEVEL)

    logger.info("Starting NLCD data ingestion...")
    try:
        raster_path = run_ingestion()
        print(f"SUCCESS: Data ingested to {raster_path}")
    except RetryError as e:
        logger.critical(f"Ingestion failed after retries: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during ingestion: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
