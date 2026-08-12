import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from config import Config, load_config
from features.constants import get_atomic_mass, get_atomic_radius, get_electronegativity

logger = logging.getLogger(__name__)

def parse_composition_string(composition_str: str) -> Dict[str, float]:
    """
    Parse a composition string like 'Fe0.5Ni0.3Cu0.2' into a dictionary.
    Handles formats: ElementMassFraction (e.g., Fe0.5) or Element:MassFraction (e.g., Fe:0.5).
    """
    if not isinstance(composition_str, str):
        raise ValueError(f"Composition must be a string, got {type(composition_str)}")
    
    composition_str = composition_str.strip()
    elements = {}
    
    # Try standard format: ElementMassFraction (e.g., Fe0.5)
    # Regex to match Element symbol (1-2 chars) followed by float
    import re
    pattern = r'([A-Z][a-z]?)(\d+\.?\d*)'
    matches = re.findall(pattern, composition_str)
    
    if not matches:
        # Try alternative format: Element:MassFraction
        parts = composition_str.split(',')
        for part in parts:
            if ':' in part:
                elem, mass = part.split(':')
                elements[elem.strip()] = float(mass.strip())
            else:
                # Fallback to regex if comma separated but no colon
                matches = re.findall(r'([A-Z][a-z]?)(\d+\.?\d*)', part)
                for elem, mass in matches:
                    elements[elem] = float(mass)
    else:
        for elem, mass in matches:
            elements[elem] = float(mass)
    
    # Normalize to sum to 1.0
    total = sum(elements.values())
    if total > 0:
        for elem in elements:
            elements[elem] /= total
    
    return elements

def mass_to_atomic_fractions(mass_fractions: Dict[str, float]) -> Dict[str, float]:
    """
    Convert mass fractions to atomic fractions.
    atomic_fraction_i = (mass_fraction_i / atomic_mass_i) / sum(mass_fraction_j / atomic_mass_j)
    """
    atomic_moles = {}
    for elem, mass_frac in mass_fractions.items():
        atomic_mass = get_atomic_mass(elem)
        if atomic_mass is None:
            logger.warning(f"Atomic mass not found for {elem}, skipping")
            continue
        atomic_moles[elem] = mass_frac / atomic_mass
    
    total_moles = sum(atomic_moles.values())
    if total_moles == 0:
        return {}
    
    atomic_fractions = {elem: moles / total_moles for elem, moles in atomic_moles.items()}
    return atomic_fractions

