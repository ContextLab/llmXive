"""
Generate synthetic local fallback data for the IL-Benchmark project.

This script creates:
1. data/IL-Benchmark-local.zip: A zip archive containing 20 ion pairs with
   XYZ coordinates and CCSD(T)/CBS reference interaction energies.
2. data/experimental_bulk_properties.csv: Density and viscosity data for
   the same 20 ion pairs.

The data is deterministic (fixed seed) to ensure reproducibility in CI.

Note: The dataset size (20 pairs) is required by Plan CI limits but contradicts
Spec Assumption (>=100). This is a known limitation.
"""
import os
import random
import zipfile
import csv
from pathlib import Path

import numpy as np
import pandas as pd

# Fixed seed for deterministic output
RANDOM_SEED = 42
NUM_ION_PAIRS = 20

# Common ionic liquid cation/anion combinations for realism
CATIONS = [
    "EMIM", "BMIM", "HMIM", "OMIM",  # 1-alkyl-3-methylimidazolium
    "EPYR", "BPYR", "HPYR",          # 1-alkylpyrrolidinium
    "TEAB", "TBA", "TPA"             # Ammonium based
]

ANIONS = [
    "BF4", "PF6", "TFSI", "FSI",     # Common anions
    "NTf2", "DCA", "SCN", "Cl",      # Others
    "Ac", "NO3", "OTf"
]

def set_seeds(seed: int):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def generate_xyz_content(pair_id: int, cation: str, anion: str) -> str:
    """
    Generate a realistic-looking XYZ file content for an ion pair.
    
    Args:
        pair_id: Unique identifier for the pair
        cation: Cation name
        anion: Anion name
        
    Returns:
        String content of the XYZ file
    """
    # Estimate number of atoms based on ion names (simplified)
    cation_atoms = len(cation) * 2 + 10  # Rough heuristic
    anion_atoms = len(anion) * 2 + 5
    total_atoms = cation_atoms + anion_atoms
    
    lines = [str(total_atoms)]
    lines.append(f" Ion pair {pair_id}: {cation}[+]-{anion}[-]")
    
    # Generate pseudo-random but deterministic coordinates
    # Using a fixed offset based on pair_id to ensure different coordinates
    rng = random.Random(pair_id * RANDOM_SEED)
    
    # Generate cation coordinates (centered around origin)
    for i in range(cation_atoms):
        element = rng.choice(["C", "H", "N", "O"])
        x = rng.uniform(-5.0, 5.0)
        y = rng.uniform(-5.0, 5.0)
        z = rng.uniform(-5.0, 5.0)
        lines.append(f"{element:2s} {x:10.6f} {y:10.6f} {z:10.6f}")
    
    # Generate anion coordinates (separated from cation)
    offset_z = 3.0 + rng.uniform(0.0, 2.0)
    for i in range(anion_atoms):
        element = rng.choice(["B", "F", "P", "S", "N", "O", "Cl"])
        x = rng.uniform(-5.0, 5.0)
        y = rng.uniform(-5.0, 5.0)
        z = rng.uniform(offset_z, offset_z + 5.0)
        lines.append(f"{element:2s} {x:10.6f} {y:10.6f} {z:10.6f}")
    
    return "\n".join(lines)

def generate_reference_energy(pair_id: int, cation: str, anion: str) -> float:
    """
    Generate a CCSD(T)/CBS reference interaction energy.
    
    Values are in Hartree and are realistic for ionic liquid ion pairs
    (typically -0.3 to -0.8 Hartree, i.e., -200 to -500 kcal/mol).
    
    Args:
        pair_id: Unique identifier
        cation: Cation name
        anion: Anion name
        
    Returns:
        Reference interaction energy in Hartree
    """
    # Base energy depends on ion types (simplified model)
    base_energy = -0.45  # Hartree
    
    # Add variation based on ion characteristics
    cation_effect = (CATIONS.index(cation) % 3) * 0.02 - 0.03
    anion_effect = (ANIONS.index(anion) % 3) * 0.02 - 0.03
    
    # Add small random variation (deterministic via pair_id)
    rng = random.Random(pair_id * RANDOM_SEED + 1000)
    noise = rng.gauss(0, 0.01)
    
    energy = base_energy + cation_effect + anion_effect + noise
    return energy

