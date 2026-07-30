"""
Module to calculate the Defense Allocation Index (DAI) from compiled trait data.

The DAI is defined as:
    DAI = (mean standardized chemical traits) / (mean standardized physical traits)

This module reads the compiled trait data from the fallback summary produced by
T025a and T025b, standardizes traits within their types (chemical/physical),
computes the means, and calculates the ratio.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from src.utils.schemas import DefenseAllocationIndex

# Initialize logger
logger = get_logger(__name__)

# Define trait categories based on typical plant defense classifications
# These should be configurable, but we use a standard set for now
CHEMICAL_TRAITS = [
    "alkaloids", "terpenoids", "phenolics", "glucosinolates",
    "cyanogenic_glycosides", "tannins", "saponins", "flavonoids"
]

PHYSICAL_TRAITS = [
    "thorns", "spines", "trichomes", "leaf_thickness", "silica_content",
    "lignin_content", "cuticle_thickness", "leaf_toughness"
]

def load_trait_fallback_summary(file_path: Path) -> Dict[str, Any]:
    """
    Load the trait fallback summary JSON file.
    
    Args:
        file_path: Path to the trait fallback summary JSON file.
        
    Returns:
        Dictionary containing the trait data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Trait fallback summary not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_trait_values(species_data: Dict[str, Any]) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Extract chemical and physical trait values for a species.
    
    Args:
        species_data: Dictionary containing trait data for a species.
        
    Returns:
        Tuple of (chemical_traits_dict, physical_traits_dict).
    """
    chemical_values = {}
    physical_values = {}
    
    # Extract from primary source results
    if "primary_source_results" in species_data:
        primary = species_data["primary_source_results"]
        if isinstance(primary, dict):
            for trait_name, trait_value in primary.items():
                trait_lower = trait_name.lower()
                if any(chem in trait_lower for chem in CHEMICAL_TRAITS):
                    chemical_values[trait_name] = float(trait_value) if trait_value is not None else np.nan
                elif any(phys in trait_lower for phys in PHYSICAL_TRAITS):
                    physical_values[trait_name] = float(trait_value) if trait_value is not None else np.nan
    
    # Extract from fallback results if not found in primary
    if "fallback_results" in species_data:
        fallback = species_data["fallback_results"]
        if isinstance(fallback, dict):
            for trait_name, trait_value in fallback.items():
                trait_lower = trait_name.lower()
                # Only add if not already present
                if trait_name not in chemical_values and trait_name not in physical_values:
                    if any(chem in trait_lower for chem in CHEMICAL_TRAITS):
                        chemical_values[trait_name] = float(trait_value) if trait_value is not None else np.nan
                    elif any(phys in trait_lower for phys in PHYSICAL_TRAITS):
                        physical_values[trait_name] = float(trait_value) if trait_value is not None else np.nan
    
    return chemical_values, physical_values

def standardize_traits(traits_dict: Dict[str, float]) -> List[float]:
    """
    Standardize trait values using z-score normalization.
    
    Args:
        traits_dict: Dictionary of trait names to values.
        
    Returns:
        List of standardized values.
    """
    values = [v for v in traits_dict.values() if not pd.isna(v)]
    
    if len(values) == 0:
        return []
    
    mean_val = np.mean(values)
    std_val = np.std(values)
    
    if std_val == 0:
        # If all values are the same, return zeros
        return [0.0] * len(values)
    
    standardized = [(v - mean_val) / std_val for v in values if not pd.isna(v)]
    return standardized

def calculate_dai(chemical_values: Dict[str, float], physical_values: Dict[str, float]) -> Optional[float]:
    """
    Calculate the Defense Allocation Index.
    
    Args:
        chemical_values: Dictionary of chemical trait values.
        physical_values: Dictionary of physical trait values.
        
    Returns:
        The DAI value, or None if calculation is not possible.
    """
    chem_std = standardize_traits(chemical_values)
    phys_std = standardize_traits(physical_values)
    
    if len(chem_std) == 0 or len(phys_std) == 0:
        logger.warning("Insufficient traits for DAI calculation")
        return None
    
    mean_chem = np.mean(chem_std)
    mean_phys = np.mean(phys_std)
    
    if mean_phys == 0:
        # Avoid division by zero
        logger.warning("Physical trait mean is zero, cannot calculate DAI")
        return None
    
    dai = mean_chem / mean_phys
    return dai

def compile_defense_allocation_index(trait_summary_path: Path, output_path: Path) -> List[Dict[str, Any]]:
    """
    Compile the Defense Allocation Index for all species.
    
    Args:
        trait_summary_path: Path to the trait fallback summary JSON file.
        output_path: Path where the output CSV will be written.
        
    Returns:
        List of DAI records.
    """
    logger.info(f"Loading trait data from {trait_summary_path}")
    trait_data = load_trait_fallback_summary(trait_summary_path)
    
    dai_records = []
    
    # Determine the structure of the data
    # The data might be in "primary_source_results" or directly as species keys
    species_keys = []
    
    if "primary_source_results" in trait_data:
        species_keys = list(trait_data["primary_source_results"].keys())
    elif "target_species" in trait_data:
        # If we have target species list, use that
        species_keys = trait_data["target_species"]
    else:
        # Try to find species keys directly
        for key in trait_data.keys():
            if key not in ["primary_source_results", "fallback_results", "missing_from_try", "target_species"]:
                species_keys.append(key)
    
    if not species_keys:
        logger.warning("No species found in trait data")
        return []
    
    logger.info(f"Processing {len(species_keys)} species")
    
    for species_name in species_keys:
        species_data = None
        
        # Try to get species data from primary_source_results
        if "primary_source_results" in trait_data and species_name in trait_data["primary_source_results"]:
            species_data = {
                "primary_source_results": trait_data["primary_source_results"][species_name]
            }
            if "fallback_results" in trait_data and species_name in trait_data["fallback_results"]:
                species_data["fallback_results"] = trait_data["fallback_results"][species_name]
        else:
            # Try direct access
            if species_name in trait_data:
                species_data = trait_data[species_name]
            else:
                logger.debug(f"Skipping {species_name}: no data found")
                continue
        
        if species_data is None:
            continue
        
        chemical_values, physical_values = extract_trait_values(species_data)
        
        if len(chemical_values) == 0 and len(physical_values) == 0:
            logger.debug(f"No traits found for {species_name}")
            continue
        
        dai = calculate_dai(chemical_values, physical_values)
        
        record = {
            "species": species_name,
            "chemical_trait_count": len(chemical_values),
            "physical_trait_count": len(physical_values),
            "dai": dai,
            "chemical_mean_std": np.mean([v for v in chemical_values.values() if not pd.isna(v)]) if chemical_values else np.nan,
            "physical_mean_std": np.mean([v for v in physical_values.values() if not pd.isna(v)]) if physical_values else np.nan
        }
        
        dai_records.append(record)
        logger.debug(f"Calculated DAI for {species_name}: {dai}")
    
    # Create DataFrame and save
    if dai_records:
        df = pd.DataFrame(dai_records)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved DAI results to {output_path}")
    else:
        # Create empty file with headers
        pd.DataFrame(columns=["species", "chemical_trait_count", "physical_trait_count", "dai", "chemical_mean_std", "physical_mean_std"]).to_csv(output_path, index=False)
        logger.warning("No DAI values could be calculated, created empty output file")
    
    return dai_records

def main():
    """Main entry point for the Defense Allocation Index calculation."""
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    trait_summary_path = project_root / "data" / "processed" / "trait_fallback_summary.json"
    output_path = project_root / "data" / "processed" / "defense_allocation_index.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        compile_defense_allocation_index(trait_summary_path, output_path)
        logger.info("Defense Allocation Index calculation completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Failed to calculate Defense Allocation Index: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
