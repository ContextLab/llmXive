"""
Validation utilities for material stability prediction pipeline.

Provides functions to check for missing bond lengths and degenerate Voronoi cells
in crystal structure data, ensuring data quality before feature engineering.
"""
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging
import numpy as np
import pandas as pd
from pymatgen.core import Structure
from pymatgen.analysis.local_env import VoronoiNN

from utils.logging import setup_logger
from config import DATA_PROCESSED_DIR, DATA_RAW_DIR

# Initialize logger for this module
logger = setup_logger(__name__)


def check_missing_bond_lengths(
    structure: Structure,
    cutoff: float = 5.0
) -> Tuple[bool, List[str]]:
    """
    Check if a structure has missing bond lengths within a given cutoff.
    
    Args:
        structure: Pymatgen Structure object to analyze.
        cutoff: Maximum distance (Angstrom) to consider for bonding.
        
    Returns:
        Tuple of (has_missing: bool, missing_bonds: List of atom indices)
    """
    try:
        vnn = VoronoiNN(cutoff=cutoff)
        bonds = vnn.get_bonds(structure)
        
        missing_bonds = []
        for i, site in enumerate(structure):
            if i not in bonds or len(bonds[i]) == 0:
                missing_bonds.append(i)
        
        has_missing = len(missing_bonds) > 0
        if has_missing:
            logger.warning(
                f"Structure has {len(missing_bonds)} sites with missing bond lengths: {missing_bonds[:5]}..."
            )
        
        return has_missing, missing_bonds
        
    except Exception as e:
        logger.error(f"Error checking bond lengths: {e}")
        return True, list(range(len(structure)))


def check_degenerate_voronoi_cells(
    structure: Structure,
    min_volume: float = 0.01
) -> Tuple[bool, List[int]]:
    """
    Check for degenerate Voronoi cells (volume too small or zero).
    
    Args:
        structure: Pymatgen Structure object to analyze.
        min_volume: Minimum acceptable cell volume (Angstrom^3).
        
    Returns:
        Tuple of (has_degenerate: bool, degenerate_indices: List of atom indices)
    """
    try:
        vnn = VoronoiNN()
        voronoi_wfs = vnn.get_voronoi_tessellation(structure)
        
        degenerate_indices = []
        for i, wf in enumerate(voronoi_wfs):
            if wf is None or wf.volume < min_volume:
                degenerate_indices.append(i)
        
        has_degenerate = len(degenerate_indices) > 0
        if has_degenerate:
            logger.warning(
                f"Structure has {len(degenerate_indices)} degenerate Voronoi cells: {degenerate_indices[:5]}..."
            )
        
        return has_degenerate, degenerate_indices
        
    except Exception as e:
        logger.error(f"Error checking Voronoi cells: {e}")
        return True, list(range(len(structure)))


def validate_structure(
    structure: Structure,
    bond_cutoff: float = 5.0,
    min_voronoi_volume: float = 0.01
) -> Dict[str, Any]:
    """
    Comprehensive validation of a crystal structure.
    
    Args:
        structure: Pymatgen Structure object to validate.
        bond_cutoff: Maximum distance for bond length check.
        min_voronoi_volume: Minimum volume for Voronoi cell check.
        
    Returns:
        Dictionary with validation results:
        - is_valid: bool
        - missing_bond_count: int
        - degenerate_voronoi_count: int
        - issues: List of issue descriptions
    """
    issues = []
    
    # Check bond lengths
    has_missing_bonds, missing_bonds = check_missing_bond_lengths(
        structure, bond_cutoff
    )
    if has_missing_bonds:
        issues.append(f"Missing bond lengths at {len(missing_bonds)} sites")
    
    # Check Voronoi cells
    has_degenerate_voronoi, degenerate_voronoi = check_degenerate_voronoi_cells(
        structure, min_voronoi_volume
    )
    if has_degenerate_voronoi:
        issues.append(f"Degenerate Voronoi cells at {len(degenerate_voronoi)} sites")
    
    is_valid = len(issues) == 0
    
    result = {
        "is_valid": is_valid,
        "missing_bond_count": len(missing_bonds),
        "degenerate_voronoi_count": len(degenerate_voronoi),
        "issues": issues
    }
    
    if not is_valid:
        logger.warning(f"Structure validation failed: {', '.join(issues)}")
    
    return result


def validate_dataset(
    structures: List[Structure],
    bond_cutoff: float = 5.0,
    min_voronoi_volume: float = 0.01,
    log_file: Optional[str] = None
) -> pd.DataFrame:
    """
    Validate a list of structures and return a DataFrame with results.
    
    Args:
        structures: List of Pymatgen Structure objects.
        bond_cutoff: Maximum distance for bond length check.
        min_voronoi_volume: Minimum volume for Voronoi cell check.
        log_file: Optional path to write detailed validation log.
        
    Returns:
        DataFrame with validation results for each structure.
    """
    results = []
    
    for idx, structure in enumerate(structures):
        validation = validate_structure(
            structure, bond_cutoff, min_voronoi_volume
        )
        results.append({
            "structure_index": idx,
            "is_valid": validation["is_valid"],
            "missing_bond_count": validation["missing_bond_count"],
            "degenerate_voronoi_count": validation["degenerate_voronoi_count"],
            "issues": "; ".join(validation["issues"]) if validation["issues"] else ""
        })
    
    df = pd.DataFrame(results)
    
    # Log summary
    total = len(df)
    valid = df["is_valid"].sum()
    invalid = total - valid
    
    logger.info(f"Dataset validation complete: {valid}/{total} structures valid")
    
    if invalid > 0:
        logger.warning(f"Found {invalid} invalid structures. Review log for details.")
    
    # Write detailed log if requested
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(log_path, index=False)
        logger.info(f"Validation details saved to {log_file}")
    
    return df


def filter_valid_structures(
    structures: List[Structure],
    bond_cutoff: float = 5.0,
    min_voronoi_volume: float = 0.01
) -> List[Tuple[Structure, int]]:
    """
    Filter a list of structures, returning only valid ones with their original indices.
    
    Args:
        structures: List of Pymatgen Structure objects.
        bond_cutoff: Maximum distance for bond length check.
        min_voronoi_volume: Minimum volume for Voronoi cell check.
        
    Returns:
        List of tuples (structure, original_index) for valid structures.
    """
    valid_structures = []
    
    for idx, structure in enumerate(structures):
        validation = validate_structure(
            structure, bond_cutoff, min_voronoi_volume
        )
        if validation["is_valid"]:
            valid_structures.append((structure, idx))
    
    logger.info(
        f"Filtered dataset: {len(valid_structures)}/{len(structures)} structures remain valid"
    )
    
    return valid_structures
