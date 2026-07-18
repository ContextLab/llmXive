import json
import os
import sys
import hashlib
import logging
from typing import Dict, Any, Optional, Tuple

def ensure_raw_directory(path: str) -> None:
    """Ensures that the raw data directory exists."""
    os.makedirs(path, exist_ok=True)

def compute_sha256(file_path: str) -> str:
    """Computes the SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def load_known_hashes(hash_file: str) -> Dict[str, str]:
    """Loads known SHA-256 hashes from a JSON file."""
    try:
        with open(hash_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_hash(hash_file: str, filename: str, hash_value: str) -> None:
    """Saves a SHA-256 hash to a JSON file."""
    hashes = load_known_hashes(hash_file)
    hashes[filename] = hash_value
    with open(hash_file, 'w') as f:
        json.dump(hashes, f, indent=4)

def download_planck_map(url: str, file_path: str) -> bytes:
    """Downloads the Planck map."""
    import requests
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
    return response.content

def download_bicep_spectrum(url: str, file_path: str) -> bytes:
    """Downloads the BICEP spectrum."""
    import requests
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
    return response.content

def apply_planck_mask(map_file: str, mask_file: str, output_file: str) -> None:
    """Applies the Planck mask to the map."""
    import healpy as hp
    # Load the map and mask
    m = hp.read_map(map_file)
    mask = hp.read_map(mask_file)

    # Apply the mask
    masked_map = m * mask

    # Save the masked map
    hp.write_map(output_file, masked_map)


def main():
    """Main function for data ingestion."""
    raw_data_dir = "data/raw"
    ensure_raw_directory(raw_data_dir)
    hash_file = "data/hashes.json"

    # Example URLs (replace with actual URLs from config)
    planck_url = "http://example.com/planck_map.fits"  # Replace
    bicep_url = "http://example.com/bicep_spectrum.dat" # Replace
    mask_file = "data/raw/plikHM_mask_2048_R3.00.fits"

    planck_map_file = os.path.join(raw_data_dir, "planck_map.fits")
    bicep_spectrum_file = os.path.join(raw_data_dir, "bicep_spectrum.dat")
    masked_map_file = os.path.join(raw_data_dir, "masked_planck_map.fits")

    try:
        # Download Planck map
        planck_data = download_planck_map(planck_url, planck_map_file)
        planck_hash = compute_sha256(planck_map_file)
        save_hash(hash_file, "planck_map.fits", planck_hash)
        logging.info(f"Downloaded and verified Planck map: {planck_hash}")

        # Download BICEP spectrum
        bicep_data = download_bicep_spectrum(bicep_url, bicep_spectrum_file)
        bicep_hash = compute_sha256(bicep_spectrum_file)
        save_hash(hash_file, "bicep_spectrum.dat", bicep_hash)
        logging.info(f"Downloaded and verified BICEP spectrum: {bicep_hash}")

        # Apply Planck mask
        apply_planck_mask(planck_map_file, mask_file, masked_map_file)
        masked_hash = compute_sha256(masked_map_file)
        save_hash(hash_file, "masked_planck_map.fits", masked_hash)
        logging.info(f"Applied Planck mask: {masked_hash}")

    except Exception as e:
        logging.error(f"An error occurred during data ingestion: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
