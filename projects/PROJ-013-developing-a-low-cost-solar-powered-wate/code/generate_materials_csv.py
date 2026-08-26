"""
Script to generate data/processed/materials.csv for User Story 1.

This script aggregates material thermal properties from the hardcoded NIST JSON,
market prices from the scraping logic, and calculated costs to produce the final
processed dataset required for downstream simulation.

Output: data/processed/materials.csv
Columns: material_id, thermal_conductivity, emissivity, specific_heat, density, unit_price, cost, status
"""
import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing project modules
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

# Define the geometry to use for cost calculation.
# Per T020, GeometryConfig supports flat-plate, single-slope, double-slope.
# We use a representative geometry for the cost function as the cost is primarily
# material-dependent for this MVP.
REPRESENTATIVE_GEOMETRY = GeometryConfig(
    geometry_id="single_slope",
    inclination_angle=45.0,
    surface_area=1.0,  # 1 m^2 for unit cost comparison
    thickness=0.003    # 3mm typical sheet metal
)

def generate_materials_csv(output_path: Path) -> None:
    """
    Generates the materials.csv file by combining thermal properties, prices, and costs.
    
    Args:
        output_path: The full path where the CSV will be written.
    """
    # 1. Load thermal properties from hardcoded NIST JSON
    logger.info("Loading thermal properties from hardcoded NIST JSON...")
    try:
        materials_data = load_nist_materials()
    except FileNotFoundError as e:
        logger.error(f"Failed to load NIST materials: {e}")
        raise
    
    # 2. Fetch market prices (scraping logic from T013)
    logger.info("Fetching market prices...")
    # fetch_market_prices returns a dict: {material_name: price_per_kg}
    # It handles failures by logging warnings and excluding invalid entries.
    prices = fetch_market_prices()
    
    # 3. Process each material
    rows = []
    valid_count = 0
    invalid_count = 0

    for material_id, props in materials_data.items():
        # Check if we have a price for this material
        if material_id in prices:
            unit_price = prices[material_id]
            status = "valid"
            valid_count += 1
        else:
            unit_price = 0.0
            status = "invalid_price"
            invalid_count += 1
            logger.warning(f"Material '{material_id}' has no valid price. Marking as invalid.")

        # Calculate mass based on the representative geometry
        # calculate_mass expects a MaterialProfile (dict) and GeometryConfig
        mass_kg = calculate_mass(props, REPRESENTATIVE_GEOMETRY)
        
        # Calculate total cost for this component
        # calculate_cost expects a list of MaterialProfiles and a GeometryConfig
        # We pass a single-item list for this specific material
        material_list = [props]
        total_cost = calculate_cost(material_list, REPRESENTATIVE_GEOMETRY)

        # If status is invalid, cost should ideally be 0 or handled, 
        # but per spec we include the row with status flag.
        if status == "invalid_price":
            total_cost = 0.0

        row = {
            "material_id": material_id,
            "thermal_conductivity": props.get("thermal_conductivity"),
            "emissivity": props.get("emissivity"),
            "specific_heat": props.get("specific_heat"),
            "density": props.get("density"),
            "unit_price": unit_price,
            "cost": total_cost,
            "status": status
        }
        rows.append(row)

    # 4. Write to CSV
    ensure_dir(output_path.parent)
    fieldnames = [
        "material_id", "thermal_conductivity", "emissivity", 
        "specific_heat", "density", "unit_price", "cost", "status"
    ]

    logger.info(f"Writing {len(rows)} rows to {output_path}...")
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Generated materials.csv: {valid_count} valid, {invalid_count} invalid.")

def main():
    project_root = get_project_root()
    output_path = project_root / "data" / "processed" / "materials.csv"
    
    try:
        generate_materials_csv(output_path)
        logger.info("Task T015 completed successfully.")
    except Exception as e:
        logger.error(f"Task T015 failed: {e}")
        raise

if __name__ == "__main__":
    main()
