"""
Generates the materials.csv file containing material properties, prices, and calculated costs.
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
    GeometryConfig,
    MaterialProfile
)
from utils import get_project_root, get_data_dir, ensure_dir, setup_logging

logger = setup_logging(__name__)

# Define the geometries to process as per T020 context (3 geometries)
GEOMETRIES = [
    GeometryConfig(
        geometry_id="flat_plate",
        inclination_angle=45.0,
        surface_area=1.0,
        thickness=0.003,
        width=1.0,
        length=1.0
    ),
    GeometryConfig(
        geometry_id="single_slope",
        inclination_angle=30.0,
        surface_area=1.15,
        thickness=0.003,
        width=1.0,
        length=1.0
    ),
    GeometryConfig(
        geometry_id="double_slope",
        inclination_angle=35.0,
        surface_area=1.2,
        thickness=0.003,
        width=1.0,
        length=1.0
    )
]

def generate_materials_csv(output_path: Optional[str] = None) -> Path:
    """
    Loads material properties and market prices, calculates mass and cost
    for each geometry, and writes the results to a CSV file.
    
    Args:
        output_path: Optional path to the output CSV. Defaults to data/processed/materials.csv.
        
    Returns:
        Path to the generated CSV file.
    """
    if output_path is None:
        output_path = str(get_data_dir() / "processed" / "materials.csv")
    
    output_path_obj = Path(output_path)
    ensure_dir(output_path_obj.parent)

    # 1. Load NIST Materials (Hardcoded/Local per T011)
    logger.info("Loading NIST material properties...")
    materials_data = load_nist_materials()
    
    if not materials_data:
        logger.error("No material data loaded from NIST source.")
        raise FileNotFoundError("NIST material data not found or empty.")

    # 2. Fetch Market Prices (Per T013)
    logger.info("Fetching market prices...")
    try:
        prices = fetch_market_prices()
        logger.info(f"Successfully fetched prices for {len(prices)} materials.")
    except Exception as e:
        logger.error(f"Failed to fetch market prices: {e}")
        # Per T013: If fetch fails, we cannot calculate costs. 
        # We must fail loudly or handle gracefully. 
        # The task requires a status field. If prices are missing, status is "invalid_price".
        prices = {}

    # 3. Prepare Output Rows
    rows = []
    fieldnames = [
        "material_id", "geometry_id", "thermal_conductivity", "emissivity", 
        "specific_heat", "density", "unit_price", "calculated_cost", "status"
    ]

    for mat in materials_data:
        mat_id = mat.material_id
        price = prices.get(mat_id)
        
        # Determine status
        if price is None:
            status = "invalid_price"
            unit_price = None
            cost = None
            logger.warning(f"Price missing for {mat_id}, marking as invalid.")
        else:
            status = "valid"
            unit_price = price
            cost = None # Will be calculated per geometry

        # Iterate over geometries to generate rows
        for geo in GEOMETRIES:
            # Calculate mass for this material-geometry combo
            mass = calculate_mass(mat, geo)
            
            current_cost = None
            if price is not None:
                current_cost = calculate_cost([mat], geo)
            
            row = {
                "material_id": mat_id,
                "geometry_id": geo.geometry_id,
                "thermal_conductivity": mat.thermal_conductivity,
                "emissivity": mat.emissivity,
                "specific_heat": mat.specific_heat,
                "density": mat.density,
                "unit_price": unit_price,
                "calculated_cost": current_cost if current_cost is not None else "",
                "status": status
            }
            rows.append(row)

    # 4. Write to CSV
    logger.info(f"Writing {len(rows)} rows to {output_path_obj}...")
    with open(output_path_obj, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info("CSV generation complete.")
    return output_path_obj

def main():
    """Entry point for the script."""
    root = get_project_root()
    os.chdir(root)
    logging.basicConfig(level=logging.INFO)
    
    try:
        path = generate_materials_csv()
        print(f"Successfully generated: {path}")
    except Exception as e:
        logger.error(f"Failed to generate materials CSV: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
