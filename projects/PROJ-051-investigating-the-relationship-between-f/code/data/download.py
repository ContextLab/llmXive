"""
Data download module for Turbulent Flow Analysis.

Implements JHTDB fetcher logic with Phase-Shifted DNS fallback mechanism.
Fallback is strictly for algorithm validation when JHTDB is unavailable.
"""
import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import requests
import h5py
import numpy as np

from utils.logging import get_logger
from config import get_config
from validation.null_model import generate_phase_shifted_dns, save_phase_shifted_dns

logger = get_logger(__name__)

# JHTDB API Configuration
JHTDB_BASE_URL = "https://data.jhtdb.org"
JHTDB_TIMEOUT = 30  # seconds

def check_jhtdb_availability() -> bool:
    """
    Check if JHTDB server is reachable.
    Returns True if server is up, False otherwise.
    """
    try:
        response = requests.get(JHTDB_BASE_URL, timeout=JHTDB_TIMEOUT)
        return response.status_code == 200
    except (requests.RequestException, OSError) as e:
        logger.warning(f"JHTDB unreachable: {e}")
        return False

def fetch_jhtdb_dataset(
    re_lambda: int,
    grid_size: str = "512",
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Fetch real DNS data from JHTDB for a specific Reynolds number.

    Args:
        re_lambda: Taylor-microscale Reynolds number (e.g., 400, 600)
        grid_size: Grid resolution (default "512")
        output_dir: Directory to save downloaded data

    Returns:
        Dictionary with metadata and path to downloaded data

    Raises:
        RuntimeError: If JHTDB is unavailable or data fetch fails
    """
    if not check_jhtdb_availability():
        raise RuntimeError(
            f"JHTDB is unavailable for Re_λ={re_lambda}. "
            "Primary data source unreachable. Cannot proceed with real data fetch."
        )

    logger.info(f"Fetching JHTDB dataset for Re_λ={re_lambda}, grid={grid_size}")

    # Construct API endpoint (simplified example - actual JHTDB API varies)
    # In production, this would use the specific JHTDB dataset ID mapping
    dataset_id = f"DNS_{grid_size}_Re{re_lambda}"
    url = f"{JHTDB_BASE_URL}/api/v1/datasets/{dataset_id}"

    try:
        response = requests.get(url, timeout=JHTDB_TIMEOUT)
        response.raise_for_status()
        data_info = response.json()

        # Create output directory if needed
        if output_dir is None:
            config = get_config()
            output_dir = Path(config.data_dir) / "jhtdb"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Download actual data file (simplified - JHTDB uses chunked downloads)
        download_url = data_info.get("download_url")
        if not download_url:
            raise RuntimeError("No download URL in JHTDB response")

        data_file = output_dir / f"jhtdb_Re{re_lambda}_{grid_size}.h5"
        
        # Stream download to handle large files
        with requests.get(download_url, stream=True, timeout=JHTDB_TIMEOUT) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            with open(data_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
        logger.info(f"Successfully downloaded {data_file} ({downloaded} bytes)")
        
        return {
            "source": "jhtdb",
            "re_lambda": re_lambda,
            "grid_size": grid_size,
            "file_path": str(data_file),
            "verified": True
        }
        
    except requests.RequestException as e:
        raise RuntimeError(f"JHTDB data fetch failed: {e}")

def fetch_fallback_null_model(
    re_lambda: int,
    grid_size: str = "512",
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate Phase-Shifted DNS fallback data for algorithm validation ONLY.
    
    This is used when JHTDB is unavailable and only for validation purposes.
    NEVER use this for primary hypothesis testing.
    
    Args:
        re_lambda: Target Reynolds number for scaling
        grid_size: Grid resolution
        output_dir: Directory to save generated data
        
    Returns:
        Dictionary with metadata and path to generated data
        
    Raises:
        RuntimeError: If generation fails
    """
    logger.warning(
        f"⚠️  JHTDB unavailable. Generating Phase-Shifted DNS fallback for Re_λ={re_lambda}. "
        "This data is FOR ALGORITHM VALIDATION ONLY. Do not use for hypothesis testing."
    )
    
    if output_dir is None:
        config = get_config()
        output_dir = Path(config.data_dir) / "fallback"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Generate phase-shifted DNS data using the null model
        # This decouples geometric thresholding from energetic magnitude
        phase_shifted_data = generate_phase_shifted_dns(
            re_lambda=re_lambda,
            grid_size=int(grid_size)
        )
        
        # Save to HDF5
        output_file = output_dir / f"phase_shifted_Re{re_lambda}_{grid_size}.h5"
        save_phase_shifted_dns(phase_shifted_data, output_file)
        
        logger.info(f"Generated fallback data: {output_file}")
        
        return {
            "source": "phase_shifted_dns_fallback",
            "re_lambda": re_lambda,
            "grid_size": grid_size,
            "file_path": str(output_file),
            "verified": False,  # Not real JHTDB data
            "is_validation_only": True
        }
        
    except Exception as e:
        raise RuntimeError(f"Phase-Shifted DNS fallback generation failed: {e}")

def get_data_source(
    re_lambda: int,
    grid_size: str = "512",
    force_fallback: bool = False
) -> Dict[str, Any]:
    """
    Get data source with automatic fallback logic.
    
    Priority:
    1. JHTDB (primary, real data)
    2. Phase-Shifted DNS fallback (validation only, when JHTDB unavailable)
    
    Args:
        re_lambda: Taylor-microscale Reynolds number
        grid_size: Grid resolution
        force_fallback: If True, skip JHTDB and use fallback immediately
        
    Returns:
        Data source dictionary with metadata
        
    Raises:
        RuntimeError: If both sources fail
    """
    config = get_config()
    output_dir = Path(config.data_dir)
    
    # Check if we already have downloaded data
    jhtdb_file = output_dir / "jhtdb" / f"jhtdb_Re{re_lambda}_{grid_size}.h5"
    if jhtdb_file.exists() and not force_fallback:
        logger.info(f"Using cached JHTDB data: {jhtdb_file}")
        return {
            "source": "jhtdb_cached",
            "re_lambda": re_lambda,
            "grid_size": grid_size,
            "file_path": str(jhtdb_file),
            "verified": True
        }
    
    fallback_file = output_dir / "fallback" / f"phase_shifted_Re{re_lambda}_{grid_size}.h5"
    if fallback_file.exists() and not force_fallback:
        logger.info(f"Using cached fallback data: {fallback_file}")
        return {
            "source": "phase_shifted_dns_cached",
            "re_lambda": re_lambda,
            "grid_size": grid_size,
            "file_path": str(fallback_file),
            "verified": False,
            "is_validation_only": True
        }
    
    # Attempt primary source (JHTDB)
    if not force_fallback:
        try:
            return fetch_jhtdb_dataset(re_lambda, grid_size, output_dir / "jhtdb")
        except RuntimeError as e:
            logger.warning(f"JHTDB fetch failed: {e}")
            logger.info("Attempting Phase-Shifted DNS fallback...")
    
    # Fallback to Phase-Shifted DNS (validation only)
    return fetch_fallback_null_model(re_lambda, grid_size, output_dir / "fallback")

def main():
    """CLI entry point for data download."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download turbulent flow data from JHTDB with fallback"
    )
    parser.add_argument(
        "--re-lambda",
        type=int,
        required=True,
        help="Taylor-microscale Reynolds number (e.g., 200, 400, 600)"
    )
    parser.add_argument(
        "--grid-size",
        type=str,
        default="512",
        help="Grid resolution (default: 512)"
    )
    parser.add_argument(
        "--force-fallback",
        action="store_true",
        help="Force use of Phase-Shifted DNS fallback"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: from config)"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting data download for Re_λ={args.re_lambda}")
    
    try:
        data_info = get_data_source(
            re_lambda=args.re_lambda,
            grid_size=args.grid_size,
            force_fallback=args.force_fallback
        )
        
        logger.info(f"Data source: {data_info['source']}")
        logger.info(f"File path: {data_info['file_path']}")
        logger.info(f"Verified real data: {data_info.get('verified', False)}")
        
        if not data_info.get('verified', False):
            logger.warning("⚠️  Using fallback data - validation only!")
            
        return 0
        
    except RuntimeError as e:
        logger.error(f"Data download failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
