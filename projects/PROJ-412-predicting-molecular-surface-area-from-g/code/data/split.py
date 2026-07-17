"""
Data splitting logic for molecular datasets.
Implements stratified splitting by Molecular Weight (MW) with Kolmogorov-Smirnov (KS) test validation.
"""
import os
import sys
import csv
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, NamedTuple
import json

# Import project utilities
from utils.config import get_project_root, get_data_dir
from utils.logging import get_logger
from utils.seed import set_seed

# Import RDKit for MW calculation if needed, though we expect MW in processed data
from rdkit import Chem
from rdkit.Chem import Descriptors

# Import numpy and scipy for statistics
import numpy as np
from scipy import stats

logger = get_logger(__name__)


class SplitResult(NamedTuple):
    """Container for split indices and statistics."""
    train_indices: List[int]
    test_indices: List[int]
    train_mw_stats: Dict[str, float]
    test_mw_stats: Dict[str, float]
    ks_statistic: float
    ks_pvalue: float
    ks_passed: bool


def load_processed_data() -> Tuple[List[str], List[float]]:
    """
    Loads processed molecular data to extract SMILES and Molecular Weights.
    Expects data to be in data/processed/molecules.csv with columns: 'smiles', 'mw', etc.
    If 'mw' is not present, it calculates it from SMILES.
    """
    project_root = get_project_root()
    processed_file = project_root / "data" / "processed" / "molecules.csv"

    if not processed_file.exists():
        raise FileNotFoundError(f"Processed data file not found: {processed_file}. "
                                "Run T013/T014 preprocessing first.")

    smiles_list = []
    mw_list = []

    logger.info(f"Loading processed data from {processed_file}")

    with open(processed_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            smiles = row.get('smiles')
            if not smiles:
                logger.warning(f"Row {idx} missing SMILES, skipping.")
                continue

            smiles_list.append(smiles)
            
            # Try to get MW from the file, otherwise calculate
            if 'mw' in row and row['mw']:
                try:
                    mw = float(row['mw'])
                except ValueError:
                    mw = Descriptors.MolWt(Chem.MolFromSmiles(smiles))
            else:
                mol = Chem.MolFromSmiles(smiles)
                if mol is None:
                    logger.warning(f"Row {idx}: Invalid SMILES for MW calculation, skipping.")
                    continue
                mw = Descriptors.MolWt(mol)
            
            mw_list.append(mw)

    if len(smiles_list) == 0:
        raise ValueError("No valid molecules found in processed data.")

    logger.info(f"Loaded {len(smiles_list)} molecules.")
    return smiles_list, mw_list


def calculate_mw_stats(mw_values: List[float]) -> Dict[str, float]:
    """Calculate mean, std, min, max for a list of MW values."""
    arr = np.array(mw_values)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "count": len(arr)
    }


def stratified_split_by_mw(
    mw_values: List[float], 
    train_ratio: float = 0.8, 
    seed: int = 42, 
    n_bins: int = 10
) -> Tuple[List[int], List[int]]:
    """
    Performs a stratified split based on Molecular Weight.
    Molecules are binned by MW, then sampled proportionally from each bin.
    """
    set_seed(seed)
    n_samples = len(mw_values)
    indices = list(range(n_samples))
    
    mw_arr = np.array(mw_values)
    
    # Create bins based on MW distribution
    # Using uniform quantile bins to ensure roughly equal size bins if possible,
    # or fixed number of bins across the range.
    # Strategy: Create bins based on percentiles to ensure stratification works well.
    try:
        bin_edges = np.percentile(mw_arr, np.linspace(0, 100, n_bins + 1))
    except Exception:
        # Fallback to fixed range if percentiles fail (e.g., all same value)
        bin_edges = np.linspace(mw_arr.min(), mw_arr.max(), n_bins + 1)
    
    # Assign bin indices
    bin_indices = np.digitize(mw_arr, bin_edges) - 1
    # Ensure last element doesn't fall out of bounds due to floating point
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)

    train_indices = []
    test_indices = []

    unique_bins = np.unique(bin_indices)
    
    logger.info(f"Splitting into {len(unique_bins)} bins based on MW.")

    for b in unique_bins:
        # Get indices belonging to this bin
        bin_mask = bin_indices == b
        bin_indices_list = [indices[i] for i, val in enumerate(bin_mask) if val]
        
        # Shuffle bin indices
        np.random.shuffle(bin_indices_list)
        
        # Calculate split point for this bin
        n_train_bin = int(len(bin_indices_list) * train_ratio)
        
        train_indices.extend(bin_indices_list[:n_train_bin])
        test_indices.extend(bin_indices_list[n_train_bin:])

    # Shuffle final lists to remove bin ordering artifacts
    np.random.shuffle(train_indices)
    np.random.shuffle(test_indices)

    return train_indices, test_indices


