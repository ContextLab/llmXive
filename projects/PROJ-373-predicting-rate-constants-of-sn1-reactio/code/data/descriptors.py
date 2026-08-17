import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, rdPartialCharges
from rdkit import RDLogger

# Suppress RDKit warnings to keep logs clean, but keep errors
RDLogger.DisableLog('rdApp.*')

from config import DataConfig, ensure_dirs
from utils.logger import get_logger

def compute_gasteiger_charges(mol: Chem.Mol) -> Optional[List[float]]:
    """
    Compute Gasteiger partial charges for a molecule.
    Returns a list of charges (one per atom) or None if computation fails.
    """
    try:
        # Ensure the molecule has hydrogens added for charge calculation
        mol_with_h = Chem.AddHs(mol)
        rdPartialCharges.ComputeGasteigerCharges(mol_with_h)
        
        charges = []
        for atom in mol_with_h.GetAtoms():
            charge = atom.GetDoubleProp('_GasteigerCharge')
            # Handle cases where RDKit returns NaN
            if np.isnan(charge):
                return None
            charges.append(charge)
        
        return charges
    except Exception as e:
        logging.warning(f"Gasteiger charge computation failed: {e}")
        return None

def compute_topological_indices(mol: Chem.Mol) -> Dict[str, float]:
    """
    Compute standard topological indices for a molecule.
    Returns a dictionary of index names to values.
    """
    indices = {}
    try:
        # Molecular weight
        indices['molecular_weight'] = Descriptors.MolWt(mol)
        
        # LogP (XLogP)
        indices['logp'] = Descriptors.MolLogP(mol)
        
        # Topological polar surface area
        indices['tpsa'] = Descriptors.TPSA(mol)
        
        # Number of heavy atoms
        indices['heavy_atom_count'] = mol.GetNumHeavyAtoms()
        
        # Number of rotatable bonds
        indices['num_rotatable_bonds'] = rdMolDescriptors.CalcNumRotatableBonds(mol)
        
        # Number of aromatic rings
        indices['num_aromatic_rings'] = rdMolDescriptors.CalcNumAromaticRings(mol)
        
        # Number of aliphatic rings
        indices['num_aliphatic_rings'] = rdMolDescriptors.CalcNumAliphaticRings(mol)
        
        # Number of H-bond donors
        indices['num_hbd'] = rdMolDescriptors.CalcNumHBD(mol)
        
        # Number of H-bond acceptors
        indices['num_hba'] = rdMolDescriptors.CalcNumHBA(mol)
        
        # Bertz CT (complexity)
        indices['bertz_ct'] = Descriptors.BertzCT(mol)
        
        # Kier alpha shape index (first order)
        indices['kier_alpha'] = Descriptors.KierAlpha1(mol)
        
        return indices
    except Exception as e:
        logging.warning(f"Topological index computation failed: {e}")
        return {}

def process_single_row(row: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Process a single row from the dataset to compute descriptors.
    Returns (descriptor_dict, error_reason).
    If error_reason is not None, the row failed and should be logged.
    """
    smiles = row.get('smiles')
    if not smiles or not isinstance(smiles, str):
        return None, 'invalid_smiles'

    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None, 'rdkit_parse_fail'
        
        # Compute Gasteiger charges
        charges = compute_gasteiger_charges(mol)
        if charges is None:
            return None, 'gasteiger_fail'
        
        # Compute topological indices
        topo_indices = compute_topological_indices(mol)
        if not topo_indices:
            return None, 'topo_indices_fail'
        
        # Combine results
        result = {
            'smiles': smiles,
            'gasteiger_charges': charges,
            'charge_sum': sum(charges),
            'charge_mean': np.mean(charges),
            'charge_std': np.std(charges),
            'charge_max': max(charges),
            'charge_min': min(charges),
            **topo_indices
        }
        
        return result, None
        
    except Exception as e:
        logging.warning(f"Unexpected error processing row {smiles[:20]}...: {e}")
        return None, 'unexpected_error'

def compute_descriptors_for_dataset(input_path: str, output_path: str, exclusion_log_path: str) -> None:
    """
    Main function to compute descriptors for the entire dataset.
    Reads from input_path, writes descriptors to output_path,
    and logs failures to exclusion_log_path.
    """
    logger = get_logger('descriptors')
    logger.info(f"Starting descriptor computation for {input_path}")
    
    # Ensure output directories exist
    ensure_dirs([output_path, exclusion_log_path])
    
    # Load input data
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        raise ValueError(f"Input file missing or invalid: {input_path}")
    
    if df.empty:
        logger.warning("Input dataframe is empty. No descriptors to compute.")
        # Write empty output with headers
        pd.DataFrame(columns=['smiles', 'gasteiger_charges', 'charge_sum', 'charge_mean', 
                              'charge_std', 'charge_max', 'charge_min', 'molecular_weight', 
                              'logp', 'tpsa', 'heavy_atom_count', 'num_rotatable_bonds', 
                              'num_aromatic_rings', 'num_aliphatic_rings', 'num_hbd', 
                              'num_hba', 'bertz_ct', 'kier_alpha']).to_csv(output_path, index=False)
        return
    
    results = []
    failures = []
    
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        result, error = process_single_row(row_dict)
        
        if result is not None:
            results.append(result)
        else:
            failures.append({
                'row_index': idx,
                'smiles': row_dict.get('smiles', 'unknown'),
                'reason': error
            })
            logger.debug(f"Row {idx} failed: {error}")
    
    # Write successful results
    if results:
        result_df = pd.DataFrame(results)
        # Convert charge list to string for CSV storage
        result_df['gasteiger_charges'] = result_df['gasteiger_charges'].apply(lambda x: str(x))
        result_df.to_csv(output_path, index=False)
        logger.info(f"Successfully computed descriptors for {len(results)} rows")
    else:
        logger.warning("No rows succeeded. Output file will be empty.")
        pd.DataFrame(columns=['smiles', 'gasteiger_charges', 'charge_sum', 'charge_mean', 
                              'charge_std', 'charge_max', 'charge_min', 'molecular_weight', 
                              'logp', 'tpsa', 'heavy_atom_count', 'num_rotatable_bonds', 
                              'num_aromatic_rings', 'num_aliphatic_rings', 'num_hbd', 
                              'num_hba', 'bertz_ct', 'kier_alpha']).to_csv(output_path, index=False)
    
    # Write exclusion log
    if failures:
        failure_df = pd.DataFrame(failures)
        failure_df.to_csv(exclusion_log_path, index=False, mode='a', header=not os.path.exists(exclusion_log_path))
        logger.info(f"Logged {len(failures)} failures to {exclusion_log_path}")
    else:
        logger.info("No failures to log.")

def main():
    """CLI entry point for descriptor computation."""
    parser = argparse.ArgumentParser(description="Compute molecular descriptors for SN1 dataset")
    parser.add_argument('--input', type=str, required=True, help="Path to input CSV")
    parser.add_argument('--output', type=str, required=True, help="Path to output descriptors CSV")
    parser.add_argument('--exclusion-log', type=str, required=True, help="Path to exclusion log CSV")
    args = parser.parse_args()
    
    compute_descriptors_for_dataset(args.input, args.output, args.exclusion_log)

if __name__ == '__main__':
    main()
