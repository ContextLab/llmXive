"""
Generate segregation profiles for ternary systems.

This script loads equilibrium compositions and DFT energies,
applies the McLean isotherm model, and outputs the results
to data/processed/segregation_profiles.json.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd

# Import from project modules
from code.config import PROCESSED_PATH, DATA_RAW_PATH, get_logger
from code.models.mclean import calculate_mclean_concentration, McLeanResult
from code.errors import DataLoadError, ConfigurationError

# Ensure the logger is configured
logger = get_logger(__name__)

def load_equilibrium_compositions(filepath: Path) -> pd.DataFrame:
    """Load equilibrium compositions from CSV."""
    if not filepath.exists():
        raise DataLoadError(f"Equilibrium compositions file not found: {filepath}")
    
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df)} equilibrium composition records from {filepath}")
        return df
    except Exception as e:
        raise DataLoadError(f"Failed to load equilibrium compositions: {e}")

def load_dft_energies(filepath: Path) -> Dict[str, Any]:
    """Load DFT energies from JSON."""
    if not filepath.exists():
        raise DataLoadError(f"DFT energies file not found: {filepath}")
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded DFT energies for {len(data)} systems from {filepath}")
        return data
    except json.JSONDecodeError as e:
        raise DataLoadError(f"Invalid JSON in DFT energies file: {e}")
    except Exception as e:
        raise DataLoadError(f"Failed to load DFT energies: {e}")

def get_system_base_elements(system_name: str) -> List[str]:
    """Extract base elements from a system name (e.g., 'Fe-Cr-Mo' -> ['Fe', 'Cr', 'Mo'])."""
    # Handle common naming conventions
    if '-' in system_name:
        return system_name.split('-')
    elif '_' in system_name:
        return system_name.split('_')
    else:
        # Fallback: try to parse common ternary patterns
        logger.warning(f"Could not parse system name: {system_name}")
        return []

def compute_segregation_profile(
    system_name: str,
    bulk_composition: Dict[str, float],
    temperature: float,
    dft_energies: Dict[str, Any],
    reference_element: str = "Fe"
) -> Optional[Dict[str, Any]]:
    """
    Compute segregation profile for a specific system and condition.
    
    Args:
        system_name: Name of the alloy system (e.g., "Fe-Cr-Mo")
        bulk_composition: Dictionary of bulk concentrations (e.g., {"Fe": 0.8, "Cr": 0.15, "Mo": 0.05})
        temperature: Temperature in Kelvin
        dft_energies: Dictionary of DFT segregation energies
        reference_element: The solvent element (default: Fe)
        
    Returns:
        Dictionary containing the segregation profile or None if data is missing
    """
    elements = get_system_base_elements(system_name)
    if len(elements) < 3:
        logger.warning(f"Skipping {system_name}: not a ternary system")
        return None
    
    # Extract solute elements (all except reference)
    solutes = [e for e in elements if e != reference_element]
    
    profile = {
        "system": system_name,
        "temperature_K": temperature,
        "bulk_composition": bulk_composition,
        "segregation_data": []
    }
    
    for solute in solutes:
        # Look up DFT energy for this solute in this system
        # Try different key formats
        energy_key = f"{system_name}_{solute}"
        if energy_key not in dft_energies:
            energy_key = f"{solute}_in_{system_name}"
        if energy_key not in dft_energies:
            # Try to find any entry containing the solute
            for key, value in dft_energies.items():
                if solute in key and system_name.replace("-", "_") in key:
                    energy_key = key
                    break
        
        if energy_key not in dft_energies:
            logger.warning(f"No DFT energy found for {solute} in {system_name}")
            continue
        
        segregation_energy_eV = dft_energies[energy_key]
        bulk_conc = bulk_composition.get(solute, 0.0)
        
        if bulk_conc <= 0:
            continue
        
        try:
            result = calculate_mclean_concentration(
                segregation_energy_eV,
                bulk_conc,
                temperature
            )
            
            profile["segregation_data"].append({
                "solute": solute,
                "segregation_energy_eV": segregation_energy_eV,
                "bulk_concentration": bulk_conc,
                "equilibrium_concentration": result.equilibrium_concentration,
                "saturation_flag": result.saturation_flag
            })
            
            logger.info(
                f"Computed segregation for {solute} in {system_name}: "
                f"E_seg={segregation_energy_eV:.3f} eV, "
                f"C_gb={result.equilibrium_concentration:.4f}"
            )
            
        except Exception as e:
            logger.error(f"Error computing McLean concentration for {solute}: {e}")
            continue
    
    return profile if profile["segregation_data"] else None

def main():
    """Main entry point for generating segregation profiles."""
    logger.info("Starting segregation profile generation")
    
    # Define paths
    equilibrium_compositions_path = PROCESSED_PATH / "equilibrium_compositions.csv"
    dft_energies_path = DATA_RAW_PATH / "dft_energies.json"
    output_path = PROCESSED_PATH / "segregation_profiles.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load input data
    try:
        equilibrium_df = load_equilibrium_compositions(equilibrium_compositions_path)
        dft_energies = load_dft_energies(dft_energies_path)
    except DataLoadError as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)
    
    # Process each system
    all_profiles = []
    
    # Iterate through unique systems in the equilibrium data
    systems = equilibrium_df['system'].unique() if 'system' in equilibrium_df.columns else []
    
    for system in systems:
        # Filter data for this system
        system_data = equilibrium_df[equilibrium_df['system'] == system]
        
        # Check if this is a ternary system
        if not system.startswith("Fe-") or len(system.split('-')) != 3:
            logger.debug(f"Skipping non-ternary system: {system}")
            continue
        
        # Process each row (temperature/bulk composition variant)
        for _, row in system_data.iterrows():
            bulk_composition = {
                col: float(row[col]) 
                for col in row.index 
                if col not in ['system', 'temperature_K'] and not pd.isna(row[col])
            }
            
            temperature = float(row['temperature_K'])
            
            profile = compute_segregation_profile(
                system_name=system,
                bulk_composition=bulk_composition,
                temperature=temperature,
                dft_energies=dft_energies
            )
            
            if profile:
                all_profiles.append(profile)
    
    # Write output
    output_data = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "total_profiles": len(all_profiles),
        "profiles": all_profiles
    }
    
    try:
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Successfully wrote {len(all_profiles)} profiles to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        sys.exit(1)
    
    logger.info("Segregation profile generation completed")
    return output_data

if __name__ == "__main__":
    main()
