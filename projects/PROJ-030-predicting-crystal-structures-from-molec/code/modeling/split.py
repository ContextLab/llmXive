"""
Scaffold Splitting for Crystal Structure Dataset.
Ensures zero scaffold overlap between train and test sets.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_path_processed_data, ensure_directory
from logging_config import setup_logging, get_logger
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

setup_logging(level=logging.INFO)
logger = get_logger("split")

def get_murcko_scaffold(smiles: str) -> Optional[str]:
    """
    Extracts the Bemis-Murcko scaffold from a SMILES string.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    scaffold = MurckoScaffold.GetScaffoldForMol(mol)
    return Chem.MolToSmiles(scaffold)

def load_dataset(input_file: str) -> Any:
    """
    Loads the dataset from a Parquet or CSV file.
    """
    import pandas as pd
    if input_file.endswith('.parquet'):
        return pd.read_parquet(input_file)
    else:
        return pd.read_csv(input_file)

def scaffold_split(df: Any, smiles_col: str = "smiles", test_size: float = 0.2) -> Tuple[List[int], List[int]]:
    """
    Performs a scaffold split.
    Returns indices for train and test sets.
    """
    # Group by scaffold
    df['scaffold'] = df[smiles_col].apply(get_murcko_scaffold)
    
    # Drop rows with None scaffold
    df_clean = df.dropna(subset=['scaffold'])
    
    scaffolds = df_clean['scaffold'].unique()
    n_test_scaffolds = int(len(scaffolds) * test_size)
    
    # Randomly select test scaffolds
    import random
    random.seed(42)
    test_scaffolds = random.sample(list(scaffolds), n_test_scaffolds)
    
    train_indices = df_clean[df_clean['scaffold'].isin(test_scaffolds) == False].index.tolist()
    test_indices = df_clean[df_clean['scaffold'].isin(test_scaffolds)].index.tolist()
    
    return train_indices, test_indices

def verify_zero_overlap(train_indices: List[int], test_indices: List[int], df: Any, smiles_col: str = "smiles") -> bool:
    """
    Verifies that there is no scaffold overlap between train and test sets.
    """
    train_scaffolds = set(df.iloc[train_indices]['scaffold'].unique())
    test_scaffolds = set(df.iloc[test_indices]['scaffold'].unique())
    
    overlap = train_scaffolds.intersection(test_scaffolds)
    if overlap:
        logger.error(f"Scaffold overlap detected: {overlap}")
        return False
    return True

def save_split_indices(train_indices: List[int], test_indices: List[int], output_file: str) -> None:
    """
    Saves the split indices to a JSON file.
    """
    data = {
        "train": train_indices,
        "test": test_indices
    }
    with open(output_file, 'w') as f:
        json.dump(data, f)
    logger.info(f"Saved split indices to {output_file}")

def run_split(input_file: str, output_dir: str) -> None:
    """
    Runs the splitting pipeline.
    """
    df = load_dataset(input_file)
    train_indices, test_indices = scaffold_split(df)
    
    # Verify overlap
    if not verify_zero_overlap(train_indices, test_indices, df):
        raise RuntimeError("Scaffold overlap detected. Split failed.")
    
    ensure_directory(output_dir)
    output_file = os.path.join(output_dir, "split_indices.json")
    save_split_indices(train_indices, test_indices, output_file)

def main():
    parser = argparse.ArgumentParser(description="Scaffold Split")
    parser.add_argument("--input", type=str, required=True, help="Input dataset file.")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory for split indices.")
    args = parser.parse_args()

    run_split(args.input, args.output_dir)

if __name__ == "__main__":
    main()