"""
Parsers for molecular data formats (SMILES, XYZ) with error handling.

This module provides utilities to convert SMILES strings to RDKit molecules,
parse XYZ files into molecular structures, and validate molecular integrity.
"""
import logging
from typing import List, Optional, Tuple, Union

from rdkit import Chem
from rdkit.Chem import AllChem

# Configure module logger
logger = logging.getLogger(__name__)


def smiles_to_mol(smiles: str, sanitize: bool = True) -> Optional[Chem.Mol]:
    """
    Convert a SMILES string to an RDKit Mol object.

    Args:
        smiles: The SMILES string representing the molecule.
        sanitize: If True, perform RDKit sanitization (valence check, aromaticity, etc.).

    Returns:
        RDKit Mol object if successful, None if parsing fails.
    """
    if not smiles or not isinstance(smiles, str):
        logger.warning("Invalid SMILES input: %s", smiles)
        return None

    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning("RDKit failed to parse SMILES: %s", smiles)
            return None

        if sanitize:
            # Attempt sanitization to catch valence/aromaticity errors
            Chem.SanitizeMol(mol)

        # Add hydrogens for 3D consistency if needed later
        # Note: We don't add hydrogens here by default to keep 2D parsing fast,
        # but the caller can request it.
        return mol

    except Exception as e:
        logger.error("Error parsing SMILES '%s': %s", smiles, str(e))
        return None


def parse_xyz_to_mol(xyz_content: Union[str, List[str]]) -> Optional[Chem.Mol]:
    """
    Parse XYZ file content into an RDKit Mol object.

    Args:
        xyz_content: Either a string containing the full XYZ file content,
                     or a list of lines from an XYZ file.

    Returns:
        RDKit Mol object if successful, None if parsing fails.
    """
    try:
        if isinstance(xyz_content, str):
            lines = xyz_content.strip().split('\n')
        else:
            lines = [line.strip() for line in xyz_content if line.strip()]

        if len(lines) < 3:
            logger.warning("XYZ content too short to be valid.")
            return None

        # Skip comment lines (line 1 and 2 in standard XYZ)
        # Line 0: Atom count
        # Line 1: Comment
        # Line 2+: Coordinates
        try:
            num_atoms = int(lines[0])
        except ValueError:
            logger.warning("First line of XYZ is not an integer: %s", lines[0])
            return None

        if len(lines) < num_atoms + 2:
            logger.warning("XYZ file declares %d atoms but only has %d lines.", num_atoms, len(lines) - 2)
            return None

        # Extract atom data
        atoms = []
        coords = []
        for i in range(1, num_atoms + 1):
            line = lines[i]
            parts = line.split()
            if len(parts) < 4:
                logger.warning("Malformed atom line in XYZ: %s", line)
                return None

            symbol = parts[0]
            try:
                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
            except ValueError:
                logger.warning("Invalid coordinates in XYZ line: %s", line)
                return None

            atoms.append(symbol)
            coords.append((x, y, z))

        # Create RDKit editable molecule
        mol = Chem.RWMol()
        atom_indices = []

        # Add atoms
        for symbol in atoms:
            atom = Chem.Atom(symbol)
            idx = mol.AddAtom(atom)
            atom_indices.append(idx)

        # Add bonds (Heuristic: connect atoms within a distance threshold)
        # This is a simple connectivity heuristic for XYZ files which lack bond info
        # A more robust approach would use covalent radii, but this is a baseline.
        # We use a generous threshold to ensure connectivity for small molecules.
        # For QM9, we can assume standard bonding.
        
        # Calculate distances and add bonds
        for i in range(len(atom_indices)):
            for j in range(i + 1, len(atom_indices)):
                p1 = coords[i]
                p2 = coords[j]
                dist = ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)**0.5
                
                # Heuristic bond detection based on covalent radii sum
                # Using a simplified lookup for common elements in QM9
                radii = {'H': 0.31, 'C': 0.76, 'N': 0.71, 'O': 0.66, 'F': 0.57}
                r1 = radii.get(atoms[i], 0.8)
                r2 = radii.get(atoms[j], 0.8)
                threshold = (r1 + r2) * 1.3  # 30% tolerance

                if dist < threshold:
                    mol.AddBond(i, j, Chem.BondType.SINGLE)

        # Convert to immutable mol and sanitize
        mol = mol.GetMol()
        Chem.SanitizeMol(mol)
        
        # Set 3D coordinates
        conf = Chem.Conformer(mol.GetNumAtoms())
        for i, (x, y, z) in enumerate(coords):
            conf.SetAtomPosition(i, (x, y, z))
        mol.AddConformer(conf)

        return mol

    except Exception as e:
        logger.error("Error parsing XYZ content: %s", str(e))
        return None


def validate_molecule(mol: Optional[Chem.Mol]) -> Tuple[bool, str]:
    """
    Validate an RDKit molecule for common issues.

    Checks:
    - Mol is not None
    - Has at least one atom
    - No undefined valences (if sanitized)
    - No explicit hydrogens issues (optional)

    Args:
        mol: RDKit Mol object to validate.

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    if mol is None:
        return False, "Molecule is None"

    if mol.GetNumAtoms() == 0:
        return False, "Molecule has no atoms"

    # Check for undefined valences
    try:
        Chem.SanitizeMol(mol)
    except Exception as e:
        return False, f"Sanitization failed: {str(e)}"

    # Check for explicit hydrogens if they seem inconsistent
    # (Optional, depending on data source)
    # For QM9, we expect explicit hydrogens to be present in 3D structures
    
    return True, ""


def parse_smiles_list(smiles_list: List[str]) -> List[Tuple[str, Optional[Chem.Mol]]]:
    """
    Parse a list of SMILES strings into Mol objects, handling errors gracefully.

    Args:
        smiles_list: List of SMILES strings.

    Returns:
        List of tuples (original_smiles, mol_object). 
        mol_object is None if parsing failed for that entry.
    """
    results = []
    for i, smiles in enumerate(smiles_list):
        mol = smiles_to_mol(smiles)
        results.append((smiles, mol))
        if mol is None:
            logger.warning("Failed to parse SMILES at index %d: %s", i, smiles)
    
    return results