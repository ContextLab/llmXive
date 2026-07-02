"""
Data validation utilities for molecular conductivity prediction pipeline.

This module provides functions to validate SMILES strings and check
target variable ranges for scientific plausibility.
"""
import logging
from typing import Tuple, List, Optional

import numpy as np
import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem

from config import OUTLIER_SIGMA, VIF_THRESHOLD, TARGET_VAR

logger = logging.getLogger(__name__)


def validate_smiles(smiles_str: str) -> Tuple[bool, Optional[str], Optional[Chem.Mol]]:
    """
    Validate a SMILES string and return the corresponding RDKit molecule object.

    Args:
        smiles_str: The SMILES string to validate.

    Returns:
        A tuple containing:
            - valid: Boolean indicating if the SMILES is valid.
            - error_msg: Error message if invalid, None otherwise.
            - mol: RDKit Mol object if valid, None otherwise.
    """
    if not isinstance(smiles_str, str) or not smiles_str.strip():
        return False, "SMILES string is empty or not a string", None

    try:
        # Sanitize and validate the SMILES
        mol = Chem.MolFromSmiles(smiles_str.strip())
        
        if mol is None:
            return False, "RDKit failed to parse SMILES string", None

        # Perform basic sanitization to catch chemical validity issues
        Chem.SanitizeMol(mol)
        
        # Additional check: ensure the molecule has at least one atom
        if mol.GetNumAtoms() == 0:
            return False, "Parsed molecule has no atoms", None

        return True, None, mol

    except Exception as e:
        error_msg = str(e)
        # Specific common errors
        if "MolFromSmiles" in error_msg:
            error_msg = "Invalid SMILES syntax"
        elif "SanitizeMol" in error_msg:
            error_msg = "Chemical sanitization failed (valence error, etc.)"
        
        logger.warning(f"SMILES validation failed: {error_msg}")
        return False, error_msg, None


def check_target_range(values: np.ndarray, min_log_range: float = 3.0) -> Tuple[bool, float]:
    """
    Check if the target variable values span a sufficient dynamic range.

    This function verifies that the logarithmic range of the target values
    meets the minimum required span for meaningful regression analysis.

    Args:
        values: 1D numpy array of target values (conductivity or HOMO-LUMO gap).
        min_log_range: Minimum required range in log10 space (default 3.0).

    Returns:
        A tuple containing:
            - valid: Boolean indicating if the range is sufficient.
            - log_range: The calculated log10 range of the values.
    
    Raises:
        ValueError: If values contain non-positive numbers (cannot take log).
    """
    if not isinstance(values, np.ndarray):
        values = np.array(values)

    if values.size == 0:
        raise ValueError("Input values array is empty")

    # Check for non-positive values
    if np.any(values <= 0):
        non_positive_count = int(np.sum(values <= 0))
        raise ValueError(
            f"Found {non_positive_count} non-positive values in target data. "
            "Log-transformation requires strictly positive values."
        )

    # Calculate log10 range
    log_values = np.log10(values)
    log_range = float(np.max(log_values) - np.min(log_values))

    valid = log_range >= min_log_range

    if not valid:
        logger.warning(
            f"Target variable range ({log_range:.2f}) is below minimum "
            f"threshold ({min_log_range}). Consider data augmentation or "
            "relaxing the threshold."
        )
    else:
        logger.info(f"Target variable range check passed: {log_range:.2f} >= {min_log_range}")

    return valid, log_range