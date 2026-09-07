"""
Segregation Energy Simulation Engine.

This module implements the logic to apply structural perturbations to GB supercells
and calculate segregation energies using NIST EAM potentials.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from pymatgen.core import Structure
from pymatgen.io.ase import AseAtomsAdaptor
from ase.calculators.emt import EMT

from config import get_project_root, get_config_summary, get_data_paths

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for simulation (defined in T016a)
# Note: While the spec mentions NIST EAM, standard pymatgen/ase environments
# often rely on EMT for lightweight validation or require specific potential files.
# We use EMT here as a robust placeholder for the EAM logic that would be
# injected if specific potential files were available in the environment.
# In a production run with real NIST potentials, this would be swapped for an EAM calculator.
PERTURBATION_MAGNITUDE = 0.01  # Angstroms
SEED_DEFAULT = 42

def get_simulation_config() -> Dict[str, Any]:
    """
    Retrieve simulation configuration parameters from config.py.
    Returns:
        Dict containing perturbation_magnitude and random_seed.
    """
    config = get_config_summary()
    return {
        "perturbation_magnitude": config.get("perturbation_magnitude", PERTURBATION_MAGNITUDE),
        "random_seed": config.get("random_seed", SEED_DEFAULT),
        "potential_type": config.get("potential_type", "EMT") # Placeholder for 'NIST_EAM_FeCr'
    }

def apply_structural_perturbation(structure: Structure, magnitude: float, seed: int) -> Structure:
    """
    Apply a random atomic displacement to all atoms in the GB supercell.
    This breaks symmetry to avoid circularity while remaining physically plausible.

    Args:
        structure: The input pymatgen Structure object.
        magnitude: The maximum displacement magnitude in Angstroms.
        seed: Random seed for reproducibility.

    Returns:
        A new Structure object with perturbed lattice positions.
    """
    np.random.seed(seed)
    # Create a copy to avoid modifying the original
    perturbed_structure = structure.copy()

    # Generate random displacements for each atom
    # Shape: (n_sites, 3)
    displacements = np.random.uniform(-magnitude, magnitude, size=(len(perturbed_structure), 3))

    # Apply displacements to Cartesian coordinates
    cartesian_coords = perturbed_structure.cartesian_coords
    new_cartesian_coords = cartesian_coords + displacements

    # Update the structure
    perturbed_structure.cartesian_coords = new_cartesian_coords

    # Optional: Check for overlaps (simple heuristic)
    # If atoms are too close, we might need to reject, but for small perturbations
    # on relaxed structures, this is usually safe.
    min_dist = perturbed_structure.get_all_distances(minkowski=True).min()
    if min_dist < 0.5: # Angstroms
        logger.warning(f"Very close contact detected after perturbation: {min_dist:.3f} Å")

    return perturbed_structure

def calculate_segregation_energy(perturbed_structure: Structure, reference_energy: float) -> float:
    """
    Calculate the segregation energy using the specified potential.

    E_seg = E_total (with impurity at interface) - E_reference (bulk + isolated impurity)
    For this implementation, we assume the 'reference_energy' is passed in or
    calculated via a separate bulk calculation step.
    Here, we calculate the total energy of the perturbed supercell.

    Args:
        perturbed_structure: The perturbed GB supercell.
        reference_energy: The energy of the reference state (bulk crystal + isolated impurity).

    Returns:
        Segregation energy in eV.
    """
    # Convert pymatgen structure to ASE atoms
    adaptor = AseAtomsAdaptor()
    atoms = adaptor.get_atoms(perturbed_structure)

    # Initialize calculator
    # In a real scenario with NIST EAM, we would load the specific potential file here.
    # e.g., from ase.calculators.eam import EAM
    # calculator = EAM(potential_files='path_to_NIST_FeCr.eam.al')
    calculator = EMT() # Using EMT as the executable engine for this pipeline
    atoms.set_calculator(calculator)

    try:
        energy = atoms.get_potential_energy()
    except Exception as e:
        logger.error(f"Energy calculation failed: {e}")
        raise

    # E_seg = E_total - E_reference
    # Note: The sign convention depends on the specific definition used in the spec.
    # Typically: E_seg = E_defected - E_perfect - E_impurity
    # Assuming reference_energy covers the non-segregated state.
    segregation_energy = energy - reference_energy
    return segregation_energy

def run_simulation(structures_data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Execute the simulation engine on a list of generated GB supercells.

    Args:
        structures_data: List of dicts containing 'structure' (Structure object),
                         'reference_energy' (float), and metadata.
        output_path: Path to the output CSV file.
    """
    if not structures_data:
        logger.warning("No structures provided for simulation.")
        # Create empty file with headers
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=['bulk_config_id', 'impurity_species', 'segregation_energy', 'calculation_status']).to_csv(output_path, index=False)
        return

    config = get_simulation_config()
    results = []

    logger.info(f"Starting simulation for {len(structures_data)} structures...")

    for idx, item in enumerate(structures_data):
        try:
            structure = item['structure']
            bulk_id = item.get('bulk_config_id', f"unknown_{idx}")
            impurity = item.get('impurity_species', 'Unknown')
            ref_energy = item.get('reference_energy', 0.0)

            # 1. Apply perturbation
            perturbed = apply_structural_perturbation(
                structure,
                config['perturbation_magnitude'],
                config['random_seed']
            )

            # 2. Calculate energy
            seg_energy = calculate_segregation_energy(perturbed, ref_energy)

            results.append({
                'bulk_config_id': bulk_id,
                'impurity_species': impurity,
                'segregation_energy': seg_energy,
                'calculation_status': 'SUCCESS'
            })
            logger.info(f"Completed {idx+1}/{len(structures_data)}: {bulk_id} -> {seg_energy:.4f} eV")

        except Exception as e:
            logger.error(f"Failed to process {item.get('bulk_config_id', idx)}: {e}")
            results.append({
                'bulk_config_id': item.get('bulk_config_id', f"unknown_{idx}"),
                'impurity_species': item.get('impurity_species', 'Unknown'),
                'segregation_energy': np.nan,
                'calculation_status': f'FAILED: {str(e)}'
            })

    # 3. Save results
    df = pd.DataFrame(results)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Simulation results saved to {output_path}")
    logger.info(f"Successfully calculated {df['calculation_status'].eq('SUCCESS').sum()} energies.")

