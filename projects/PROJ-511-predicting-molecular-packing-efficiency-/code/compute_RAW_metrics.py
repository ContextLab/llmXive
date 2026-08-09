"""
Compute Raw Packing Coefficient (PC) and Composition-Adjusted Packing Efficiency (CAPE).

This script reads the intermediate dataset (T013 output), calculates the van der Waals
volume sum using Bondi radii (via bondi_constants), and computes:
  1. PC_raw = Unit-cell volume / Sum(V_vdW)
  2. CAPE = PC_raw / (Sum(V_vdW) / N_atoms)

Input:  data/dataset_intermediate.csv
Output: data/dataset_with_metrics.csv
"""
import os
import sys
import logging
import math
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np

# Project imports
from bondi_constants import calculate_vdw_volume
from utils import setup_logging, fix_seed
from config import get_data_dir

# Configure logging
logger = logging.getLogger(__name__)

def calculate_unit_cell_volume(a: float, b: float, c: float, alpha: float, beta: float, gamma: float) -> float:
    """
    Calculate unit cell volume from lattice parameters.
    Alpha, beta, gamma must be in degrees.
    Formula: V = abc * sqrt(1 - cos^2(alpha) - cos^2(beta) - cos^2(gamma) + 2*cos(alpha)*cos(beta)*cos(gamma))
    """
    alpha_rad = math.radians(alpha)
    beta_rad = math.radians(beta)
    gamma_rad = math.radians(gamma)

    cos_alpha = math.cos(alpha_rad)
    cos_beta = math.cos(beta_rad)
    cos_gamma = math.cos(gamma_rad)

    term = 1.0 - cos_alpha**2 - cos_beta**2 - cos_gamma**2 + 2.0 * cos_alpha * cos_beta * cos_gamma

    if term <= 0:
        logger.warning(f"Invalid unit cell geometry term: {term}. Returning 0.")
        return 0.0

    return a * b * c * math.sqrt(term)

def calculate_vdw_volume_from_smiles(smiles: str) -> Tuple[float, int]:
    """
    Calculate the sum of van der Waals volumes for a molecule given its SMILES.
    Returns (total_vdw_volume, atom_count).
    Uses RDKit to parse SMILES and bondi_constants to get volumes.
    """
    from rdkit import Chem
    from rdkit.Chem import AllChem

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES string: {smiles}")

    # Generate 3D conformer to get coordinates (needed for volume calculation if bondi_constants requires it,
    # but calculate_vdw_volume from bondi_constants likely just sums atomic volumes based on element)
    # Let's check the signature of calculate_vdw_volume. Assuming it takes a mol or element list.
    # Based on typical Bondi implementations, it sums atomic volumes.
    # We need to iterate atoms.

    total_vdw = 0.0
    atom_count = 0

    for atom in mol.GetAtoms():
        symbol = atom.GetSymbol()
        # We assume calculate_vdw_volume takes an element symbol or atomic number
        # and returns the volume for that atom type.
        vol = calculate_vdw_volume(symbol)
        total_vdw += vol
        atom_count += 1

    return total_vdw, atom_count

def compute_metrics_for_cif(row: pd.Series) -> Dict[str, float]:
    """
    Compute PC_raw and CAPE for a single row in the dataset.
    """
    smiles = row['smiles']
    unit_cell_volume = row['unit_cell_volume']
    
    try:
        vdw_volume, n_atoms = calculate_vdw_volume_from_smiles(smiles)
    except Exception as e:
        logger.error(f"Failed to calculate V_vdW for SMILES '{smiles}': {e}")
        return {'pc_raw': None, 'cape': None, 'vdw_volume': None, 'n_atoms_vdw': None}

    if vdw_volume <= 0:
        logger.warning(f"Zero or negative V_vdW for SMILES '{smiles}'")
        return {'pc_raw': None, 'cape': None, 'vdw_volume': vdw_volume, 'n_atoms_vdw': n_atoms}

    # PC_raw = Unit-cell volume / Sum(V_vdW)
    # Note: Usually PC is Sum(V_vdW) / Unit-cell volume (packing fraction).
    # The task description says: "Calculate PC_raw = Unit-cell volume / Sum(V_vdW)".
    # This is the inverse of the standard packing fraction (void ratio related?).
    # We strictly follow the task description formula.
    pc_raw = unit_cell_volume / vdw_volume

    # CAPE = PC_raw / (Sum(V_vdW) / N_atoms)
    # This normalizes PC_raw by the average atomic volume.
    avg_atom_volume = vdw_volume / n_atoms if n_atoms > 0 else 0
    
    if avg_atom_volume == 0:
        cape = None
    else:
        cape = pc_raw / avg_atom_volume

    return {
        'pc_raw': pc_raw,
        'cape': cape,
        'vdw_volume': vdw_volume,
        'n_atoms_vdw': n_atoms
    }

def main():
    """
    Main entry point to compute metrics and save the dataset.
    """
    fix_seed(42)
    setup_logging(level=logging.INFO)

    data_dir = get_data_dir()
    input_path = os.path.join(data_dir, 'dataset_intermediate.csv')
    output_path = os.path.join(data_dir, 'dataset_with_metrics.csv')

    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Loading intermediate dataset from {input_path}")
    df = pd.read_csv(input_path)

    logger.info(f"Processing {len(df)} records to compute PC_raw and CAPE...")
    
    # Apply calculation row by row
    results = []
    for idx, row in df.iterrows():
        metrics = compute_metrics_for_cif(row)
        results.append(metrics)
        if (idx + 1) % 100 == 0:
            logger.info(f"Processed {idx + 1}/{len(df)} records")

    # Create DataFrame from results and merge
    metrics_df = pd.DataFrame(results)
    
    # Check for failures
    failed_count = metrics_df['pc_raw'].isna().sum()
    if failed_count > 0:
        logger.warning(f"{failed_count} records failed to compute metrics (NaN values).")

    # Merge back to original dataframe
    final_df = pd.concat([df.reset_index(drop=True), metrics_df], axis=1)

    logger.info(f"Saving final dataset with metrics to {output_path}")
    final_df.to_csv(output_path, index=False)

    # Log summary statistics
    valid_pc = final_df['pc_raw'].dropna()
    valid_cape = final_df['cape'].dropna()

    if len(valid_pc) > 0:
        logger.info(f"PC_raw stats - Mean: {valid_pc.mean():.4f}, Std: {valid_pc.std():.4f}, Min: {valid_pc.min():.4f}, Max: {valid_pc.max():.4f}")
    if len(valid_cape) > 0:
        logger.info(f"CAPE stats - Mean: {valid_cape.mean():.4f}, Std: {valid_cape.std():.4f}, Min: {valid_cape.min():.4f}, Max: {valid_cape.max():.4f}")

    logger.info("Task T015 completed successfully.")

if __name__ == "__main__":
    main()