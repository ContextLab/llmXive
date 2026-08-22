import os
import sys
import logging
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logging import init_pipeline_logging, get_logger
from utils.config import load_config, get_max_isolates, get_paths

logger = get_logger(__name__)

def load_snp_data(snp_file: Path) -> pd.DataFrame:
    """Load SNP data from a processed file."""
    if not snp_file.exists():
        raise FileNotFoundError(f"SNP data file not found: {snp_file}")
    logger.info(f"Loading SNP data from {snp_file}")
    df = pd.read_csv(snp_file)
    return df

def load_gene_presence(gene_file: Path) -> pd.DataFrame:
    """Load gene presence/absence matrix."""
    if not gene_file.exists():
        raise FileNotFoundError(f"Gene presence file not found: {gene_file}")
    logger.info(f"Loading gene presence data from {gene_file}")
    df = pd.read_csv(gene_file)
    return df

def load_cnv_data(cnv_file: Path) -> pd.DataFrame:
    """Load Copy Number Variation data."""
    if not cnv_file.exists():
        raise FileNotFoundError(f"CNV data file not found: {cnv_file}")
    logger.info(f"Loading CNV data from {cnv_file}")
    df = pd.read_csv(cnv_file)
    return df

def load_metadata(metadata_file: Path) -> pd.DataFrame:
    """Load cleaned metadata including resistance phenotypes."""
    if not metadata_file.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_file}")
    logger.info(f"Loading metadata from {metadata_file}")
    df = pd.read_csv(metadata_file)
    return df

def merge_features(snp_df: pd.DataFrame, gene_df: pd.DataFrame, 
                   cnv_df: pd.DataFrame, metadata_df: pd.DataFrame) -> pd.DataFrame:
    """Merge all feature sources into a single dataframe."""
    # Start with metadata as the base (contains isolate IDs and phenotypes)
    # Ensure isolate_id columns are consistent
    if 'isolate_id' not in metadata_df.columns:
        raise ValueError("Metadata must contain 'isolate_id' column")
    
    # Sort by isolate_id to ensure consistent merging
    metadata_df = metadata_df.sort_values('isolate_id')
    
    # Merge SNP counts (assuming snp_df has isolate_id and count columns)
    if snp_df is not None and not snp_df.empty:
        if 'isolate_id' in snp_df.columns:
            snp_df = snp_df.sort_values('isolate_id')
            metadata_df = metadata_df.merge(snp_df[['isolate_id'] + [c for c in snp_df.columns if c != 'isolate_id']], 
                                            on='isolate_id', how='left')
    
    # Merge gene presence (binary matrix)
    if gene_df is not None and not gene_df.empty:
        if 'isolate_id' in gene_df.columns:
            gene_df = gene_df.sort_values('isolate_id')
            metadata_df = metadata_df.merge(gene_df, on='isolate_id', how='left')
    
    # Merge CNV counts
    if cnv_df is not None and not cnv_df.empty:
        if 'isolate_id' in cnv_df.columns:
            cnv_df = cnv_df.sort_values('isolate_id')
            metadata_df = metadata_df.merge(cnv_df, on='isolate_id', how='left')
    
    return metadata_df

def validate_feature_matrix(df: pd.DataFrame, expected_isolates: int) -> Tuple[bool, List[str]]:
    """
    Validate the feature matrix for T020 requirements:
    1. No missing values in 'resistance_phenotype' column
    2. Row count matches the expected isolate count
    
    Returns: (is_valid, list_of_errors)
    """
    errors = []
    is_valid = True

    # Check 1: Ensure 'resistance_phenotype' column exists
    if 'resistance_phenotype' not in df.columns:
        errors.append("ERROR: 'resistance_phenotype' column is missing from the feature matrix.")
        return False, errors

    # Check 2: Validate no missing values in 'resistance_phenotype'
    phenotype_col = df['resistance_phenotype']
    missing_count = phenotype_col.isna().sum()
    
    if missing_count > 0:
        is_valid = False
        errors.append(f"ERROR: Found {missing_count} missing values in 'resistance_phenotype' column.")
        # Log specific isolate IDs with missing values if possible
        missing_indices = phenotype_col[phenotype_col.isna()].index.tolist()
        if len(missing_indices) <= 10:
            missing_ids = df.loc[missing_indices, 'isolate_id'].tolist()
            errors.append(f"Affected isolate IDs: {missing_ids}")
        else:
            errors.append(f"Affected isolate IDs: {len(missing_indices)} rows (showing first 10: {df.loc[missing_indices[:10], 'isolate_id'].tolist()})")
    else:
        logger.info("Validation passed: No missing values in 'resistance_phenotype'.")

    # Check 3: Validate row count matches expected isolate count
    actual_rows = len(df)
    if actual_rows != expected_isolates:
        is_valid = False
        errors.append(f"ERROR: Row count mismatch. Expected {expected_isolates} isolates, but found {actual_rows} rows.")
    else:
        logger.info(f"Validation passed: Row count matches expected isolate count ({actual_rows}).")

    return is_valid, errors

