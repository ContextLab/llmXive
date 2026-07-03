"""
GB Builder Module: Constructs Grain Boundary (GB) supercells and inserts impurities.

This module implements the logic to:
1. Load bulk crystal structures (assumed to be in data/raw/ or provided as Structure objects).
2. Construct a symmetric tilt grain boundary (STGB) supercell using a simple
   2x2x2 supercell expansion and a defined shear/shift to create the boundary.
   *Note*: For a full production pipeline, a dedicated library like pymatgen's
   `GrainBoundary` or `SymmetricTiltGrainBoundary` would be used. Here, we implement
   a robust construction logic compatible with the project's MVP scope and CPU constraints.
3. Identify the interface region (atoms near the GB plane).
4. Insert impurity atoms into the interface region.
5. Save the resulting structure to `data/processed/gb_supercells/`.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from pymatgen.core import Structure, Lattice, Element
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.transformations.standard_transformations import SupercellTransformation

# Project-local imports (matching the provided API surface)
from code.config import get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GB_PLANE_NORMAL = [0, 0, 1]  # Simplified: assume (001) tilt for MVP
INTERFACE_THICKNESS = 3.0    # Angstroms from the GB plane
OUTPUT_DIR = Path("data/processed/gb_supercells")
METADATA_PATH = Path("data/processed/gb_builder_metadata.json")

def _ensure_directories():
    """Ensure output directories exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def _create_supercell(structure: Structure, scale_factors: List[float] = None) -> Structure:
    """
    Create a supercell of the given structure.
    
    Args:
        structure: Input bulk structure.
        scale_factors: List of [x, y, z] scale factors. Defaults to [2, 2, 2].
        
    Returns:
        Expanded Structure object.
    """
    if scale_factors is None:
        scale_factors = [2, 2, 2]
    
    transformation = SupercellTransformation(scale_factors)
    return transformation.apply_transformation(structure)

def _create_gb_interface(structure: Structure) -> Structure:
    """
    Construct a simplified Grain Boundary supercell.
    
    Logic:
    1. Create a supercell.
    2. Split the supercell into two halves along the GB plane (z-axis).
    3. Shift the top half to create a misorientation (simplified as a shear for MVP).
    4. Merge the two halves.
    
    Note: In a full implementation, we would use `GrainBoundary.from_structure`
    with specific Miller indices and misorientation angles. For this MVP, we
    simulate the GB by duplicating the cell, shifting, and merging.
    """
    # Step 1: Create supercell
    supercell = _create_supercell(structure)
    
    # Step 2: Identify atoms above and below z=0.5 (normalized)
    # We assume the structure is centered. We will split along the c-axis.
    # To simulate a GB, we create a "slab" logic:
    # 1. Get the lattice parameters.
    # 2. Duplicate the structure to make a vacuum gap or interface.
    
    # Simplified approach for MVP:
    # We will take the supercell, and for every atom, we check its z-coordinate.
    # We will shift atoms in the upper half by a small vector to break symmetry
    # and simulate the grain boundary displacement.
    
    # Get lattice
    lattice = supercell.lattice
    z_len = lattice.c
    
    # Create a new structure with the same lattice
    new_structure = Structure(lattice, [], [], coords=[], coords_are_cartesian=True)
    
    # Define shift vector (simplified shear along x)
    # A real GB would have a specific shift based on the CSL (Coincident Site Lattice)
    # For MVP, we apply a random but reproducible shift based on the structure ID
    # to ensure distinct representations without complex CSL calculations.
    # However, to be deterministic and "real", we use a fixed fraction of the lattice vector.
    shift_x = lattice.a * 0.25  # 1/4 shift along a
    
    atoms_above = []
    atoms_below = []
    
    for site in supercell:
        if site.frac_coords[2] > 0.5:
            # Shift this atom
            new_frac = site.frac_coords.copy()
            new_frac[0] += shift_x / lattice.a  # Convert cartesian shift to frac
            # Normalize
            new_frac[0] %= 1.0
            atoms_above.append((site.species, new_frac))
        else:
            atoms_below.append((site.species, site.frac_coords))
    
    # Reconstruct structure
    for species, coords in atoms_below:
        new_structure.append(species, coords)
    for species, coords in atoms_above:
        new_structure.append(species, coords)
        
    # Update species list for pymatgen
    new_structure.add_oxidation_state_by_site([0] * len(new_structure)) # Neutral for now
    
    return new_structure

def _identify_interface_atoms(structure: Structure, plane_normal: List[float] = [0, 0, 1]) -> List[int]:
    """
    Identify atoms within the interface region.
    
    Args:
        structure: The GB supercell structure.
        plane_normal: Normal vector of the GB plane.
        
    Returns:
        List of site indices that are within the interface thickness.
    """
    interface_indices = []
    lattice = structure.lattice
    
    # Project atomic positions onto the normal vector
    # For (001), this is simply the fractional z * c
    
    # Calculate the center of the cell along the normal
    # We assume the GB plane is at the center of the supercell (z=0.5 in frac coords)
    
    for i, site in enumerate(structure):
        # Get Cartesian coordinate along the normal
        # For (0,0,1), it's just the z Cartesian coordinate
        z_cart = site.coords[2]
        
        # The cell height is lattice.c
        # We consider the "plane" to be at z = 0.5 * lattice.c
        # We want atoms within [0.5*c - thickness, 0.5*c + thickness]
        
        center_z = 0.5 * lattice.c
        
        if abs(z_cart - center_z) <= INTERFACE_THICKNESS:
            interface_indices.append(i)
            
    return interface_indices

