import os
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, NamedTuple

from utils import get_project_root, get_data_dir, ensure_dir, setup_logging, ProjectError
from config import get_config

# Configure logging
logger = setup_logging(__name__)

# --- Data Classes ---

class MaterialProfile(NamedTuple):
    """Represents a material with its thermal properties."""
    material_id: str
    thermal_conductivity: float  # W/(m·K)
    emissivity: float
    specific_heat: float  # J/(kg·K)
    density: float  # kg/m^3
    price_per_kg: float  # USD/kg
    status: str  # "valid", "invalid_price"

class GeometryConfig(NamedTuple):
    """Represents a system geometry configuration."""
    geometry_id: str
    surface_area: float  # m^2
    thickness: float  # m
    inclination_angle: float  # degrees
    # Additional fields if needed for mass calculation
    component_name: str = "main_absorber"

# --- Helper Functions ---

def load_material_schema(path: str) -> Dict[str, Any]:
    """Load the material schema definition (placeholder for future validation)."""
    # In a full implementation, this would validate JSON schema structure.
    # For now, it just ensures the file exists and is readable.
    schema_path = Path(path)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(schema_path, 'r') as f:
        return json.load(f)

def compute_file_checksum(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_nist_materials() -> List[MaterialProfile]:
    """
    Load thermal properties from the hardcoded JSON file.
    T011 requirement: Load from data/raw/nist_materials.json.
    """
    project_root = get_project_root()
    nist_path = project_root / "data" / "raw" / "nist_materials.json"
    
    if not nist_path.exists():
        # Fallback logic if the file is missing (should not happen if T012 ran)
        logger.error(f"NIST materials file not found at {nist_path}. Ensure T012 has run.")
        raise FileNotFoundError(f"Missing NIST materials file: {nist_path}")

    with open(nist_path, 'r') as f:
        data = json.load(f)

    materials = []
    for item in data:
        # Map JSON keys to MaterialProfile fields
        # Ensure keys match data-model.md: thermal_conductivity, emissivity, specific_heat, density
        mat = MaterialProfile(
            material_id=item.get('material_id', 'unknown'),
            thermal_conductivity=float(item.get('thermal_conductivity', 0)),
            emissivity=float(item.get('emissivity', 0)),
            specific_heat=float(item.get('specific_heat', 0)),
            density=float(item.get('density', 0)),
            price_per_kg=float(item.get('price_per_kg', 0.0)),
            status=item.get('status', 'valid')
        )
        materials.append(mat)
    
    logger.info(f"Loaded {len(materials)} materials from {nist_path}")
    return materials

def calculate_mass(geometry: GeometryConfig, density: float) -> float:
    """
    Calculate mass based on geometry volume and material density.
    Mass = Volume * Density = (Area * Thickness) * Density
    """
    volume = geometry.surface_area * geometry.thickness
    mass = volume * density
    return mass

def calculate_cost(materials: List[MaterialProfile], geometry: GeometryConfig) -> float:
    """
    Calculate total cost C for a specific geometry.
    Formula: C = sum(mass_i * price_i) for all components.
    Strictly follows spec: C = sum(mass * price).
    
    Ensures all costs are strictly positive. If a material is invalid (status != 'valid'),
    it is excluded from the cost calculation, but the function assumes at least one valid
    material exists for the calculation to make sense. If no valid materials are found,
    it returns 0.0 (or raises an error if strictness is required, but here we return 0).
    
    Args:
        materials: List of MaterialProfile objects (from T013/T011).
        geometry: GeometryConfig object defining dimensions.
    
    Returns:
        Total cost as a float.
    
    Raises:
        ValueError: If the calculated cost is not positive when valid materials are present.
    """
    total_cost = 0.0
    valid_materials_count = 0

    for mat in materials:
        if mat.status == 'valid':
            valid_materials_count += 1
            mass = calculate_mass(geometry, mat.density)
            cost_component = mass * mat.price_per_kg
            total_cost += cost_component
            logger.debug(f"Cost component for {mat.material_id}: mass={mass:.4f}kg, price={mat.price_per_kg:.2f} USD/kg, cost={cost_component:.4f} USD")
    
    if valid_materials_count == 0:
        logger.warning("No valid materials found to calculate cost.")
        return 0.0

    if total_cost <= 0:
        # This should theoretically not happen if prices and densities are positive
        raise ValueError(f"Calculated cost {total_cost} is not strictly positive. Check input data.")
    
    return total_cost

def fetch_market_prices(materials: List[MaterialProfile]) -> List[MaterialProfile]:
    """
    Fetch current market prices for materials.
    T013 requirement: Scrape or fetch prices. If fails, exclude material and set status.
    Since T013 is marked as completed in the prompt, this function represents the logic
    that would have been implemented there to update the MaterialProfile with prices.
    In this context, we assume the prices are already loaded in the NIST JSON (as per T011/T012 flow).
    However, to strictly follow the task flow where T013 updates prices, this function
    simulates the update or retrieval.
    
    For this implementation (T014), we rely on the data already prepared in `load_nist_materials`.
    If T013 was supposed to update the JSON file, `load_nist_materials` reads that updated file.
    """
    # Placeholder: In a real pipeline, this would update the `materials` list
    # with fresh prices from an API or CSV, updating `price_per_kg` and `status`.
    # Since we are implementing T014 which depends on T013, we assume the data
    # coming into `calculate_cost` is already processed by T013.
    return materials

def fetch_and_checksum_nist_data():
    """
    T012 implementation: Fetch raw NIST data (if available) or ensure hardcoded JSON exists,
    save to data/raw/nist_materials.json, and compute checksum.
    """
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"
    ensure_dir(raw_dir)
    output_path = raw_dir / "nist_materials.json"
    checksum_path = raw_dir / "nist_materials.json.sha256"

    # If the file already exists, we assume it's valid (T011 uses it).
    # T012 is a one-time fetch. For this task, we ensure the file exists.
    # If T013 (scraping) was run, it might have updated this file.
    # We just compute the checksum if the file exists.
    if output_path.exists():
        checksum = compute_file_checksum(str(output_path))
        with open(checksum_path, 'w') as f:
            f.write(checksum)
        logger.info(f"Checksum computed for {output_path}: {checksum}")
    else:
        logger.warning(f"NIST data file {output_path} not found. T012/T013 must run first.")
        # In a real scenario, we might fetch here, but T011 says "hardcoded JSON",
        # implying the file is static or pre-populated.

def main():
    """
    Main entry point for data ingestion and cost calculation.
    Demonstrates the flow: Load materials -> Define Geometry -> Calculate Cost.
    """
    # Setup logging
    logger.info("Starting data ingestion and cost calculation (T014).")

    # 1. Load Materials (T011/T013 data)
    try:
        materials = load_nist_materials()
    except FileNotFoundError as e:
        logger.error(str(e))
        return

    # 2. Define a sample Geometry (T020 will define these formally, but we need one for T014 test)
    # Using a representative geometry for testing the cost function
    sample_geometry = GeometryConfig(
        geometry_id="test_single_slope_1m2",
        surface_area=1.0,  # m^2
        thickness=0.002,   # 2mm
        inclination_angle=30.0,
        component_name="absorber_plate"
    )

    # 3. Calculate Cost (T014 Core Logic)
    try:
        total_cost = calculate_cost(materials, sample_geometry)
        logger.info(f"Total cost for geometry {sample_geometry.geometry_id}: ${total_cost:.2f}")
        
        # Validation: Ensure cost is positive
        if total_cost <= 0:
            logger.error("Cost calculation failed: Result is not positive.")
            return
        
        # Generate output for T015 (materials.csv)
        # We create a simple CSV with material info and the calculated cost for the test geometry
        output_path = get_data_dir() / "processed" / "materials.csv"
        ensure_dir(output_path.parent)
        
        import csv
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['material_id', 'thermal_conductivity', 'emissivity', 'specific_heat', 'density', 'unit_price', 'calculated_cost', 'status'])
            
            for mat in materials:
                if mat.status == 'valid':
                    mass = calculate_mass(sample_geometry, mat.density)
                    cost = mass * mat.price_per_kg
                else:
                    cost = 0.0
                
                writer.writerow([
                    mat.material_id,
                    mat.thermal_conductivity,
                    mat.emissivity,
                    mat.specific_heat,
                    mat.density,
                    mat.price_per_kg,
                    cost,
                    mat.status
                ])
        
        logger.info(f"Materials data written to {output_path}")

    except ValueError as e:
        logger.error(f"Cost calculation error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}", exc_info=True)

if __name__ == "__main__":
    main()