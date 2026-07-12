"""
Parsers for molecular data: SMILES conversion and XYZ file parsing.
Includes error handling for malformed molecules and invalid geometries.
"""
import logging
from typing import List, Optional, Tuple, Union, Dict, Any

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import RDLogger

# Disable RDKit warnings to keep logs clean
RDLogger.DisableLog('rdApp.*')

logger = logging.getLogger(__name__)


def smiles_to_mol(smiles: str, sanitize: bool = True) -> Optional[Chem.Mol]:
    """
    Convert a SMILES string to an RDKit Mol object.

    Args:
        smiles: The SMILES string representing the molecule.
        sanitize: Whether to run RDKit's sanitization step.

    Returns:
        RDKit Mol object if successful, None if parsing fails.
    """
    if not smiles or not isinstance(smiles, str):
        logger.warning("Invalid input: SMILES must be a non-empty string.")
        return None

    try:
        mol = Chem.MolFromSmiles(smiles, sanitize=sanitize)
        if mol is None:
            logger.warning(f"Failed to parse SMILES: {smiles}")
            return None

        # Optional: Add hydrogens if needed for 3D, but return base mol here
        return mol
    except Exception as e:
        logger.error(f"Exception during SMILES parsing for '{smiles}': {e}")
        return None


def parse_xyz_to_mol(xyz_content: Union[str, List[str]], title: str = "") -> Optional[Chem.Mol]:
    """
    Parse XYZ format content into an RDKit Mol object.

    Args:
        xyz_content: Either a string containing the full XYZ file content
                     or a list of lines.
        title: Optional title line from the XYZ file (for logging).

    Returns:
        RDKit Mol object with 3D coordinates if successful, None on failure.
    """
    try:
        if isinstance(xyz_content, str):
            lines = xyz_content.strip().split('\n')
        else:
            lines = xyz_content

        if len(lines) < 3:
            logger.warning(f"Invalid XYZ content (too few lines) for title: {title}")
            return None

        # Skip comment line (line 1)
        # Line 0: Atom count
        try:
            n_atoms = int(lines[0].strip())
        except ValueError:
            logger.warning(f"Invalid atom count in XYZ for title: {title}")
            return None

        if len(lines) < n_atoms + 2:
            logger.warning(f"XYZ content truncated for title: {title}")
            return None

        symbols = []
        coords = []

        for i in range(1, n_atoms + 1):
            line = lines[i].strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 4:
                logger.warning(f"Malformed atom line in XYZ for title: {title}")
                return None

            symbol = parts[0]
            try:
                x, y, z = map(float, parts[1:4])
            except ValueError:
                logger.warning(f"Invalid coordinates in XYZ for title: {title}")
                return None

            symbols.append(symbol)
            coords.append([x, y, z])

        # Create RDKit molecule
        mol = Chem.RWMol()
        for symbol in symbols:
            atom = Chem.Atom(symbol)
            mol.AddAtom(atom)

        # Create 3D conformation
        conf = Chem.Conformer(mol.GetNumAtoms())
        for i, coord in enumerate(coords):
            conf.SetAtomPosition(i, coord)

        mol.AddConformer(conf)

        # Attempt to infer bonds (simple distance-based heuristic for organic molecules)
        # RDKit doesn't automatically bond from XYZ without 2D/3D info usually,
        # but we can use AllChem.AssignBondOrdersFromTemplate if we had one,
        # or just rely on the fact that the geometry is stored.
        # For this task, we return the mol with geometry.
        # Note: A full parser might use distance matrix to assign bonds.
        # We will use a simple distance cutoff heuristic to assign single bonds.
        AllChem.Compute2DCoords(mol) # Dummy call to ensure topology exists if needed, though we have 3D
        
        # Basic bond assignment based on covalent radii
        # This is a simplified heuristic; real XYZ parsers often rely on connectivity lists.
        # For QM9, we often have connectivity or can infer it.
        # Let's use a simple distance check.
        coords_arr = mol.GetConformer().GetPositions()
        for i in range(mol.GetNumAtoms()):
            for j in range(i + 1, mol.GetNumAtoms()):
                dist = (coords_arr[i] - coords_arr[j]).length()
                # Heuristic: sum of covalent radii * 1.2
                # Simplified radii lookup
                radii = {'H': 0.31, 'C': 0.76, 'N': 0.71, 'O': 0.66, 'F': 0.57}
                r1 = radii.get(symbols[i], 0.7)
                r2 = radii.get(symbols[j], 0.7)
                if dist < (r1 + r2) * 1.3:
                    mol.AddBond(i, j, Chem.BondType.SINGLE)

        mol = mol.GetMol()
        return mol

    except Exception as e:
        logger.error(f"Exception during XYZ parsing for title '{title}': {e}")
        return None


def validate_molecule(mol: Optional[Chem.Mol], require_3d: bool = False) -> Tuple[bool, str]:
    """
    Validate an RDKit molecule object.

    Args:
        mol: The RDKit Mol object to validate.
        require_3d: If True, the molecule must have 3D coordinates.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if mol is None:
        return False, "Molecule object is None."

    if mol.GetNumAtoms() == 0:
        return False, "Molecule has no atoms."

    if require_3d:
        if not mol.GetNumConformers():
            return False, "Molecule has no 3D conformers."
        conf = mol.GetConformer()
        # Check for NaN or Inf in coordinates
        for i in range(mol.GetNumAtoms()):
            pos = conf.GetAtomPosition(i)
            if not (pos.x == pos.x and pos.y == pos.y and pos.z == pos.z):
                return False, f"Invalid coordinates (NaN/Inf) found for atom {i}."

    return True, "Valid."


def parse_smiles_list(
    smiles_list: List[str],
    log_failures: bool = True
) -> List[Chem.Mol]:
    """
    Parse a list of SMILES strings into a list of valid Mol objects.

    Args:
        smiles_list: List of SMILES strings.
        log_failures: Whether to log warnings for failed parses.

    Returns:
        List of successfully parsed RDKit Mol objects.
    """
    valid_mols = []
    for i, smi in enumerate(smiles_list):
        mol = smiles_to_mol(smi)
        if mol is not None:
            valid_mols.append(mol)
        elif log_failures:
            logger.warning(f"Skipped malformed SMILES at index {i}: {smi}")
    
    if log_failures:
        logger.info(f"Parsed {len(valid_mols)} valid molecules out of {len(smiles_list)}.")
    
    return valid_mols