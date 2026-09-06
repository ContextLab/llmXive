import os
import sys
import json
import logging
import argparse
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from sklearn.model_selection import train_test_split

from config import DataConfig, ensure_dirs
from utils.logger import get_logger

# Ensure we can import from the project root if run as a script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

def load_distribution_json(input_path: Path) -> Dict[str, float]:
    """
    Load the distribution of substrate classes from the cleaned dataset.
    This is used to verify the stratification in the split.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file {input_path} does not exist.")
    
    df = pd.read_csv(input_path)
    if 'substrate_class' not in df.columns:
        raise ValueError(f"Column 'substrate_class' not found in {input_path}")
    
    total = len(df)
    if total == 0:
        raise ValueError(f"Input file {input_path} is empty.")
    
    distribution = df['substrate_class'].value_counts(normalize=True).to_dict()
    return {str(k): float(v) for k, v in distribution.items()}

def stratified_split(df: pd.DataFrame, target_col: str, train_ratio: float, val_ratio: float) -> Dict[str, pd.DataFrame]:
    """
    Perform a stratified split on the dataframe.
    Returns a dictionary with keys: 'train', 'val', 'test'.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe.")
    
    # Check for small classes that might cause stratification issues
    class_counts = df[target_col].value_counts()
    min_class_count = class_counts.min()
    
    if min_class_count < 3:
        logging.warning(f"Minimum class count is {min_class_count}. Stratification might be unstable.")

    # First split: Train vs (Val + Test)
    # We want val_ratio and test_ratio relative to the TOTAL dataset.
    # So (Val + Test) ratio = val_ratio + test_ratio
    test_ratio = 1.0 - train_ratio - val_ratio
    
    temp_df, test_df = train_test_split(
        df, 
        test_size=test_ratio, 
        stratify=df[target_col], 
        random_state=42
    )
    
    # Second split: Train vs Val from the temp_df
    # The ratio for val within temp_df needs to be adjusted:
    # val_size = val_ratio * total
    # temp_size = (train_ratio + val_ratio) * total
    # val_fraction_in_temp = val_ratio / (train_ratio + val_ratio)
    val_fraction_in_temp = val_ratio / (train_ratio + val_ratio)
    
    train_df, val_df = train_test_split(
        temp_df,
        test_size=val_fraction_in_temp,
        stratify=temp_df[target_col],
        random_state=42
    )
    
    return {
        'train': train_df,
        'val': val_df,
        'test': test_df
    }

def verify_distribution(original_dist: Dict[str, float], split_dists: Dict[str, Dict[str, float]], tolerance: float = 0.05) -> Dict[str, Any]:
    """
    Verify that the distribution in each split matches the original within tolerance.
    Returns a report dict.
    """
    report = {
        "original_distribution": original_dist,
        "split_distributions": split_dists,
        "variance_check": {},
        "passed": True
    }
    
    for split_name, split_dist in split_dists.items():
        max_variance = 0.0
        for cls, orig_prop in original_dist.items():
            split_prop = split_dist.get(cls, 0.0)
            variance = abs(orig_prop - split_prop)
            if variance > max_variance:
                max_variance = variance
            if variance > tolerance:
                report["variance_check"][f"{split_name}_{cls}"] = {
                    "original": orig_prop,
                    "split": split_prop,
                    "variance": variance,
                    "status": "FAIL"
                }
                report["passed"] = False
            else:
                report["variance_check"][f"{split_name}_{cls}"] = {
                    "original": orig_prop,
                    "split": split_prop,
                    "variance": variance,
                    "status": "PASS"
                }
    
    report["max_variance"] = max_variance
    return report

def save_split_datasets(splits: Dict[str, pd.DataFrame], output_dir: Path):
    """
    Save the split dataframes to CSV files.
    """
    ensure_dirs(output_dir)
    for name, df in splits.items():
        file_path = output_dir / f"split_{name}.csv"
        df.to_csv(file_path, index=False)
        logging.info(f"Saved {name} split to {file_path} with {len(df)} rows.")

def main():
    config = DataConfig()
    logger = get_logger("split", config.paths.processed_dir)
    
    input_file = config.paths.processed_dir / "cleaned_sn1.csv"
    
    if not input_file.exists():
        logger.error(f"Input file {input_file} not found. Cannot proceed with splitting.")
        sys.exit(1)
    
    logger.info(f"Loading cleaned dataset from {input_file}")
    df = pd.read_csv(input_file)
    
    if 'substrate_class' not in df.columns:
        logger.error("Column 'substrate_class' not found in the dataset. Cannot stratify.")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} rows. Starting stratified split.")
    
    # Load original distribution
    original_dist = load_distribution_json(input_file)
    logger.info(f"Original distribution: {original_dist}")
    
    # Perform split
    splits = stratified_split(df, target_col='substrate_class', train_ratio=0.8, val_ratio=0.1)
    
    # Calculate distributions for each split
    split_dists = {}
    for name, split_df in splits.items():
        split_dists[name] = load_distribution_json(Path(input_file).parent / f"split_{name}.csv")
    
    # Verify distributions
    verification_report = verify_distribution(original_dist, split_dists)
    
    # Save split files
    save_split_datasets(splits, config.paths.processed_dir)
    
    # Save verification report
    report_file = config.paths.processed_dir / "split_report.json"
    with open(report_file, 'w') as f:
        json.dump(verification_report, f, indent=2)
    
    logger.info(f"Split report saved to {report_file}")
    logger.info(f"Verification passed: {verification_report['passed']}")
    
    if not verification_report['passed']:
        logger.warning("Distribution variance exceeded 5% tolerance in some classes.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())