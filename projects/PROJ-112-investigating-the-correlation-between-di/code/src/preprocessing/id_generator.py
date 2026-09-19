import hashlib
import pandas as pd
import logging
import argparse
from typing import List, Optional, Tuple
from pathlib import Path
from src.utils.logger import get_logger

def generate_sample_id(cohort: str, original_id: str) -> str:
    """
    Generate a unique SHA256 sample ID based on cohort and original_id.

    Args:
        cohort: The cohort name (e.g., 'AGP', 'UKBB').
        original_id: The original sample ID from the dataset.

    Returns:
        A 64-character hexadecimal SHA256 hash string.
    """
    if not cohort or not original_id:
        raise ValueError("Both cohort and original_id must be non-empty strings.")

    # Create a deterministic string for hashing
    raw_string = f"{cohort}:{original_id}"
    
    # Generate SHA256 hash
    hash_object = hashlib.sha256(raw_string.encode('utf-8'))
    return hash_object.hexdigest()

def generate_sample_ids_dataframe(df: pd.DataFrame, cohort_col: str, id_col: str, new_col_name: str = "sample_id") -> pd.DataFrame:
    """
    Generate SHA256 sample IDs for a DataFrame and add them as a new column.

    Args:
        df: Input DataFrame containing cohort and original ID columns.
        cohort_col: Name of the column containing cohort identifiers.
        id_col: Name of the column containing original sample IDs.
        new_col_name: Name for the new column to store generated IDs.

    Returns:
        DataFrame with an additional column containing generated sample IDs.
    """
    logger = get_logger(__name__)
    
    # Validate columns exist
    if cohort_col not in df.columns:
        raise ValueError(f"Column '{cohort_col}' not found in DataFrame. Available columns: {df.columns.tolist()}")
    if id_col not in df.columns:
        raise ValueError(f"Column '{id_col}' not found in DataFrame. Available columns: {df.columns.tolist()}")
    
    # Check for missing values
    if df[cohort_col].isnull().any() or df[id_col].isnull().any():
        logger.warning("Found missing values in cohort or ID columns. These will result in empty hash strings or errors.")
    
    # Apply generation function
    df[new_col_name] = df.apply(
        lambda row: generate_sample_id(str(row[cohort_col]), str(row[id_col])), 
        axis=1
    )
    
    logger.info(f"Generated {len(df)} sample IDs and stored in column '{new_col_name}'.")
    return df

def main():
    """
    CLI entry point for generating sample IDs.
    Expects an input TSV/CSV file and outputs a new file with a 'sample_id' column.
    """
    parser = argparse.ArgumentParser(description="Generate SHA256 sample IDs from cohort and original ID columns.")
    parser.add_argument("--input", required=True, help="Path to input TSV/CSV file.")
    parser.add_argument("--output", required=True, help="Path to output TSV/CSV file.")
    parser.add_argument("--cohort-col", default="cohort", help="Name of the cohort column.")
    parser.add_argument("--id-col", default="original_id", help="Name of the original ID column.")
    parser.add_argument("--output-col", default="sample_id", help="Name of the new sample ID column.")
    parser.add_argument("--format", default="tsv", choices=["tsv", "csv"], help="Output file format.")
    
    args = parser.parse_args()
    
    logger = get_logger(__name__)
    logger.info(f"Starting ID generation for {args.input}")
    
    # Determine separator
    sep = '\t' if args.format == 'tsv' else ','
    
    try:
        # Load data
        df = pd.read_csv(args.input, sep=sep)
        logger.info(f"Loaded {len(df)} rows from {args.input}")
        
        # Generate IDs
        df_with_ids = generate_sample_ids_dataframe(
            df, 
            cohort_col=args.cohort_col, 
            id_col=args.id_col, 
            new_col_name=args.output_col
        )
        
        # Save output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df_with_ids.to_csv(output_path, sep=sep, index=False)
        logger.info(f"Successfully wrote {len(df_with_ids)} rows to {args.output}")
        
    except Exception as e:
        logger.error(f"Failed to process file: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()