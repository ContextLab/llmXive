from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging
import numpy as np
import pandas as pd
from pymatgen.core import Structure
from pymatgen.analysis.local_env import VoronoiNN

logger = logging.getLogger(__name__)

def check_missing_bond_lengths(structure: Structure) -> bool:
    """
    Check if the structure has missing bond lengths (degenerate bonds).
    Returns True if missing bond lengths are detected.
    """
    try:
        vnn = VoronoiNN()
        neighbors = vnn.get_nn(structure, list(range(len(structure))))
        for site_neighbors in neighbors:
            for neighbor in site_neighbors:
                if neighbor.distance is None or neighbor.distance == 0:
                    return True
        return False
    except Exception as e:
        logger.warning(f"Error checking bond lengths: {e}")
        return True  # Assume missing if check fails

def check_degenerate_voronoi_cells(structure: Structure) -> bool:
    """
    Check if the structure has degenerate Voronoi cells.
    Returns True if degenerate cells are detected.
    """
    try:
        vnn = VoronoiNN()
        # Attempt to compute Voronoi tessellation
        vnn.get_voronoi_polyhedra(structure)
        return False
    except Exception as e:
        logger.warning(f"Degenerate Voronoi cell detected: {e}")
        return True

def validate_structure(structure: Structure) -> Tuple[bool, List[str]]:
    """
    Validate a structure for feature engineering.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    if structure is None:
        return False, ["Structure is None"]
    
    if len(structure) == 0:
        return False, ["Structure has no sites"]
    
    if check_missing_bond_lengths(structure):
        errors.append("Missing bond lengths detected")
    
    if check_degenerate_voronoi_cells(structure):
        errors.append("Degenerate Voronoi cells detected")
    
    return len(errors) == 0, errors

def validate_dataset(df: pd.DataFrame, structure_col: str = "structure") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validate a dataset of structures.
    Returns (valid_df, invalid_df).
    """
    valid_indices = []
    invalid_indices = []
    
    for idx, row in df.iterrows():
        try:
            structure = row[structure_col]
            is_valid, _ = validate_structure(structure)
            if is_valid:
                valid_indices.append(idx)
            else:
                invalid_indices.append(idx)
        except Exception as e:
            logger.warning(f"Error validating row {idx}: {e}")
            invalid_indices.append(idx)
    
    valid_df = df.loc[valid_indices].reset_index(drop=True)
    invalid_df = df.loc[invalid_indices].reset_index(drop=True)
    
    return valid_df, invalid_df

def filter_valid_structures(df: pd.DataFrame, structure_col: str = "structure") -> pd.DataFrame:
    """
    Filter a dataset to keep only valid structures.
    """
    valid_df, _ = validate_dataset(df, structure_col)
    return valid_df
