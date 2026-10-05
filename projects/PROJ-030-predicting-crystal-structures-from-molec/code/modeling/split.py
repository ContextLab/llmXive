"""
Scaffold-based split implementation for crystal structure prediction.

Performs a Bemis-Murcko scaffold split on the grouped dataset to ensure
zero scaffold overlap between train and test sets.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import pandas as pd
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
import hashlib

# Import path utilities from config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    get_project_root,
    get_path_processed_data,
    ensure_directory,
    get_path_results
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_dataset(input_file: Optional[str] = None) -> pd.DataFrame:
    """
    Load the grouped dataset from the specified file.
    
    Args:
        input_file: Path to the grouped dataset CSV. If None, uses default path.
        
    Returns:
        DataFrame containing the grouped dataset.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if input_file is None:
        input_file = get_path_processed_data("grouped_dataset.csv")
        
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
        
    logger.info(f"Loading dataset from {input_file}")
    df = pd.read_csv(input_file)
    
    required_cols = ['smiles', 'space_group', 'lattice_a', 'lattice_b', 
                    'lattice_c', 'alpha', 'beta', 'gamma']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    logger.info(f"Loaded {len(df)} samples with {len(df['smiles'].unique())} unique SMILES")
    return df

def get_murcko_scaffold(smiles: str) -> Optional[str]:
    """
    Extract the Bemis-Murcko scaffold from a SMILES string.
    
    Args:
        smiles: SMILES string of the molecule.
        
    Returns:
        Canonical SMILES of the scaffold, or None if extraction fails.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
            
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        scaffold_smiles = Chem.MolToSmiles(scaffold, isomericSmiles=False)
        return scaffold_smiles
    except Exception as e:
        logger.warning(f"Failed to extract scaffold from SMILES '{smiles}': {e}")
        return None

def scaffold_split(
    df: pd.DataFrame,
    test_fraction: float = 0.2,
    random_state: int = 42
) -> Tuple[List[int], List[int]]:
    """
    Perform a scaffold-based split ensuring no scaffold overlap between train and test.
    
    Args:
        df: DataFrame with 'smiles' column.
        test_fraction: Fraction of data to allocate to test set.
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_indices, test_indices).
    """
    import numpy as np
    np.random.seed(random_state)
    
    # Extract scaffolds for all molecules
    logger.info("Extracting scaffolds...")
    scaffolds = []
    valid_indices = []
    
    for idx, row in df.iterrows():
        scaffold = get_murcko_scaffold(row['smiles'])
        if scaffold is not None:
            scaffolds.append(scaffold)
            valid_indices.append(idx)
        else:
            logger.warning(f"Skipping row {idx} due to scaffold extraction failure")
    
    if len(valid_indices) == 0:
        raise ValueError("No valid scaffolds found in dataset")
    
    # Group indices by scaffold
    scaffold_to_indices: Dict[str, List[int]] = {}
    for idx, scaffold in zip(valid_indices, scaffolds):
        if scaffold not in scaffold_to_indices:
            scaffold_to_indices[scaffold] = []
        scaffold_to_indices[scaffold].append(idx)
    
    logger.info(f"Found {len(scaffold_to_indices)} unique scaffolds")
    
    # Shuffle scaffolds
    unique_scaffolds = list(scaffold_to_indices.keys())
    np.random.shuffle(unique_scaffolds)
    
    # Allocate scaffolds to train/test
    train_indices = []
    test_indices = []
    
    for scaffold in unique_scaffolds:
        indices = scaffold_to_indices[scaffold]
        # Assign entire scaffold to either train or test
        if np.random.random() < test_fraction:
            test_indices.extend(indices)
        else:
            train_indices.extend(indices)
    
    logger.info(f"Train set: {len(train_indices)} samples")
    logger.info(f"Test set: {len(test_indices)} samples")
    
    return train_indices, test_indices

def verify_zero_overlap(
    train_indices: List[int],
    test_indices: List[int],
    df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Verify that there is zero scaffold overlap between train and test sets.
    
    Args:
        train_indices: List of train set indices.
        test_indices: List of test set indices.
        df: Original DataFrame.
        
    Returns:
        Dictionary with verification results.
    """
    train_scaffolds = set()
    test_scaffolds = set()
    
    for idx in train_indices:
        scaffold = get_murcko_scaffold(df.iloc[idx]['smiles'])
        if scaffold:
            train_scaffolds.add(scaffold)
    
    for idx in test_indices:
        scaffold = get_murcko_scaffold(df.iloc[idx]['smiles'])
        if scaffold:
            test_scaffolds.add(scaffold)
    
    overlap = train_scaffolds & test_scaffolds
    
    return {
        'train_scaffold_count': len(train_scaffolds),
        'test_scaffold_count': len(test_scaffolds),
        'overlap_count': len(overlap),
        'overlap_scaffolds': list(overlap),
        'zero_overlap': len(overlap) == 0
    }

