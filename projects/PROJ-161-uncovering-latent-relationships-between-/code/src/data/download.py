"""
Data download module for antibiotic resistance research.
Handles fetching data from ChEMBL, ZINC15, and NCBI with checksum verification.
"""
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from src.config import get_project_root, get_data_raw_path, load_config
from src.data.utils import fetch_with_backoff, fetch_with_backoff_bytes
from src.data.schema import save_data_version_to_file, load_data_version_from_file

logger = logging.getLogger(__name__)

# Real data sources as per project requirements
CHEMBL_URL = "https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_32_mol_sdf.gz"
ZINC15_URL = "https://zinc15.docking.org/substances/subsets/antibiotics.smiles.gz"
NCBI_URL = "https://ftp.ncbi.nlm.nih.gov/pathogen/Antimicrobial_resistance/Data/latest/Resistance_Tables/AMR_resistance_frequencies.csv"

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum
        
    Returns:
        Hex string of SHA256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify file checksum against expected value.
    
    Args:
        file_path: Path to the file to verify
        expected_checksum: Expected SHA256 hash string
        
    Returns:
        True if checksum matches, False otherwise
    """
    actual_checksum = calculate_sha256(file_path)
    return actual_checksum == expected_checksum

def fetch_chembl_smiles(output_path: Optional[Path] = None) -> Path:
    """
    Fetch ChEMBL molecular structures (SMILES/SDF).
    
    Args:
        output_path: Optional custom output path
        
    Returns:
        Path to downloaded file
    """
    if output_path is None:
        output_path = get_data_raw_path() / "chembl_structures.sdf.gz"
    
    logger.info(f"Fetching ChEMBL data from {CHEMBL_URL}")
    fetch_with_backoff(CHEMBL_URL, output_path)
    
    # Calculate and return checksum
    checksum = calculate_sha256(output_path)
    logger.info(f"ChEMBL file downloaded: {output_path}, SHA256: {checksum}")
    
    return output_path

def fetch_zinc15_smiles(output_path: Optional[Path] = None) -> Path:
    """
    Fetch ZINC15 antibiotic SMILES data.
    
    Args:
        output_path: Optional custom output path
        
    Returns:
        Path to downloaded file
    """
    if output_path is None:
        output_path = get_data_raw_path() / "zinc15_antibiotics.smiles.gz"
    
    logger.info(f"Fetching ZINC15 data from {ZINC15_URL}")
    fetch_with_backoff(ZINC15_URL, output_path)
    
    # Calculate and return checksum
    checksum = calculate_sha256(output_path)
    logger.info(f"ZINC15 file downloaded: {output_path}, SHA256: {checksum}")
    
    return output_path

def fetch_ncbi_resistance_frequencies(output_path: Optional[Path] = None) -> Path:
    """
    Fetch NCBI Pathogen Detection resistance frequencies.
    
    Args:
        output_path: Optional custom output path
        
    Returns:
        Path to downloaded file
    """
    if output_path is None:
        output_path = get_data_raw_path() / "ncbi_resistance_frequencies.csv"
    
    logger.info(f"Fetching NCBI data from {NCBI_URL}")
    fetch_with_backoff(NCBI_URL, output_path)
    
    # Calculate and return checksum
    checksum = calculate_sha256(output_path)
    logger.info(f"NCBI file downloaded: {output_path}, SHA256: {checksum}")
    
    return output_path

def log_data_version(source_url: str, file_path: Path, data_version_path: Optional[Path] = None) -> None:
    """
    Log data version information to data_version.json.
    
    Args:
        source_url: URL from which the data was fetched
        file_path: Path to the downloaded file
        data_version_path: Optional custom path for data_version.json
    """
    if data_version_path is None:
        data_version_path = get_project_root() / "data" / "data_version.json"
    
    # Ensure data directory exists
    data_version_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Calculate checksum
    checksum = calculate_sha256(file_path)
    
    # Create version entry
    version_entry = {
        "source_url": source_url,
        "checksum_sha256": checksum,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Load existing data version or create new one
    try:
        data_version = load_data_version_from_file(data_version_path)
    except (FileNotFoundError, json.JSONDecodeError):
        data_version = {"files": []}
    
    # Check if this source_url already exists and update or append
    source_url_exists = False
    for entry in data_version["files"]:
        if entry["source_url"] == source_url:
            entry.update(version_entry)
            source_url_exists = True
            break
    
    if not source_url_exists:
        data_version["files"].append(version_entry)
    
    # Save updated data version
    save_data_version_to_file(data_version_path, data_version)
    logger.info(f"Logged data version for {source_url} to {data_version_path}")

def download_all_data() -> Dict[str, Path]:
    """
    Download all required datasets and log their versions.
    
    Returns:
        Dictionary mapping dataset names to file paths
    """
    logger.info("Starting download of all required datasets")
    
    data_files = {}
    
    # Fetch ChEMBL
    chembl_path = fetch_chembl_smiles()
    log_data_version(CHEMBL_URL, chembl_path)
    data_files["chembl"] = chembl_path
    
    # Fetch ZINC15
    zinc15_path = fetch_zinc15_smiles()
    log_data_version(ZINC15_URL, zinc15_path)
    data_files["zinc15"] = zinc15_path
    
    # Fetch NCBI
    ncbi_path = fetch_ncbi_resistance_frequencies()
    log_data_version(NCBI_URL, ncbi_path)
    data_files["ncbi"] = ncbi_path
    
    logger.info("All datasets downloaded and logged successfully")
    return data_files

def main():
    """Main entry point for data download script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        data_files = download_all_data()
        print("Downloaded files:")
        for name, path in data_files.items():
            print(f"  {name}: {path}")
    except Exception as e:
        logger.error(f"Failed to download data: {e}")
        raise

if __name__ == "__main__":
    main()
