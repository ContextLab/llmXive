"""
Ingests antibiotic susceptibility metadata for E. coli isolates.

Parses metadata files (CSV/TSV), handles missing values, logs exclusion counts,
and outputs a cleaned metadata file ready for feature matrix generation.

Edge Case: Missing metadata for isolates with sequence data.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

# Import project utilities
from utils.logging import get_logger, setup_file_logging
from utils.config import load_config, get_paths, get_max_isolates

logger = get_logger(__name__)

# Standard antibiotic resistance phenotype values
RESISTANCE_VALUES = {
    'S': 0, 'Susceptible': 0, 'Susceptible': 0,
    'I': 1, 'Intermediate': 1, 'Intermediate': 1,
    'R': 2, 'Resistant': 2, 'Resistant': 2
}

def load_metadata_file(file_path: Path) -> pd.DataFrame:
    """
    Load metadata from CSV or TSV file.
    
    Args:
        file_path: Path to the metadata file
        
    Returns:
        DataFrame with loaded metadata
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is unsupported
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {file_path}")
    
    suffix = file_path.suffix.lower()
    if suffix == '.csv':
        df = pd.read_csv(file_path)
    elif suffix in ['.tsv', '.tab']:
        df = pd.read_csv(file_path, sep='\t')
    else:
        raise ValueError(f"Unsupported metadata file format: {suffix}")
    
    logger.info(f"Loaded metadata with {len(df)} rows and {len(df.columns)} columns")
    return df

