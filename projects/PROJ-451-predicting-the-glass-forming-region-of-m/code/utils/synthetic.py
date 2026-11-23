"""
Synthetic data generator for CI reproducibility fallback.

Generates valid alloy compositions with realistic descriptors when
the canonical Zenodo DOI is inaccessible.

This module is used ONLY as a fallback mechanism and does not
replace real experimental data.
"""
import os
import sys
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Import from existing project modules
from features.descriptors import (
    compute_atomic_radius,
    compute_electronegativity,
    compute_valence_electron_concentration,
    compute_atomic_size_mismatch,
    compute_electronegativity_difference,
    compute_mixing_enthalpy,
    parse_composition
)
from utils.config import get_raw_data_path, ensure_data_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Common alloy systems for metallic glasses
COMMON_ALLOY_SYSTEMS = [
    ['Zr', 'Cu', 'Al'],
    ['Zr', 'Cu', 'Ni'],
    ['Zr', 'Ti', 'Cu'],
    ['Pd', 'Cu', 'Si'],
    ['Pd', 'Ni', 'P'],
    ['Mg', 'Cu', 'Y'],
    ['La', 'Al', 'Ni'],
    ['Fe', 'B', 'Si'],
    ['Co', 'Fe', 'B'],
    ['Ti', 'Cu', 'Ni'],
    ['Zr', 'Al', 'Ni'],
    ['Cu', 'Zr', 'Ti'],
    ['Ni', 'Nb', 'Zr'],
    ['Fe', 'B', 'C'],
    ['Zr', 'Cu', 'Ag', 'Al']
]

# Common phases
PHASES = ['amorphous', 'crystalline']

# Element properties for synthetic generation (simplified periodic table data)
ELEMENT_PROPERTIES = {
    'Zr': {'atomic_radius': 160.0, 'electronegativity': 1.33, 'valence_electrons': 4, 'atomic_number': 40},
    'Cu': {'atomic_radius': 128.0, 'electronegativity': 1.90, 'valence_electrons': 11, 'atomic_number': 29},
    'Al': {'atomic_radius': 143.0, 'electronegativity': 1.61, 'valence_electrons': 3, 'atomic_number': 13},
    'Ni': {'atomic_radius': 124.0, 'electronegativity': 1.91, 'valence_electrons': 10, 'atomic_number': 28},
    'Ti': {'atomic_radius': 147.0, 'electronegativity': 1.54, 'valence_electrons': 4, 'atomic_number': 22},
    'Pd': {'atomic_radius': 137.0, 'electronegativity': 2.20, 'valence_electrons': 10, 'atomic_number': 46},
    'Si': {'atomic_radius': 117.0, 'electronegativity': 1.90, 'valence_electrons': 4, 'atomic_number': 14},
    'P': {'atomic_radius': 110.0, 'electronegativity': 2.19, 'valence_electrons': 5, 'atomic_number': 15},
    'Mg': {'atomic_radius': 160.0, 'electronegativity': 1.31, 'valence_electrons': 2, 'atomic_number': 12},
    'Y': {'atomic_radius': 180.0, 'electronegativity': 1.22, 'valence_electrons': 3, 'atomic_number': 39},
    'La': {'atomic_radius': 187.0, 'electronegativity': 1.10, 'valence_electrons': 3, 'atomic_number': 57},
    'Fe': {'atomic_radius': 126.0, 'electronegativity': 1.83, 'valence_electrons': 8, 'atomic_number': 26},
    'B': {'atomic_radius': 85.0, 'electronegativity': 2.04, 'valence_electrons': 3, 'atomic_number': 5},
    'Co': {'atomic_radius': 125.0, 'electronegativity': 1.88, 'valence_electrons': 9, 'atomic_number': 27},
    'Ag': {'atomic_radius': 144.0, 'electronegativity': 1.93, 'valence_electrons': 11, 'atomic_number': 47},
    'Nb': {'atomic_radius': 146.0, 'electronegativity': 1.60, 'valence_electrons': 5, 'atomic_number': 41},
    'C': {'atomic_radius': 77.0, 'electronegativity': 2.55, 'valence_electrons': 4, 'atomic_number': 6},
    'Be': {'atomic_radius': 112.0, 'electronegativity': 1.57, 'valence_electrons': 2, 'atomic_number': 4},
    'Gd': {'atomic_radius': 180.0, 'electronegativity': 1.20, 'valence_electrons': 3, 'atomic_number': 64},
    'Dy': {'atomic_radius': 178.0, 'electronegativity': 1.22, 'valence_electrons': 3, 'atomic_number': 66}
}

def generate_composition_from_system(elements: List[str], rng: Optional[np.random.Generator] = None) -> str:
    """
    Generate a random composition from a given set of elements.
    
    Args:
        elements: List of element symbols
        rng: NumPy random generator for reproducibility
        
    Returns:
        Composition string in format "Element1_x1Element2_x2..."
    """
    if rng is None:
        rng = np.random.default_rng()
    
    num_elements = len(elements)
    
    # Generate random fractions that sum to 1
    fractions = rng.random(num_elements)
    fractions = fractions / fractions.sum()
    
    # Convert to atomic percentages (integers summing to 100)
    percentages = (fractions * 100).astype(int)
    
    # Ensure sum is exactly 100
    diff = 100 - percentages.sum()
    if diff != 0:
        percentages[0] += diff
    
    # Build composition string
    parts = []
    for elem, pct in zip(elements, percentages):
        if pct > 0:
            parts.append(f"{elem}{pct}")
    
    return "".join(parts)

