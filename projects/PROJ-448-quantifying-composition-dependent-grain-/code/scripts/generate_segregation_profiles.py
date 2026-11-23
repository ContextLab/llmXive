"""
T018: Generate segregation profiles for ternary systems.

This script implements User Story 1 (FR-003) by:
1. Loading equilibrium compositions from T048-Exec (data/processed/equilibrium_compositions.csv)
2. Loading DFT energies from T013-Exec (data/processed/surrogate_energies.json)
3. Applying the McLean isotherm model (T014) to compute GB concentrations
4. Saving results to data/processed/segregation_profiles.json

Constraint: If input files are missing, this script MUST raise a hard error.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

# Import from existing API surface
from code.models.mclean import calculate_mclean_concentration, McLeanResult
from code.config import get_logger, PROCESSED_PATH, DATA_RAW_PATH
from code.errors import DataLoadError

# Setup logging
logger = get_logger(__name__)

def load_equilibrium_compositions(filepath: Path) -> pd.DataFrame:
    """Load equilibrium compositions from CSV."""
    if not filepath.exists():
        raise DataLoadError(f"Equilibrium compositions file not found: {filepath}")
    
    logger.info(f"Loading equilibrium compositions from {filepath}")
    df = pd.read_csv(filepath)
    
    if df.empty:
        raise DataLoadError(f"Equilibrium compositions file is empty: {filepath}")
    
    logger.info(f"Loaded {len(df)} equilibrium composition records")
    return df

def load_dft_energies(filepath: Path) -> Dict[str, Any]:
    """Load surrogate DFT energies from JSON."""
    if not filepath.exists():
        raise DataLoadError(f"Surrogate energies file not found: {filepath}")
    
    logger.info(f"Loading surrogate DFT energies from {filepath}")
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    if not data:
        raise DataLoadError(f"Surrogate energies file is empty: {filepath}")
    
    # Check for fallback flag
    if data.get('source_type') == 'fallback' or data.get('MISSING_SOURCE'):
        logger.warning("Surrogate energies contain fallback data - proceeding with caution")
    
    logger.info(f"Loaded surrogate energies for {len(data.get('entries', data))} systems")
    return data

def get_system_base_elements(system_name: str) -> List[str]:
    """Extract base elements from system name (e.g., 'Fe-Cr-Mo' -> ['Fe', 'Cr', 'Mo'])."""
    return system_name.replace(' ', '').split('-')

def compute_segregation_profile(
    composition_row: pd.Series,
    dft_energies: Dict[str, Any],
    temperature: float,
    bulk_element: str,
    gb_element: str
) -> Optional[McLeanResult]:
    """
    Compute segregation profile for a single composition using McLean isotherm.
    
    Args:
        composition_row: Row from equilibrium_compositions.csv
        dft_energies: Loaded DFT energy data
        temperature: Temperature in Kelvin
        bulk_element: The bulk element (e.g., 'Fe')
        gb_element: The segregating element (e.g., 'Cr')
        
    Returns:
        McLeanResult if successful, None if data not found
    """
    # Build system key for DFT lookup
    elements = sorted([bulk_element, gb_element])
    system_key = '-'.join(elements)
    
    # Extract segregation energy from DFT data
    # DFT data structure: {'entries': [{'system': 'Fe-Cr', 'energy_eV': 0.5, ...}]}
    dft_entries = dft_energies.get('entries', dft_energies)
    seg_energy = None
    
    for entry in dft_entries:
        if entry.get('system') == system_key:
            seg_energy = entry.get('energy_eV')
            break
        
        # Fallback: check if system_key is in entry keys
        if system_key in entry:
            seg_energy = entry[system_key]
            break
    
    if seg_energy is None:
        logger.warning(f"No DFT energy found for system {system_key}, skipping")
        return None
    
    # Extract bulk concentration
    # Expected columns: 'Fe', 'Cr', 'Mo', etc.
    bulk_conc = composition_row.get(gb_element, 0.0)
    
    if bulk_conc <= 0.0:
        logger.debug(f"Bulk concentration for {gb_element} is zero, skipping")
        return None
    
    # Apply McLean isotherm
    result = calculate_mclean_concentration(
        segregation_energy_eV=seg_energy,
        bulk_concentration=bulk_conc,
        temperature_K=temperature,
        bulk_element=bulk_element,
        gb_element=gb_element
    )
    
    return result

def main():
    """Main entry point for T018."""
    logger.info("Starting T018: Generate segregation profiles for ternary systems")
    
    # Define input paths
    equilibrium_path = PROCESSED_PATH / "equilibrium_compositions.csv"
    dft_path = PROCESSED_PATH / "surrogate_energies.json"
    output_path = PROCESSED_PATH / "segregation_profiles.json"
    
    # Load input data (will raise hard error if missing)
    try:
        compositions_df = load_equilibrium_compositions(equilibrium_path)
        dft_energies = load_dft_energies(dft_path)
    except DataLoadError as e:
        logger.error(f"Failed to load required input data: {e}")
        raise
    
    # Define ternary systems to process
    ternary_systems = [
        "Fe-Cr-Mo",
        "Fe-Cr-V",
        "Fe-Mo-V",
        "Fe-Cr-W",
        "Fe-Mo-W"
    ]
    
    # Define solute elements to check for segregation
    solute_elements = ["Cr", "Mo", "V", "W"]
    
    # Process each row and compute profiles
    all_profiles = []
    
    for _, row in compositions_df.iterrows():
        system_name = row.get('system', '')
        
        if system_name not in ternary_systems:
            continue
        
        # Get temperature from row
        temperature = row.get('temperature_K', 800.0)
        
        # Compute segregation for each solute in this system
        for solute in solute_elements:
            if solute not in system_name:
                continue
            
            result = compute_segregation_profile(
                composition_row=row,
                dft_energies=dft_energies,
                temperature=temperature,
                bulk_element="Fe",
                gb_element=solute
            )
            
            if result is not None:
                profile_entry = {
                    "system": system_name,
                    "temperature_K": temperature,
                    "solute": solute,
                    "bulk_concentration": result.bulk_concentration,
                    "segregation_energy_eV": result.segregation_energy,
                    "equilibrium_concentration": result.equilibrium_concentration,
                    "saturation_flag": result.saturation_flag,
                    "source_type": "mclean_model",
                    "source_id": "T018_generate_profiles"
                }
                all_profiles.append(profile_entry)
    
    if not all_profiles:
        logger.warning("No segregation profiles were generated. Check input data.")
        # Still write empty file to indicate completion
        output_data = {
            "profiles": [],
            "metadata": {
                "generated_at": str(pd.Timestamp.now()),
                "source_script": "code/scripts/generate_segregation_profiles.py",
                "status": "no_data_generated"
            }
        }
    else:
        output_data = {
            "profiles": all_profiles,
            "metadata": {
                "generated_at": str(pd.Timestamp.now()),
                "source_script": "code/scripts/generate_segregation_profiles.py",
                "total_profiles": len(all_profiles),
                "systems_processed": list(set(p["system"] for p in all_profiles)),
                "status": "success"
            }
        }
    
    # Write output
    logger.info(f"Writing {len(all_profiles)} segregation profiles to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info("T018 completed successfully")
    return output_path

if __name__ == "__main__":
    main()