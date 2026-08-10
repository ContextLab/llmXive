import hashlib
import logging
import os
import sys
import requests
import json
import healpy as hp
from pathlib import Path
from typing import Optional, Dict, Any

from config import PROCESSED_MAP_FILENAME, MASK_STATS_FILENAME, MASK_VALIDATION_FILENAME
from logging_config import get_logger

logger = get_logger(__name__)

def calculate_sha256(filepath: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_planck_map(url: str, output_path: str, expected_checksum: Optional[str] = None) -> str:
    """Download Planck SMICA map with checksum validation."""
    logger.info(f"Starting download of Planck map from {url}")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Download completed. Saving to {output_path}")
        
        if expected_checksum:
            actual_checksum = calculate_sha256(output_path)
            if actual_checksum != expected_checksum:
                error_msg = f"Checksum mismatch. Expected: {expected_checksum}, Got: {actual_checksum}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            logger.info(f"Checksum validation passed: {actual_checksum}")
        
        return output_path
    except Exception as e:
        logger.error(f"Failed to download Planck map: {e}")
        raise

def load_planck_map(filepath: str) -> hp.Map:
    """Load a Planck map from FITS file."""
    logger.info(f"Loading Planck map from {filepath}")
    try:
        map_data = hp.read_map(filepath, field=[0, 1, 2])
        logger.info(f"Map loaded successfully with shape {map_data.shape}")
        return map_data
    except Exception as e:
        logger.error(f"Failed to load Planck map from {filepath}: {e}")
        raise

def apply_galactic_mask(map_data: hp.Map, mask_path: str, output_masked_path: str, 
                        output_stats_path: str, output_validation_path: str) -> hp.Map:
    """Apply Commander mask to the CMB map."""
    logger.info(f"Applying galactic mask from {mask_path}")
    try:
        mask = hp.read_map(mask_path, field=0)
        
        # Pre-validate mask
        total_pixels = len(mask)
        unmasked_pixels = np.sum(mask > 0)
        retention = unmasked_pixels / total_pixels
        
        logger.info(f"Mask validation: Retention rate = {retention:.4f} ({retention*100:.2f}%)")
        
        validation_report = {
            "mask_filename": mask_path,
            "total_pixels": int(total_pixels),
            "unmasked_pixels": int(unmasked_pixels),
            "retention_rate": float(retention),
            "validation_status": "PASS" if retention >= 0.95 else "FAIL"
        }
        
        if retention < 0.95:
            error_msg = f"Mask retention {retention*100:.2f}% is below required 95%. Aborting."
            logger.error(error_msg)
            with open(output_validation_path, 'w') as f:
                json.dump(validation_report, f, indent=2)
            raise ValueError(error_msg)
        
        # Apply mask
        masked_data = map_data * mask
        
        # Save masked map
        hp.write_map(output_masked_path, masked_data, overwrite=True)
        logger.info(f"Masked map saved to {output_masked_path}")
        
        # Save statistics
        stats = {
            "mask_filename": mask_path,
            "retention_rate": float(retention),
            "unmasked_pixels": int(unmasked_pixels),
            "total_pixels": int(total_pixels)
        }
        with open(output_stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        # Save validation report
        with open(output_validation_path, 'w') as f:
            json.dump(validation_report, f, indent=2)
        
        logger.info("Mask application and validation complete")
        return masked_data
    except Exception as e:
        logger.error(f"Failed to apply galactic mask: {e}")
        raise

def downgrade_resolution(map_data: hp.Map, nside_target: int = 128, output_path: Optional[str] = None) -> hp.Map:
    """Downgrade map resolution using healpy."""
    logger.info(f"Downgrading map resolution to Nside={nside_target}")
    try:
        current_nside = hp.get_nside(map_data)
        logger.info(f"Current Nside: {current_nside}")
        
        if current_nside < nside_target:
            error_msg = f"Cannot downgrade from Nside={current_nside} to Nside={nside_target}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Use healpy's built-in downgrade
        downgraded = hp.ud_grade(map_data, nside_target)
        
        # Check for NaN/inf
        if np.any(np.isnan(downgraded)) or np.any(np.isinf(downgraded)):
            logger.warning("NaN or Inf values detected in downgraded map. Replacing with 0.")
            downgraded = np.nan_to_num(downgraded, nan=0.0, posinf=0.0, neginf=0.0)
        
        logger.info(f"Downgraded map shape: {downgraded.shape}")
        
        if output_path:
            hp.write_map(output_path, downgraded, overwrite=True)
            logger.info(f"Downgraded map saved to {output_path}")
        
        return downgraded
    except Exception as e:
        logger.error(f"Failed to downgrade map resolution: {e}")
        raise

def save_processed_map(map_data: hp.Map, output_path: str, checksum: str, provenance: str):
    """Save the final processed map with metadata."""
    logger.info(f"Saving processed map to {output_path}")
    try:
        # Create header with metadata
        header = {
            'PROVENANCE': provenance,
            'CHECKSUM': checksum,
            'NPIX': hp.get_npix(hp.get_nside(map_data)),
            'NSIDE': hp.get_nside(map_data),
            'COORDSYS': 'G'  # Galactic coordinates
        }
        
        hp.write_map(output_path, map_data, overwrite=True, 
                    hdu_header=hp.fitsfunc.write_map_hdu_header(map_data, header))
        
        logger.info(f"Processed map saved with provenance: {provenance}")
        logger.info(f"Checksum included: {checksum}")
    except Exception as e:
        logger.error(f"Failed to save processed map: {e}")
        raise

def main():
    """Main function to run the data loading pipeline."""
    logger.info("Starting Planck CMB data loading pipeline")
    
    # Configuration (example values - should come from config.py)
    smica_url = "https://pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID=COM_CMB_MOCK_L2_SMICA_R3.011.fits"
    mask_url = "https://pla.esac.esa.int/pla/aio/product-action?MASK.MASK_ID=COM_Mask_R3.011_CMB.fits"
    expected_smica_checksum = "PLACEHOLDER_CHECKSUM"  # Should be retrieved from spec
    
    # Ensure directories exist
    from config import ensure_directories
    ensure_directories()
    
    # Download and validate
    smica_path = "data/raw/planck_smica_n2048.fits"
    mask_path = "data/raw/planck_mask.fits"
    
    download_planck_map(smica_url, smica_path, expected_smica_checksum)
    # Note: Mask download logic would be similar
    
    # Load and process
    map_data = load_planck_map(smica_path)
    
    # Apply mask
    masked_map = apply_galactic_mask(
        map_data, 
        mask_path,
        "data/processed/masked_n2048.fits",
        "data/processed/mask_stats.json",
        "data/processed/mask_validation_report.json"
    )
    
    # Downgrade
    downgraded_map = downgrade_resolution(
        masked_map, 
        nside_target=128,
        output_path="data/processed/masked_n128.fits"
    )
    
    # Save final
    final_checksum = calculate_sha256("data/processed/masked_n128.fits")
    save_processed_map(
        downgraded_map,
        "data/processed/masked_n128.fits",
        final_checksum,
        "Planck SMICA N2048 -> Commander Mask -> N128 Downgrade"
    )
    
    logger.info("Data loading pipeline completed successfully")

if __name__ == "__main__":
    main()