def insert_impurity(structure: Structure, impurity_species: str, interface_indices: List[int]) -> Structure:
    """
    Insert impurity atoms into the interface region.
    
    Logic:
    1. Select a subset of interface atoms (or empty space if we were doing substitution).
    2. For this MVP, we will perform a substitution: Replace a fraction of the
       host atoms in the interface with the impurity.
    3. If the interface is too small, we expand the selection or add interstitials
       (simplified: just replace the first N available atoms).
    
    Args:
        structure: The GB supercell.
        impurity_species: Element symbol (e.g., "Cr", "C").
        interface_indices: Indices of atoms in the interface.
        
    Returns:
        Modified structure with impurities.
    """
    if not interface_indices:
        logger.warning("No interface atoms found. Inserting impurities randomly in the cell.")
        # Fallback: pick random atoms from the whole structure
        import random
        random.seed(42) # Reproducibility
        interface_indices = random.sample(range(len(structure)), min(5, len(structure)))
    
    # Determine how many to replace (e.g., 10% of interface, at least 1)
    n_replace = max(1, int(len(interface_indices) * 0.1))
    indices_to_replace = interface_indices[:n_replace]
    
    new_structure = structure.copy()
    impurity_element = Element(impurity_species)
    
    for idx in indices_to_replace:
        # Replace the species at this index
        # We need to update the site's species
        old_species = new_structure[idx].species
        # Create a new site with the impurity
        # Note: pymatgen Structure is mutable
        new_structure[idx] = impurity_element
        
    logger.info(f"Replaced {n_replace} atoms in the interface with {impurity_species}.")
    return new_structure

def build_gb_supercell(bulk_structure: Structure, impurity_species: str, config_id: str) -> Structure:
    """
    Main entry point to build a GB supercell with an impurity.
    
    Args:
        bulk_structure: Input bulk structure (Pymatgen Structure).
        impurity_species: Element symbol of the impurity.
        config_id: Unique identifier for the bulk configuration.
        
    Returns:
        Structure: The constructed GB supercell with impurity.
    """
    logger.info(f"Building GB supercell for {config_id} with impurity {impurity_species}")
    
    # 1. Create GB Interface
    gb_structure = _create_gb_interface(bulk_structure)
    
    # 2. Identify Interface
    interface_indices = _identify_interface_atoms(gb_structure)
    
    # 3. Insert Impurity
    final_structure = insert_impurity(gb_structure, impurity_species, interface_indices)
    
    return final_structure

def save_structure(structure: Structure, output_path: Path, metadata: Dict[str, Any]):
    """
    Save the structure to a file (CIF or POSCAR) and update metadata.
    """
    # Determine file extension
    if output_path.suffix == '.cif':
        structure.to_file(str(output_path), fmt='cif')
    else:
        structure.to_file(str(output_path), fmt='poscar')
        
    logger.info(f"Saved structure to {output_path}")

def main():
    """
    Runner function to process bulk configurations from data/raw/ and generate GB supercells.
    """
    _ensure_directories()
    
    # Check if data/raw exists and has files
    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        logger.error("data/raw directory not found. Run T013 (download) first.")
        return
        
    # Load metadata if exists to track progress
    processed_metadata = []
    if METADATA_PATH.exists():
        with open(METADATA_PATH, 'r') as f:
            processed_metadata = json.load(f)
    
    # Find bulk structures (assuming .cif or .poscar in data/raw)
    bulk_files = list(raw_dir.glob("*.cif")) + list(raw_dir.glob("*.poscar"))
    
    if not bulk_files:
        logger.warning("No bulk structure files found in data/raw/.")
        return

    logger.info(f"Found {len(bulk_files)} bulk structures to process.")

    # Define a default impurity for this run if not specified elsewhere
    # In a full pipeline, this would come from a config or a loop over a dataset
    default_impurity = "Cr" 

    count = 0
    for bulk_file in bulk_files:
        try:
            # Load structure
            structure = Structure.from_file(str(bulk_file))
            
            # Generate a simple config ID from filename
            config_id = bulk_file.stem
            
            # Build GB
            gb_structure = build_gb_supercell(structure, default_impurity, config_id)
            
            # Save output
            output_filename = f"{config_id}_gb_{default_impurity}.cif"
            output_path = OUTPUT_DIR / output_filename
            save_structure(gb_structure, output_path, {
                "source": str(bulk_file),
                "impurity": default_impurity,
                "config_id": config_id
            })
            
            processed_metadata.append({
                "input": str(bulk_file),
                "output": str(output_path),
                "impurity": default_impurity,
                "config_id": config_id
            })
            count += 1
            
        except Exception as e:
            logger.error(f"Failed to process {bulk_file}: {e}")
            continue

    # Save metadata
    with open(METADATA_PATH, 'w') as f:
        json.dump(processed_metadata, f, indent=2)
        
    logger.info(f"Successfully built {count} GB supercells.")

if __name__ == "__main__":
    main()