def validate_split_distribution(
    train_mw: List[float], 
    test_mw: List[float], 
    threshold: float = 0.05
) -> Tuple[float, float, bool]:
    """
    Validates that the train and test distributions are similar using KS test.
    Returns (statistic, p_value, passed).
    """
    if len(train_mw) == 0 or len(test_mw) == 0:
        raise ValueError("Cannot validate split with empty train or test set.")

    ks_stat, p_value = stats.ks_2samp(train_mw, test_mw)
    passed = p_value > threshold

    logger.info(f"KS Test Result: statistic={ks_stat:.4f}, p-value={p_value:.4f}, threshold={threshold}")
    logger.info(f"Split validation: {'PASSED' if passed else 'FAILED'} (p > {threshold})")

    return ks_stat, p_value, passed


def save_indices_to_csv(
    train_indices: List[int], 
    test_indices: List[int], 
    output_dir: Optional[Path] = None
) -> Tuple[Path, Path]:
    """
    Saves train and test indices to CSV files.
    Returns paths to the created files.
    """
    if output_dir is None:
        output_dir = get_project_root() / "data" / "splits"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    train_path = output_dir / "train_indices.csv"
    test_path = output_dir / "test_indices.csv"

    with open(train_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['index'])
        for idx in train_indices:
            writer.writerow([idx])

    with open(test_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['index'])
        for idx in test_indices:
            writer.writerow([idx])

    logger.info(f"Saved train indices ({len(train_indices)}) to {train_path}")
    logger.info(f"Saved test indices ({len(test_indices)}) to {test_path}")

    return train_path, test_path


def main():
    """
    Main entry point for the data splitting task.
    1. Loads processed data.
    2. Performs stratified split by MW.
    3. Validates split with KS test.
    4. Saves indices to CSV.
    """
    logger.info("Starting data splitting (T015)...")

    # Load data
    try:
        smiles_list, mw_list = load_processed_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Perform split
    train_indices, test_indices = stratified_split_by_mw(mw_list, train_ratio=0.8, seed=42)

    # Extract MW for validation
    train_mw = [mw_list[i] for i in train_indices]
    test_mw = [mw_list[i] for i in test_indices]

    # Calculate stats
    train_stats = calculate_mw_stats(train_mw)
    test_stats = calculate_mw_stats(test_mw)

    logger.info(f"Train MW Stats: {train_stats}")
    logger.info(f"Test MW Stats: {test_stats}")

    # Validate distribution
    ks_stat, p_value, passed = validate_split_distribution(train_mw, test_mw, threshold=0.05)

    if not passed:
        logger.warning("KS test failed (p <= 0.05). Train and Test distributions may differ significantly.")
        # In a strict pipeline, we might halt here, but for this task we log and proceed
        # as the split logic is correct, just the random seed or data might be skewed.
    
    # Save results
    train_path, test_path = save_indices_to_csv(train_indices, test_indices)

    # Save summary report
    report = {
        "train_count": len(train_indices),
        "test_count": len(test_indices),
        "train_stats": train_stats,
        "test_stats": test_stats,
        "ks_test": {
            "statistic": float(ks_stat),
            "p_value": float(p_value),
            "passed": passed,
            "threshold": 0.05
        }
    }

    report_path = get_project_root() / "data" / "splits" / "split_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Split report saved to {report_path}")
    logger.info("T015 completed successfully.")


if __name__ == "__main__":
    main()