def generate_bulk_properties(pair_id: int, cation: str, anion: str) -> dict:
    """
    Generate experimental bulk properties for an ion pair.
    
    Args:
        pair_id: Unique identifier
        cation: Cation name
        anion: Anion name
        
    Returns:
        Dictionary with density (g/cm3) and viscosity (cP) at 298K
    """
    rng = random.Random(pair_id * RANDOM_SEED + 2000)
    
    # Density: typically 1.1 to 1.6 g/cm3 for ionic liquids
    base_density = 1.35
    density_variation = rng.gauss(0, 0.1)
    density = max(1.1, min(1.6, base_density + density_variation))
    
    # Viscosity: highly variable, typically 20 to 500 cP
    # Use log-normal distribution for more realistic spread
    base_viscosity_log = np.log(100)  # 100 cP as median
    viscosity_log = base_viscosity_log + rng.gauss(0, 0.5)
    viscosity = np.exp(viscosity_log)
    
    return {
        "density_g_cm3": round(density, 3),
        "viscosity_cP": round(viscosity, 1)
    }

def main():
    """Main function to generate all synthetic data."""
    # Ensure deterministic output
    set_seeds(RANDOM_SEED)
    
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Prepare data structures
    xyz_files = []
    reference_data = []
    bulk_properties_data = []
    
    # Generate 20 ion pairs
    for i in range(NUM_ION_PAIRS):
        pair_id = f"IL-{i+1:03d}"
        cation = CATIONS[i % len(CATIONS)]
        anion = ANIONS[i % len(ANIONS)]
        
        # Generate XYZ content
        xyz_content = generate_xyz_content(pair_id, cation, anion)
        xyz_filename = f"{pair_id}.xyz"
        xyz_files.append((xyz_filename, xyz_content))
        
        # Generate reference energy
        ref_energy = generate_reference_energy(i, cation, anion)
        reference_data.append({
            "pair_id": pair_id,
            "cation": cation,
            "anion": anion,
            "reference_energy_Hartree": round(ref_energy, 6)
        })
        
        # Generate bulk properties
        bulk_props = generate_bulk_properties(i, cation, anion)
        bulk_properties_data.append({
            "pair_id": pair_id,
            "cation": cation,
            "anion": anion,
            "density_g_cm3": bulk_props["density_g_cm3"],
            "viscosity_cP": bulk_props["viscosity_cP"]
        })
    
    # Create zip file with XYZ coordinates
    zip_path = data_dir / "IL-Benchmark-local.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filename, content in xyz_files:
            zipf.writestr(filename, content)
    
    # Write reference data to CSV (embedded in zip or separate)
    # For simplicity, we'll include a metadata file in the zip
    metadata_csv = "metadata.csv"
    metadata_content = "pair_id,cation,anion,reference_energy_Hartree\n"
    for row in reference_data:
        metadata_content += f"{row['pair_id']},{row['cation']},{row['anion']},{row['reference_energy_Hartree']}\n"
    
    with zipfile.ZipFile(zip_path, 'a', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr(metadata_csv, metadata_content)
    
    # Write experimental bulk properties to CSV
    bulk_csv_path = data_dir / "experimental_bulk_properties.csv"
    bulk_df = pd.DataFrame(bulk_properties_data)
    bulk_df.to_csv(bulk_csv_path, index=False)
    
    print(f"Generated {zip_path} with {NUM_ION_PAIRS} ion pairs")
    print(f"Generated {bulk_csv_path} with bulk properties")
    print("Data generation complete.")

if __name__ == "__main__":
    main()
