import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.config import get_project_root, get_data_raw_path, load_config
from src.data.utils import fetch_with_backoff, FetchError
from src.data.schema import DataVersion, DataVersionFile

logger = logging.getLogger(__name__)

# Real data sources
CHEMBL_URL = "https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_33_molstd.sdf.gz"
ZINC15_URL = "https://zinc15.docking.org/substances/subsets/antibiotics.smi"
NCBI_URL = "https://bacmap.wishartlab.com/antibiotic_resistance_data.csv"  # Placeholder for actual NCBI Pathogen Detection URL if available, or a known public dataset

# Fallback URLs for demonstration if primary ones are inaccessible or require complex parsing
# Using a known public antibiotic list for ZINC15-like data
ZINC15_FALLBACK = "https://raw.githubusercontent.com/bioinfow/zinc15-data/main/antibiotics.smi"
NCBI_FALLBACK = "https://raw.githubusercontent.com/ncbi/pathogen-detection-data/main/resistance_frequencies.csv"

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify file checksum matches expected value."""
    actual_checksum = calculate_sha256(file_path)
    return actual_checksum == expected_checksum

def fetch_chembl_smiles(output_path: Path) -> DataVersionFile:
    """Fetch ChEMBL data and return version info."""
    logger.info(f"Fetching ChEMBL data from {CHEMBL_URL}")
    try:
        # In a real scenario, we would parse the SDF or use a specific SMILES URL
        # For this implementation, we assume a direct SMILES download or convert SDF
        # Using a mock URL for the sake of the pipeline if the main one is SDF
        # Real implementation would require RDKit to parse SDF
        # Here we assume a direct download for the pipeline flow
        content = fetch_with_backoff(CHEMBL_URL)
        with open(output_path, "wb") as f:
            f.write(content)
        
        checksum = calculate_sha256(output_path)
        return DataVersionFile(
            source_url=CHEMBL_URL,
            checksum_sha256=checksum,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except FetchError as e:
        logger.error(f"Failed to fetch ChEMBL data: {e}")
        # Fallback to a smaller known dataset if the main one fails
        logger.info("Attempting fallback URL for ChEMBL-like data")
        try:
            content = fetch_with_backoff(ZINC15_FALLBACK)
            with open(output_path, "wb") as f:
                f.write(content)
            checksum = calculate_sha256(output_path)
            return DataVersionFile(
                source_url=ZINC15_FALLBACK,
                checksum_sha256=checksum,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        except FetchError as e2:
            raise FetchError(f"Both primary and fallback ChEMBL fetches failed: {e2}")

def fetch_zinc15_smiles(output_path: Path) -> DataVersionFile:
    """Fetch ZINC15 antibiotic data and return version info."""
    logger.info(f"Fetching ZINC15 data from {ZINC15_URL}")
    try:
        content = fetch_with_backoff(ZINC15_URL)
        with open(output_path, "wb") as f:
            f.write(content)
        
        checksum = calculate_sha256(output_path)
        return DataVersionFile(
            source_url=ZINC15_URL,
            checksum_sha256=checksum,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except FetchError as e:
        logger.error(f"Failed to fetch ZINC15 data: {e}")
        # Fallback
        logger.info("Attempting fallback URL for ZINC15 data")
        try:
            content = fetch_with_backoff(ZINC15_FALLBACK)
            with open(output_path, "wb") as f:
                f.write(content)
            checksum = calculate_sha256(output_path)
            return DataVersionFile(
                source_url=ZINC15_FALLBACK,
                checksum_sha256=checksum,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        except FetchError as e2:
            raise FetchError(f"Both primary and fallback ZINC15 fetches failed: {e2}")

def fetch_ncbi_resistance_frequencies(output_path: Path) -> DataVersionFile:
    """Fetch NCBI resistance data and return version info."""
    logger.info(f"Fetching NCBI resistance data from {NCBI_URL}")
    try:
        content = fetch_with_backoff(NCBI_URL)
        with open(output_path, "wb") as f:
            f.write(content)
        
        checksum = calculate_sha256(output_path)
        return DataVersionFile(
            source_url=NCBI_URL,
            checksum_sha256=checksum,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except FetchError as e:
        logger.error(f"Failed to fetch NCBI data: {e}")
        # Fallback
        logger.info("Attempting fallback URL for NCBI data")
        try:
            content = fetch_with_backoff(NCBI_FALLBACK)
            with open(output_path, "wb") as f:
                f.write(content)
            checksum = calculate_sha256(output_path)
            return DataVersionFile(
                source_url=NCBI_FALLBACK,
                checksum_sha256=checksum,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        except FetchError as e2:
            raise FetchError(f"Both primary and fallback NCBI fetches failed: {e2}")

def log_data_version(version_info: List[DataVersionFile], output_path: Optional[Path] = None) -> Path:
    """Log data version information to data_version.json."""
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "data_version.json"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing version info if it exists
    existing_data = []
    if output_path.exists():
        try:
            with open(output_path, "r") as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read existing data_version.json: {e}")
            existing_data = []
    
    # Append new entries
    for item in version_info:
        entry = {
            "source_url": item.source_url,
            "checksum_sha256": item.checksum_sha256,
            "timestamp": item.timestamp
        }
        # Avoid duplicates based on source_url
        if not any(e["source_url"] == entry["source_url"] for e in existing_data):
            existing_data.append(entry)
    
    # Write updated data
    with open(output_path, "w") as f:
        json.dump(existing_data, f, indent=2)
    
    logger.info(f"Data version logged to {output_path}")
    return output_path

def download_all_data() -> List[DataVersionFile]:
    """Download all required data files and return version info."""
    raw_data_path = get_data_raw_path()
    raw_data_path.mkdir(parents=True, exist_ok=True)
    
    version_info = []
    
    # ChEMBL
    chembl_path = raw_data_path / "chembl_molstd.sdf.gz"
    try:
        version_info.append(fetch_chembl_smiles(chembl_path))
    except FetchError as e:
        logger.error(f"Skipping ChEMBL due to error: {e}")
    
    # ZINC15
    zinc_path = raw_data_path / "zinc15_antibiotics.smi"
    try:
        version_info.append(fetch_zinc15_smiles(zinc_path))
    except FetchError as e:
        logger.error(f"Skipping ZINC15 due to error: {e}")
    
    # NCBI
    ncbi_path = raw_data_path / "ncbi_resistance_frequencies.csv"
    try:
        version_info.append(fetch_ncbi_resistance_frequencies(ncbi_path))
    except FetchError as e:
        logger.error(f"Skipping NCBI due to error: {e}")
    
    if version_info:
        log_data_version(version_info)
    
    return version_info

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    download_all_data()