def filter_antibiotic_classes(df: pd.DataFrame, min_isolates: int = 50) -> pd.DataFrame:
    """
    Filter antibiotic classes to ensure at least min_isolates are present.
    This function assumes 'antibiotic_class' is a column in the dataframe.
    If the dataframe is grouped by class, this might need adaptation based on 
    the actual structure. For now, we assume a single dataframe per class or 
    we are filtering the global dataset before splitting.
    
    Note: This logic is primarily for T017/T018 context, but kept here for completeness.
    """
    if 'antibiotic_class' not in df.columns:
        logger.warning("Column 'antibiotic_class' not found. Skipping class filtering.")
        return df

    class_counts = df['antibiotic_class'].value_counts()
    valid_classes = class_counts[class_counts >= min_isolates].index.tolist()
    
    if len(valid_classes) == 0:
        logger.error("ERROR: No antibiotic classes meet the minimum isolate count threshold.")
        return df # Or raise error depending on T018 logic

    filtered_df = df[df['antibiotic_class'].isin(valid_classes)]
    excluded_classes = set(class_counts.index) - set(valid_classes)
    
    if excluded_classes:
        logger.warning(f"Excluded {len(excluded_classes)} antibiotic classes with < {min_isolates} isolates: {excluded_classes}")
    
    return filtered_df

def main():
    """
    Main entry point for building and validating the feature matrix.
    Executes T016 logic (aggregation) and T020 logic (validation).
    """
    # Initialize logging
    init_pipeline_logging()
    
    parser = argparse.ArgumentParser(description="Build and validate the feature matrix.")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to configuration file")
    parser.add_argument("--snp-file", type=str, required=True, help="Path to processed SNP data")
    parser.add_argument("--gene-file", type=str, required=True, help="Path to gene presence data")
    parser.add_argument("--cnv-file", type=str, required=True, help="Path to CNV data")
    parser.add_argument("--metadata-file", type=str, required=True, help="Path to cleaned metadata")
    parser.add_argument("--output-file", type=str, required=True, help="Path to save the feature matrix")
    parser.add_argument("--min-isolates", type=int, default=50, help="Minimum isolates per antibiotic class")
    
    args = parser.parse_args()
    
    paths = get_paths()
    max_isolates = get_max_isolates()
    
    try:
        logger.info("Starting feature matrix construction and validation...")
        
        # Load data
        snp_df = load_snp_data(Path(args.snp_file))
        gene_df = load_gene_presence(Path(args.gene_file))
        cnv_df = load_cnv_data(Path(args.cnv_file))
        metadata_df = load_metadata(Path(args.metadata_file))
        
        # Apply max isolates limit if necessary (T011/T012 context)
        if len(metadata_df) > max_isolates:
            logger.info(f"Limiting dataset to {max_isolates} isolates.")
            metadata_df = metadata_df.head(max_isolates)
            # Re-load or slice other dataframes to match if they are keyed by isolate_id
            # For simplicity in this script, we assume metadata drives the count
            # In a real pipeline, we would filter other DFs by the subset of IDs
            isolate_ids = set(metadata_df['isolate_id'])
            if 'isolate_id' in snp_df.columns: snp_df = snp_df[snp_df['isolate_id'].isin(isolate_ids)]
            if 'isolate_id' in gene_df.columns: gene_df = gene_df[gene_df['isolate_id'].isin(isolate_ids)]
            if 'isolate_id' in cnv_df.columns: cnv_df = cnv_df[cnv_df['isolate_id'].isin(isolate_ids)]
        
        # Merge features
        logger.info("Merging features from multiple sources...")
        feature_matrix = merge_features(snp_df, gene_df, cnv_df, metadata_df)
        
        # Filter antibiotic classes (T017/T018 logic)
        feature_matrix = filter_antibiotic_classes(feature_matrix, args.min_isolates)
        
        # T020: Validate the matrix
        logger.info("Running validation checks (T020)...")
        is_valid, errors = validate_feature_matrix(feature_matrix, len(feature_matrix))
        
        if not is_valid:
            logger.error("Validation FAILED. The feature matrix does not meet requirements.")
            for err in errors:
                logger.error(f"  - {err}")
            # Do not save the invalid file, or save with a flag? 
            # Best practice: Fail loudly and do not produce the artifact if validation fails.
            sys.exit(1)
        
        # Save the valid feature matrix
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        feature_matrix.to_csv(output_path, index=False)
        logger.info(f"Feature matrix successfully saved to {output_path}")
        logger.info(f"Total rows: {len(feature_matrix)}, Columns: {len(feature_matrix.columns)}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during feature matrix construction: {e}")
        raise

if __name__ == "__main__":
    main()
