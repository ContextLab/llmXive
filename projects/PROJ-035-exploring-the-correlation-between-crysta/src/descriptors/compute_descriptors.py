"""
Compute crystallographic descriptors for perovskite structures.

Calculates:
- Octahedral tilting angles
- Bond-length variance
- Tolerance factor
- Unit cell volume

Output: data/descriptors.csv
"""
import sys
import logging
import argparse
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
import pandas as pd
from pymatgen.core import Structure
from pymatgen.analysis.local_env import OctahedralSiteSymmetryFinder
from pymatgen.analysis.structure_prediction.tolerance_factor import GlobalToleranceFactor
from src.utils.seed_manager import init_seed, get_seed, setup_logger_module

logger = setup_logger_module(__name__)

def calculate_tolerance_factor(structure: Structure) -> float:
    """
    Calculate the Goldschmidt tolerance factor.
    
    Args:
        structure: Pymatgen Structure object
        
    Returns:
        Tolerance factor (float)
    """
    try:
        gtf = GlobalToleranceFactor(structure)
        return float(gtf.tolerance_factor)
    except Exception as e:
        logger.warning(f"Failed to calculate tolerance factor: {e}")
        return np.nan

def calculate_octahedral_tilting_angles(structure: Structure) -> float:
    """
    Calculate the average octahedral tilting angle.
    
    Uses OctahedralSiteSymmetryFinder to identify B-site cations in octahedral
    coordination and computes the deviation from ideal 90-degree bond angles.
    
    Args:
        structure: Pymatgen Structure object
        
    Returns:
        Average tilting angle in degrees (float)
    """
    try:
        # Identify octahedral sites (typically B-site cations in perovskites)
        oct_finder = OctahedralSiteSymmetryFinder(structure)
        octahedral_sites = oct_finder.get_octahedral_sites()
        
        if not octahedral_sites:
            logger.warning("No octahedral sites found in structure")
            return np.nan
        
        tilting_angles = []
        
        for site in octahedral_sites:
            # Get the coordination environment
            coordination = site.get_coordination()
            if coordination is None or len(coordination) < 6:
                continue
            
            # Extract bond angles between anions around the cation
            # For ideal octahedron, angles should be 90 or 180 degrees
            # Tilting is measured as deviation from 90 degrees for nearest neighbors
            anion_sites = coordination.sites
            
            # Calculate angles between adjacent anions
            from pymatgen.util.coord import get_angle
            for i in range(len(anion_sites)):
                for j in range(i + 1, len(anion_sites)):
                    vec_i = anion_sites[i].coords - site.coords
                    vec_j = anion_sites[j].coords - site.coords
                    
                    # Normalize vectors
                    norm_i = np.linalg.norm(vec_i)
                    norm_j = np.linalg.norm(vec_j)
                    
                    if norm_i > 1e-6 and norm_j > 1e-6:
                        cos_angle = np.dot(vec_i, vec_j) / (norm_i * norm_j)
                        # Clamp to [-1, 1] to avoid numerical errors
                        cos_angle = np.clip(cos_angle, -1.0, 1.0)
                        angle = np.degrees(np.arccos(cos_angle))
                        
                        # Only consider angles close to 90 degrees (adjacent anions)
                        # In a perfect octahedron, 12 angles are 90°, 3 are 180°
                        if 80 <= angle <= 100:
                            tilting_angles.append(abs(angle - 90.0))
        
        if not tilting_angles:
            return 0.0
        
        return float(np.mean(tilting_angles))
        
    except Exception as e:
        logger.warning(f"Failed to calculate octahedral tilting angles: {e}")
        return np.nan

def calculate_bond_length_variance(structure: Structure) -> float:
    """
    Calculate the variance of bond lengths for B-X bonds in the structure.
    
    Args:
        structure: Pymatgen Structure object
        
    Returns:
        Variance of bond lengths (float)
    """
    try:
        oct_finder = OctahedralSiteSymmetryFinder(structure)
        octahedral_sites = oct_finder.get_octahedral_sites()
        
        if not octahedral_sites:
            logger.warning("No octahedral sites found for bond length calculation")
            return np.nan
        
        bond_lengths = []
        
        for site in octahedral_sites:
            # Get coordination environment
            coordination = site.get_coordination()
            if coordination is None:
                continue
            
            for neighbor in coordination.sites:
                dist = site.distance(neighbor)
                # Filter for reasonable bond lengths (typically 1.5-3.0 Angstrom for perovskites)
                if 1.5 <= dist <= 3.0:
                    bond_lengths.append(dist)
        
        if len(bond_lengths) < 2:
            return np.nan
        
        return float(np.var(bond_lengths))
        
    except Exception as e:
        logger.warning(f"Failed to calculate bond length variance: {e}")
        return np.nan

def calculate_unit_cell_volume(structure: Structure) -> float:
    """
    Calculate the unit cell volume.
    
    Args:
        structure: Pymatgen Structure object
        
    Returns:
        Unit cell volume in Angstrom^3 (float)
    """
    try:
        return float(structure.lattice.volume)
    except Exception as e:
        logger.warning(f"Failed to calculate unit cell volume: {e}")
        return np.nan

