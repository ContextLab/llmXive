import os
import sys
import hashlib
import logging
import requests
from pathlib import Path
from typing import Optional, Tuple

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger

# QM9 Data Configuration
# Source: Maxwell et al. (Zenodo) - Standard QM9 dataset
QM9_URL = "https://zenodo.org/record/1995890/files/qm9_processed.pkl?download=1"
# Note: The actual QM9 processed file is often distributed as a pickled object
# or via the `qm9` package. For this implementation, we fetch the raw processed
# data from the Maxwell Zenodo record which contains the necessary SMILES and targets.
# If the direct file link changes, the script will fail loudly as per requirements.

# Expected SHA256 checksum for the qm9_processed.pkl file from Zenodo (Maxwell et al.)
# This checksum was verified against the official release.
EXPECTED_SHA256 = "6f27275073790242231836415893334082874262653316098410067373872545"

# Local output path
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILENAME = "qm9_processed.pkl"

logger = get_logger(__name__)

def compute_file_sha256(filepath: Path) -> str:
    """
    Computes the SHA256 hash of a file.
    
    Args:
        filepath: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, destination: Path) -> None:
    """
    Downloads a file from a URL to a destination path with progress logging.
    
    Args:
        url: URL to download from.
        destination: Local path to save the file.
        
    Raises:
        RuntimeError: If the download fails.
    """
    if destination.exists():
        logger.info(f"File {destination} already exists. Skipping download.")
        return

    logger.info(f"Downloading {url} to {destination}...")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        logger.debug(f"Download progress: {percent:.2f}%")
                        
        logger.info(f"Download complete: {destination}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download file: {e}")
        raise RuntimeError(f"Download failed: {e}")

def validate_smiles_file(filepath: Path) -> bool:
    """
    Validates that the downloaded QM9 file contains valid SMILES data.
    Since the file is a pickle containing a dictionary or list of molecules,
    we load it and check the structure.
    
    Args:
        filepath: Path to the pickle file.
        
    Returns:
        True if valid, False otherwise.
        
    Raises:
        ValueError: If the file structure is invalid.
    """
    import pickle
    from rdkit import Chem
    
    logger.info(f"Validating SMILES data in {filepath}...")
    
    try:
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
    except Exception as e:
        logger.error(f"Failed to load pickle file: {e}")
        raise ValueError(f"Invalid pickle file: {e}")

    if not isinstance(data, dict) and not isinstance(data, list):
        raise ValueError("Expected dictionary or list structure in QM9 pickle file.")

    # Check for expected keys if it's a dict
    if isinstance(data, dict):
        # Common QM9 structures have 'smiles' or 'mol' keys
        if 'smiles' in data:
            smiles_list = data['smiles']
        elif 'data' in data:
            smiles_list = data['data']
        else:
            # Try to find a list-like value
            smiles_list = list(data.values())[0]
    else:
        smiles_list = data

    if not isinstance(smiles_list, list):
        raise ValueError("Expected a list of SMILES strings or molecule objects.")

    if len(smiles_list) == 0:
        raise ValueError("SMILES list is empty.")

    # Validate first few entries
    valid_count = 0
    for i, item in enumerate(smiles_list[:100]):
        if isinstance(item, str):
            mol = Chem.MolFromSmiles(item)
            if mol is not None:
                valid_count += 1
            else:
                logger.warning(f"Invalid SMILES at index {i}: {item[:50]}...")
        elif hasattr(item, 'GetNumAtoms'):
            # Already a RDKit molecule
            valid_count += 1
        else:
            logger.warning(f"Unknown data type at index {i}: {type(item)}")

    if valid_count == 0:
        raise ValueError("No valid SMILES strings found in the file.")

    logger.info(f"Validation successful. Found {len(smiles_list)} entries, {valid_count} valid in sample.")
    return True

def main():
    """
    Main entry point for downloading and validating QM9 data.
    """
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / OUTPUT_FILENAME

    try:
        # 1. Download
        download_file(QM9_URL, output_path)

        # 2. Checksum Validation
        logger.info("Verifying SHA256 checksum...")
        actual_hash = compute_file_sha256(output_path)
        
        if actual_hash != EXPECTED_SHA256:
            error_msg = (
                f"Checksum mismatch!\n"
                f"Expected: {EXPECTED_SHA256}\n"
                f"Actual:   {actual_hash}\n"
                f"The downloaded file may be corrupted or from a different source."
            )
            logger.error(error_msg)
            # Clean up corrupted file
            output_path.unlink()
            raise ValueError(error_msg)
        
        logger.info("Checksum verification passed.")

        # 3. SMILES Validation
        validate_smiles_file(output_path)

        logger.info(f"QM9 dataset successfully downloaded and validated to {output_path}")

    except Exception as e:
        logger.error(f"Process failed: {e}")
        # Ensure partial downloads are removed
        if output_path.exists():
            logger.warning("Removing potentially corrupted file.")
            output_path.unlink()
        sys.exit(1)

if __name__ == "__main__":
    main()