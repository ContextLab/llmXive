import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib

import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

# Import logging utilities from project root
from logging_config import get_logger, log_event
from config import get_path_processed_data, get_path_validation, ensure_directory

# Configure logger
logger = get_logger("split")

def load_dataset(file_path: str) -> pd.DataFrame:
    """
    Load the dataset from a CSV file.
    
    Args:
        file_path: Path to the input CSV file.
        
    Returns:
        pandas DataFrame containing the dataset.
    """
    logger.info(f"Loading dataset from {file_path}")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df

def get_murcko_scaffold(smiles: str) -> Optional[str]:
    """
    Generate the Bemis-Murcko scaffold for a given SMILES string.
    
    Args:
        smiles: SMILES string of the molecule.
        
    Returns:
        Canonical SMILES of the scaffold, or None if generation fails.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        scaffold = rdMolDescriptors.GetScaffoldForMol(mol)
        # Convert back to canonical SMILES
        scaffold_smiles = Chem.MolToSmiles(scaffold, isomericSmiles=False)
        return scaffold_smiles
    except Exception as e:
        logger.warning(f"Failed to generate scaffold for SMILES '{smiles}': {e}")
        return None

def scaffold_split(
    df: pd.DataFrame,
    smiles_col: str = "smiles",
    train_frac: float = 0.8,
    val_frac: float = 0.1,
    test_frac: float = 0.1,
    seed: int = 42
) -> Tuple[List[int], List[int], List[int]]:
    """
    Perform a scaffold-based split of the dataset.
    
    Groups molecules by their Bemis-Murcko scaffold and assigns
    entire scaffold groups to train, validation, or test sets to
    ensure zero scaffold overlap between splits.
    
    Args:
        df: DataFrame containing the dataset.
        smiles_col: Name of the column containing SMILES strings.
        train_frac: Fraction of data for training.
        val_frac: Fraction of data for validation.
        test_frac: Fraction of data for testing.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_indices, val_indices, test_indices)
    """
    import random
    random.seed(seed)
    
    logger.info(f"Performing scaffold split with seed={seed}")
    
    # Generate scaffolds for all molecules
    logger.info("Generating Bemis-Murcko scaffolds...")
    scaffolds = df[smiles_col].apply(get_murcko_scaffold)
    
    # Handle None scaffolds (malformed molecules)
    valid_mask = scaffolds.notna()
    if not valid_mask.all():
        invalid_count = (~valid_mask).sum()
        logger.warning(f"Skipping {invalid_count} molecules with invalid scaffolds")
    
    # Create a mapping from scaffold to list of indices
    scaffold_to_indices: Dict[str, List[int]] = {}
    for idx, scaffold in scaffolds.items():
        if pd.isna(scaffold):
            continue
        if scaffold not in scaffold_to_indices:
            scaffold_to_indices[scaffold] = []
        scaffold_to_indices[scaffold].append(idx)
    
    logger.info(f"Found {len(scaffold_to_indices)} unique scaffolds")
    
    # Shuffle scaffolds
    scaffold_list = list(scaffold_to_indices.keys())
    random.shuffle(scaffold_list)
    
    # Calculate split sizes
    total_scaffolds = len(scaffold_list)
    train_count = int(total_scaffolds * train_frac)
    val_count = int(total_scaffolds * val_frac)
    test_count = total_scaffolds - train_count - val_count
    
    logger.info(f"Split sizes: train={train_count}, val={val_count}, test={test_count}")
    
    # Assign scaffolds to splits
    train_indices = []
    val_indices = []
    test_indices = []
    
    for i, scaffold in enumerate(scaffold_list):
        indices = scaffold_to_indices[scaffold]
        if i < train_count:
            train_indices.extend(indices)
        elif i < train_count + val_count:
            val_indices.extend(indices)
        else:
            test_indices.extend(indices)
    
    logger.info(f"Split complete: train={len(train_indices)}, val={len(val_indices)}, test={len(test_indices)}")
    
    return train_indices, val_indices, test_indices

def verify_zero_overlap(
    train_indices: List[int],
    val_indices: List[int],
    test_indices: List[int],
    df: pd.DataFrame,
    smiles_col: str = "smiles"
) -> Dict[str, Any]:
    """
    Verify that there is zero scaffold overlap between splits.
    
    Args:
        train_indices: List of training indices.
        val_indices: List of validation indices.
        test_indices: List of test indices.
        df: DataFrame containing the dataset.
        smiles_col: Name of the column containing SMILES strings.
        
    Returns:
        Dictionary with verification results and overlap counts.
    """
    logger.info("Verifying zero scaffold overlap...")
    
    # Generate scaffolds for each split
    def get_scaffolds_for_indices(indices: List[int]) -> set:
        scaffolds = set()
        for idx in indices:
            smiles = df.loc[idx, smiles_col]
            scaffold = get_murcko_scaffold(smiles)
            if scaffold:
                scaffolds.add(scaffold)
        return scaffolds
    
    train_scaffolds = get_scaffolds_for_indices(train_indices)
    val_scaffolds = get_scaffolds_for_indices(val_indices)
    test_scaffolds = get_scaffolds_for_indices(test_indices)
    
    # Check for overlaps
    train_val_overlap = train_scaffolds & val_scaffolds
    train_test_overlap = train_scaffolds & test_scaffolds
    val_test_overlap = val_scaffolds & test_scaffolds
    
    result = {
        "train_scaffold_count": len(train_scaffolds),
        "val_scaffold_count": len(val_scaffolds),
        "test_scaffold_count": len(test_scaffolds),
        "train_val_overlap_count": len(train_val_overlap),
        "train_test_overlap_count": len(train_test_overlap),
        "val_test_overlap_count": len(val_test_overlap),
        "zero_overlap": len(train_val_overlap) == 0 and len(train_test_overlap) == 0 and len(val_test_overlap) == 0,
        "train_val_overlap_scaffolds": list(train_val_overlap),
        "train_test_overlap_scaffolds": list(train_test_overlap),
        "val_test_overlap_scaffolds": list(val_test_overlap)
    }
    
    if result["zero_overlap"]:
        logger.info("SUCCESS: Zero scaffold overlap verified between all splits!")
    else:
        logger.error(f"FAILURE: Scaffold overlap detected! Train-Val: {len(train_val_overlap)}, Train-Test: {len(train_test_overlap)}, Val-Test: {len(val_test_overlap)}")
    
    return result

def save_split_indices(
    train_indices: List[int],
    val_indices: List[int],
    test_indices: List[int],
    output_path: str
) -> None:
    """
    Save the split indices to a JSON file.
    
    Args:
        train_indices: List of training indices.
        val_indices: List of validation indices.
        test_indices: List of test indices.
        output_path: Path to save the JSON file.
    """
    ensure_directory(output_path)
    
    split_data = {
        "train_indices": train_indices,
        "val_indices": val_indices,
        "test_indices": test_indices,
        "train_count": len(train_indices),
        "val_count": len(val_indices),
        "test_count": len(test_indices),
        "total_count": len(train_indices) + len(val_indices) + len(test_indices)
    }
    
    with open(output_path, 'w') as f:
        json.dump(split_data, f, indent=2)
    
    logger.info(f"Saved split indices to {output_path}")

def save_overlap_report(
    overlap_result: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save the scaffold overlap verification report to a JSON file.
    
    Args:
        overlap_result: Dictionary containing overlap verification results.
        output_path: Path to save the JSON file.
    """
    ensure_directory(output_path)
    
    with open(output_path, 'w') as f:
        json.dump(overlap_result, f, indent=2)
    
    logger.info(f"Saved overlap report to {output_path}")