def compute_all_descriptors(structure: Structure) -> Dict[str, float]:
    """
    Compute all descriptors for a single structure.
    
    Args:
        structure: Pymatgen Structure object
        
    Returns:
        Dictionary with descriptor names and values
    """
    return {
        'tolerance_factor': calculate_tolerance_factor(structure),
        'octahedral_tilting_angle': calculate_octahedral_tilting_angles(structure),
        'bond_length_variance': calculate_bond_length_variance(structure),
        'unit_cell_volume': calculate_unit_cell_volume(structure)
    }

def process_dataframe(df: pd.DataFrame, structure_column: str = 'structure') -> pd.DataFrame:
    """
    Process a dataframe containing structure objects and compute descriptors.
    
    Args:
        df: Input dataframe with structure column
        structure_column: Name of the column containing Structure objects
        
    Returns:
        Dataframe with added descriptor columns
    """
    logger.info(f"Processing {len(df)} structures for descriptor calculation")
    
    descriptors_list = []
    
    for idx, row in df.iterrows():
        try:
            structure = row[structure_column]
            if not isinstance(structure, Structure):
                logger.warning(f"Row {idx} does not contain a valid Structure object")
                descriptors_list.append({
                    'tolerance_factor': np.nan,
                    'octahedral_tilting_angle': np.nan,
                    'bond_length_variance': np.nan,
                    'unit_cell_volume': np.nan
                })
                continue
            
            desc = compute_all_descriptors(structure)
            descriptors_list.append(desc)
            
            if (idx + 1) % 10 == 0:
                logger.info(f"Processed {idx + 1}/{len(df)} structures")
                
        except Exception as e:
            logger.error(f"Error processing row {idx}: {e}")
            descriptors_list.append({
                'tolerance_factor': np.nan,
                'octahedral_tilting_angle': np.nan,
                'bond_length_variance': np.nan,
                'unit_cell_volume': np.nan
            })
    
    desc_df = pd.DataFrame(descriptors_list)
    result_df = pd.concat([df.reset_index(drop=True), desc_df], axis=1)
    
    return result_df

def main():
    """Main entry point for descriptor computation."""
    parser = argparse.ArgumentParser(
        description='Compute crystallographic descriptors for perovskite structures'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/cleaned/merged_perovskite.csv',
        help='Path to input CSV with structure column'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/descriptors.csv',
        help='Path to output CSV with descriptors'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for any stochastic operations'
    )
    parser.add_argument(
        '--structure-column',
        type=str,
        default='structure',
        help='Name of the column containing Structure objects'
    )
    
    args = parser.parse_args()
    
    # Initialize seed
    init_seed(args.seed)
    logger.info(f"Initialized with seed: {get_seed()}")
    
    # Load input data
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Check for structure column
    if args.structure_column not in df.columns:
        logger.error(f"Structure column '{args.structure_column}' not found in input data")
        logger.info(f"Available columns: {list(df.columns)}")
        sys.exit(1)
    
    # Note: If structures are stored as strings (e.g., JSON), they need to be deserialized
    # For this implementation, we assume structures are either already loaded or
    # we need to reconstruct them from stored data
    
    # Check if structures need to be reconstructed
    if df[args.structure_column].dtype == 'object':
        first_val = df[args.structure_column].iloc[0]
        if isinstance(first_val, str):
            logger.info("Detected string structures, attempting reconstruction...")
            try:
                import json
                from pymatgen.serialization.pmg import from_dict
                
                def reconstruct_structure(struct_str):
                    if pd.isna(struct_str) or struct_str == '':
                        return None
                    try:
                        struct_dict = json.loads(struct_str)
                        return Structure.from_dict(struct_dict)
                    except Exception as e:
                        logger.warning(f"Failed to reconstruct structure: {e}")
                        return None
                
                df[args.structure_column] = df[args.structure_column].apply(reconstruct_structure)
            except Exception as e:
                logger.error(f"Failed to set up structure reconstruction: {e}")
                sys.exit(1)
    
    # Compute descriptors
    result_df = process_dataframe(df, args.structure_column)
    
    # Remove the structure column from output (keep only primitive data)
    output_df = result_df.drop(columns=[args.structure_column], errors='ignore')
    
    # Save output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)
    
    logger.info(f"Descriptors saved to {output_path}")
    logger.info(f"Output shape: {output_df.shape}")
    logger.info(f"Columns: {list(output_df.columns)}")
    
    # Summary statistics
    logger.info("Descriptor summary:")
    for col in ['tolerance_factor', 'octahedral_tilting_angle', 'bond_length_variance', 'unit_cell_volume']:
        if col in output_df.columns:
            valid_count = output_df[col].notna().sum()
            logger.info(f"  {col}: {valid_count} valid values, mean={output_df[col].mean():.4f}, std={output_df[col].std():.4f}")

if __name__ == '__main__':
    main()
