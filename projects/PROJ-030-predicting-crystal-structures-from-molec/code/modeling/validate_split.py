"""
Validate scaffold split to ensure zero overlap between train and test sets.

This script verifies that the Bemis-Murcko scaffolds used for splitting
the dataset result in truly distinct chemical space between training
and testing sets, preventing data leakage.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set

import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

# Import from project modules
from config import get_path_processed_data, get_path_validation, ensure_directory
from logging_config import get_logger, log_event

# Configure logger
logger = get_logger(__name__)


def load_dataset(path: str) -> pd.DataFrame:
    """Load the grouped dataset."""
    logger.info(f"Loading dataset from {path}")
    df = pd.read_csv(path)
    if 'smiles' not in df.columns:
        raise ValueError(f"Dataset must contain 'smiles' column. Found: {df.columns.tolist()}")
    return df


def get_murcko_scaffold(smiles: str) -> str:
    """
    Generate the Bemis-Murcko scaffold for a given SMILES string.

    Returns the scaffold as a canonical SMILES string, or None if parsing fails.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Get the Bemis-Murcko scaffold
        scaffold = rdMolDescriptors.GetScaffoldForMol(mol)
        
        if scaffold is None:
            return None
        
        # Convert back to canonical SMILES
        scaffold_smiles = Chem.MolToSmiles(scaffold, isomericSmiles=True)
        return scaffold_smiles
    except Exception as e:
        logger.warning(f"Failed to generate scaffold for SMILES '{smiles[:50]}...': {e}")
        return None


def verify_zero_overlap(
    train_scaffolds: Set[str],
    test_scaffolds: Set[str]
) -> Tuple[bool, List[str], int, int]:
    """
    Verify that there is no scaffold overlap between train and test sets.

    Returns:
        Tuple of (is_valid, overlapping_scaffolds, train_count, test_count)
    """
    overlap = train_scaffolds.intersection(test_scaffolds)
    is_valid = len(overlap) == 0
    
    logger.info(f"Train scaffolds: {len(train_scaffolds)}")
    logger.info(f"Test scaffolds: {len(test_scaffolds)}")
    logger.info(f"Overlapping scaffolds: {len(overlap)}")
    
    return is_valid, list(overlap), len(train_scaffolds), len(test_scaffolds)


def save_overlap_report(
    report: Dict[str, Any],
    output_path: str
) -> None:
    """Save the scaffold overlap report to a JSON file."""
    ensure_directory(output_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved overlap report to {output_path}")


def run_validation(
    dataset_path: str,
    split_indices_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Run the scaffold overlap validation.

    Args:
        dataset_path: Path to the grouped dataset CSV
        split_indices_path: Path to the split indices JSON
        output_path: Path for the output report JSON

    Returns:
        Dictionary containing the validation results
    """
    logger.info("Starting scaffold overlap validation")
    
    # Load dataset
    df = load_dataset(dataset_path)
    
    # Load split indices
    with open(split_indices_path, 'r', encoding='utf-8') as f:
        split_indices = json.load(f)
    
    train_indices = set(split_indices['train'])
    test_indices = set(split_indices['test'])
    
    logger.info(f"Train set size: {len(train_indices)}")
    logger.info(f"Test set size: {len(test_indices)}")
    
    # Extract scaffolds for train and test sets
    train_scaffolds: Set[str] = set()
    test_scaffolds: Set[str] = set()
    failed_molecules: List[Dict[str, Any]] = []
    
    for idx, row in df.iterrows():
        smiles = row['smiles']
        scaffold = get_murcko_scaffold(smiles)
        
        if scaffold is None:
            failed_molecules.append({
                'index': idx,
                'smiles': smiles,
                'reason': 'Failed to parse or generate scaffold'
            })
            continue
        
        if idx in train_indices:
            train_scaffolds.add(scaffold)
        elif idx in test_indices:
            test_scaffolds.add(scaffold)
    
    # Verify zero overlap
    is_valid, overlapping_scaffolds, train_count, test_count = verify_zero_overlap(
        train_scaffolds, test_scaffolds
    )
    
    # Build report
    report = {
        'validation_status': 'PASS' if is_valid else 'FAIL',
        'is_zero_overlap': is_valid,
        'train_scaffold_count': train_count,
        'test_scaffold_count': test_count,
        'overlapping_scaffold_count': len(overlapping_scaffolds),
        'overlapping_scaffolds': overlapping_scaffolds[:10],  # Limit to first 10 if any
        'total_train_samples': len(train_indices),
        'total_test_samples': len(test_indices),
        'failed_molecule_count': len(failed_molecules),
        'failed_molecules_sample': failed_molecules[:5],  # Sample of failures
        'message': (
            'Zero scaffold overlap confirmed' if is_valid 
            else f'Found {len(overlapping_scaffolds)} overlapping scaffolds'
        )
    }
    
    # Save report
    save_overlap_report(report, output_path)
    
    log_event(
        logger,
        'scaffold_validation_complete',
        {
            'status': report['validation_status'],
            'overlap_count': report['overlapping_scaffold_count']
        }
    )
    
    return report


def main() -> int:
    """Main entry point for the validation script."""
    logger.info("Starting scaffold split validation")
    
    # Define paths
    dataset_path = get_path_processed_data("grouped_dataset.csv")
    split_indices_path = get_path_processed_data("split_indices.json")
    output_path = get_path_validation("scaffold_overlap_report.json")
    
    # Run validation
    try:
        report = run_validation(dataset_path, split_indices_path, output_path)
        
        if report['is_zero_overlap']:
            logger.info("Validation PASSED: Zero scaffold overlap confirmed")
            return 0
        else:
            logger.error(
                f"Validation FAILED: Found {report['overlapping_scaffold_count']} "
                "overlapping scaffolds"
            )
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Validation failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