def save_split_indices(
    train_indices: List[int],
    test_indices: List[int],
    output_file: Optional[str] = None
) -> str:
    """
    Save split indices to a JSON file.
    
    Args:
        train_indices: List of train set indices.
        test_indices: List of test set indices.
        output_file: Path to output JSON file. If None, uses default path.
        
    Returns:
        Path to the saved file.
    """
    if output_file is None:
        output_file = get_path_processed_data("split_indices.json")
        
    ensure_directory(output_file)
    
    split_data = {
        'train_indices': train_indices,
        'test_indices': test_indices,
        'train_count': len(train_indices),
        'test_count': len(test_indices)
    }
    
    with open(output_file, 'w') as f:
        json.dump(split_data, f, indent=2)
    
    logger.info(f"Saved split indices to {output_file}")
    return output_file

def save_overlap_report(
    verification_result: Dict[str, Any],
    output_file: Optional[str] = None
) -> str:
    """
    Save scaffold overlap verification report.
    
    Args:
        verification_result: Result from verify_zero_overlap.
        output_file: Path to output JSON file. If None, uses default path.
        
    Returns:
        Path to the saved file.
    """
    if output_file is None:
        output_file = get_path_processed_data("scaffold_overlap_report.json")
        
    ensure_directory(output_file)
    
    with open(output_file, 'w') as f:
        json.dump(verification_result, f, indent=2)
    
    logger.info(f"Saved overlap report to {output_file}")
    return output_file

def run_split(
    input_file: Optional[str] = None,
    output_dir: Optional[str] = None,
    test_fraction: float = 0.2,
    random_state: int = 42
) -> Tuple[List[int], List[int], Dict[str, Any]]:
    """
    Run the complete scaffold split pipeline.
    
    Args:
        input_file: Path to input dataset. If None, uses default path.
        output_dir: Directory for output files. If None, uses default path.
        test_fraction: Fraction of data for test set.
        random_state: Random seed.
        
    Returns:
        Tuple of (train_indices, test_indices, verification_result).
    """
    # Load dataset
    df = load_dataset(input_file)
    
    # Perform scaffold split
    train_indices, test_indices = scaffold_split(
        df, 
        test_fraction=test_fraction,
        random_state=random_state
    )
    
    # Verify zero overlap
    verification_result = verify_zero_overlap(
        train_indices, 
        test_indices, 
        df
    )
    
    if not verification_result['zero_overlap']:
        logger.error(f"SCAFFOLD OVERLAP DETECTED: {verification_result['overlap_count']} overlapping scaffolds")
        raise ValueError(
            f"Scaffold overlap detected: {verification_result['overlap_count']} scaffolds "
            f"appear in both train and test sets. This violates the strict separation requirement."
        )
    
    # Save outputs
    if output_dir is not None:
        ensure_directory(output_dir)
        split_file = os.path.join(output_dir, "split_indices.json")
        report_file = os.path.join(output_dir, "scaffold_overlap_report.json")
    else:
        split_file = None
        report_file = None
        
    save_split_indices(train_indices, test_indices, split_file)
    save_overlap_report(verification_result, report_file)
    
    return train_indices, test_indices, verification_result

def main():
    """Main entry point for the split script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Perform scaffold-based split on crystal structure dataset"
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='Path to input grouped dataset CSV. Default: data/processed/grouped_dataset.csv'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default=None,
        help='Directory for output files. Default: data/processed/'
    )
    parser.add_argument(
        '--test_fraction',
        type=float,
        default=0.2,
        help='Fraction of data for test set (default: 0.2)'
    )
    parser.add_argument(
        '--random_state',
        type=int,
        default=42,
        help='Random seed (default: 42)'
    )
    
    args = parser.parse_args()
    
    try:
        train_indices, test_indices, verification = run_split(
            input_file=args.input,
            output_dir=args.output_dir,
            test_fraction=args.test_fraction,
            random_state=args.random_state
        )
        
        logger.info("=== SPLIT COMPLETE ===")
        logger.info(f"Train samples: {len(train_indices)}")
        logger.info(f"Test samples: {len(test_indices)}")
        logger.info(f"Zero overlap: {verification['zero_overlap']}")
        logger.info(f"Train scaffolds: {verification['train_scaffold_count']}")
        logger.info(f"Test scaffolds: {verification['test_scaffold_count']}")
        
        # Exit with error if overlap detected (should not happen due to check in run_split)
        if not verification['zero_overlap']:
            sys.exit(1)
            
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Split failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()