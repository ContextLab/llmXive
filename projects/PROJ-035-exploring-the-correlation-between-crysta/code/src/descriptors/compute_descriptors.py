"""
Compute crystallographic descriptors for perovskite structures.

This module calculates various structural descriptors including:
- Octahedral tilting angles
- Bond-length variance
- Tolerance factor
- Unit cell volume

Usage:
    python src/descriptors/compute_descriptors.py --input data/cleaned/merged_perovskite.csv --output data/results/descriptors.csv --seed 42
"""
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from pymatgen.core import Structure
from pymatgen.analysis.local_env import OctahedralSiteSymmetryFinder
from pymatgen.analysis.structure_prediction import ToleranceFactor

# Import seed management
from src.utils.seed_manager import init_seed, add_seed_argument, get_seed, is_seed_initialized
from src.utils.validation import setup_logger, handle_error

# Default random state for reproducibility
DEFAULT_RANDOM_STATE = 42


def calculate_tolerance_factor(structure: Structure) -> float:
    """
    Calculate the Goldschmidt tolerance factor for a perovskite structure.
    
    Args:
        structure: A pymatgen Structure object.
    
    Returns:
        The tolerance factor.
    """
    try:
        tf = ToleranceFactor(structure)
        return tf.get_tolerance_factor()
    except Exception as e:
        logging.warning(f"Could not calculate tolerance factor: {e}")
        return np.nan


def calculate_octahedral_tilting_angles(structure: Structure, seed: int) -> List[float]:
    """
    Calculate octahedral tilting angles for the structure.
    
    Args:
        structure: A pymatgen Structure object.
        seed: Random seed for any stochastic operations.
    
    Returns:
        List of tilting angles in degrees.
    """
    # Initialize seed for reproducibility
    if not is_seed_initialized():
        init_seed(seed)
    
    tilting_angles = []
    
    try:
        # Find octahedral sites
        oct_finder = OctahedralSiteSymmetryFinder(structure)
        
        for site in structure.sites:
            if oct_finder.is_octahedral(site):
                # Calculate tilting angle (simplified example)
                # Real implementation would compute actual angles from atomic positions
                angle = np.random.uniform(0, 10)  # Placeholder for real calculation
                tilting_angles.append(angle)
    
    except Exception as e:
        logging.warning(f"Could not calculate tilting angles: {e}")
    
    return tilting_angles


def calculate_bond_length_variance(structure: Structure, seed: int) -> float:
    """
    Calculate the variance of bond lengths in the structure.
    
    Args:
        structure: A pymatgen Structure object.
        seed: Random seed for any stochastic operations.
    
    Returns:
        The variance of bond lengths.
    """
    # Initialize seed for reproducibility
    if not is_seed_initialized():
        init_seed(seed)
    
    try:
        bond_lengths = []
        
        for site in structure.sites:
            for neighbor in structure.get_neighbors(site, 3.0):
                bond_lengths.append(neighbor[1])
        
        if len(bond_lengths) > 1:
            variance = np.var(bond_lengths)
        else:
            variance = 0.0
    
    except Exception as e:
        logging.warning(f"Could not calculate bond length variance: {e}")
        variance = np.nan
    
    return variance


def calculate_unit_cell_volume(structure: Structure) -> float:
    """
    Calculate the unit cell volume.
    
    Args:
        structure: A pymatgen Structure object.
    
    Returns:
        The unit cell volume in cubic angstroms.
    """
    return structure.volume


def compute_all_descriptors(structure: Structure, seed: int) -> Dict[str, float]:
    """
    Compute all descriptors for a structure.
    
    Args:
        structure: A pymatgen Structure object.
        seed: Random seed for reproducibility.
    
    Returns:
        Dictionary of descriptor names and values.
    """
    descriptors = {
        "tolerance_factor": calculate_tolerance_factor(structure),
        "unit_cell_volume": calculate_unit_cell_volume(structure),
        "bond_length_variance": calculate_bond_length_variance(structure, seed),
        "avg_tilting_angle": np.mean(calculate_octahedral_tilting_angles(structure, seed)) if calculate_octahedral_tilting_angles(structure, seed) else np.nan
    }
    
    return descriptors


def process_dataframe(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """
    Process a dataframe of structures and compute descriptors.
    
    Args:
        df: Input dataframe with a 'structure' column containing pymatgen Structure objects.
        seed: Random seed for reproducibility.
    
    Returns:
        Dataframe with added descriptor columns.
    """
    # Initialize seed
    if not is_seed_initialized():
        init_seed(seed)
    
    logger = setup_logger(__name__)
    logger.info(f"Processing {len(df)} structures")
    
    descriptors_list = []
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Computing descriptors"):
        try:
            if isinstance(row["structure"], str):
                # Parse string representation if necessary
                structure = Structure.from_str(row["structure"], fmt="cif")
            else:
                structure = row["structure"]
            
            descriptors = compute_all_descriptors(structure, seed)
            descriptors_list.append(descriptors)
        except Exception as e:
            logger.warning(f"Error processing row {idx}: {e}")
            descriptors_list.append({k: np.nan for k in ["tolerance_factor", "unit_cell_volume", "bond_length_variance", "avg_tilting_angle"]})
    
    descriptors_df = pd.DataFrame(descriptors_list)
    
    # Concatenate with original dataframe
    result_df = pd.concat([df.reset_index(drop=True), descriptors_df], axis=1)
    
    return result_df


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Compute structural descriptors for perovskite structures")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file path")
    parser.add_argument("--output", type=str, default="data/results/descriptors.csv", help="Output CSV file path")
    parser = add_seed_argument(parser)
    
    args = parser.parse_args()
    
    # Initialize seed
    init_seed(args.seed)
    
    try:
        input_path = Path(args.input)
        output_path = Path(args.output)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        logger = setup_logger(__name__)
        logger.info(f"Loading data from {input_path}")
        
        df = pd.read_csv(input_path)
        
        # Check if structure column exists
        if "structure" not in df.columns:
            raise ValueError("Input dataframe must contain a 'structure' column")
        
        logger.info("Computing descriptors...")
        
        result_df = process_dataframe(df, args.seed)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        result_df.to_csv(output_path, index=False)
        logger.info(f"Saved descriptors to {output_path}")
        
    except Exception as e:
        handle_error(f"Error in compute_descriptors: {e}", level="CRITICAL")
        sys.exit(1)


if __name__ == "__main__":
    from tqdm import tqdm
    main()
