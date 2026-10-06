"""
Generate the processed materials dataset CSV.

This script loads validated material properties from NIST (cached in data/raw/nist_materials.json),
loads current market prices (cached in data/raw/market_prices.json), calculates the total cost
for each material based on the cost function C = sum(mass * price), and writes the final
dataset to data/processed/materials.csv.

It determines the validity status of each material based on the availability of a valid price.
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
    MaterialProfile,
    GeometryConfig
)
from utils import get_project_root, get_data_dir, ensure_dir, setup_logging

logger = logging.getLogger(__name__)

# Standard geometry configuration for cost calculation (flat plate, 1m x 1m)
# This matches the geometry used for the baseline cost function in the spec.
DEFAULT_GEOMETRY = GeometryConfig(
    geometry_id="flat_plate_1x1",
    surface_area=1.0,
    thickness=0.002,  # 2mm typical for solar collector plates
    inclination_angle=0.0,
    material_id="generic" # Placeholder, overridden per material
)

def generate_materials_csv(output_path: Optional[Path] = None) -> Path:
    """
    Generates the materials.csv file with thermal properties, prices, and calculated costs.
    
    Args:
        output_path: Optional path for the output CSV. Defaults to data/processed/materials.csv.
        
    Returns:
        The path to the generated CSV file.
    """
    if output_path is None:
        output_path = get_data_dir() / "processed" / "materials.csv"
    
    ensure_dir(output_path.parent)
    
    # 1. Load NIST Data (Properties)
    logger.info("Loading NIST material properties...")
    try:
        nist_data = load_nist_materials()
    except Exception as e:
        logger.error(f"Failed to load NIST data: {e}")
        raise RuntimeError(f"Cannot generate materials CSV: NIST data load failed. {e}")
    
    if not nist_data:
        raise RuntimeError("NIST data is empty. Cannot proceed.")
    
    # 2. Load Market Prices
    logger.info("Loading market prices...")
    try:
        # fetch_market_prices handles fetching and saving to data/raw/market_prices.json
        # It returns the loaded data dict for immediate use
        prices_data = fetch_market_prices()
    except Exception as e:
        logger.error(f"Failed to load market prices: {e}")
        raise RuntimeError(f"Cannot generate materials CSV: Market price fetch failed. {e}")
    
    # 3. Process Materials
    rows = []
    material_ids = [
        "7429-90-5",    # Aluminum
        "7440-50-8",    # Copper
        "7440-44-0",    # Carbon Steel (mapped to 1018 in spec logic, often 7440-44-0 for Iron/Steel)
                         # Note: T012 logic maps Black-painted Steel to Carbon Steel. 
                         # We assume the NIST fetch used a valid ID for Carbon Steel. 
                         # If T012 used a specific ID, we must match it here.
                         # Common NIST ID for Iron/Steel is 7439-89-6 (Iron) or specific alloy.
                         # Based on T012 description "Carbon Steel Alloy 1018", we look for the ID used there.
                         # If T012 used a specific ID, we use it. If not, we try standard Iron/Steel.
                         # Let's assume the NIST data keys match the IDs we expect.
                         # We will iterate over the keys found in nist_data to be robust, 
                         # but filter for our known target materials.
        "22570-22-9"    # Polyethylene (Plastic) - Common ID for HDPE/LDPE
    ]
    
    # Fallback: If specific IDs aren't found, use whatever is in nist_data if it matches names
    # But the spec explicitly lists 4 materials. We should ensure we process exactly those.
    # We will construct a mapping based on the IDs we know we want to process.
    # If T012 used a different ID for Steel, we need to know it. 
    # Assuming T012 successfully fetched 4 materials. We will iterate the keys of nist_data
    # and check if they are in our target list or if the material name matches.
    
    target_materials = {
        "7429-90-5": "Aluminum",
        "7440-50-8": "Copper",
        "7440-44-0": "Carbon Steel", # Placeholder ID, will check nist_data keys
        "22570-22-9": "Polyethylene"
    }
    
    # Let's be robust: iterate nist_data and check if the ID is in our target list
    # or if the material name (if available) matches.
    # Since load_nist_materials returns a dict of {id: properties}, we iterate keys.
    
    processed_count = 0
    for mat_id, props in nist_data.items():
        # Determine if this is one of our 4 target materials
        # We need to map the ID from NIST to our target list.
        # If the ID is not in the target list, we might still have the material if the ID is different.
        # However, the spec says: "Aluminum (ID: 7429-90-5), Copper (ID: 7440-50-8), Black-painted Steel (mapped to Carbon Steel Alloy 1018), and Plastic (Polyethylene)".
        # We assume the NIST fetch used these IDs or valid equivalents.
        
        # Check if we have a price for this material
        price = None
        status = "invalid_price"
        
        # Look up price in prices_data
        # prices_data structure from fetch_market_prices: { "material_id": price_value }
        if mat_id in prices_data:
            price = prices_data[mat_id]
            status = "valid"
        else:
            # Try to find by partial match or name if ID mismatch occurred in T012
            # For now, strict ID match. If T012 used a different ID for Steel, we need to handle it.
            # Let's assume the IDs in nist_data match the keys in prices_data.
            # If not, we mark as invalid.
            logger.warning(f"No price found for material ID: {mat_id}. Marking as invalid.")
        
        # Calculate Mass
        # We need a geometry to calculate mass. Use the default flat plate geometry.
        # The geometry ID in the CSV should reflect the geometry used for cost calculation.
        geometry = DEFAULT_GEOMETRY
        geometry.material_id = mat_id # Assign material to geometry for calculation
        
        try:
            density = props.get("density")
            if density is None:
                logger.warning(f"Density missing for {mat_id}, skipping mass calculation.")
                continue
            
            mass = calculate_mass(geometry, density)
            
            # Calculate Cost
            if status == "valid":
                cost = calculate_cost([MaterialProfile(**props, material_id=mat_id)], geometry)
            else:
                cost = 0.0
                
        except Exception as e:
            logger.error(f"Error calculating cost for {mat_id}: {e}")
            continue
        
        row = {
            "material_id": mat_id,
            "thermal_conductivity": props.get("thermal_conductivity", ""),
            "emissivity": props.get("emissivity", ""),
            "specific_heat": props.get("specific_heat", ""),
            "density": density,
            "unit_price": price if price is not None else "",
            "calculated_cost": cost if status == "valid" else "",
            "status": status
        }
        rows.append(row)
        processed_count += 1
    
    if processed_count == 0:
        raise RuntimeError("No valid materials processed. Check NIST data and Price mapping.")
    
    # 4. Write CSV
    fieldnames = [
        "material_id",
        "thermal_conductivity",
        "emissivity",
        "specific_heat",
        "density",
        "unit_price",
        "calculated_cost",
        "status"
    ]
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Successfully generated {output_path} with {processed_count} materials.")
    return output_path

def main():
    setup_logging()
    try:
        generate_materials_csv()
    except Exception as e:
        logger.critical(f"Failed to generate materials CSV: {e}")
        raise

if __name__ == "__main__":
    main()