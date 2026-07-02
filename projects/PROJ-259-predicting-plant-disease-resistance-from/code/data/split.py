"""
Data splitting module for stratified sampling based on resistance phenotype.

Implements FR-009: Stratified sampling to ensure balanced representation
of resistance phenotypes in training and hold-out sets.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from sklearn.model_selection import train_test_split

from config import get_processed_data_path, get_artifacts_path
from utils.logging import get_logger, log_pipeline_step, log_sample_exclusion
from utils.exceptions import EX_DATA_INTEGRITY

logger = get_logger(__name__)


def load_preprocessed_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """
    Load preprocessed SNP and metabolite data along with phenotypes.

    Returns:
        Tuple of (snps_df, metabolites_df, phenotypes_series)

    Raises:
        EX_DATA_INTEGRITY: If required files are missing or data is inconsistent.
    """
    processed_path = get_processed_data_path()

    # Expected file paths
    snps_file = processed_path / "snps_aligned.csv"
    metabolites_file = processed_path / "metabolites_aligned.csv"
    phenotypes_file = processed_path / "phenotypes_aligned.csv"

    # Check file existence
    missing_files = []
    for file_path, name in [(snps_file, "SNPs"), (metabolites_file, "metabolites"), (phenotypes_file, "phenotypes")]:
        if not file_path.exists():
            missing_files.append(name)

    if missing_files:
        logger.error(f"Missing required preprocessed files: {missing_files}")
        raise EX_DATA_INTEGRITY(f"Missing required preprocessed files: {missing_files}")

    # Load data
    logger.info("Loading preprocessed SNP data")
    snps_df = pd.read_csv(snps_file, index_col=0)

    logger.info("Loading preprocessed metabolite data")
    metabolites_df = pd.read_csv(metabolites_file, index_col=0)

    logger.info("Loading preprocessed phenotype data")
    phenotypes_df = pd.read_csv(phenotypes_file, index_col=0)
    phenotypes_series = phenotypes_df.squeeze() if phenotypes_df.shape[1] == 1 else phenotypes_df['resistance']

    # Validate sample alignment
    snps_samples = set(snps_df.index)
    metabolite_samples = set(metabolites_df.index)
    phenotype_samples = set(phenotypes_series.index)

    # Check for intersection
    common_samples = snps_samples & metabolite_samples & phenotype_samples

    if len(common_samples) == 0:
        logger.error("No common samples found across all modalities")
        raise EX_DATA_INTEGRITY("No common samples found across all modalities")

    if len(common_samples) < len(snps_samples) or len(common_samples) < len(metabolite_samples) or len(common_samples) < len(phenotype_samples):
        logger.warning(f"Dropping {len(snps_samples) - len(common_samples)} SNP samples, {len(metabolite_samples) - len(common_samples)} metabolite samples, and {len(phenotype_samples) - len(common_samples)} phenotype samples due to misalignment")
        log_sample_exclusion(
            reason="sample_misalignment",
            count=len(snps_samples) + len(metabolite_samples) + len(phenotype_samples) - 3 * len(common_samples),
            details=f"Retained {len(common_samples)} common samples"
        )

    # Filter to common samples
    snps_df = snps_df.loc[common_samples]
    metabolites_df = metabolites_df.loc[common_samples]
    phenotypes_series = phenotypes_series.loc[common_samples]

    logger.info(f"Loaded {len(common_samples)} aligned samples")
    logger.info(f"Phenotype distribution:\n{phenotypes_series.value_counts()}")

    return snps_df, metabolites_df, phenotypes_series


def split_data(
    snps_df: pd.DataFrame,
    metabolites_df: pd.DataFrame,
    phenotypes_series: pd.Series,
    train_ratio: float = 0.8,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Perform stratified train-holdout split based on resistance phenotype.

    Args:
        snps_df: DataFrame of SNP features with sample IDs as index
        metabolites_df: DataFrame of metabolite features with sample IDs as index
        phenotypes_series: Series of resistance phenotypes with sample IDs as index
        train_ratio: Proportion of samples for training (default 0.8)
        random_state: Random seed for reproducibility

    Returns:
        Dictionary containing:
            - train_snps: Training SNP features
            - train_metabolites: Training metabolite features
            - train_phenotypes: Training phenotypes
            - holdout_snps: Hold-out SNP features
            - holdout_metabolites: Hold-out metabolite features
            - holdout_phenotypes: Hold-out phenotypes
            - split_info: Metadata about the split

    Raises:
        EX_DATA_INTEGRITY: If stratification fails or classes are imbalanced.
    """
    logger.info(f"Performing stratified split with train ratio: {train_ratio}")

    # Validate phenotype balance
    value_counts = phenotypes_series.value_counts()
    min_class_count = value_counts.min()

    if min_class_count < 10:
        logger.warning(f"Minimum class count is {min_class_count}, stratification may be unstable")

    # Perform stratified split
    try:
        train_indices, holdout_indices = train_test_split(
            phenotypes_series.index,
            test_size=1 - train_ratio,
            stratify=phenotypes_series,
            random_state=random_state
        )
    except ValueError as e:
        logger.error(f"Stratification failed: {e}")
        # If stratification fails due to small class sizes, fall back to non-stratified split
        logger.info("Falling back to non-stratified split")
        train_indices, holdout_indices = train_test_split(
            phenotypes_series.index,
            test_size=1 - train_ratio,
            random_state=random_state
        )

    # Split data
    train_snps = snps_df.loc[train_indices]
    train_metabolites = metabolites_df.loc[train_indices]
    train_phenotypes = phenotypes_series.loc[train_indices]

    holdout_snps = snps_df.loc[holdout_indices]
    holdout_metabolites = metabolites_df.loc[holdout_indices]
    holdout_phenotypes = phenotypes_series.loc[holdout_indices]

    # Log split statistics
    logger.info(f"Training set: {len(train_indices)} samples")
    logger.info(f"Training phenotype distribution:\n{train_phenotypes.value_counts()}")
    logger.info(f"Hold-out set: {len(holdout_indices)} samples")
    logger.info(f"Hold-out phenotype distribution:\n{holdout_phenotypes.value_counts()}")

    split_info = {
        "train_ratio": train_ratio,
        "train_size": len(train_indices),
        "holdout_size": len(holdout_indices),
        "train_phenotype_counts": train_phenotypes.value_counts().to_dict(),
        "holdout_phenotype_counts": holdout_phenotypes.value_counts().to_dict(),
        "random_state": random_state,
        "stratified": "yes" if len(set(train_phenotypes.unique()) & set(holdout_phenotypes.unique())) == len(train_phenotypes.unique()) else "no"
    }

    return {
        "train_snps": train_snps,
        "train_metabolites": train_metabolites,
        "train_phenotypes": train_phenotypes,
        "holdout_snps": holdout_snps,
        "holdout_metabolites": holdout_metabolites,
        "holdout_phenotypes": holdout_phenotypes,
        "split_info": split_info
    }