def add_atomic_fractions_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a column 'atomic_fractions' containing the atomic fraction dict for each row.
    """
    def compute_atomic(row):
        mass_fractions = row['composition']
        if isinstance(mass_fractions, str):
            mass_fractions = parse_composition_string(mass_fractions)
        return mass_to_atomic_fractions(mass_fractions)
    
    df['atomic_fractions'] = df.apply(compute_atomic, axis=1)
    return df

def compute_mean_atomic_mass(atomic_fractions: Dict[str, float]) -> float:
    """Compute mean atomic mass: Σ(atomic_fraction_i × atomic_mass_i)"""
    if not atomic_fractions:
        return 0.0
    
    total_mass = 0.0
    for elem, frac in atomic_fractions.items():
        mass = get_atomic_mass(elem)
        if mass is not None:
            total_mass += frac * mass
    return total_mass

def compute_mean_atomic_radius(atomic_fractions: Dict[str, float]) -> float:
    """Compute mean atomic radius: Σ(atomic_fraction_i × atomic_radius_i)"""
    if not atomic_fractions:
        return 0.0
    
    total_radius = 0.0
    for elem, frac in atomic_fractions.items():
        radius = get_atomic_radius(elem)
        if radius is not None:
            total_radius += frac * radius
    return total_radius

def compute_electronegativity_variance(atomic_fractions: Dict[str, float]) -> float:
    """Compute electronegativity variance: Σ(atomic_fraction_i × (χ_i - χ_mean)^2)"""
    if not atomic_fractions:
        return 0.0
    
    # First compute mean electronegativity
    chi_mean = 0.0
    for elem, frac in atomic_fractions.items():
        chi = get_electronegativity(elem)
        if chi is not None:
            chi_mean += frac * chi
    
    # Compute variance
    variance = 0.0
    for elem, frac in atomic_fractions.items():
        chi = get_electronegativity(elem)
        if chi is not None:
            variance += frac * (chi - chi_mean) ** 2
    
    return variance

def compute_atomic_radius_mismatch(atomic_fractions: Dict[str, float]) -> float:
    """
    Compute atomic radius mismatch: σ_r / r_mean
    where σ_r is the standard deviation of atomic radii weighted by atomic fraction.
    """
    if not atomic_fractions:
        return 0.0
    
    radii = []
    weights = []
    for elem, frac in atomic_fractions.items():
        radius = get_atomic_radius(elem)
        if radius is not None:
            radii.append(radius)
            weights.append(frac)
    
    if not radii:
        return 0.0
    
    radii = np.array(radii)
    weights = np.array(weights)
    
    r_mean = np.average(radii, weights=weights)
    if r_mean == 0:
        return 0.0
    
    variance = np.average((radii - r_mean) ** 2, weights=weights)
    sigma_r = np.sqrt(variance)
    
    return sigma_r / r_mean

def compute_packing_efficiency(atomic_fractions: Dict[str, float]) -> float:
    """
    Compute Packing Efficiency Proxy:
    PE = 1 - (σ_r / r_mean)^2 * (1 - 0.5 * (Δr/r_mean)^2)
    
    Where:
    - σ_r is the standard deviation of atomic radii (weighted by atomic fraction)
    - r_mean is the mean atomic radius
    - Δr is the atomic radius mismatch (σ_r / r_mean)
    
    Guard Clause: If σ_r = 0, set PE = 1.0
    """
    if not atomic_fractions:
        return 0.0
    
    radii = []
    weights = []
    for elem, frac in atomic_fractions.items():
        radius = get_atomic_radius(elem)
        if radius is not None:
            radii.append(radius)
            weights.append(frac)
    
    if not radii:
        return 0.0
    
    radii = np.array(radii)
    weights = np.array(weights)
    
    r_mean = np.average(radii, weights=weights)
    
    if r_mean == 0:
        return 0.0
    
    variance = np.average((radii - r_mean) ** 2, weights=weights)
    sigma_r = np.sqrt(variance)
    
    # Guard Clause: If σ_r = 0, set PE = 1.0
    if sigma_r == 0:
        return 1.0
    
    # Calculate atomic radius mismatch (Δr / r_mean)
    delta_r_over_r_mean = sigma_r / r_mean
    
    # Calculate PE
    # PE = 1 - (σ_r / r_mean)^2 * (1 - 0.5 * (Δr/r_mean)^2)
    pe = 1.0 - (delta_r_over_r_mean ** 2) * (1.0 - 0.5 * (delta_r_over_r_mean ** 2))
    
    return pe

def add_compositional_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all compositional descriptors to the DataFrame:
    - mean_atomic_mass
    - mean_atomic_radius
    - electronegativity_variance
    - atomic_radius_mismatch
    - packing_efficiency
    """
    def compute_row_descriptors(row):
        atomic_fractions = row.get('atomic_fractions')
        if atomic_fractions is None:
            # Try to compute from composition if atomic_fractions not present
            composition = row.get('composition')
            if isinstance(composition, str):
                mass_fractions = parse_composition_string(composition)
                atomic_fractions = mass_to_atomic_fractions(mass_fractions)
                row['atomic_fractions'] = atomic_fractions
            elif isinstance(composition, dict):
                atomic_fractions = mass_to_atomic_fractions(composition)
                row['atomic_fractions'] = atomic_fractions
            else:
                return {
                    'mean_atomic_mass': 0.0,
                    'mean_atomic_radius': 0.0,
                    'electronegativity_variance': 0.0,
                    'atomic_radius_mismatch': 0.0,
                    'packing_efficiency': 0.0
                }
        
        return {
            'mean_atomic_mass': compute_mean_atomic_mass(atomic_fractions),
            'mean_atomic_radius': compute_mean_atomic_radius(atomic_fractions),
            'electronegativity_variance': compute_electronegativity_variance(atomic_fractions),
            'atomic_radius_mismatch': compute_atomic_radius_mismatch(atomic_fractions),
            'packing_efficiency': compute_packing_efficiency(atomic_fractions)
        }
    
    descriptors = df.apply(compute_row_descriptors, axis=1)
    descriptors_df = pd.DataFrame(descriptors.tolist(), index=df.index)
    df = pd.concat([df, descriptors_df], axis=1)
    
    return df

def main():
    """
    Main entry point to compute packing efficiency and save to clean_data.csv.
    """
    config = load_config()
    logger.info("Starting packing efficiency computation...")
    
    input_path = config.data_dir / "clean_data.csv"
    output_path = config.data_dir / "clean_data.csv"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Ensure composition column exists
    if 'composition' not in df.columns:
        logger.error("Column 'composition' not found in DataFrame")
        raise ValueError("Column 'composition' not found in DataFrame")
    
    # Compute packing efficiency
    logger.info("Computing packing efficiency...")
    df = add_compositional_descriptors(df)
    
    # Verify packing_efficiency column was added
    if 'packing_efficiency' not in df.columns:
        logger.error("Failed to add 'packing_efficiency' column")
        raise RuntimeError("Failed to add 'packing_efficiency' column")
    
    # Save to clean_data.csv
    logger.info(f"Saving updated data to {output_path}")
    df.to_csv(output_path, index=False)
    
    logger.info(f"Packing efficiency computation complete. Saved to {output_path}")
    logger.info(f"Sample packing efficiency values:\n{df['packing_efficiency'].head()}")
    
    return df

if __name__ == "__main__":
    main()