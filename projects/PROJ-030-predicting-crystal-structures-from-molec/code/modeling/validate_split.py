"""
Module to validate scaffold splits for zero overlap between train and test sets.

This module implements the hard gate for SC-002, ensuring that no Bemis-Murcko
scaffold appears in both the training and test sets. If overlap is detected,
the script exits with code 1.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set, Optional
import pandas as pd
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

# Import project configuration utilities
from config import get_path_processed_data, ensure_directory

# Setup logger
logger = logging.getLogger(__name__)


def load_dataset(dataset_path: str) -> pd.DataFrame:
    """
    Load the dataset from the specified path.

    Args:
        dataset_path: Path to the dataset CSV file.

    Returns:
        pandas DataFrame containing the dataset.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
        ValueError: If the dataset is empty or missing required columns.
    """
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    df = pd.read_csv(path)
    required_columns = ['smiles']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Dataset missing required columns: {missing_columns}")

    if df.empty:
        raise ValueError("Dataset is empty")

    logger.info(f"Loaded dataset with {len(df)} rows from {dataset_path}")
    return df


def get_murcko_scaffold(smiles: str) -> Optional[str]:
    """
    Compute the Bemis-Murcko scaffold for a given SMILES string.

    Args:
        smiles: SMILES string of the molecule.

    Returns:
        Canonical SMILES of the scaffold, or None if parsing fails.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaffold)
    except Exception as e:
        logger.warning(f"Failed to generate scaffold for SMILES '{smiles}': {e}")
        return None


def verify_zero_overlap(
    df: pd.DataFrame,
    split_indices: Dict[str, List[int]],
    tolerance: int = 0
) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify that there is zero scaffold overlap between train and test sets.

    Args:
        df: DataFrame containing the dataset with 'smiles' column.
        split_indices: Dictionary with 'train' and 'test' lists of indices.
        tolerance: Allowed number of overlapping scaffolds (default 0).

    Returns:
        Tuple of (is_valid, report_dict).
        is_valid: True if overlap <= tolerance, False otherwise.
        report_dict: Detailed report of the overlap analysis.
    """
    train_indices = set(split_indices.get('train', []))
    test_indices = set(split_indices.get('test', []))

    # Extract scaffolds for train and test sets
    train_scaffolds: Set[str] = set()
    test_scaffolds: Set[str] = set()
    scaffold_map: Dict[int, str] = {}
    failed_indices: List[int] = []

    for idx in train_indices:
        if idx < len(df):
            smiles = df.iloc[idx]['smiles']
            scaffold = get_murcko_scaffold(smiles)
            if scaffold:
                train_scaffolds.add(scaffold)
                scaffold_map[idx] = scaffold
            else:
                failed_indices.append(idx)

    for idx in test_indices:
        if idx < len(df):
            smiles = df.iloc[idx]['smiles']
            scaffold = get_murcko_scaffold(smiles)
            if scaffold:
                test_scaffolds.add(scaffold)
                scaffold_map[idx] = scaffold
            else:
                failed_indices.append(idx)

    # Find overlapping scaffolds
    overlapping_scaffolds = train_scaffolds.intersection(test_scaffolds)
    overlap_count = len(overlapping_scaffolds)

    # Build report
    report = {
        "train_size": len(train_indices),
        "test_size": len(test_indices),
        "train_scaffold_count": len(train_scaffolds),
        "test_scaffold_count": len(test_scaffolds),
        "overlap_count": overlap_count,
        "overlap_percentage": (overlap_count / len(train_scaffolds) * 100) if train_scaffolds else 0.0,
        "overlapping_scaffolds": list(overlapping_scaffolds)[:50],  # Limit to first 50 for readability
        "failed_scaffold_generation": failed_indices[:50],
        "is_valid": overlap_count <= tolerance,
        "tolerance": tolerance
    }

    logger.info(f"Scaffold overlap analysis: {overlap_count} overlaps found (tolerance: {tolerance})")
    return overlap_count <= tolerance, report


def save_overlap_report(report: Dict[str, Any], output_path: str) -> None:
    """
    Save the overlap report to a JSON file.

    Args:
        report: The overlap report dictionary.
        output_path: Path to save the JSON file.
    """
    path = Path(output_path)
    ensure_directory(path.parent)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Saved overlap report to {output_path}")


def run_validation(
    dataset_path: Optional[str] = None,
    split_indices_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> bool:
    """
    Run the full validation pipeline.

    Args:
        dataset_path: Path to the dataset CSV file. Defaults to 'grouped_dataset.csv'.
        split_indices_path: Path to the split indices JSON file. Defaults to 'split_indices.json'.
        output_path: Path to save the overlap report. Defaults to 'scaffold_overlap_report.json'.

    Returns:
        True if validation passes, False otherwise.
    """
    # Use default paths if not provided
    if dataset_path is None:
        dataset_path = str(get_path_processed_data("grouped_dataset.csv"))
    if split_indices_path is None:
        split_indices_path = str(get_path_processed_data("split_indices.json"))
    if output_path is None:
        output_path = str(get_path_processed_data("scaffold_overlap_report.json"))

    logger.info(f"Starting scaffold overlap validation")
    logger.info(f"Dataset path: {dataset_path}")
    logger.info(f"Split indices path: {split_indices_path}")
    logger.info(f"Output path: {output_path}")

    # Load dataset
    try:
        df = load_dataset(dataset_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load dataset: {e}")
        return False

    # Load split indices
    try:
        with open(split_indices_path, 'r', encoding='utf-8') as f:
            split_indices = json.load(f)
    except FileNotFoundError:
        logger.error(f"Split indices file not found: {split_indices_path}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in split indices file: {e}")
        return False

    # Verify zero overlap
    is_valid, report = verify_zero_overlap(df, split_indices)

    # Save report
    save_overlap_report(report, output_path)

    if not is_valid:
        logger.error(f"VALIDATION FAILED: {report['overlap_count']} scaffold overlaps detected!")
        logger.error("This violates SC-002 (zero scaffold overlap). Exiting with code 1.")
        return False

    logger.info("VALIDATION PASSED: Zero scaffold overlap confirmed.")
    return True


def main() -> None:
    """
    Main entry point for the script.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate scaffold split for zero overlap between train and test sets."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Path to the dataset CSV file. Defaults to 'grouped_dataset.csv'."
    )
    parser.add_argument(
        "--split",
        type=str,
        default=None,
        help="Path to the split indices JSON file. Defaults to 'split_indices.json'."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save the overlap report. Defaults to 'scaffold_overlap_report.json'."
    )
    parser.add_argument(
        "--tolerance",
        type=int,
        default=0,
        help="Allowed number of overlapping scaffolds (default 0)."
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    is_valid = run_validation(
        dataset_path=args.dataset,
        split_indices_path=args.split,
        output_path=args.output
    )

    if not is_valid:
        logger.error("Exiting with code 1 due to scaffold overlap.")
        sys.exit(1)
    else:
        logger.info("Validation completed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    import sys
    main()
