"""
Generate the processed materials CSV file for User Story 1.

This script loads material data (from the hardcoded NIST JSON and fetched market prices),
calculates costs based on geometry, and outputs a comprehensive CSV file.

Output: data/processed/materials.csv
"""
import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from data_ingestion import (
    load_nist_materials,
    fetch_market_prices,
    calculate_mass,
    calculate_cost,
    GeometryConfig
)
from utils import get_project_root, get_data_dir, ensure_dir, setup_logging

# Configure logging
logger = setup_logging(__name__)

# Define the geometries to process
GEOMETRIES = [
    GeometryConfig(
        geometry_id="flat_plate",
        surface_area=1.0,  # m^2
        thickness=0.003,   # m (3mm)
        inclination_angle=30.0
    ),
    GeometryConfig(
        geometry_id="single_slope",
        surface_area=1.0,  # m^2
        thickness=0.003,   # m (3mm)
        inclination_angle=30.0
    ),
    GeometryConfig(
        geometry_id="double_slope",
        surface_area=1.0,  # m^2
        thickness=0.003,   # m (3mm)
        inclination_angle=30.0
    )
]

def generate_materials_csv(output_path: Path) -> None:
    """
    Generate the materials CSV containing thermal properties, prices, and calculated costs.
    
    Args:
        output_path: Path to the output CSV file.
    """
    # Load materials from hardcoded NIST JSON
    materials = load_nist_materials()
    logger.info(f"Loaded {len(materials)} materials from NIST data.")

    # Fetch market prices
    price_data = fetch_market_prices(materials)
    
    # Prepare data rows
    rows = []
    for material in materials:
        material_id = material.material_id
        price_info = price_data.get(material_id, {})
        
        # Determine price and status
        unit_price = price_info.get('price_per_kg')
        status = price_info.get('status', 'invalid_price')
        
        # If price is missing or invalid, we still record the material but mark it
        # and set cost to 0 or a sentinel if required, but spec says exclude from simulation.
        # Here we include it in the CSV for traceability as per T015 requirements.
        
        for geometry in GEOMETRIES:
            # Calculate mass for this material-geometry combination
            mass = calculate_mass(material, geometry)
            
            # Calculate cost
            if unit_price is not None and status == "valid":
                total_cost = calculate_cost([material], geometry)
            else:
                total_cost = 0.0
                status = "invalid_price"

            row = {
                'material_id': material_id,
                'geometry_id': geometry.geometry_id,
                'thermal_conductivity': material.thermal_conductivity,
                'emissivity': material.emissivity,
                'specific_heat': material.specific_heat,
                'density': material.density,
                'unit_price_kg': unit_price if unit_price is not None else 0.0,
                'mass_kg': mass,
                'total_cost': total_cost,
                'status': status
            }
            rows.append(row)
            if status == "invalid_price":
                logger.warning(f"Material {material_id} in geometry {geometry.geometry_id} has invalid price. Cost set to 0.")

    # Ensure output directory exists
    ensure_dir(output_path.parent)

    # Write to CSV
    fieldnames = [
        'material_id', 'geometry_id', 'thermal_conductivity', 'emissivity',
        'specific_heat', 'density', 'unit_price_kg', 'mass_kg', 'total_cost', 'status'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Successfully generated {output_path} with {len(rows)} rows.")

def main():
    """Main entry point for the script."""
    project_root = get_project_root()
    output_path = project_root / "data" / "processed" / "materials.csv"
    
    logger.info(f"Starting materials CSV generation. Output: {output_path}")
    generate_materials_csv(output_path)
    logger.info("Task T015 completed.")

if __name__ == "__main__":
    main()