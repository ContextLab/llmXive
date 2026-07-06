import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger(__name__)
config = get_config()


def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    logger.info(f"Calculating SHA256 for: {file_path}")
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        raise


def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """
    Verify the SHA256 checksum of a file against an expected hash.

    Args:
        file_path: Path to the file.
        expected_hash: Expected SHA256 hash string.

    Returns:
        True if checksum matches, False otherwise.
    """
    actual_hash = calculate_sha256(file_path)
    if actual_hash == expected_hash:
        logger.info(f"Checksum verified for {file_path}")
        return True
    else:
        logger.error(
            f"Checksum mismatch for {file_path}. "
            f"Expected: {expected_hash}, Got: {actual_hash}"
        )
        return False


def store_metadata(
    file_paths: List[str],
    metadata_path: str,
    data_source: str = "CDS ERA5",
    download_params: Optional[Dict[str, Any]] = None
) -> None:
    """
    Calculate checksums for a list of files and store metadata in a YAML file.

    Args:
        file_paths: List of paths to raw NetCDF files.
        metadata_path: Path to the output metadata YAML file.
        data_source: Source of the data (default: "CDS ERA5").
        download_params: Optional dictionary of download parameters to store.
    """
    metadata_dir = os.path.dirname(metadata_path)
    if metadata_dir:
        os.makedirs(metadata_dir, exist_ok=True)

    metadata_entry = {
        "data_source": data_source,
        "download_parameters": download_params or {},
        "files": []
    }

    for f_path in file_paths:
        if not os.path.exists(f_path):
            logger.warning(f"File not found, skipping checksum: {f_path}")
            continue

        file_hash = calculate_sha256(f_path)
        file_size = os.path.getsize(f_path)
        file_name = os.path.basename(f_path)

        metadata_entry["files"].append({
            "filename": file_name,
            "path": os.path.abspath(f_path),
            "sha256": file_hash,
            "size_bytes": file_size
        })
        logger.info(f"Stored metadata for {file_name}: {file_hash}")

    try:
        with open(metadata_path, "w") as f:
            yaml.dump(metadata_entry, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Metadata stored successfully at {metadata_path}")
    except Exception as e:
        logger.error(f"Failed to write metadata to {metadata_path}: {e}")
        raise


def main():
    """
    Main entry point for checksum verification and metadata storage.
    This script is intended to be run after download.py (T006) has fetched the data.
    It scans the data directory for NetCDF files, calculates their SHA256 checksums,
    and writes the results to data/metadata.yaml.
    """
    data_dir = config.get("data_dir", "data")
    raw_dir = os.path.join(data_dir, "raw")
    metadata_path = os.path.join(data_dir, "metadata.yaml")

    if not os.path.exists(raw_dir):
        logger.warning(f"Raw data directory not found: {raw_dir}. Nothing to verify.")
        return

    # Find all NetCDF files in the raw directory
    nc_files = list(Path(raw_dir).glob("*.nc"))
    
    if not nc_files:
        logger.warning(f"No NetCDF files found in {raw_dir}. Nothing to verify.")
        return

    logger.info(f"Found {len(nc_files)} NetCDF files to verify.")
    
    file_paths = [str(f) for f in nc_files]
    
    # Store metadata
    store_metadata(
        file_paths=file_paths,
        metadata_path=metadata_path,
        data_source="CDS ERA5 (IVT & Geopotential)",
        download_params={
            "variable": ["integrated_water_vapor_transport", "geopotential"],
            "product_type": "reanalysis",
            "resolution": "0.25",
            "domain": "20N-60N, 100E-60W",
            "years": "1979-2023"
        }
    )

if __name__ == "__main__":
    main()
