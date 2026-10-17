import os
import sys
import logging
import time
import hashlib
import requests
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from utils.config import get_project_root, get_data_processed_path, get_data_raw_path
from utils.io import write_csv_with_associational_flag
from llmxive_toolkit import paths
from analysis.metadata_utils import load_metadata, save_metadata

logger = logging.getLogger(__name__)

# API Configuration
TNG_API_BASE = "https://www.tng-project.org/api"
TNG_SNAPSHOT = 99  # Snapshot 099 is typically the latest (z=0) for TNG100-1

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_api_key() -> Optional[str]:
    """Retrieve TNG API key from environment variable."""
    return os.environ.get("TNG_API_KEY")

# ----------------------------------------------------------------------
# Existing halo list / galaxy property functions (unchanged)
# ----------------------------------------------------------------------
def fetch_halos_list(snapshot: int = TNG_SNAPSHOT) -> List[Dict[str, Any]]:
    """
    Fetch the list of halos for a given snapshot from the TNG API.
    Returns a list of dictionaries containing halo metadata.
    """
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("TNG_API_KEY environment variable is not set.")

    url = f"{TNG_API_BASE}/snapshots/{snapshot}/halos"
    params = {"key": api_key, "format": "json"}

    halos = []
    page = 1
    while True:
        params["page"] = page
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if "results" not in data or not data["results"]:
                break
            halos.extend(data["results"])
            # Break if fewer results than total count indicates last page
            if len(data["results"]) < data.get("count", float('inf')):
                break
            page += 1
        except requests.RequestException as e:
            logger.error(f"Failed to fetch halo list page {page}: {e}")
            break

    return halos

def get_halo_files_for_snapshot(snapshot: int = TNG_SNAPSHOT) -> List[str]:
    """
    Get the list of available HDF5 files for a snapshot.
    Returns a list of filenames.
    """
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("TNG_API_KEY environment variable is not set.")

    url = f"{TNG_API_BASE}/snapshots/{snapshot}/files"
    params = {"key": api_key, "format": "json"}

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        # The API returns a list of filenames under the "results" key
        return data.get("results", [])
    except requests.RequestException as e:
        logger.error(f"Failed to fetch file list: {e}")
        return []

def download_file(url: str, dest_path: str, chunk_size: int = 8192) -> bool:
    """Download a file from a URL to a destination path."""
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    f.write(chunk)
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

# ----------------------------------------------------------------------
# New raw‑data ingestion functionality
# ----------------------------------------------------------------------
def download_raw_hdf5_files(
    snapshot: int = TNG_SNAPSHOT,
    max_files: int = 1,
) -> List[Path]:
    """
    Download up to ``max_files`` HDF5 files for the given snapshot.
    Files are stored under ``data/raw/tng100/`` (created if necessary).
    For each successful download, the SHA‑256 checksum is computed and
    stored in ``data/metadata.yaml`` under ``datasets.tng100.files``.
    Returns a list of ``Path`` objects pointing to the downloaded files.
    """
    logger.info(f"Starting download of up to {max_files} HDF5 file(s) for snapshot {snapshot}")

    file_names = get_halo_files_for_snapshot(snapshot)
    if not file_names:
        logger.error("No HDF5 files reported by the TNG API for this snapshot.")
        return []

    # Ensure the raw data directory exists
    raw_dir: Path = paths.data("raw", "tng100")
    raw_dir.mkdir(parents=True, exist_ok=True)

    downloaded_paths: List[Path] = []
    for filename in file_names[:max_files]:
        if not filename.lower().endswith(".hdf5"):
            continue  # Skip non‑HDF5 entries just in case

        file_url = f"{TNG_API_BASE}/snapshots/{snapshot}/files/{filename}"
        dest_path = raw_dir / filename

        logger.info(f"Downloading {filename} from {file_url}")
        success = download_file(file_url, str(dest_path))
        if not success:
            logger.error(f"Failed to download {filename}; aborting further downloads.")
            continue

        checksum = calculate_sha256(str(dest_path))
        logger.info(f"Downloaded {filename} (SHA‑256: {checksum})")

        # Update metadata.yaml
        metadata = load_metadata()
        dataset_entry = metadata.setdefault("datasets", {}).setdefault("tng100", {})
        files_entry = dataset_entry.setdefault("files", {})
        files_entry[filename] = checksum
        save_metadata(metadata)

        downloaded_paths.append(dest_path)

    if not downloaded_paths:
        logger.warning("No HDF5 files were downloaded.")
    else:
        logger.info(f"Successfully downloaded {len(downloaded_paths)} file(s).")

    return downloaded_paths

