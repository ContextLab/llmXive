import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs
from utils.logger import get_logger

logger = get_logger(__name__)

def compute_gasteiger_charges(smiles: str) -> List[float]:
    """
    Compute Gasteiger partial charges.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import rdPartialCharges
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return []
        
        # Compute Gasteiger charges
        rdPartialCharges.ComputeGasteigerCharges(mol)
        charges = []
        for atom in mol.GetAtoms():
            charge = atom.GetDoubleProp('_GasteigerCharge')
            charges.append(charge)
        return charges
    except Exception as e:
        logger.warning(f"Error computing Gasteiger charges for {smiles}: {e}")
        return []

def compute_topological_indices(smiles: str) -> List[float]:
    """
    Compute topological indices (e.g., Wiener index, Zagreb index).
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return []
        
        # Example indices
        indices = [
            Descriptors.WienerIndex(mol),
            Descriptors.ZagrebIndex(mol),
            Descriptors.BertzCT(mol)
        ]
        return indices
    except Exception as e:
        logger.warning(f"Error computing topological indices for {smiles}: {e}")
        return []

def process_single_row(row: Dict) -> Dict:
    """
    Process a single row to add descriptors.
    """
    smiles = row['smiles']
    charges = compute_gasteiger_charges(smiles)
    indices = compute_topological_indices(smiles)
    
    row['gasteiger_charges'] = charges
    row['topological_indices'] = indices
    return row

def compute_descriptors_for_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute descriptors for the entire dataset.
    """
    logger.info("Computing descriptors for dataset")
    # Apply processing
    # Note: In a real scenario, we might use parallel processing
    processed_rows = []
    for idx, row in df.iterrows():
        processed_rows.append(process_single_row(row.to_dict()))
    
    return pd.DataFrame(processed_rows)

def main():
    parser = argparse.ArgumentParser(description="Compute descriptors for SN1 data")
    parser.add_argument("--input", type=str, default="data/processed/cleaned_sn1.csv")
    parser.add_argument("--output", type=str, default="data/processed/cleaned_sn1_descriptors.csv")
    args = parser.parse_args()

    ensure_dirs()
    
    df = pd.read_csv(args.input)
    df_with_desc = compute_descriptors_for_dataset(df)
    
    # Convert lists to strings for CSV
    df_with_desc['gasteiger_charges'] = df_with_desc['gasteiger_charges'].apply(lambda x: ','.join(map(str, x)))
    df_with_desc['topological_indices'] = df_with_desc['topological_indices'].apply(lambda x: ','.join(map(str, x)))
    
    df_with_desc.to_csv(args.output, index=False)
    logger.info(f"Descriptors saved to {args.output}")

if __name__ == "__main__":
    main()
