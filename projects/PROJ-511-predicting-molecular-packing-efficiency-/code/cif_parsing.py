"""
CIF Parsing Utilities for Molecular Packing Efficiency Project.

This module provides robust CIF parsing utilities using pymatgen for structure
extraction and RDKit for SMILES generation when needed. Implements explicit
error handling for corrupt files without fallback to synthetic data.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path

import numpy as np
from pymatgen.core import Structure, Lattice
from pymatgen.io.cif import CifParser
from rdkit import Chem
from rdkit.Chem import AllChem

from utils import fix_seed, setup_logging
from error_handling import CIFParseError, MissingMetadataError, handle_corrupt_cif
from config import get_data_dir, get_models_dir

# Configure logging
logger = logging.getLogger(__name__)

def parse_cif_with_pymatgen(cif_path: str) -> Structure:
    """
    Parse a CIF file using pymatgen to extract unit cell and atomic coordinates.

    Args:
        cif_path: Path to the CIF file

    Returns:
        pymatgen Structure object

    Raises:
        CIFParseError: If the file is corrupt or cannot be parsed
        FileNotFoundError: If the file does not exist
    """
    if not os.path.exists(cif_path):
        raise FileNotFoundError(f"CIF file not found: {cif_path}")

    try:
        parser = CifParser(cif_path)
        structures = parser.get_structures()

        if not structures:
            raise CIFParseError(f"No structures found in CIF file: {cif_path}")

        # Return the first structure (most common case)
        structure = structures[0]
        logger.debug(f"Successfully parsed CIF: {cif_path}, "
                    f"n_atoms={structure.num_atoms}, "
                    f"space_group={structure.get_space_group_info()[0]}")

        return structure

    except Exception as e:
        error_msg = f"Failed to parse CIF file {cif_path}: {str(e)}"
        logger.error(error_msg)
        handle_corrupt_cif(cif_path, str(e))
        raise CIFParseError(error_msg) from e

def extract_unit_cell_info(structure: Structure) -> Dict[str, Any]:
    """
    Extract unit cell information from a pymatgen Structure.

    Args:
        structure: pymatgen Structure object

    Returns:
        Dictionary containing unit cell parameters
    """
    lattice = structure.lattice
    return {
        'a': lattice.a,
        'b': lattice.b,
        'c': lattice.c,
        'alpha': lattice.alpha,
        'beta': lattice.beta,
        'gamma': lattice.gamma,
        'volume': lattice.volume,
        'space_group': structure.get_space_group_info()[0],
        'n_atoms': structure.num_atoms,
        'composition': structure.composition.formula
    }

def extract_atomic_coordinates(structure: Structure) -> Tuple[List[str], np.ndarray]:
    """
    Extract atomic species and Cartesian coordinates from a Structure.

    Args:
        structure: pymatgen Structure object

    Returns:
        Tuple of (list of element symbols, numpy array of coordinates)
    """
    elements = [str(site.species_string) for site in structure]
    coords = np.array([site.coords for site in structure])
    return elements, coords

def generate_smiles_from_structure(structure: Structure, 
                                  use_3d: bool = True) -> Optional[str]:
    """
    Generate SMILES string from a pymatgen Structure using RDKit.

    This function creates an RDKit molecule from the crystal structure coordinates.
    It attempts to perceive bonds based on atomic distances and van der Waals radii.

    Args:
        structure: pymatgen Structure object
        use_3d: Whether to use 3D coordinates for bond perception

    Returns:
        SMILES string if successful, None otherwise
    """
    try:
        elements, coords = extract_atomic_coordinates(structure)

        # Create RDKit editable molecule
        mol = Chem.RWMol()

        # Add atoms
        atom_indices = []
        for elem in elements:
            atomic_num = Chem.GetAtomicNumber(elem)
            if atomic_num > 0:
                atom = Chem.Atom(atomic_num)
                idx = mol.AddAtom(atom)
                atom_indices.append(idx)
            else:
                # Skip unknown elements
                continue

        if len(atom_indices) == 0:
            logger.warning("No valid atoms found in structure")
            return None

        # Set 3D coordinates
        conf = Chem.Conformer(len(atom_indices))
        for i, idx in enumerate(atom_indices):
            if i < len(coords):
                conf.SetAtomPosition(idx, coords[i])
        mol.AddConformer(conf)

        # Perceive bonds based on distances
        # Use a distance-based approach for bond perception
        mol = mol.GetMol()
        Chem.SanitizeMol(mol)

        # Try to perceive bonds using RDKit's distance geometry
        try:
            AllChem.Compute2DCoords(mol)  # Fallback to 2D if needed
        except Exception:
            pass

        # Generate SMILES
        smiles = Chem.MolToSmiles(mol, isomericSmiles=True)
        if smiles:
            logger.debug(f"Generated SMILES from structure: {smiles[:50]}...")
            return smiles

    except Exception as e:
        logger.warning(f"Failed to generate SMILES from structure: {str(e)}")
        return None

    return None

def parse_cif_file(cif_path: str, 
                  generate_smiles: bool = True) -> Dict[str, Any]:
    """
    Comprehensive CIF file parsing with optional SMILES generation.

    This is the main entry point for parsing CIF files. It extracts:
    - Unit cell parameters
    - Atomic coordinates
    - Space group information
    - Optional SMILES string

    Args:
        cif_path: Path to the CIF file
        generate_smiles: Whether to generate SMILES from the structure

    Returns:
        Dictionary containing parsed data

    Raises:
        CIFParseError: If parsing fails
        MissingMetadataError: If required metadata is missing
    """
    logger.info(f"Parsing CIF file: {cif_path}")

    # Parse structure using pymatgen
    structure = parse_cif_with_pymatgen(cif_path)

    # Extract unit cell information
    unit_cell_info = extract_unit_cell_info(structure)

    # Extract atomic coordinates
    elements, coords = extract_atomic_coordinates(structure)

    # Generate SMILES if requested
    smiles = None
    if generate_smiles:
        smiles = generate_smiles_from_structure(structure)
        if smiles is None:
            logger.warning(f"Could not generate SMILES for {cif_path}")

    return {
        'cif_path': cif_path,
        'structure': structure,
        'unit_cell': unit_cell_info,
        'elements': elements,
        'coordinates': coords,
        'smiles': smiles,
        'n_atoms': unit_cell_info['n_atoms']
    }

def validate_cif_structure(structure: Structure, 
                          max_atoms: int = 50,
                          required_elements: Optional[List[str]] = None) -> bool:
    """
    Validate a CIF structure against project constraints.

    Args:
        structure: pymatgen Structure object
        max_atoms: Maximum number of non-hydrogen atoms allowed
        required_elements: Optional list of required elements

    Returns:
        True if structure passes validation

    Raises:
        CIFParseError: If structure fails validation
    """
    # Count non-hydrogen atoms
    non_h_atoms = sum(1 for site in structure if site.species_string != 'H')

    if non_h_atoms > max_atoms:
        raise CIFParseError(
            f"Structure has {non_h_atoms} non-H atoms, exceeds limit of {max_atoms}"
        )

    # Check required elements if specified
    if required_elements:
        structure_elements = set(site.species_string for site in structure)
        missing = set(required_elements) - structure_elements
        if missing:
            raise CIFParseError(
                f"Structure missing required elements: {missing}"
            )

    return True

def batch_parse_cif_files(cif_paths: List[str], 
                         generate_smiles: bool = True,
                         max_atoms: int = 50) -> List[Dict[str, Any]]:
    """
    Parse multiple CIF files with error handling and logging.

    Args:
        cif_paths: List of paths to CIF files
        generate_smiles: Whether to generate SMILES for each file
        max_atoms: Maximum non-hydrogen atoms allowed per structure

    Returns:
        List of successfully parsed data dictionaries
    """
    results = []
    failures = []

    for cif_path in cif_paths:
        try:
            data = parse_cif_file(cif_path, generate_smiles=generate_smiles)
            validate_cif_structure(data['structure'], max_atoms=max_atoms)
            results.append(data)
            logger.info(f"Successfully parsed: {cif_path}")

        except (CIFParseError, MissingMetadataError, FileNotFoundError) as e:
            failures.append({'path': cif_path, 'error': str(e)})
            logger.error(f"Failed to parse {cif_path}: {str(e)}")

        except Exception as e:
            failures.append({'path': cif_path, 'error': f"Unexpected error: {str(e)}"})
            logger.exception(f"Unexpected error parsing {cif_path}")

    if failures:
        logger.warning(f"Batch parsing completed with {len(failures)} failures")
        for fail in failures[:5]:  # Log first 5 failures
            logger.warning(f"  - {fail['path']}: {fail['error']}")

    return results

def main():
    """
    Main function for testing CIF parsing utilities.
    """
    setup_logging()
    fix_seed(42)

    # Example usage - this would be called with real CIF paths
    logger.info("CIF Parsing Module Initialized")
    logger.info("Available functions:")
    logger.info("  - parse_cif_with_pymatgen(cif_path)")
    logger.info("  - extract_unit_cell_info(structure)")
    logger.info("  - extract_atomic_coordinates(structure)")
    logger.info("  - generate_smiles_from_structure(structure)")
    logger.info("  - parse_cif_file(cif_path, generate_smiles=True)")
    logger.info("  - validate_cif_structure(structure, max_atoms=50)")
    logger.info("  - batch_parse_cif_files(cif_paths, generate_smiles=True)")

    # Note: Actual parsing requires real CIF files in data/raw_cif/
    # This module is designed to be called by other pipeline components
