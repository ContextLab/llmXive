"""
Descriptor computation for SN1 rate constant prediction.
Computes Gasteiger partial charges and topological indices using RDKit.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, rdPartialCharges
from rdkit import RDLogger

# Suppress RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

# Import logging setup from utils
from utils.logger import setup_logging, get_logger

def compute_gasteiger_charges(mol: Chem.Mol) -> Tuple[Optional[float], Optional[float]]:
    """
    Compute max and mean absolute Gasteiger partial charges for a molecule.
    
    Args:
        mol: RDKit Mol object.
        
    Returns:
        Tuple of (max_abs_charge, mean_abs_charge) or (None, None) on failure.
    """
    try:
        # Create a copy to avoid modifying the original
        mol_copy = Chem.Mol(mol)
        
        # Add hydrogens
        mol_copy = Chem.AddHs(mol_copy)
        
        # Compute Gasteiger charges
        # This may fail for some molecules, so we wrap in try/except
        rdPartialCharges.ComputeGasteigerCharges(mol_copy)
        
        charges = []
        for atom in mol_copy.GetAtoms():
            charge_str = atom.GetProp('_GasteigerCharge')
            try:
                charge = float(charge_str)
                charges.append(abs(charge))
            except ValueError:
                continue
        
        if not charges:
            return None, None
        
        max_charge = max(charges)
        mean_charge = sum(charges) / len(charges)
        
        return max_charge, mean_charge
    except Exception as e:
        # Log the error but don't crash
        logging.warning(f"Gasteiger charge computation failed: {e}")
        return None, None

def compute_topological_indices(mol: Chem.Mol) -> Dict[str, float]:
    """
    Compute topological indices for a molecule.
    
    Args:
        mol: RDKit Mol object.
        
    Returns:
        Dictionary of topological indices.
    """
    indices = {}
    
    try:
        # Wiener index
        try:
            indices['wiener_index'] = Descriptors.WienerIndex(mol)
        except Exception:
            indices['wiener_index'] = None
        
        # Balaban J index
        try:
            indices['balaban_j'] = Descriptors.BalabanJ(mol)
        except Exception:
            indices['balaban_j'] = None
        
        # Number of rotatable bonds
        indices['num_rotatable_bonds'] = rdMolDescriptors.CalcNumRotatableBonds(mol)
        
        # Number of rings
        indices['num_rings'] = rdMolDescriptors.CalcNumRings(mol)
        
        # Molecular weight
        indices['molecular_weight'] = Descriptors.MolWt(mol)
        
        # LogP (Crippen)
        try:
            indices['logp'] = Descriptors.MolLogP(mol)
        except Exception:
            indices['logp'] = None
        
        # Topological polar surface area
        try:
            indices['tpsa'] = Descriptors.TPSA(mol)
        except Exception:
            indices['tpsa'] = None
        
        # Number of heavy atoms
        indices['num_heavy_atoms'] = mol.GetNumHeavyAtoms()
        
        # Number of aromatic rings
        indices['num_aromatic_rings'] = rdMolDescriptors.CalcNumAromaticRings(mol)
        
    except Exception as e:
        logging.warning(f"Topological index computation failed: {e}")
    
    return indices

def process_single_row(row: pd.Series, row_index: int, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """
    Process a single row from the dataset.
    
    Args:
        row: Pandas Series containing SMILES and other data.
        row_index: Index of the row for logging.
        logger: Logger instance.
        
    Returns:
        Dictionary with computed descriptors or None on failure.
    """
    smiles = row.get('smiles', '')
    
    if not smiles or pd.isna(smiles):
        logger.error(f"Row {row_index}: Empty or missing SMILES")
        return None
    
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.error(f"Row {row_index}: Invalid SMILES - {smiles}")
            return None
        
        # Compute Gasteiger charges
        max_charge, mean_charge = compute_gasteiger_charges(mol)
        
        if max_charge is None or mean_charge is None:
            logger.warning(f"Row {row_index}: Gasteiger charge computation failed - {smiles}")
            return None
        
        # Compute topological indices
        topological_indices = compute_topological_indices(mol)
        
        result = {
            'row_index': row_index,
            'smiles': smiles,
            'gasteiger_max_charge': max_charge,
            'gasteiger_mean_charge': mean_charge,
        }
        
        # Add topological indices
        for key, value in topological_indices.items():
            result[f'topo_{key}'] = value
        
        return result
        
    except Exception as e:
        logger.error(f"Row {row_index}: Exception processing SMILES - {smiles}: {e}")
        return None

def compute_descriptors_for_dataset(
    input_path: str,
    output_log_path: str,
    output_csv_path: Optional[str] = None
) -> None:
    """
    Compute descriptors for the entire dataset.
    
    Args:
        input_path: Path to input CSV file.
        output_log_path: Path to write descriptor log file.
        output_csv_path: Optional path to write processed CSV file.
    """
    logger = get_logger('descriptors')
    logger.info(f"Loading data from {input_path}")
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        raise
    
    logger.info(f"Loaded {len(df)} rows")
    
    results = []
    excluded_count = 0
    
    for idx, row in df.iterrows():
        result = process_single_row(row, idx, logger)
        if result is not None:
            results.append(result)
        else:
            excluded_count += 1
    
    logger.info(f"Processed {len(results)} rows, excluded {excluded_count} rows")
    
    # Write descriptor log
    log_dir = Path(output_log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_log_path, 'w') as f:
        f.write("# Descriptor Computation Log\n")
        f.write(f"# Total rows processed: {len(df)}\n")
        f.write(f"# Successful: {len(results)}\n")
        f.write(f"# Excluded: {excluded_count}\n")
        f.write("#\n")
        f.write("# Format: row_index, smiles, status, message\n")
        
        for idx, row in df.iterrows():
            smiles = row.get('smiles', '')
            # Find if this row was successful
            successful_row = next((r for r in results if r['row_index'] == idx), None)
            if successful_row:
                f.write(f"{idx},{smiles},SUCCESS,Descriptor computation completed\n")
            else:
                f.write(f"{idx},{smiles},FAILED,Descriptor computation failed\n")
    
    logger.info(f"Descriptor log written to {output_log_path}")
    
    # Optionally write CSV with descriptors
    if output_csv_path and results:
        results_df = pd.DataFrame(results)
        results_csv_dir = Path(output_csv_path).parent
        results_csv_dir.mkdir(parents=True, exist_ok=True)
        results_df.to_csv(output_csv_path, index=False)
        logger.info(f"Descriptor CSV written to {output_csv_path}")

def main():
    """Main entry point for descriptor computation."""
    parser = argparse.ArgumentParser(description="Compute molecular descriptors")
    parser.add_argument("--input", required=True, help="Input CSV file path")
    parser.add_argument("--output", required=True, help="Output log file path")
    parser.add_argument("--csv-output", help="Optional output CSV file path")
    
    args = parser.parse_args()
    
    setup_logging()
    
    compute_descriptors_for_dataset(
        input_path=args.input,
        output_log_path=args.output,
        output_csv_path=args.csv_output
    )

if __name__ == "__main__":
    main()