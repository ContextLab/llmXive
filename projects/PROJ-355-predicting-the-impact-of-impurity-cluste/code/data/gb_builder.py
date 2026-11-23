import os
import json
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

from pymatgen.core import Structure, Lattice, Element

from config import get_project_root, get_data_paths

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def insert_impurity(structure: Structure, impurity_species: str, site_indices: List[int]) -> Structure:
    """
    Inserts impurity atoms into specific sites of a structure.
    """
    # Create a copy to avoid modifying the original
    new_structure = structure.copy()
    for site_idx in site_indices:
        # Replace the species at the site
        new_structure.replace(site_idx, Element(impurity_species))
    return new_structure

def _build_gb_supercell_logic(bulk_structure: Structure,
                              misorientation_angle: float = 90.0,
                              boundary_plane: Tuple[float, float, float] = (0.0, 0.0, 1.0)
                              ) -> Structure:
    """
    Core placeholder logic for building a GB supercell.
    Returns a copy of the bulk structure for now.
    """
    logger.warning("GB Builder logic is a placeholder. Returning bulk structure copy.")
    return bulk_structure.copy()

def build_gb_supercell(bulk_structure: Structure,
                       misorientation_angle: float,
                       boundary_plane: Tuple[float, float, float]) -> Structure:
    """
    Public API retained for backward compatibility.
    """
    return _build_gb_supercell_logic(bulk_structure, misorientation_angle, boundary_plane)

def build_gb_supercell_from_file(input_path: Path, output_dir: Path) -> Path:
    """
    New API used by the integration test.

    Parameters
    ----------
    input_path : Path
        Path to a bulk configuration file (CIF or JSON) on disk.
    output_dir : Path
        Directory where the generated GB supercell will be written.

    Returns
    -------
    Path
        Path to the saved GB supercell file.
    """
    # Load the bulk structure using pymatgen (supports CIF, POSCAR, etc.)
    try:
        bulk_structure = Structure.from_file(str(input_path))
    except Exception as exc:
        logger.error(f"Failed to load structure from {input_path}: {exc}")
        raise

    # Use the deterministic misorientation angle required by the spec.
    gb_structure = _build_gb_supercell_logic(bulk_structure,
                                             misorientation_angle=90.0,
                                             boundary_plane=(0.0, 0.0, 1.0))

    # Ensure the output directory exists.
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save using the same stem as the input file but with a suffix.
    output_path = output_dir / f"{input_path.stem}_gb.cif"
    gb_structure.to(filename=str(output_path))
    logger.info(f"GB supercell saved to {output_path}")
    return output_path

def save_structure(structure: Structure, output_path: Path):
    """
    Saves a structure to a file (e.g., CIF or POSCAR).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    structure.to(filename=str(output_path))
    logger.info(f"Saved structure to {output_path}")

def main():
    """
    Main entry point for the GB Builder script.
    """
    logger.info("GB Builder module loaded. Use build_gb_supercell_from_file() to construct GBs.")

if __name__ == "__main__":
    main()
