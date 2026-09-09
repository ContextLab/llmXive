import os
import sys
import hashlib
import logging
import requests
import gzip
from pathlib import Path

from utils.logging_config import get_logger

logger = get_logger(__name__)

# QM9 Data Source (Zenodo via Maxwell)
QM9_URL = "https://zenodo.org/record/7298654/files/qm9_smiles.csv.gz"
QM9_CHECKSUM = "e5d30937064805233817299153218785"  # Placeholder, replace with real checksum if available

def ensure_data_dir():
    """Ensure the data/raw directory exists."""
    data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, filepath: Path):
    """Download a file from URL with progress logging."""
    logger.info(f"Downloading {url} to {filepath}")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Downloaded {filepath.name} successfully.")
    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

def validate_checksum(filepath: Path, expected_checksum: str) -> bool:
    """Validate file checksum."""
    if not os.path.exists(filepath):
        return False
    actual_checksum = compute_file_sha256(filepath)
    if actual_checksum == expected_checksum:
        logger.info(f"Checksum validated for {filepath.name}")
        return True
    else:
        logger.error(f"Checksum mismatch for {filepath.name}: expected {expected_checksum}, got {actual_checksum}")
        return False

def validate_smiles_string(smiles: str) -> bool:
    """Basic validation of a SMILES string."""
    if not smiles or not isinstance(smiles, str):
        return False
    # Very basic check: non-empty, no spaces, allowed characters
    allowed = set("CcnnOoSsFClBrIP")
    # Simplified check; real validation would use RDKit
    return all(c in allowed or c in "[]()1234567890=" for c in smiles)

def validate_smiles_file(filepath: Path) -> int:
    """Validate SMILES in a file, return count of valid lines."""
    valid_count = 0
    try:
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 1:
                    smiles = parts[0]
                    if validate_smiles_string(smiles):
                        valid_count += 1
    except Exception as e:
        logger.error(f"Error validating {filepath}: {e}")
        raise
    logger.info(f"Validated {valid_count} SMILES strings in {filepath.name}")
    return valid_count

def main():
    """Main entry point for QM9 download."""
    data_dir = ensure_data_dir()
    output_file = data_dir / "qm9_smiles.csv.gz"

    # Check if file exists
    if output_file.exists():
        logger.info(f"{output_file.name} already exists. Skipping download.")
    else:
        download_file(QM9_URL, output_file)

    # Validate checksum (if known)
    # if QM9_CHECKSUM and not validate_checksum(output_file, QM9_CHECKSUM):
    #     logger.critical("Checksum validation failed. Exiting.")
    #     sys.exit(1)

    # Validate SMILES content
    validate_smiles_file(output_file)
    logger.info("QM9 data preparation complete.")

if __name__ == "__main__":
    main()
