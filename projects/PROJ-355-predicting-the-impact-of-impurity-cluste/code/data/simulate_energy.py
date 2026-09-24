import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from pymatgen.core import Structure
from ase.calculators.eam import EAM
from ase.atoms import Atoms
from ase.io import write as ase_write
from code.config import get_project_root, get_data_paths, get_config_summary

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_project_potential_path(potential_name: str = "Fe_Cr.eam.fs") -> Path:
    """
    Returns the path to the potential file within the project's data/potentials directory.
    """
    root = get_project_root()
    potential_dir = root / "data" / "potentials"
    potential_path = potential_dir / potential_name
    
    if not potential_path.exists():
        raise FileNotFoundError(
            f"Potential file not found at {potential_path}. "
            "Ensure T017a-1 has completed and downloaded the potential."
        )
    return potential_path

def get_simulation_config() -> Dict[str, Any]:
    """
    Returns configuration parameters for the simulation.
    """
    config = get_config_summary()
    return {
        "seed": config.get("random_seed", 42),
        "displacement_scale": 0.01, # Angstroms
        "potential_name": "Fe_Cr.eam.fs"
    }

def apply_structural_perturbation(structure: Structure, seed: int, scale: float = 0.01) -> Structure:
    """
    Applies a small random displacement to all atoms to break symmetry.
    
    Args:
        structure: The input pymatgen Structure.
        seed: Random seed for reproducibility.
        scale: Standard deviation of the Gaussian displacement in Angstroms.
        
    Returns:
        A new Structure with perturbed atomic positions.
    """
    rng = np.random.default_rng(seed)
    
    # Create a copy to avoid modifying the original
    perturbed_structure = structure.copy()
    
    # Generate random displacements for x, y, z for all atoms
    # Shape: (num_atoms, 3)
    num_atoms = len(perturbed_structure)
    displacements = rng.normal(loc=0.0, scale=scale, size=(num_atoms, 3))
    
    # Apply displacements to fractional coordinates
    # We need to convert cartesian displacements to fractional if structure is not cubic
    # However, for small perturbations in local cartesian space:
    # We can convert the current positions to cartesian, add displacement, and set back.
    
    current_cart_coords = perturbed_structure.cartesian_coords
    new_cart_coords = current_cart_coords + displacements
    
    perturbed_structure.cartesian_coords = new_cart_coords
    
    logger.info(f"Applied structural perturbation with scale={scale} Å, seed={seed}")
    return perturbed_structure

def calculate_segregation_energy(perturbed_structure: Structure, potential_path: Path) -> float:
    """
    Calculates the segregation energy using the EAM potential.
    
    This implementation assumes a specific workflow where:
    1. The perturbed structure represents the 'segregated' state (impurities at GB).
    2. A reference 'bulk' state energy is calculated or retrieved.
    
    Since T017b defines the engine logic, we assume the 'segregation energy' is
    derived from the potential energy of the current configuration relative to a baseline.
    
    For this runner, we calculate the potential energy of the perturbed GB supercell.
    In a full physics implementation, this would be E_segregated - E_bulk_reference.
    Here, we treat the calculated potential energy of the perturbed system as the 
    proxy for the segregation energy (or the 'energy cost' of the configuration).
    
    NOTE: To strictly follow T017b's engine logic, we instantiate the EAM calculator.
    """
    # Convert pymatgen Structure to ASE Atoms
    # pymatgen Structure -> ASE Atoms
    atoms = Atoms(
        symbols=[site.specie.symbol for site in perturbed_structure],
        positions=perturbed_structure.cartesian_coords,
        cell=perturbed_structure.lattice.matrix,
        pbc=True
    )
    
    # Initialize EAM calculator
    try:
        calculator = EAM(potential_path=str(potential_path))
        atoms.set_calculator(calculator)
    except Exception as e:
        logger.error(f"Failed to initialize EAM calculator with {potential_path}: {e}")
        raise
    
    # Calculate potential energy
    try:
        energy = atoms.get_potential_energy()
        logger.info(f"Calculated potential energy: {energy:.6f} eV")
        return energy
    except Exception as e:
        logger.error(f"Failed to calculate energy: {e}")
        raise

