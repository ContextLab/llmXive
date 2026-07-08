"""
Graph Safety Utilities for Molecular Diffusion Prediction Pipeline.

This module detects high molecular weight molecules and implements
sampling/truncation logic during featurization to prevent memory crashes
as per Spec Edge Case SC-005.
"""
import logging
from typing import List, Tuple, Optional, Dict, Any
from rdkit import Chem
from rdkit.Chem import Descriptors

# Configure logger for this module
logger = logging.getLogger(__name__)

# Constants
MAX_MOLECULAR_WEIGHT = 1000.0  # g/mol threshold
MAX_ATOM_COUNT = 200  # Safety cap on number of atoms
MAX_GRAPH_NODES = 200  # Corresponds to atom count for molecular graphs

class MolecularSafetyError(Exception):
    """Raised when a molecule exceeds safety limits for graph construction."""
    pass

def check_molecular_weight(smiles: str) -> Tuple[bool, float]:
    """
    Check if a molecule's molecular weight exceeds the safety threshold.

    Args:
        smiles: SMILES string of the molecule.

    Returns:
        Tuple of (is_safe, molecular_weight).
        is_safe is True if MW <= MAX_MOLECULAR_WEIGHT.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False, 0.0
        mw = Descriptors.MolWt(mol)
        return mw <= MAX_MOLECULAR_WEIGHT, mw
    except Exception as e:
        logger.warning(f"Error calculating MW for {smiles}: {e}")
        return False, 0.0

def check_atom_count(smiles: str) -> Tuple[bool, int]:
    """
    Check if a molecule's atom count exceeds the safety threshold.

    Args:
        smiles: SMILES string of the molecule.

    Returns:
        Tuple of (is_safe, atom_count).
        is_safe is True if atom_count <= MAX_ATOM_COUNT.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False, 0
        count = mol.GetNumAtoms()
        return count <= MAX_ATOM_COUNT, count
    except Exception as e:
        logger.warning(f"Error counting atoms for {smiles}: {e}")
        return False, 0

def validate_molecule_safety(smiles: str) -> Dict[str, Any]:
    """
    Comprehensive safety validation for a molecule.

    Checks molecular weight and atom count against defined thresholds.

    Args:
        smiles: SMILES string of the molecule.

    Returns:
        Dictionary with validation results:
        {
            "is_safe": bool,
            "reason": str,
            "mw": float,
            "atom_count": int
        }
    """
    mw_safe, mw = check_molecular_weight(smiles)
    atom_safe, atom_count = check_atom_count(smiles)

    if not mw_safe:
        return {
            "is_safe": False,
            "reason": f"Molecular weight {mw:.2f} exceeds limit {MAX_MOLECULAR_WEIGHT}",
            "mw": mw,
            "atom_count": atom_count
        }

    if not atom_safe:
        return {
            "is_safe": False,
            "reason": f"Atom count {atom_count} exceeds limit {MAX_ATOM_COUNT}",
            "mw": mw,
            "atom_count": atom_count
        }

    return {
        "is_safe": True,
        "reason": "Molecule within safety limits",
        "mw": mw,
        "atom_count": atom_count
    }

def filter_safe_molecules(smiles_list: List[str]) -> Tuple[List[str], List[str]]:
    """
    Filter a list of SMILES to keep only safe molecules.

    Args:
        smiles_list: List of SMILES strings.

    Returns:
        Tuple of (safe_smiles, unsafe_smiles).
    """
    safe = []
    unsafe = []

    for smiles in smiles_list:
        result = validate_molecule_safety(smiles)
        if result["is_safe"]:
            safe.append(smiles)
        else:
            unsafe.append(smiles)
            logger.warning(f"Excluded unsafe molecule: {smiles} - {result['reason']}")

    return safe, unsafe

def truncate_molecule(smiles: str, max_atoms: Optional[int] = None) -> Optional[str]:
    """
    Attempt to truncate a molecule to fit within atom limits by removing
    peripheral atoms (simple heuristic: keep largest connected component).

    Args:
        smiles: SMILES string of the molecule.
        max_atoms: Maximum number of atoms allowed (defaults to MAX_ATOM_COUNT).

    Returns:
        Truncated SMILES if successful and within limits, None otherwise.
    """
    if max_atoms is None:
        max_atoms = MAX_ATOM_COUNT

    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None

        atom_count = mol.GetNumAtoms()
        if atom_count <= max_atoms:
            return smiles

        # Get largest connected component
        fragments = Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=True)
        if not fragments:
            return None

        # Sort by number of atoms (descending)
        sorted_frags = sorted(fragments, key=lambda m: m.GetNumAtoms(), reverse=True)
        largest_frag = sorted_frags[0]

        if largest_frag.GetNumAtoms() <= max_atoms:
            return Chem.MolToSmiles(largest_frag)

        # If still too large, return None
        return None

    except Exception as e:
        logger.error(f"Failed to truncate molecule {smiles}: {e}")
        return None

def safe_featurization_wrapper(featurize_func):
    """
    Decorator to wrap featurization functions with safety checks.

    This ensures that any featurization operation first validates the
    molecule against safety limits before attempting to construct graphs
    that could cause memory issues.

    Args:
        featurize_func: The featurization function to wrap.

    Returns:
        Wrapped function with safety checks.
    """
    def wrapper(smiles: str, *args, **kwargs):
        # Validate safety before featurization
        safety_result = validate_molecule_safety(smiles)

        if not safety_result["is_safe"]:
            raise MolecularSafetyError(
                f"Cannot featurize molecule: {safety_result['reason']}"
            )

        # Proceed with featurization
        return featurize_func(smiles, *args, **kwargs)

    return wrapper

def get_safety_config() -> Dict[str, Any]:
    """
    Return the current safety configuration.

    Returns:
        Dictionary with current safety thresholds and limits.
    """
    return {
        "max_molecular_weight": MAX_MOLECULAR_WEIGHT,
        "max_atom_count": MAX_ATOM_COUNT,
        "max_graph_nodes": MAX_GRAPH_NODES
    }

def update_safety_config(new_limits: Dict[str, Any]) -> None:
    """
    Update safety thresholds dynamically.

    Args:
        new_limits: Dictionary with new threshold values.
            Expected keys: 'max_molecular_weight', 'max_atom_count'
    """
    global MAX_MOLECULAR_WEIGHT, MAX_ATOM_COUNT, MAX_GRAPH_NODES

    if "max_molecular_weight" in new_limits:
        MAX_MOLECULAR_WEIGHT = float(new_limits["max_molecular_weight"])
    if "max_atom_count" in new_limits:
        MAX_ATOM_COUNT = int(new_limits["max_atom_count"])
    if "max_graph_nodes" in new_limits:
        MAX_GRAPH_NODES = int(new_limits["max_graph_nodes"])

    logger.info(f"Updated safety config: {get_safety_config()}")