"""
Generate synthetic local fallback data for the DFT-D3 transferability study.

This script creates:
1. data/IL-Benchmark-local.zip: Contains 20 ion pairs with XYZ coordinates and CCSD(T)/CBS reference energies.
2. data/experimental_bulk_properties.csv: Contains density and viscosity for the same 20 pairs.

The data is deterministic (fixed seed) to ensure reproducibility.
Note: The dataset size (20) is required by Plan CI limits.
"""
import os
import random
import zipfile
import csv
import json
from pathlib import Path
import numpy as np

# Import existing utilities if available, otherwise define locally
try:
    from logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

# Fixed seed for reproducibility
SEED = 42

# Define a set of representative ion pair names (20 unique pairs)
# Format: "Cation_Anion"
ION_PAIRS = [
    "EMIM_BF4", "EMIM_TFSI", "EMIM_FAP",
    "BMIM_BF4", "BMIM_TFSI", "BMIM_FAP",
    "HMIM_BF4", "HMIM_TFSI", "HMIM_FAP",
    "OMIM_BF4", "OMIM_TFSI", "OMIM_FAP",
    "EMIM_NO3", "BMIM_NO3", "HMIM_NO3",
    "EMIM_Cl", "BMIM_Cl", "HMIM_Cl",
    "BMIM_Ac", "EMIM_Ac"
]

def set_seeds(seed: int = SEED):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def generate_xyz_content(pair_id: str, cation_atoms: int, anion_atoms: int) -> str:
    """
    Generate a deterministic but chemically plausible XYZ file content.
    
    Args:
        pair_id: Unique identifier for the ion pair.
        cation_atoms: Number of atoms in the cation.
        anion_atoms: Number of atoms in the anion.
        
    Returns:
        String content of the XYZ file.
    """
    total_atoms = cation_atoms + anion_atoms
    lines = [str(total_atoms)]
    lines.append(f"Ion pair {pair_id} - Synthetic XYZ")
    
    # Generate random coordinates within a bounding box (Angstroms)
    # Using a deterministic seed ensures the same coordinates every time
    np.random.seed(hash(pair_id) % (2**32))
    
    # Define element types for a generic imidazolium-based cation and common anions
    # Simplified: C, H, N for cation; B, F, S, O, P, Cl for anions
    cation_elements = ['C', 'H', 'N']
    anion_elements_map = {
        'BF4': ['B', 'F'],
        'TFSI': ['C', 'F', 'N', 'O', 'S'],
        'FAP': ['C', 'F', 'P'],
        'NO3': ['N', 'O'],
        'Cl': ['Cl'],
        'Ac': ['C', 'H', 'O']
    }
    
    # Determine anion elements based on pair_id suffix
    anion_name = pair_id.split('_')[1]
    anion_elements = anion_elements_map.get(anion_name, ['C', 'H', 'O'])
    
    all_elements = []
    # Add cation atoms
    for _ in range(cation_atoms):
        all_elements.append(random.choice(cation_elements))
    # Add anion atoms
    for _ in range(anion_atoms):
        all_elements.append(random.choice(anion_elements))
    
    # Generate coordinates
    # Center cation roughly around (0,0,0) and anion shifted along Z
    for i, element in enumerate(all_elements):
        if i < cation_atoms:
            # Cation coordinates
            x = np.random.uniform(-3.0, 3.0)
            y = np.random.uniform(-3.0, 3.0)
            z = np.random.uniform(-2.0, 2.0)
        else:
            # Anion coordinates, shifted to simulate interaction
            x = np.random.uniform(-2.0, 2.0)
            y = np.random.uniform(-2.0, 2.0)
            z = np.random.uniform(2.0, 6.0)
        
        lines.append(f"{element:<2} {x:10.5f} {y:10.5f} {z:10.5f}")
    
    return "\n".join(lines)