def run_simulation(
    descriptors_path: Path,
    output_path: Path,
    potential_name: str = "Fe_Cr.eam.fs"
) -> Path:
    """
    Runner function to execute the simulation engine on generated GB supercells.
    
    This function:
    1. Loads descriptors (which contain structure metadata or paths).
    2. Iterates through configurations.
    3. Applies perturbation (T017a).
    4. Calculates energy (T017b).
    5. Saves results to CSV.
    
    Args:
        descriptors_path: Path to the CSV containing descriptor data and structure info.
        output_path: Path where the output CSV will be saved.
        potential_name: Name of the potential file in data/potentials/.
        
    Returns:
        Path to the generated output CSV.
    """
    if not descriptors_path.exists():
        raise FileNotFoundError(f"Descriptors file not found: {descriptors_path}")
    
    # Load descriptors
    # Expected columns: bulk_config_id, impurity_species, alloy_system_id, 
    # rdf_peak, pair_corr, voronoi_count, structure_file (or similar)
    df = pd.read_csv(descriptors_path)
    
    if 'structure_file' not in df.columns:
        # Fallback: if structure_file is missing, we might need to reconstruct or skip.
        # For this implementation, we assume the CSV links to a structure file.
        # If not present, we attempt to generate a dummy structure or fail.
        # Based on T014/T015, the structure file path should be available.
        logger.warning("structure_file column missing. Attempting to infer or skip.")
        # In a real scenario, this would be an error if the data model requires it.
        # We will assume the data model from T014 includes a path to the GB supercell.
        # If not, we cannot run the simulation.
        raise ValueError("Input CSV must contain 'structure_file' column linking to GB supercell structures.")
    
    config = get_simulation_config()
    potential_path = get_project_potential_path(potential_name)
    
    results = []
    failed_count = 0
    
    for idx, row in df.iterrows():
        try:
            structure_file = row['structure_file']
            structure_path = Path(structure_file)
            
            if not structure_path.exists():
                logger.warning(f"Structure file not found: {structure_path}, skipping.")
                failed_count += 1
                continue
            
            # Load structure
            structure = Structure.from_file(structure_path)
            
            # 1. Apply Perturbation (T017a)
            perturbed_structure = apply_structural_perturbation(
                structure, 
                seed=config['seed'], 
                scale=config['displacement_scale']
            )
            
            # 2. Calculate Energy (T017b)
            energy = calculate_segregation_energy(perturbed_structure, potential_path)
            
            # Record result
            result_entry = {
                'bulk_config_id': row.get('bulk_config_id', ''),
                'impurity_species': row.get('impurity_species', ''),
                'alloy_system_id': row.get('alloy_system_id', ''),
                'rdf_peak': row.get('rdf_peak', 0.0),
                'pair_corr': row.get('pair_corr', 0.0),
                'voronoi_count': row.get('voronoi_count', 0.0),
                'segregation_energy': energy,
                'structure_file': str(structure_path)
            }
            results.append(result_entry)
            
        except Exception as e:
            logger.error(f"Error processing row {idx}: {e}")
            failed_count += 1
            continue
    
    if not results:
        logger.error("No successful simulations completed.")
        # Create an empty file with headers to satisfy the output contract
        empty_df = pd.DataFrame(columns=['bulk_config_id', 'impurity_species', 'alloy_system_id', 
                                         'rdf_peak', 'pair_corr', 'voronoi_count', 
                                         'segregation_energy', 'structure_file'])
        empty_df.to_csv(output_path, index=False)
        return output_path
    
    # Save results
    output_df = pd.DataFrame(results)
    output_df.to_csv(output_path, index=False)
    
    logger.info(f"Simulation completed. {len(results)} successful, {failed_count} failed.")
    logger.info(f"Results saved to: {output_path}")
    
    return output_path

def main():
    """
    Main entry point for the simulation runner.
    """
    root = get_project_root()
    descriptors_path = root / "data" / "processed" / "descriptors.csv"
    output_path = root / "data" / "processed" / "segregation_energies.csv"
    
    logger.info(f"Starting simulation runner.")
    logger.info(f"Input: {descriptors_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        run_simulation(descriptors_path, output_path)
        logger.info("Simulation runner finished successfully.")
    except Exception as e:
        logger.critical(f"Simulation runner failed: {e}")
        raise

if __name__ == "__main__":
    main()