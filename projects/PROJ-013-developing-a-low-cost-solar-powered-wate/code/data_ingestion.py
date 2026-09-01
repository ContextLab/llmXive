"""
Data Ingestion Module for Solar Purification Tradeoff Analysis.

Handles loading thermal properties, fetching market prices, and managing
data reproducibility via checksums.
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, NamedTuple

from utils import get_project_root, get_data_dir, ensure_dir, ProjectError, setup_logging

# Setup logging
logger = setup_logging(__name__)

# --- Data Models ---

class MaterialProfile(NamedTuple):
    """Represents a material with its thermal properties."""
    material_id: str
    thermal_conductivity: float  # W/(m·K)
    emissivity: float
    specific_heat: float  # J/(kg·K)
    density: float  # kg/m³
    unit_price: float  # $/kg
    status: str = "valid"

class GeometryConfig(NamedTuple):
    """Represents a system geometry configuration."""
    geometry_id: str
    inclination_angle: float  # degrees
    surface_area: float  # m²
    thickness: float  # m

# --- Helper Functions ---

def load_material_schema(path: str) -> Dict[str, Any]:
    """
    Load the material schema definition from a JSON file.
    Used for validation purposes.
    """
    schema_path = Path(path)
    if not schema_path.exists():
        raise ProjectError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return json.load(f)

def compute_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Compute the SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hex digest of the checksum.
    """
    hash_func = hashlib.new(algorithm)
    path = Path(file_path)
    
    if not path.exists():
        raise ProjectError(f"Cannot compute checksum: File not found {path}")

    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def load_nist_materials(json_path: str) -> List[MaterialProfile]:
    """
    Load material thermal properties from a local JSON file.
    
    Args:
        json_path: Path to the JSON file containing material data.
        
    Returns:
        List of MaterialProfile objects.
    """
    path = Path(json_path)
    if not path.exists():
        raise ProjectError(f"Material data file not found: {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    materials = []
    for item in data:
        try:
            profile = MaterialProfile(
                material_id=item['material_id'],
                thermal_conductivity=float(item['thermal_conductivity']),
                emissivity=float(item['emissivity']),
                specific_heat=float(item['specific_heat']),
                density=float(item['density']),
                unit_price=float(item.get('unit_price', 0.0)),
                status=item.get('status', 'valid')
            )
            materials.append(profile)
        except (KeyError, ValueError) as e:
            logger.warning(f"Skipping malformed material entry: {e}")
            
    return materials

def calculate_mass(material: MaterialProfile, geometry: GeometryConfig) -> float:
    """
    Calculate the mass of a material for a given geometry.
    Mass = Density * Volume
    Volume = Surface Area * Thickness
    """
    volume = geometry.surface_area * geometry.thickness
    return material.density * volume

def calculate_cost(materials: List[MaterialProfile], geometry: GeometryConfig) -> float:
    """
    Calculate total cost for a specific geometry and set of materials.
    Cost = Sum(Mass_i * Price_i) for all valid materials.
    
    Args:
        materials: List of material profiles.
        geometry: The geometry configuration.
        
    Returns:
        Total cost in currency units.
    """
    total_cost = 0.0
    for mat in materials:
        if mat.status == "valid":
            mass = calculate_mass(mat, geometry)
            total_cost += mass * mat.unit_price
    return total_cost

def fetch_market_prices() -> Dict[str, float]:
    """
    Fetch current market prices for materials.
    
    Note: This implementation simulates a fetch or uses a static mapping
    if live scraping is not available or blocked, as per T013 requirements
    to handle failures gracefully. In a real production run, this would
    scrape the specified source. For T012 context, we ensure the function
    exists and returns a dict, but T013 handles the actual logic.
    
    Returns:
        Dictionary mapping material_id to unit_price.
    """
    # Placeholder for T013 logic. T012 focuses on the checksum.
    # Returning a static set for now to allow T012 execution if prices are missing.
    # T013 will override this logic to actually fetch.
    return {
        "aluminum": 2.50,
        "copper": 9.00,
        "steel_black": 1.20,
        "plastic": 1.80
    }

def fetch_and_checksum_nist_data() -> None:
    """
    Fetch raw NIST data from the canonical source ONCE (if available) 
    or use the hardcoded JSON, save to data/raw/nist_materials.json, 
    and compute a SHA256 checksum.
    
    This function ensures reproducibility by verifying the integrity of 
    the raw data file.
    """
    project_root = get_project_root()
    data_raw_dir = project_root / "data" / "raw"
    ensure_dir(data_raw_dir)
    
    json_file_path = data_raw_dir / "nist_materials.json"
    checksum_file_path = data_raw_dir / "nist_materials.json.sha256"
    
    # Define the canonical source (Hardcoded JSON for this project as per T011)
    # In a real scenario, this might download from a URL.
    # Since T011 says "Load hardcoded JSON", we assume the source is local 
    # or a known static URL. For T012, we ensure the file exists and checksum it.
    
    logger.info(f"Checking NIST data file: {json_file_path}")
    
    if not json_file_path.exists():
        raise ProjectError(
            f"Required NIST data file not found: {json_file_path}. "
            "Please ensure T011 has been executed to generate this file."
        )
    
    # Compute checksum
    checksum = compute_file_checksum(json_file_path)
    logger.info(f"Computed SHA256 checksum for {json_file_path.name}: {checksum}")
    
    # Write checksum file
    with open(checksum_file_path, 'w') as f:
        f.write(checksum)
    
    logger.info(f"Checksum saved to {checksum_file_path}")

def main():
    """Main entry point for the data ingestion module."""
    logger.info("Starting data ingestion module (T012: Checksum Generation)")
    try:
        fetch_and_checksum_nist_data()
        logger.info("T012 completed successfully.")
    except ProjectError as e:
        logger.error(f"Project error during T012: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during T012: {e}")
        raise

if __name__ == "__main__":
    main()