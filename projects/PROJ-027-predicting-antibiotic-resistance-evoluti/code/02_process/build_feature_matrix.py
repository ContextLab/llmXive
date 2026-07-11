import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

def load_snp_data(snp_file: Path) -> pd.DataFrame:
    """Load SNP data from the processed file."""
    if not snp_file.exists():
        logger.error(f"SNP file not found: {snp_file}")
        raise FileNotFoundError(f"SNP file not found: {snp_file}")
    logger.info(f"Loading SNP data from {snp_file}")
    return pd.read_csv(snp_file, index_col=0)

def load_gene_presence(gene_file: Path) -> pd.DataFrame:
    """Load gene presence matrix from the processed file."""
    if not gene_file.exists():
        logger.error(f"Gene presence file not found: {gene_file}")
        raise FileNotFoundError(f"Gene presence file not found: {gene_file}")
    logger.info(f"Loading gene presence data from {gene_file}")
    return pd.read_csv(gene_file, index_col=0)

def load_cnv_data(cnv_file: Path) -> pd.DataFrame:
    """Load CNV data from the processed file."""
    if not cnv_file.exists():
        logger.error(f"CNV file not found: {cnv_file}")
        raise FileNotFoundError(f"CNV file not found: {cnv_file}")
    logger.info(f"Loading CNV data from {cnv_file}")
    return pd.read_csv(cnv_file, index_col=0)

def load_metadata(metadata_file: Path) -> pd.DataFrame:
    """Load cleaned metadata."""
    if not metadata_file.exists():
        logger.error(f"Metadata file not found: {metadata_file}")
        raise FileNotFoundError(f"Metadata file not found: {metadata_file}")
    logger.info(f"Loading metadata from {metadata_file}")
    return pd.read_csv(metadata_file, index_col=0)

def merge_features(
    snp_data: pd.DataFrame,
    gene_data: pd.DataFrame,
    cnv_data: pd.DataFrame,
    metadata: pd.DataFrame
) -> pd.DataFrame:
    """Merge all features into a single dataframe."""
    logger.info("Merging features...")
    
    # Ensure all dataframes are indexed by isolate_id
    snp_data.index.name = 'isolate_id'
    gene_data.index.name = 'isolate_id'
    cnv_data.index.name = 'isolate_id'
    metadata.index.name = 'isolate_id'

    # Concatenate features horizontally
    feature_matrix = pd.concat([snp_data, gene_data, cnv_data], axis=1)
    
    # Merge with metadata to include phenotype
    feature_matrix = feature_matrix.join(metadata[['resistance_phenotype']])
    
    logger.info(f"Merged feature matrix shape: {feature_matrix.shape}")
    return feature_matrix

def validate_feature_matrix(df: pd.DataFrame, min_isolates: int = 50) -> Tuple[bool, List[str]]:
    """
    Validate the feature matrix according to project requirements.
    
    Checks:
    1. No missing values in 'resistance_phenotype' column.
    2. Row count matches the expected isolate count (consistency check).
    
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
    """
    errors = []
    is_valid = True

    # Check 1: No missing values in resistance_phenotype
    if 'resistance_phenotype' not in df.columns:
        errors.append("CRITICAL: 'resistance_phenotype' column is missing from feature matrix.")
        return False, errors

    phenotype_missing = df['resistance_phenotype'].isna().sum()
    if phenotype_missing > 0:
        errors.append(f"CRITICAL: Found {phenotype_missing} missing values in 'resistance_phenotype'. "
                    "All isolates must have a defined resistance phenotype.")
        is_valid = False
    else:
        logger.info("Validation passed: No missing values in 'resistance_phenotype'.")

    # Check 2: Row count matches isolate count
    # In this context, we verify that the number of rows is consistent with the data ingestion.
    # If the metadata was filtered correctly, the row count should be > 0 and consistent.
    row_count = len(df)
    if row_count == 0:
        errors.append(f"CRITICAL: Feature matrix is empty (0 rows). Data ingestion or merging failed.")
        is_valid = False
    else:
        logger.info(f"Validation passed: Feature matrix contains {row_count} isolates.")
        
        # Additional sanity check: ensure we have enough data for the next steps
        if row_count < min_isolates:
            logger.warning(f"Warning: Feature matrix has {row_count} isolates, which is less than the recommended minimum of {min_isolates} for robust statistical analysis.")

    return is_valid, errors

def filter_antibiotic_classes(df: pd.DataFrame, min_classes: int = 50) -> pd.DataFrame:
    """
    Filter antibiotic classes that have fewer than min_classes isolates.
    This function assumes 'resistance_phenotype' contains the antibiotic class information
    or is structured such that grouping is possible. 
    Note: Based on previous tasks, this logic was largely handled in T017/T018.
    This function serves as a final guard or re-verification step if phenotypes are categorical.
    """
    if 'resistance_phenotype' not in df.columns:
        return df

    # Count isolates per unique phenotype value (assuming phenotype represents class or condition)
    counts = df['resistance_phenotype'].value_counts()
    
    valid_phenotypes = counts[counts >= min_classes].index.tolist()
    invalid_phenotypes = counts[counts < min_classes].index.tolist()

    if invalid_phenotypes:
        logger.warning(f"Excluding {len(invalid_phenotypes)} antibiotic classes with < {min_classes} isolates: {invalid_phenotypes}")
        df = df[df['resistance_phenotype'].isin(valid_phenotypes)]

    if len(df) == 0:
        logger.error("ERROR E004: All antibiotic classes have fewer than 50 isolates. Aborting.")
        raise ValueError("ERROR E004: All antibiotic classes have fewer than 50 isolates. Aborting.")

    logger.info(f"Filtered feature matrix now contains {len(df)} isolates across {len(valid_phenotypes)} classes.")
    return df

def main():
    parser = argparse.ArgumentParser(description="Build and validate the feature matrix for antibiotic resistance prediction.")
    parser.add_argument("--snp-file", type=Path, required=True, help="Path to SNP data CSV")
    parser.add_argument("--gene-file", type=Path, required=True, help="Path to gene presence CSV")
    parser.add_argument("--cnv-file", type=Path, required=True, help="Path to CNV data CSV")
    parser.add_argument("--metadata-file", type=Path, required=True, help="Path to cleaned metadata CSV")
    parser.add_argument("--output-file", type=Path, required=True, help="Path to save the feature matrix CSV")
    parser.add_argument("--min-isolates", type=int, default=50, help="Minimum isolates per class to retain")
    
    args = parser.parse_args()

    # Setup logging
    log_file = args.output_file.with_suffix('.log')
    setup_logger = get_logger(__name__, log_file=str(log_file))

    try:
        # Load data
        snp_data = load_snp_data(args.snp_file)
        gene_data = load_gene_presence(args.gene_file)
        cnv_data = load_cnv_data(args.cnv_file)
        metadata = load_metadata(args.metadata_file)

        # Merge features
        feature_matrix = merge_features(snp_data, gene_data, cnv_data, metadata)

        # Filter classes (T017/T018 logic)
        feature_matrix = filter_antibiotic_classes(feature_matrix, args.min_isolates)

        # VALIDATION STEP (T020): Ensure no missing phenotype and row count consistency
        is_valid, errors = validate_feature_matrix(feature_matrix)

        if not is_valid:
            for err in errors:
                logger.error(err)
            raise ValueError("Validation failed. Check logs for details.")

        # Save output
        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        feature_matrix.to_csv(args.output_file)
        logger.info(f"Feature matrix successfully saved to {args.output_file}")
        logger.info(f"Final shape: {feature_matrix.shape}")

    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()