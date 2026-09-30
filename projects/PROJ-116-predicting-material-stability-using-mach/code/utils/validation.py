from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging
import numpy as np
import pandas as pd
from pymatgen.core import Structure

def check_missing_bond_lengths(structure: Structure) -> bool:
    """Check if structure has missing bond lengths."""
    try:
        # Attempt to get bond lengths
        bonds = structure.get_bond_distances()
        return len(bonds) == 0
    except Exception:
        return True

def check_degenerate_voronoi_cells(structure: Structure) -> bool:
    """Check if structure has degenerate Voronoi cells."""
    try:
        from pymatgen.analysis.voronoi import VoronoiNN
        vnn = VoronoiNN()
        # Try to get coordination numbers
        cn = vnn.get_cn(structure)
        return any(np.isnan(c) for c in cn)
    except Exception:
        return True

def validate_structure(structure: Structure) -> Tuple[bool, str]:
    """
    Validate a pymatgen Structure object.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if structure is None:
        return False, "Structure is None"

    if len(structure) == 0:
        return False, "Structure is empty"

    if not structure.is_ordered:
        return False, "Structure is disordered"

    try:
        structure.validate()
    except Exception as e:
        return False, f"Structure validation failed: {str(e)}"

    return True, ""

def validate_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Validate a dataset DataFrame.

    Args:
        df: DataFrame with material entries

    Returns:
        Tuple of (validated DataFrame, list of warnings)
    """
    warnings = []
    validated_df = df.copy()

    # Check for required columns
    required_cols = ['material_id', 'composition']
    for col in required_cols:
        if col not in validated_df.columns:
            warnings.append(f"Missing required column: {col}")

    # Check for missing values in critical columns
    if 'formation_energy' in validated_df.columns:
        missing = validated_df['formation_energy'].isna().sum()
        if missing > 0:
            warnings.append(f"Missing {missing} formation energy values")

    return validated_df, warnings

def filter_valid_structures(structures: List[Structure]) -> List[Structure]:
    """
    Filter a list of structures to remove invalid ones.

    Args:
        structures: List of pymatgen Structure objects

    Returns:
        List of valid structures
    """
    valid_structures = []
    for structure in structures:
        is_valid, error = validate_structure(structure)
        if is_valid:
            valid_structures.append(structure)
        else:
            logging.warning(f"Skipping invalid structure: {error}")

    return valid_structures
