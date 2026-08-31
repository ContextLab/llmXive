import os
import sys
import logging
import csv
import random
from pathlib import Path
from typing import List, Dict, Any

from utils.config import get_paths, set_random_seed
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Mendeleev elemental properties (simplified for synthetic generation)
ELEMENTS = {
    "Zr": {"atomic_mass": 91.22, "electronegativity": 1.33, "atomic_radius": 160},
    "Cu": {"atomic_mass": 63.55, "electronegativity": 1.90, "atomic_radius": 128},
    "Pd": {"atomic_mass": 106.42, "electronegativity": 2.20, "atomic_radius": 137},
    "Ni": {"atomic_mass": 58.69, "electronegativity": 1.91, "atomic_radius": 124},
    "La": {"atomic_mass": 138.91, "electronegativity": 1.10, "atomic_radius": 187},
    "Al": {"atomic_mass": 26.98, "electronegativity": 1.61, "atomic_radius": 143},
    "Ti": {"atomic_mass": 47.87, "electronegativity": 1.54, "atomic_radius": 147},
    "Be": {"atomic_mass": 9.01, "electronegativity": 1.57, "atomic_radius": 112},
    "Mg": {"atomic_mass": 24.31, "electronegativity": 1.31, "atomic_radius": 160},
    "Fe": {"atomic_mass": 55.85, "electronegativity": 1.83, "atomic_radius": 126}
}

ALLOY_FAMILIES = ["Zr-based", "Pd-based", "La-based", "Ti-based", "Mg-based"]

def generate_synthetic_bmg_data(count: int = 100, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate a synthetic BMG dataset based on literature-documented composition distributions.
    
    This function creates synthetic data that mimics real BMG compositions and properties.
    It uses Mendeleev elemental properties to calculate approximate shear modulus values.
    
    Args:
        count: Number of synthetic samples to generate.
        seed: Random seed for reproducibility.
        
    Returns:
        List of dictionaries containing synthetic BMG data.
    """
    set_random_seed(seed)
    data = []
    
    for i in range(count):
        # Randomly select an alloy family
        family = random.choice(ALLOY_FAMILIES)
        
        # Generate a composition based on the family
        if family == "Zr-based":
            elements = ["Zr", "Cu", "Ni", "Al", "Be"]
            weights = [0.5, 0.2, 0.15, 0.1, 0.05]
        elif family == "Pd-based":
            elements = ["Pd", "Ni", "Cu", "P", "Si"]
            weights = [0.4, 0.25, 0.2, 0.1, 0.05]
        elif family == "La-based":
            elements = ["La", "Al", "Cu", "Ni", "Mg"]
            weights = [0.55, 0.25, 0.1, 0.05, 0.05]
        elif family == "Ti-based":
            elements = ["Ti", "Cu", "Ni", "Zr", "Be"]
            weights = [0.4, 0.25, 0.2, 0.1, 0.05]
        else:  # Mg-based
            elements = ["Mg", "Cu", "Zn", "Y", "Gd"]
            weights = [0.5, 0.2, 0.15, 0.1, 0.05]
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Generate atomic percentages
        composition = {}
        remaining = 1.0
        for j, elem in enumerate(elements[:-1]):
            pct = random.uniform(0.0, weights[j] * 1.2)
            pct = min(pct, remaining)
            composition[elem] = pct
            remaining -= pct
        composition[elements[-1]] = remaining
        
        # Format composition string
        comp_str = "".join([f"{elem}{int(pct*100)}" for elem, pct in composition.items()])
        
        # Calculate approximate shear modulus based on composition
        # Simplified model: weighted average of elemental shear moduli + noise
        base_modulus = 0.0
        for elem, pct in composition.items():
            if elem in ELEMENTS:
                # Rough approximation of shear modulus contribution
                # Real values would come from literature or DFT calculations
                elem_mod = 30.0  # Base value
                if elem == "Zr": elem_mod = 33.0
                elif elem == "Cu": elem_mod = 48.0
                elif elem == "Pd": elem_mod = 35.0
                elif elem == "Ni": elem_mod = 96.0
                elif elem == "La": elem_mod = 14.0
                elif elem == "Al": elem_mod = 26.0
                elif elem == "Ti": elem_mod = 45.0
                elif elem == "Be": elem_mod = 132.0
                elif elem == "Mg": elem_mod = 17.0
                
                base_modulus += pct * elem_mod
        
        # Add some noise to make it more realistic
        noise = random.gauss(0, 5.0)
        shear_modulus = max(10.0, base_modulus + noise)  # Ensure positive value
        
        record = {
            "composition": comp_str,
            "family": family,
            "shear_modulus_GPa": round(shear_modulus, 2),
            "source": "synthetic"
        }
        data.append(record)
    
    return data

def main():
    """
    Main function to generate and save synthetic BMG data.
    """
    paths = get_paths()
    output_file = paths["data_raw"] / "synthetic_bmg_seed.csv"
    
    logger.info(f"Generating synthetic BMG dataset to {output_file}")
    
    data = generate_synthetic_bmg_data(count=100)
    
    # Save to CSV
    fieldnames = list(data[0].keys())
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Generated {len(data)} synthetic samples and saved to {output_file}")

if __name__ == "__main__":
    main()