# ----------------------------------------------------------------------
# Existing galaxy‑property ingestion (unchanged apart from minor formatting)
# ----------------------------------------------------------------------
def fetch_tng_halo_data(halo_id: int, snapshot: int = TNG_SNAPSHOT) -> Optional[Dict[str, Any]]:
    """
    Fetch detailed data for a specific halo from the TNG API.
    This includes subhalo information which is crucial for identifying the central galaxy.
    """
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("TNG_API_KEY environment variable is not set.")

    url = f"{TNG_API_BASE}/snapshots/{snapshot}/halos/{halo_id}"
    params = {"key": api_key, "format": "json"}

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch data for halo {halo_id}: {e}")
        return None

def load_galaxy_properties_from_tng(output_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extract SFR, effective radius, and stellar mass for the most massive subhalo (central) within each halo.
    """
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("TNG_API_KEY environment variable is not set.")

    logger.info("Starting galaxy property ingestion from TNG-100...")

    halos_list = fetch_halos_list()
    if not halos_list:
        logger.warning("No halos found in the TNG API response.")
        return []

    galaxy_properties = []

    for halo_info in halos_list:
        halo_id = halo_info.get("id")
        if halo_id is None:
            continue

        halo_data = fetch_tng_halo_data(halo_id)
        if not halo_data:
            continue

        subhalos = halo_data.get("subhalos", [])
        if not subhalos:
            continue

        central_subhalo = None
        max_stellar_mass = -1.0

        for subhalo in subhalos:
            stellar_mass = subhalo.get("stellar_mass", 0.0)
            if stellar_mass == 0.0 and "mass" in subhalo:
                stellar_mass = subhalo["mass"][2] if len(subhalo["mass"]) > 2 else 0.0

            if stellar_mass > max_stellar_mass:
                max_stellar_mass = stellar_mass
                central_subhalo = subhalo

        if central_subhalo is None:
            continue

        sfr = float(central_subhalo.get("sfr", 0.0))
        effective_radius = float(central_subhalo.get("half_mass_rad", 0.0))
        stellar_mass = float(central_subhalo.get("stellar_mass", 0.0))
        if stellar_mass == 0.0 and "mass" in central_subhalo:
            stellar_mass = float(central_subhalo["mass"][2] if len(central_subhalo["mass"]) > 2 else 0.0)

        if stellar_mass > 0:
            galaxy_properties.append({
                "galaxy_id": central_subhalo.get("subhalo_id", -1),
                "halo_id": halo_id,
                "sfr": sfr,
                "effective_radius": effective_radius,
                "stellar_mass": stellar_mass
            })

        # Small delay to respect API rate limits
        time.sleep(0.1)

    logger.info(f"Extracted galaxy properties for {len(galaxy_properties)} central galaxies.")

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        write_csv_with_associational_flag(
            galaxy_properties,
            output_path,
            ["galaxy_id", "halo_id", "sfr", "effective_radius", "stellar_mass"]
        )
        logger.info(f"Galaxy properties written to {output_path}")

    return galaxy_properties

def load_galaxy_properties(output_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Wrapper to load galaxy properties.
    """
    if output_path is None:
        output_path = str(get_data_processed_path() / "galaxy_properties.csv")
    return load_galaxy_properties_from_tng(output_path)

# ----------------------------------------------------------------------
# Main entry point – orchestrates raw download then galaxy‑property extraction
# ----------------------------------------------------------------------
def main():
    """Main entry point for the TNG loader script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 1. Download raw HDF5 file(s)
    try:
        downloaded = download_raw_hdf5_files(max_files=1)
        if downloaded:
            logger.info(f"Raw data download complete: {[p.name for p in downloaded]}")
        else:
            logger.warning("No raw HDF5 files were downloaded.")
    except Exception as e:
        logger.error(f"Raw data download failed: {e}")
        sys.exit(1)

    # 2. Extract and write galaxy properties
    output_path = str(get_data_processed_path() / "galaxy_properties.csv")
    logger.info(f"Running TNG galaxy property ingestion. Output: {output_path}")

    try:
        properties = load_galaxy_properties(output_path)
        logger.info("Galaxy property ingestion completed successfully.")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