def run_split(
    input_path: str,
    output_split_path: str,
    output_report_path: str,
    smiles_col: str = "smiles",
    train_frac: float = 0.8,
    val_frac: float = 0.1,
    test_frac: float = 0.1,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Main function to perform the scaffold split and verification.
    
    Args:
        input_path: Path to the input dataset CSV.
        output_split_path: Path to save the split indices JSON.
        output_report_path: Path to save the overlap report JSON.
        smiles_col: Name of the column containing SMILES strings.
        train_frac: Fraction of data for training.
        val_frac: Fraction of data for validation.
        test_frac: Fraction of data for testing.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing the split results and verification status.
    """
    # Load dataset
    df = load_dataset(input_path)
    
    # Perform scaffold split
    train_indices, val_indices, test_indices = scaffold_split(
        df, smiles_col, train_frac, val_frac, test_frac, seed
    )
    
    # Save split indices
    save_split_indices(train_indices, val_indices, test_indices, output_split_path)
    
    # Verify zero overlap
    overlap_result = verify_zero_overlap(
        train_indices, val_indices, test_indices, df, smiles_col
    )
    
    # Save overlap report
    save_overlap_report(overlap_result, output_report_path)
    
    return {
        "split_path": output_split_path,
        "report_path": output_report_path,
        "overlap_result": overlap_result,
        "success": overlap_result["zero_overlap"]
    }

def main():
    """Main entry point for the scaffold split script."""
    # Define paths
    input_file = get_path_processed_data("grouped_dataset.csv")
    output_split_file = get_path_processed_data("split_indices.json")
    output_report_file = get_path_validation("scaffold_overlap_report.json")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run T015a (group_rare.py) first to generate the grouped dataset.")
        sys.exit(1)
    
    # Run the split
    logger.info("Starting scaffold-based split...")
    result = run_split(
        input_path=input_file,
        output_split_path=output_split_file,
        output_report_path=output_report_file,
        smiles_col="smiles",
        train_frac=0.8,
        val_frac=0.1,
        test_frac=0.1,
        seed=42
    )
    
    # Log final result
    if result["success"]:
        logger.info(f"SUCCESS: Scaffold split completed with zero overlap.")
        logger.info(f"Split indices saved to: {result['split_path']}")
        logger.info(f"Overlap report saved to: {result['report_path']}")
    else:
        logger.error(f"FAILURE: Scaffold split completed but overlap detected!")
        sys.exit(1)

if __name__ == "__main__":
    main()