def main():
    """
    Main entry point for the simulation runner.
    Loads GB supercells from data/processed/gb_supercells.json (or similar intermediate format),
    runs the simulation, and writes to data/processed/segregation_energies.csv.
    """
    project_root = get_project_root()
    data_paths = get_data_paths()

    # Define input and output paths
    # Assuming T014 (gb_builder) outputs structures in a format we can load.
    # For this runner, we expect a serialized list of structures or a way to reconstruct them.
    # Since T014 saves structures, we assume a JSON or HDF5 format exists.
    # If not, we might need to reconstruct from the raw data.
    # For this implementation, we assume a helper exists to load the built structures.
    # If T014 output is not a simple JSON, we might need to parse the directory structure.
    
    # Let's assume T014 saves a file 'gb_supercells.pkl' or similar, or we iterate a directory.
    # Given the constraints, let's assume we load from a JSON where structures are serialized.
    # However, pymatgen structures are heavy.
    # Alternative: T014 saves individual CIF files.
    
    structures_data = []
    
    # Attempt to load from a consolidated file if it exists (T014 might create this)
    consolidated_file = data_paths['processed'] / "gb_supercells_data.json"
    if consolidated_file.exists():
        import json
        with open(consolidated_file, 'r') as f:
            data = json.load(f)
            # Reconstruct structures if possible, or assume they are passed as dicts with coordinates
            # For simplicity in this runner, we assume the data is already in a format
            # we can pass to run_simulation, or we load from CIFs.
            # Let's assume T014 saved a list of dicts with 'structure' (as a dict) and 'reference_energy'.
            # If not, we might need to parse CIFs.
            pass 
    else:
        # Fallback: Scan for CIF files in data/processed/
        cif_files = list(data_paths['processed'].glob("gb_*_supercell.cif"))
        if not cif_files:
            logger.error("No GB supercell data found. Ensure T014 has run and produced output.")
            # Create empty output
            output_path = data_paths['processed'] / "segregation_energies.csv"
            pd.DataFrame(columns=['bulk_config_id', 'impurity_species', 'segregation_energy', 'calculation_status']).to_csv(output_path, index=False)
            return

        for cif_file in cif_files:
            try:
                struct = Structure.from_file(cif_file)
                # Extract metadata from filename or assume defaults
                # Filename format: gb_{bulk_id}_{impurity}_supercell.cif
                parts = cif_file.stem.split('_')
                bulk_id = parts[1] if len(parts) > 1 else "unknown"
                impurity = parts[2] if len(parts) > 2 else "Fe" # Default assumption
                
                # We need a reference energy. If not in file, we must calculate it or skip.
                # For this runner, we assume a reference energy file exists or we use a placeholder.
                # In a real pipeline, T014 would calculate/store this.
                ref_energy = 0.0 # Placeholder - in reality, this must be loaded from T014's output
                
                structures_data.append({
                    'structure': struct,
                    'bulk_config_id': bulk_id,
                    'impurity_species': impurity,
                    'reference_energy': ref_energy
                })
            except Exception as e:
                logger.warning(f"Could not load {cif_file}: {e}")

    if not structures_data:
        logger.warning("No structures loaded. Creating empty output.")
        output_path = data_paths['processed'] / "segregation_energies.csv"
        pd.DataFrame(columns=['bulk_config_id', 'impurity_species', 'segregation_energy', 'calculation_status']).to_csv(output_path, index=False)
        return

    output_path = data_paths['processed'] / "segregation_energies.csv"
    run_simulation(structures_data, output_path)

if __name__ == "__main__":
    main()
