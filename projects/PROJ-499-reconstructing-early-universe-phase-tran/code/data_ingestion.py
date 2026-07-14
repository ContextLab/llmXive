import json
import os
import sys
import hashlib
import logging
from typing import Dict, Any, Optional
import numpy as np

# Configure logging for data ingestion and masking operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import from utils as per API surface
from utils import verify_checksum, retry_download
# Import from config as per API surface
from config import get_config

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_raw_directory() -> str:
    """Ensure the data/raw directory exists."""
    raw_dir = "data/raw"
    os.makedirs(raw_dir, exist_ok=True)
    return raw_dir

def load_known_hashes() -> Dict[str, str]:
    """Load known checksums from data/hashes.json."""
    hash_file = "data/hashes.json"
    if os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            return json.load(f)
    return {}

def save_hash(file_path: str, hash_value: str) -> None:
    """Save a file's hash to data/hashes.json."""
    hash_file = "data/hashes.json"
    known_hashes = load_known_hashes()
    known_hashes[file_path] = hash_value
    with open(hash_file, "w") as f:
        json.dump(known_hashes, f, indent=2)
    logger.info(f"Saved checksum for {file_path}: {hash_value}")

def download_planck_map(map_id: str, url: str, output_filename: str) -> str:
    """Download Planck SMICA B-mode map with logging and checksum verification."""
    raw_dir = ensure_raw_directory()
    output_path = os.path.join(raw_dir, output_filename)

    logger.info(f"Downloading Planck map {map_id} from {url}")
    try:
        data = retry_download(url)
        
        # Write to temporary file first
        temp_path = output_path + ".tmp"
        with open(temp_path, "wb") as f:
            f.write(data)
        
        # Compute checksum
        computed_hash = compute_sha256(temp_path)
        logger.info(f"Computed checksum for {output_filename}: {computed_hash}")

        # Verify checksum if known
        known_hashes = load_known_hashes()
        expected_hash = known_hashes.get(output_filename)
        
        if expected_hash:
            if verify_checksum(temp_path, expected_hash):
                logger.info(f"Checksum verification PASSED for {output_filename}")
                os.rename(temp_path, output_path)
                save_hash(output_filename, computed_hash)
                return output_path
            else:
                logger.error(f"Checksum verification FAILED for {output_filename}")
                logger.error(f"Expected: {expected_hash}, Got: {computed_hash}")
                os.remove(temp_path)
                raise ValueError(f"Checksum mismatch for {output_filename}")
        else:
            logger.warning(f"No known checksum for {output_filename}. Saving anyway.")
            os.rename(temp_path, output_path)
            save_hash(output_filename, computed_hash)
            return output_path
            
    except Exception as e:
        logger.error(f"Failed to download Planck map {map_id}: {str(e)}")
        if os.path.exists(output_path + ".tmp"):
            os.remove(output_path + ".tmp")
        raise

def download_bicep_spectrum(url: str, output_filename: str) -> str:
    """Download BICEP/Keck spectrum with logging and checksum verification."""
    raw_dir = ensure_raw_directory()
    output_path = os.path.join(raw_dir, output_filename)

    logger.info(f"Downloading BICEP/Keck spectrum from {url}")
    try:
        data = retry_download(url)
        
        # Write to temporary file first
        temp_path = output_path + ".tmp"
        with open(temp_path, "wb") as f:
            f.write(data)
        
        # Compute checksum
        computed_hash = compute_sha256(temp_path)
        logger.info(f"Computed checksum for {output_filename}: {computed_hash}")

        # Verify checksum if known
        known_hashes = load_known_hashes()
        expected_hash = known_hashes.get(output_filename)
        
        if expected_hash:
            if verify_checksum(temp_path, expected_hash):
                logger.info(f"Checksum verification PASSED for {output_filename}")
                os.rename(temp_path, output_path)
                save_hash(output_filename, computed_hash)
                return output_path
            else:
                logger.error(f"Checksum verification FAILED for {output_filename}")
                logger.error(f"Expected: {expected_hash}, Got: {computed_hash}")
                os.remove(temp_path)
                raise ValueError(f"Checksum mismatch for {output_filename}")
        else:
            logger.warning(f"No known checksum for {output_filename}. Saving anyway.")
            os.rename(temp_path, output_path)
            save_hash(output_filename, computed_hash)
            return output_path
            
    except Exception as e:
        logger.error(f"Failed to download BICEP/Keck spectrum: {str(e)}")
        if os.path.exists(output_path + ".tmp"):
            os.remove(output_path + ".tmp")
        raise

def apply_planck_mask(input_map_path: str, mask_path: str, output_path: str) -> str:
    """Apply Planck 2015 Common Mask to B-mode maps with logging."""
    import healpy as hp
    
    logger.info(f"Applying Planck 2015 Common Mask to {input_map_path}")
    
    try:
        # Load the map
        map_data = hp.read_map(input_map_path, field=[0, 1, 2])
        logger.info(f"Loaded map with {len(map_data)} components")
        
        # Load the mask
        mask = hp.read_map(mask_path)
        logger.info(f"Loaded mask with {len(mask)} pixels")
        
        # Apply mask (element-wise multiplication)
        masked_data = []
        for component in map_data:
            masked_component = component * mask
            masked_data.append(masked_component)
        
        # Calculate sky coverage
        total_pixels = len(mask)
        non_masked_pixels = np.sum(mask > 0.5)
        coverage = non_masked_pixels / total_pixels
        logger.info(f"Sky coverage after masking: {coverage:.4f} ({coverage*100:.2f}%)")
        
        if coverage < 0.70:
            logger.warning(f"Sky coverage {coverage:.4f} is below 70% threshold")
            # Note: Validation logic in spectrum_computation.py will raise ValueError if needed
        
        # Save masked map
        hp.write_map(output_path, masked_data)
        logger.info(f"Saved masked map to {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to apply mask: {str(e)}")
        raise

def main():
    """Main entry point for data ingestion pipeline."""
    config = get_config()
    
    logger.info("Starting data ingestion pipeline")
    
    # Download Planck map
    planck_map_id = config.get('PLANCK_MAP_ID', 'PLK')
    planck_url = config.get('PLANCK_URL', 'https://example.com/planck_map.fits')
    try:
        planck_path = download_planck_map(planck_map_id, planck_url, "planck_smica_bmode.fits")
        logger.info(f"Successfully downloaded Planck map to {planck_path}")
    except Exception as e:
        logger.error(f"Planck download failed: {e}")
        # In a real scenario, we might continue with other data or exit
    
    # Download BICEP spectrum
    bicep_url = config.get('BICEP_URL', 'https://example.com/bicep_spectrum.txt')
    try:
        bicep_path = download_bicep_spectrum(bicep_url, "bicep_keck_spectrum.txt")
        logger.info(f"Successfully downloaded BICEP/Keck spectrum to {bicep_path}")
    except Exception as e:
        logger.error(f"BICEP download failed: {e}")
    
    logger.info("Data ingestion pipeline completed")

if __name__ == "__main__":
    main()
