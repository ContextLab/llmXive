import os
import sys
import argparse
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs, DataConfig
from utils.logger import get_logger

logger = get_logger(__name__)

def compute_gasteiger_charges(smiles: str):
    """Compute Gasteiger partial charges using RDKit."""
    try:
        from rdkit import Chem
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None, "invalid_smiles"
        
        # Initialize charges
        Chem.ComputeGasteigerCharges(mol)
        
        charges = []
        for atom in mol.GetAtoms():
            try:
                charge = atom.GetDoubleProp('_GasteigerCharge')
                # Handle NaN/None gracefully
                if charge != charge:  # NaN check
                    charges.append(0.0)
                else:
                    charges.append(charge)
            except Exception:
                charges.append(0.0)
        
        return charges, None
    except Exception as e:
        logger.warning(f"Failed to compute Gasteiger charges for {smiles}: {e}")
        return None, "gasteiger_error"

def compute_topological_indices(smiles: str):
    """Compute topological indices using RDKit."""
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None, "invalid_smiles"
        
        # Compute some topological indices
        indices = {
            'mol_wt': Descriptors.MolWt(mol),
            'logp': Descriptors.MolLogP(mol),
            'num_h_donors': Descriptors.NumHDonors(mol),
            'num_h_acceptors': Descriptors.NumHAcceptors(mol),
            'num_rotatable_bonds': Descriptors.NumRotatableBonds(mol),
            'tpsa': Descriptors.TPSA(mol),
        }
        
        return indices, None
    except Exception as e:
        logger.warning(f"Failed to compute topological indices for {smiles}: {e}")
        return None, "topological_error"

def process_single_row(row: Dict[str, Any]):
    """Process a single row and compute descriptors."""
    smiles = row.get('smiles', '')
    if not smiles:
        return None, "missing_smiles"
    
    # Compute Gasteiger charges
    charges, error = compute_gasteiger_charges(smiles)
    if error:
        return None, error
    
    # Compute topological indices
    indices, error = compute_topological_indices(smiles)
    if error:
        return None, error
    
    # Combine results
    result = {
        'smiles': smiles,
        'gasteiger_charges': charges,
        **indices
    }
    
    return result, None

def ensure_exclusion_log_header(exclusion_log_path: str):
    """Ensure the exclusion log has the correct header."""
    if not os.path.exists(exclusion_log_path):
        with open(exclusion_log_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['row_index', 'reason', 'original_smiles'])

def append_to_exclusion_log(exclusion_log_path: str, row_index: int, reason: str, smiles: str):
    """Append a single exclusion entry to the log."""
    ensure_exclusion_log_header(exclusion_log_path)
    with open(exclusion_log_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([row_index, reason, smiles])

def compute_descriptors_for_dataset(input_path: str, output_path: str, exclusion_log_path: str):
    """Compute descriptors for entire dataset."""
    import pandas as pd
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    results = []
    
    # Ensure exclusion log header exists before processing
    ensure_exclusion_log_header(exclusion_log_path)
    
    for idx, row in df.iterrows():
        result, error = process_single_row(row.to_dict())
        if error:
            # Append directly to exclusion log
            append_to_exclusion_log(
                exclusion_log_path, 
                idx, 
                error, 
                row.get('smiles', '')
            )
            logger.warning(f"Row {idx} failed: {error}")
        else:
            results.append(result)
    
    # Save results
    if results:
        result_df = pd.DataFrame(results)
        result_df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(results)} rows to {output_path}")
    else:
        logger.warning("No valid results to save.")

def main():
    parser = argparse.ArgumentParser(description="Compute molecular descriptors")
    parser.add_argument("--input", type=str, default="data/processed/cleaned_intermediate.csv", help="Input file path")
    parser.add_argument("--output", type=str, default="data/processed/descriptors.csv", help="Output file path")
    parser.add_argument("--exclusion-log", type=str, default="data/processed/exclusion_raw.log", help="Exclusion log path")
    args = parser.parse_args()

    ensure_dirs()
    
    try:
        compute_descriptors_for_dataset(args.input, args.output, args.exclusion_log)
        logger.info("Descriptor computation completed successfully")
    except Exception as e:
        logger.error(f"Descriptor computation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()