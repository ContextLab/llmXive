"""
Generate simulation_results.csv containing material_id, geometry_id,
steady_state_efficiency, total_cost, and convergence_status.

This script runs the validation (T023) on all material-geometry combinations
and only includes results where validation passes (energy balance closure).
"""
import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

from data_ingestion import load_nist_materials, GeometryConfig, calculate_cost
from simulation import (
    get_solar_irradiance_profile,
    run_simulation,
    calculate_time_averaged_efficiency,
    GeometryConfig as SimGeometryConfig,
)
from validation import validate_simulation_result
from utils import get_project_root, get_data_dir, ensure_dir, setup_logging

logger = logging.getLogger(__name__)

# Define the geometries to simulate (as per T026: 3 geometries, no angle sweep)
GEOMETRY_CONFIGS = [
    SimGeometryConfig(
        geometry_id="flat_plate",
        inclination_angle=0.0,
        surface_area=1.0,
        base_area=1.0,
        volume=0.005,
        material_thickness=0.002,
    ),
    SimGeometryConfig(
        geometry_id="single_slope",
        inclination_angle=30.0,
        surface_area=1.15,
        base_area=1.0,
        volume=0.005,
        material_thickness=0.002,
    ),
    SimGeometryConfig(
        geometry_id="double_slope",
        inclination_angle=45.0,
        surface_area=1.41,
        base_area=1.0,
        volume=0.005,
        material_thickness=0.002,
    ),
]

def run_batch_simulations(materials: List[Dict[str, Any]], geometries: List[SimGeometryConfig]) -> List[Dict[str, Any]]:
    """
    Run simulations for all material-geometry combinations and validate results.
    Only return results that pass T023 validation (energy balance closure).
    """
    results = []
    irradiance_profile = get_solar_irradiance_profile()
    
    if irradiance_profile is None:
        logger.error("Failed to load solar irradiance profile. Cannot proceed with simulations.")
        return results

    logger.info(f"Running {len(materials)} x {len(geometries)} = {len(materials) * len(geometries)} simulations...")

    for material in materials:
        material_id = material["material_id"]
        
        for geometry in geometries:
            geometry_id = geometry.geometry_id
            
            try:
                # Run simulation
                sim_result = run_simulation(
                    material_profile=material,
                    geometry_config=geometry,
                    irradiance_profile=irradiance_profile,
                )
                
                if sim_result is None or not sim_result.get("success", False):
                    logger.warning(f"Simulation failed for {material_id}/{geometry_id}: {sim_result.get('error', 'Unknown error')}")
                    continue
                
                # Validate result (T023 - Primary Validation: Energy Balance Closure)
                validation_result = validate_simulation_result(sim_result)
                
                if not validation_result.get("passed", False):
                    logger.info(f"Validation failed for {material_id}/{geometry_id}: {validation_result.get('reason', 'Unknown')}")
                    # T023: If validation fails, exclude from results
                    continue
                
                # Calculate cost using the material and geometry
                cost = calculate_cost([material], geometry)
                
                # Extract efficiency (time-averaged over final 30 minutes)
                efficiency = calculate_time_averaged_efficiency(sim_result)
                
                result_entry = {
                    "material_id": material_id,
                    "geometry_id": geometry_id,
                    "steady_state_efficiency": round(efficiency, 6),
                    "total_cost": round(cost, 2),
                    "convergence_status": "converged" if sim_result.get("converged", False) else "not_converged",
                }
                
                results.append(result_entry)
                logger.info(f"Successfully processed: {material_id}/{geometry_id} (eff={efficiency:.4f}, cost={cost:.2f})")
                
            except Exception as e:
                logger.error(f"Error processing {material_id}/{geometry_id}: {e}", exc_info=True)
                continue

    return results

def save_simulation_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Save simulation results to CSV."""
    ensure_dir(output_path.parent)
    
    fieldnames = ["material_id", "geometry_id", "steady_state_efficiency", "total_cost", "convergence_status"]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def main() -> None:
    """Main entry point for generating simulation results."""
    setup_logging()
    project_root = get_project_root()
    data_dir = get_data_dir()
    
    # Load materials from T015 output
    materials_path = data_dir / "processed" / "materials.csv"
    if not materials_path.exists():
        logger.error(f"Materials CSV not found at {materials_path}. Run T015 first.")
        return
    
    # Load materials from CSV
    materials = []
    with open(materials_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("status") == "valid":
                materials.append({
                    "material_id": row["material_id"],
                    "thermal_conductivity": float(row["thermal_conductivity"]),
                    "emissivity": float(row["emissivity"]),
                    "specific_heat": float(row["specific_heat"]),
                    "density": float(row["density"]),
                    "unit_price": float(row["unit_price"]),
                })
    
    if not materials:
        logger.error("No valid materials found in materials.csv. Cannot proceed.")
        return
    
    logger.info(f"Loaded {len(materials)} valid materials")
    
    # Run batch simulations and validation
    results = run_batch_simulations(materials, GEOMETRY_CONFIGS)
    
    if not results:
        logger.warning("No results passed validation. No CSV will be generated.")
        return
    
    # Save results
    output_path = data_dir / "processed" / "simulation_results.csv"
    save_simulation_results(results, output_path)
    
    logger.info(f"Generated {output_path} with {len(results)} valid entries")

if __name__ == "__main__":
    main()