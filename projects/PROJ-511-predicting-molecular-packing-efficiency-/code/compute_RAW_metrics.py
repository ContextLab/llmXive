"""
Compute Raw Packing Coefficient (PC) and CAPE metrics.

Reads: data/dataset_intermediate.csv
Writes: data/dataset_with_metrics.csv

Logic:
  1. Load intermediate dataset.
  2. For each row, generate a 3D conformer from SMILES.
  3. Calculate the sum of van der Waals volumes using Bondi radii.
  4. Calculate Raw PC = Unit-cell volume / Sum(V_vdW).
  5. Calculate CAPE = Raw PC / (Sum(V_vdW) / N_atoms).
  6. Save results.
"""
import os
import sys
import logging
import math
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem

# Import local utilities ensuring API compatibility
from bondi_constants import BOND_RADII, calculate_vdw_volume
from utils import fix_seed, setup_logging
from config import get_data_dir

# Configure logging
logger = setup_logging(__name__)
fix_seed(42)

def calculate_unit_cell_volume(a: float, b: float, c: float,
                               alpha: float, beta: float, gamma: float) -> float:
    """
    Calculate unit cell volume from lattice parameters.
    Angles are expected in degrees.
    Formula: V = abc * sqrt(1 - cos^2(alpha) - cos^2(beta) - cos^2(gamma)
                     + 2*cos(alpha)*cos(beta)*cos(gamma))
    """
    alpha_rad = math.radians(alpha)
    beta_rad = math.radians(beta)
    gamma_rad = math.radians(gamma)

    cos_alpha = math.cos(alpha_rad)
    cos_beta = math.cos(beta_rad)
    cos_gamma = math.cos(gamma_rad)

    # Handle potential floating point errors slightly outside [-1, 1]
    term = 1 - cos_alpha**2 - cos_beta**2 - cos_gamma**2 + 2 * cos_alpha * cos_beta * cos_gamma
    if term < 0:
        if term > -1e-6:
            term = 0.0
        else:
            raise ValueError(f"Invalid lattice parameters resulting in negative volume term: {term}")

    return a * b * c * math.sqrt(term)

def calculate_vdw_volume_from_smiles(smiles: str) -> Tuple[float, int]:
    """
    Calculate the sum of van der Waals volumes for atoms in a molecule.
    Uses Bondi radii.
    Returns: (total_vdw_volume, atom_count)
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")

    # Generate a 3D conformer to ensure we have coordinates if needed,
    # though for volume sum we mostly need atom types.
    # However, RDKit's AddHs is important for accurate volume if hydrogens are implicit.
    mol_h = Chem.AddHs(mol)
    AllChem.EmbedMolecule(mol_h, randomSeed=42)

    total_volume = 0.0
    atom_count = 0

    for atom in mol_h.GetAtoms():
        symbol = atom.GetSymbol()
        if symbol in BOND_RADII:
            r = BOND_RADII[symbol]
            vol = calculate_vdw_volume(r)
            total_volume += vol
            atom_count += 1
        else:
            # Fallback for unknown elements (log warning)
            logger.warning(f"Unknown element {symbol} in SMILES {smiles}. Skipping volume contribution.")

    return total_volume, atom_count

def compute_metrics_for_cif(row: pd.Series) -> Dict[str, Any]:
    """
    Compute PC_raw and CAPE for a single row.
    """
    smiles = row['smiles']
    unit_cell_volume = row['unit_cell_volume']
    n_atoms_recorded = row['n_atoms']

    try:
        v_vdw, n_atoms_calc = calculate_vdw_volume_from_smiles(smiles)
    except Exception as e:
        logger.error(f"Failed to calculate V_vdW for SMILES {smiles}: {e}")
        return {
            'raw_pc': np.nan,
            'cape': np.nan,
            'sum_vdw': np.nan,
            'n_atoms_calc': np.nan,
            'error': str(e)
        }

    if v_vdw == 0:
        logger.warning(f"Calculated V_vdW is 0 for {smiles}.")
        return {
            'raw_pc': np.nan,
            'cape': np.nan,
            'sum_vdw': 0.0,
            'n_atoms_calc': n_atoms_calc,
            'error': "Zero V_vdW"
        }

    # PC_raw = Unit-cell volume / Sum(V_vdW)
    raw_pc = unit_cell_volume / v_vdw

    # CAPE = PC_raw / (Sum(V_vdW) / N_atoms)
    # Note: Using n_atoms_calc from the SMILES analysis for consistency,
    # or n_atoms_recorded if the task implies using the CIF count.
    # The task says "N_atoms", likely referring to the molecule count.
    # We use the calculated count from the SMILES for accuracy.
    if n_atoms_calc == 0:
        cape = np.nan
    else:
        cape = raw_pc / (v_vdw / n_atoms_calc)

    return {
        'raw_pc': raw_pc,
        'cape': cape,
        'sum_vdw': v_vdw,
        'n_atoms_calc': n_atoms_calc,
        'error': None
    }

def main():
    """
    Main entry point to compute metrics.
    """
    data_dir = get_data_dir()
    input_path = os.path.join(data_dir, 'dataset_intermediate.csv')
    output_path = os.path.join(data_dir, 'dataset_with_metrics.csv')

    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Loading dataset from {input_path}")
    df = pd.read_csv(input_path)

    logger.info(f"Processing {len(df)} records...")
    results = []

    for idx, row in df.iterrows():
        metrics = compute_metrics_for_cif(row)
        results.append(metrics)
        if (idx + 1) % 100 == 0:
            logger.info(f"Processed {idx + 1}/{len(df)} records")

    results_df = pd.DataFrame(results)

    # Merge results back to original dataframe
    # Only keep the relevant metric columns
    final_df = pd.concat([df, results_df], axis=1)

    # Drop the 'error' column if all are None, or keep it for debugging
    if final_df['error'].isna().all():
        final_df = final_df.drop(columns=['error'])

    logger.info(f"Saving results to {output_path}")
    final_df.to_csv(output_path, index=False)

    logger.info("Metrics computation complete.")
    # Log summary statistics
    logger.info(f"Mean Raw PC: {final_df['raw_pc'].mean():.4f}")
    logger.info(f"Mean CAPE: {final_df['cape'].mean():.4f}")

if __name__ == "__main__":
    main()
