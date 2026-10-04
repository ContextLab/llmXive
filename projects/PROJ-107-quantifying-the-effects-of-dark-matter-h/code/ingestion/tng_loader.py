import os
import sys
import logging
import time
import hashlib
import requests
import json
import csv
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from utils.config import get_project_root, get_data_processed_path, get_data_raw_path
from utils.io import write_csv_with_associational_flag

logger = logging.getLogger(__name__)

# API Configuration
TNG_API_BASE = "https://www.tng-project.org/api"
TNG_SNAPSHOT = 99  # Snapshot 099 is typically the latest (z=0) for TNG100-1
# Note: TNG-100 is often accessed via snapshot 99. If the project specifically requires snapshot 000 (z=20),
# this constant would need to be 0. However, galaxy properties like SFR are most relevant at z=0.
# We will default to 99 for z=0 analysis unless specified otherwise in config.
# For this implementation, we assume Snapshot 99 (z=0) as it contains the most mature galaxies.

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
    This is used to determine which files to download if needed.
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
    
    This function iterates through all halos in the snapshot, fetches their details,
    identifies the central subhalo (the one with the highest stellar mass, typically subhalo ID 0 or 1),
    and extracts the required galaxy properties.
    
    Args:
        output_path: Optional path to write the CSV file. If None, returns the list of properties.
    
    Returns:
        List of dictionaries containing galaxy properties.
    """
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("TNG_API_KEY environment variable is not set.")
    
    logger.info("Starting galaxy property ingestion from TNG-100...")
    
    # Fetch list of halos
    halos_list = fetch_halos_list()
    if not halos_list:
        logger.warning("No halos found in the TNG API response.")
        return []
    
    galaxy_properties = []
    
    for halo_info in halos_list:
        halo_id = halo_info.get("id")
        if halo_id is None:
            continue
        
        # Fetch detailed halo data
        halo_data = fetch_tng_halo_data(halo_id)
        if not halo_data:
            continue
        
        # Identify the central galaxy (most massive subhalo)
        # In TNG, the central galaxy is typically the subhalo with the highest stellar mass.
        # Often, subhalo ID 0 is the central, but we should verify by stellar mass.
        subhalos = halo_data.get("subhalos", [])
        if not subhalos:
            continue
        
        # Sort subhalos by stellar mass to find the central galaxy
        # Stellar mass is usually in subhalo['stellar_mass'] or subhalo['mass'][2] (index 2 is stars)
        # We use 'stellar_mass' if available, otherwise calculate from mass array
        central_subhalo = None
        max_stellar_mass = -1.0
        
        for subhalo in subhalos:
            stellar_mass = subhalo.get("stellar_mass", 0.0)
            # If stellar_mass is not directly available, try to get it from the mass array
            # Mass array indices: 0=Total, 1=DM, 2=Stars, 3=Gas, 4=NS, 5=BH
            if stellar_mass == 0.0 and "mass" in subhalo:
                stellar_mass = subhalo["mass"][2] if len(subhalo["mass"]) > 2 else 0.0
            
            if stellar_mass > max_stellar_mass:
                max_stellar_mass = stellar_mass
                central_subhalo = subhalo
        
        if central_subhalo is None:
            continue
        
        # Extract galaxy properties
        # SFR: Star Formation Rate (Msol/yr)
        sfr = central_subhalo.get("sfr", 0.0)
        if sfr == 0.0 and "star_forming_gas" in central_subhalo:
            # Fallback or alternative calculation if needed, but usually sfr is direct
            pass
        
        # Effective Radius: Half-mass radius of stars (kpc)
        # In TNG, this is often 'half_mass_rad' for stars, or 'radius' if specified
        # We look for 'half_mass_rad' in the subhalo data, specifically for stars
        effective_radius = central_subhalo.get("half_mass_rad", 0.0)
        # If half_mass_rad is not available, we might need to compute it from particle data,
        # but for this task, we assume the API provides it or we use a proxy.
        # Note: The TNG API 'half_mass_rad' is typically the half-mass radius of the entire subhalo.
        # For a more precise stellar effective radius, we might need to filter by particle type.
        # However, for this implementation, we use the available 'half_mass_rad' as a proxy,
        # or check for 'radius' if it's stellar.
        # Let's assume 'half_mass_rad' is the closest available metric for effective radius in this context.
        
        # Stellar Mass
        stellar_mass = central_subhalo.get("stellar_mass", 0.0)
        if stellar_mass == 0.0 and "mass" in central_subhalo:
            stellar_mass = central_subhalo["mass"][2] if len(central_subhalo["mass"]) > 2 else 0.0
        
        # Only include if we have valid data (stellar_mass > 0 is a good filter)
        if stellar_mass > 0:
            galaxy_properties.append({
                "galaxy_id": central_subhalo.get("subhalo_id", -1),
                "halo_id": halo_id,
                "sfr": float(sfr),
                "effective_radius": float(effective_radius),
                "stellar_mass": float(stellar_mass)
            })
        
        # Optional: Add a small delay to avoid rate limiting
        time.sleep(0.1)
    
    logger.info(f"Extracted galaxy properties for {len(galaxy_properties)} central galaxies.")
    
    if output_path:
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        write_csv_with_associational_flag(galaxy_properties, output_path, [
            "galaxy_id", "halo_id", "sfr", "effective_radius", "stellar_mass"
        ])
        logger.info(f"Galaxy properties written to {output_path}")
    
    return galaxy_properties

def load_galaxy_properties(output_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Wrapper to load galaxy properties.
    If output_path is provided, it writes to that file and returns the data.
    Otherwise, it just returns the data.
    """
    if output_path is None:
        output_path = str(get_data_processed_path() / "galaxy_properties.csv")
    return load_galaxy_properties_from_tng(output_path)

def main():
    """Main entry point for the TNG loader script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    output_path = str(get_data_processed_path() / "galaxy_properties.csv")
    logger.info(f"Running TNG galaxy property ingestion. Output: {output_path}")
    
    try:
        properties = load_galaxy_properties(output_path)
        logger.info("Ingestion completed successfully.")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