def generate_synthetic_phase(rng: Optional[np.random.Generator] = None) -> str:
    """
    Generate a synthetic phase label with realistic distribution.
    
    Args:
        rng: NumPy random generator for reproducibility
        
    Returns:
        Phase label ('amorphous' or 'crystalline')
    """
    if rng is None:
        rng = np.random.default_rng()
    
    # Metallic glass datasets typically have ~30-40% amorphous samples
    # Use a realistic distribution
    prob_amorphous = 0.35
    return 'amorphous' if rng.random() < prob_amorphous else 'crystalline'

def generate_synthetic_dataset(
    n_samples: int = 1000,
    seed: int = 42,
    systems: Optional[List[List[str]]] = None
) -> pd.DataFrame:
    """
    Generate a synthetic dataset of alloy compositions with descriptors.
    
    Args:
        n_samples: Number of samples to generate
        seed: Random seed for reproducibility
        systems: List of element systems to sample from (defaults to COMMON_ALLOY_SYSTEMS)
        
    Returns:
        DataFrame with compositions and computed descriptors
    """
    if systems is None:
        systems = COMMON_ALLOY_SYSTEMS
    
    rng = np.random.default_rng(seed)
    
    data = []
    
    for _ in range(n_samples):
        # Select a random alloy system
        system = rng.choice(systems)
        
        # Generate composition
        composition = generate_composition_from_system(system, rng)
        
        # Generate phase
        phase = generate_synthetic_phase(rng)
        
        # Parse composition to get element fractions
        elem_fractions = parse_composition(composition)
        
        # Compute descriptors using the real descriptor functions
        try:
            atomic_radius = compute_atomic_radius(elem_fractions)
            electronegativity = compute_electronegativity(elem_fractions)
            vec = compute_valence_electron_concentration(elem_fractions)
            size_mismatch = compute_atomic_size_mismatch(elem_fractions)
            electronegativity_diff = compute_electronegativity_difference(elem_fractions)
            mixing_enthalpy = compute_mixing_enthalpy(elem_fractions)
            
            # Add some realistic noise to descriptors
            atomic_radius = max(100.0, min(200.0, atomic_radius + rng.normal(0, 2)))
            electronegativity = max(0.5, min(3.0, electronegativity + rng.normal(0, 0.05)))
            vec = max(1.0, min(12.0, vec + rng.normal(0, 0.1)))
            size_mismatch = max(0.0, min(15.0, size_mismatch + rng.normal(0, 0.5)))
            electronegativity_diff = max(0.0, min(1.5, electronegativity_diff + rng.normal(0, 0.02)))
            mixing_enthalpy = max(-30.0, min(10.0, mixing_enthalpy + rng.normal(0, 1.0)))
            
            record = {
                'composition': composition,
                'phase': phase,
                'alloy_system': '-'.join(sorted(set(system))),
                'atomic_radius': round(atomic_radius, 4),
                'electronegativity': round(electronegativity, 4),
                'vec': round(vec, 4),
                'size_mismatch': round(size_mismatch, 4),
                'electronegativity_diff': round(electronegativity_diff, 4),
                'mixing_enthalpy': round(mixing_enthalpy, 4),
                'source': 'synthetic_fallback',
                'is_synthetic': True
            }
            
            data.append(record)
            
        except Exception as e:
            logger.warning(f"Skipping composition {composition} due to descriptor computation error: {e}")
            continue
    
    df = pd.DataFrame(data)
    
    # Ensure we have at least some samples
    if len(df) < n_samples:
        logger.warning(f"Generated {len(df)} samples, requested {n_samples}. Some compositions failed validation.")
    
    logger.info(f"Generated {len(df)} synthetic alloy compositions")
    
    return df

def apply_descriptors_to_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply descriptor computation to an existing DataFrame.
    
    Args:
        df: DataFrame with 'composition' column
        
    Returns:
        DataFrame with added descriptor columns
    """
    descriptors = []
    
    for _, row in df.iterrows():
        composition = row['composition']
        elem_fractions = parse_composition(composition)
        
        descriptors.append({
            'atomic_radius': compute_atomic_radius(elem_fractions),
            'electronegativity': compute_electronegativity(elem_fractions),
            'vec': compute_valence_electron_concentration(elem_fractions),
            'size_mismatch': compute_atomic_size_mismatch(elem_fractions),
            'electronegativity_diff': compute_electronegativity_difference(elem_fractions),
            'mixing_enthalpy': compute_mixing_enthalpy(elem_fractions)
        })
    
    desc_df = pd.DataFrame(descriptors)
    return pd.concat([df.reset_index(drop=True), desc_df], axis=1)

def save_synthetic_dataset(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save synthetic dataset to CSV.
    
    Args:
        df: DataFrame to save
        output_path: Optional output path (defaults to data/raw/synthetic_fallback.csv)
        
    Returns:
        Path to saved file
    """
    if output_path is None:
        output_path = get_raw_data_path() / "synthetic_fallback.csv"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    logger.info(f"Saved synthetic dataset to {output_path}")
    
    return output_path

def main():
    """
    Main entry point for synthetic data generation.
    
    Generates a fallback dataset for CI reproducibility when
    the primary Zenodo source is unavailable.
    """
    logger.info("Starting synthetic data generation for CI fallback...")
    
    # Ensure directories exist
    ensure_data_directories()
    
    # Generate dataset
    df = generate_synthetic_dataset(n_samples=1000, seed=42)
    
    # Save dataset
    output_path = save_synthetic_dataset(df)
    
    # Verify output
    if output_path.exists():
        logger.info(f"Successfully generated {len(df)} samples to {output_path}")
        logger.info(f"Columns: {list(df.columns)}")
        logger.info(f"Phase distribution: {df['phase'].value_counts().to_dict()}")
    else:
        logger.error("Failed to write synthetic dataset")
        sys.exit(1)
    
    return df

if __name__ == "__main__":
    main()