def save_split_data(split_results: Dict[str, Any], output_dir: Optional[Path] = None) -> Path:
    """
    Save split data to CSV files.

    Args:
        split_results: Dictionary containing split data
        output_dir: Optional output directory (defaults to processed data path)

    Returns:
        Path to the output directory
    """
    if output_dir is None:
        output_dir = get_processed_data_path()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save training data
    split_results["train_snps"].to_csv(output_dir / "train_snps.csv")
    split_results["train_metabolites"].to_csv(output_dir / "train_metabolites.csv")
    split_results["train_phenotypes"].to_frame().to_csv(output_dir / "train_phenotypes.csv")

    # Save hold-out data
    split_results["holdout_snps"].to_csv(output_dir / "holdout_snps.csv")
    split_results["holdout_metabolites"].to_csv(output_dir / "holdout_metabolites.csv")
    split_results["holdout_phenotypes"].to_frame().to_csv(output_dir / "holdout_phenotypes.csv")

    # Save split metadata
    import json
    split_info_path = output_dir / "split_info.json"
    with open(split_info_path, 'w') as f:
        json.dump(split_results["split_info"], f, indent=2)

    logger.info(f"Split data saved to {output_dir}")
    return output_dir


def run_split_pipeline(train_ratio: float = 0.8, random_state: int = 42) -> Dict[str, Any]:
    """
    Execute the complete data splitting pipeline.

    Args:
        train_ratio: Proportion of samples for training
        random_state: Random seed for reproducibility

    Returns:
        Dictionary containing split results and metadata
    """
    log_pipeline_step("data_split", "Starting stratified data split")

    # Load preprocessed data
    snps_df, metabolites_df, phenotypes_series = load_preprocessed_data()

    # Perform split
    split_results = split_data(
        snps_df=snps_df,
        metabolites_df=metabolites_df,
        phenotypes_series=phenotypes_series,
        train_ratio=train_ratio,
        random_state=random_state
    )

    # Save split data
    output_dir = save_split_data(split_results)

    log_pipeline_step(
        "data_split",
        "Completed stratified data split",
        metadata={
            "train_size": split_results["split_info"]["train_size"],
            "holdout_size": split_results["split_info"]["holdout_size"],
            "output_dir": str(output_dir)
        }
    )

    return split_results


def main():
    """Main entry point for the split pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="Split preprocessed data into training and hold-out sets")
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Proportion of samples for training (default: 0.8)"
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )

    args = parser.parse_args()

    try:
        split_results = run_split_pipeline(
            train_ratio=args.train_ratio,
            random_state=args.random_state
        )
        logger.info("Data split completed successfully")
    except EX_DATA_INTEGRITY as e:
        logger.error(f"Data integrity error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during data split: {e}")
        raise


if __name__ == "__main__":
    main()