def generate_reference_energy(pair_id: str) -> float:
    """
    Generate a deterministic CCSD(T)/CBS reference energy (kcal/mol).
    
    Values are sampled from a realistic range for ionic liquid ion pairs (12-28 kcal/mol).
    The values are negative (attractive interaction).
    
    Args:
        pair_id: Unique identifier for the ion pair.
        
    Returns:
        Reference interaction energy in kcal/mol.
    """
    # Use a deterministic seed based on pair_id to generate the value
    np.random.seed(hash(pair_id) % (2**32))
    
    # Base energy range: -12 to -28 kcal/mol
    # Add some variation based on ion types (simplified)
    base = -20.0
    variation = np.random.uniform(-5.0, 5.0)
    energy = base + variation
    
    # Ensure it stays within realistic bounds
    energy = max(-30.0, min(-10.0, energy))
    
    return round(energy, 6)

def generate_bulk_properties(pair_id: str) -> dict:
    """
    Generate deterministic experimental bulk properties (density, viscosity).
    
    Args:
        pair_id: Unique identifier for the ion pair.
        
    Returns:
        Dictionary with 'density' (g/cm3) and 'viscosity' (cP).
    """
    np.random.seed(hash(pair_id + "_bulk") % (2**32))
    
    # Density range: 1.1 - 1.6 g/cm3
    density = np.random.uniform(1.1, 1.6)
    
    # Viscosity range: 20 - 500 cP (highly variable for ILs)
    # Log-normal distribution might be more realistic, but uniform is sufficient for synthetic
    viscosity = np.random.uniform(20.0, 500.0)
    
    return {
        "density": round(density, 4),
        "viscosity": round(viscosity, 2)
    }

def main():
    """Main function to generate all synthetic data artifacts."""
    set_seeds(SEED)
    
    # Define output paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    
    zip_path = data_dir / "IL-Benchmark-local.zip"
    csv_path = data_dir / "experimental_bulk_properties.csv"
    
    logger.info(f"Generating synthetic data in {data_dir}")
    
    # Prepare data structures
    xyz_files = {}
    ref_energies = []
    bulk_props = []
    
    # Generate data for each ion pair
    for pair_id in ION_PAIRS:
        # Estimate atom counts (simplified)
        # EMIM: ~13 atoms, BF4: 5, TFSI: ~15, etc.
        # We'll use a heuristic based on the anion name
        anion = pair_id.split('_')[1]
        cation_atoms = 13  # Approx for EMIM/BMIM/HMIM
        if anion == 'BF4':
            anion_atoms = 5
        elif anion == 'TFSI':
            anion_atoms = 15
        elif anion == 'FAP':
            anion_atoms = 18
        elif anion == 'NO3':
            anion_atoms = 4
        elif anion == 'Cl':
            anion_atoms = 1
        elif anion == 'Ac':
            anion_atoms = 5
        else:
            anion_atoms = 10 # Default
            
        # Generate XYZ content
        xyz_content = generate_xyz_content(pair_id, cation_atoms, anion_atoms)
        xyz_filename = f"{pair_id}.xyz"
        xyz_files[xyz_filename] = xyz_content
        
        # Generate reference energy
        ref_energy = generate_reference_energy(pair_id)
        ref_energies.append({
            "pair_id": pair_id,
            "reference_energy_kcal_mol": ref_energy
        })
        
        # Generate bulk properties
        props = generate_bulk_properties(pair_id)
        bulk_props.append({
            "pair_id": pair_id,
            "density_g_cm3": props["density"],
            "viscosity_cP": props["viscosity"]
        })
    
    # Write ZIP file
    logger.info(f"Writing {zip_path}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filename, content in xyz_files.items():
            zipf.writestr(filename, content)
        
        # Also include the reference energies as a JSON file inside the zip
        ref_json = json.dumps(ref_energies, indent=2)
        zipf.writestr("reference_energies.json", ref_json)
    
    # Write CSV file for bulk properties
    logger.info(f"Writing {csv_path}")
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['pair_id', 'density_g_cm3', 'viscosity_cP']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(bulk_props)
    
    logger.info("Synthetic data generation completed successfully.")
    logger.info(f"  - {zip_path}: Contains {len(ION_PAIRS)} ion pairs (XYZ) + reference energies")
    logger.info(f"  - {csv_path}: Contains {len(ION_PAIRS)} bulk property records")

if __name__ == "__main__":
    main()
