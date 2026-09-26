import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pickle
import pandas as pd

# RDKit import
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors
except ImportError:
    raise ImportError("RDKit is required. Install via: pip install rdkit-pypi")

# Ensure imports work relative to project root
if __name__ == '__main__' and 'code' not in sys.path[0]:
    sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

def setup_logging(log_file: Optional[str] = None):
    """Configures logging to file and console."""
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def get_atom_features(mol) -> List[Dict[str, Any]]:
    """Extracts atom features for a molecule."""
    features = []
    for atom in mol.GetAtoms():
        feat = {
            "atomic_num": atom.GetAtomicNum(),
            "hybridization": str(atom.GetHybridization()),
            "formal_charge": atom.GetFormalCharge(),
            "num_hs": atom.GetTotalNumHs(),
            "is_aromatic": atom.GetIsAromatic()
        }
        features.append(feat)
    return features

def get_bond_features(mol) -> List[Dict[str, Any]]:
    """Extracts bond features for a molecule."""
    features = []
    for bond in mol.GetBonds():
        feat = {
            "bond_type": str(bond.GetBondType()),
            "is_conjugated": bond.GetIsConjugated(),
            "is_in_ring": bond.IsInRing()
        }
        features.append(feat)
    return features

def process_molecule(smiles: str, logS: float) -> Optional[Dict[str, Any]]:
    """
    Processes a single molecule. Returns None if SMILES is invalid.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Basic validation
        Chem.SanitizeMol(mol)
        
        return {
            "smiles": smiles,
            "logS": logS,
            "atoms": get_atom_features(mol),
            "bonds": get_bond_features(mol)
        }
    except Exception as e:
        logger.warning(f"Failed to process molecule {smiles}: {e}")
        return None

def load_and_preprocess(input_csv: str, output_dir: str) -> Tuple[List[Dict], int, int]:
    """
    Loads raw CSV, parses SMILES, excludes invalid entries, and saves cleaned data.
    Returns (cleaned_data, total_count, excluded_count).
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    log_file = output_path / "exclusions.log"
    setup_logging(str(log_file))

    df = pd.read_csv(input_csv)
    total_count = len(df)
    cleaned_data = []
    excluded_count = 0

    logger.info(f"Processing {total_count} molecules from {input_csv}")

    for idx, row in df.iterrows():
        smiles = row['smiles']
        logS = row['logS']
        
        # Check for NaN logS
        if pd.isna(logS):
            excluded_count += 1
            logger.warning(f"Row {idx}: NaN logS excluded.")
            continue
        
        processed = process_molecule(smiles, logS)
        if processed is None:
            excluded_count += 1
            logger.warning(f"Row {idx}: Invalid SMILES '{smiles}' excluded.")
        else:
            cleaned_data.append(processed)

    if len(cleaned_data) == 0:
        raise ValueError("CRITICAL: No valid molecules found after preprocessing. Aborting.")

    # Save cleaned data
    pkl_path = output_path / "cleaned_graphs.pkl"
    with open(pkl_path, 'wb') as f:
        pickle.dump(cleaned_data, f)
    
    logger.info(f"Preprocessing complete. Saved {len(cleaned_data)} molecules to {pkl_path}")
    logger.info(f"Excluded {excluded_count} invalid entries. Log saved to {log_file}")

    return cleaned_data, total_count, excluded_count

def main():
    """Main entry point for preprocessing."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="Path to raw CSV")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    args = parser.parse_args()

    load_and_preprocess(args.input, args.output)

if __name__ == "__main__":
    main()