def validate_columns(df: pd.DataFrame, required_cols: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validate that required columns exist in the dataframe.
    
    Args:
        df: Input dataframe
        required_cols: List of required column names
        
    Returns:
        Tuple of (found_columns, missing_columns)
    """
    found = []
    missing = []
    
    for col in required_cols:
        if col in df.columns:
            found.append(col)
        else:
            missing.append(col)
            logger.warning(f"Required column '{col}' not found in metadata")
    
    return found, missing

def parse_resistance_phenotype(series: pd.Series) -> pd.Series:
    """
    Parse resistance phenotype values into standardized numeric format.
    
    Args:
        series: Series of resistance phenotype values
        
    Returns:
        Series with standardized numeric values (0=S, 1=I, 2=R)
    """
    def parse_value(val):
        if pd.isna(val):
            return np.nan
        val_str = str(val).strip()
        # Handle case variations
        val_normalized = val_str.replace(' ', '').lower()
        
        if val_normalized in ['s', 'susceptible']:
            return 0
        elif val_normalized in ['i', 'intermediate']:
            return 1
        elif val_normalized in ['r', 'resistant']:
            return 2
        else:
            logger.warning(f"Unknown resistance value: '{val_str}'")
            return np.nan
    
    return series.apply(parse_value)

def handle_missing_values(df: pd.DataFrame, isolate_id_col: str) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Handle missing values in the metadata dataframe.
    
    Args:
        df: Input dataframe
        isolate_id_col: Name of the isolate ID column
        
    Returns:
        Tuple of (cleaned dataframe, exclusion counts)
    """
    exclusion_counts = {
        'total_rows': len(df),
        'missing_isolate_id': 0,
        'missing_phenotype': 0,
        'duplicated_isolate_id': 0,
        'total_excluded': 0
    }
    
    # Check for missing isolate IDs
    missing_isolate = df[df[isolate_id_col].isna()]
    exclusion_counts['missing_isolate_id'] = len(missing_isolate)
    df = df.dropna(subset=[isolate_id_col])
    
    # Check for missing resistance phenotypes
    phenotype_col = 'resistance_phenotype'
    if phenotype_col in df.columns:
        missing_phenotype = df[df[phenotype_col].isna()]
        exclusion_counts['missing_phenotype'] = len(missing_phenotype)
        df = df.dropna(subset=[phenotype_col])
    
    # Check for duplicate isolate IDs
    duplicates = df[df.duplicated(subset=[isolate_id_col], keep=False)]
    if len(duplicates) > 0:
        # Keep first occurrence
        exclusion_counts['duplicated_isolate_id'] = len(duplicates) - len(df.drop_duplicates(subset=[isolate_id_col], keep='first'))
        df = df.drop_duplicates(subset=[isolate_id_col], keep='first')
    
    # Calculate total excluded
    exclusion_counts['total_excluded'] = exclusion_counts['total_rows'] - len(df)
    
    logger.info(f"Exclusion summary: {exclusion_counts}")
    return df, exclusion_counts

def apply_max_isolates_limit(df: pd.DataFrame, max_isolates: int) -> pd.DataFrame:
    """
    Apply the MAX_ISOLATES limit to the dataframe.
    
    Args:
        df: Input dataframe
        max_isolates: Maximum number of isolates to keep
        
    Returns:
        Limited dataframe
    """
    if len(df) > max_isolates:
        logger.warning(f"Dataset has {len(df)} isolates, limiting to {max_isolates}")
        # Sort by isolate_id to ensure deterministic selection
        df = df.sort_values('isolate_id').head(max_isolates)
        logger.info(f"Kept {len(df)} isolates after applying limit")
    return df

def save_cleaned_metadata(df: pd.DataFrame, exclusion_counts: Dict[str, int], output_path: Path):
    """
    Save cleaned metadata and exclusion counts to disk.
    
    Args:
        df: Cleaned dataframe
        exclusion_counts: Dictionary of exclusion counts
        output_path: Path to save the cleaned metadata
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save metadata
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned metadata to {output_path} with {len(df)} rows")
    
    # Save exclusion counts
    stats_path = output_path.parent / 'metadata_exclusion_stats.json'
    with open(stats_path, 'w') as f:
        json.dump(exclusion_counts, f, indent=2)
    logger.info(f"Saved exclusion statistics to {stats_path}")

def main():
    """
    Main function to run the metadata ingestion pipeline.
    """
    # Initialize logging
    setup_file_logging('ingest_metadata', 'data/logs/ingest_metadata.log')
    
    # Load configuration
    config = load_config()
    paths = get_paths(config)
    max_isolates = get_max_isolates(config)
    
    # Define input and output paths
    # Expected input: data/raw/metadata.csv (or similar)
    input_path = paths['data_raw'] / 'metadata.csv'
    output_path = paths['data_processed'] / 'metadata_cleaned.csv'
    
    # Check if input file exists
    if not input_path.exists():
        # Try to find alternative metadata files
        metadata_files = list(paths['data_raw'].glob('*.csv')) + list(paths['data_raw'].glob('*.tsv'))
        if metadata_files:
            input_path = metadata_files[0]
            logger.info(f"Using alternative metadata file: {input_path}")
        else:
            logger.error("No metadata file found in data/raw/")
            logger.error("Expected: data/raw/metadata.csv or similar CSV/TSV file")
            sys.exit(1)
    
    try:
        # Load metadata
        logger.info(f"Loading metadata from {input_path}")
        df = load_metadata_file(input_path)
        
        # Validate required columns
        required_cols = ['isolate_id']
        found, missing = validate_columns(df, required_cols)
        
        if len(missing) > 0:
            logger.error(f"Missing required columns: {missing}")
            sys.exit(1)
        
        # Handle missing values
        logger.info("Handling missing values...")
        df, exclusion_counts = handle_missing_values(df, 'isolate_id')
        
        # Parse resistance phenotype if present
        if 'resistance_phenotype' in df.columns:
            logger.info("Parsing resistance phenotype values...")
            df['resistance_phenotype'] = parse_resistance_phenotype(df['resistance_phenotype'])
            # Remove rows with NaN after parsing
            df = df.dropna(subset=['resistance_phenotype'])
            exclusion_counts['missing_phenotype'] += len(df) - len(df.dropna(subset=['resistance_phenotype']))
        
        # Apply max isolates limit
        df = apply_max_isolates_limit(df, max_isolates)
        
        # Save cleaned metadata
        logger.info("Saving cleaned metadata...")
        save_cleaned_metadata(df, exclusion_counts, output_path)
        
        logger.info("Metadata ingestion completed successfully")
        
    except Exception as e:
        logger.error(f"Error during metadata ingestion: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
