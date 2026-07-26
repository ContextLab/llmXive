import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import yaml

# Ensure imports work from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs
from utils.logger import get_logger

logger = get_logger(__name__)

def load_huggingface_data(dataset_name: str = "chemistry/dts-sn1", subset_size: Optional[int] = None) -> pd.DataFrame:
    """
    Load SN1 data from HuggingFace.
    
    Primary Source: chemistry/dts-sn1
    Expected columns: smiles, rate, substrate (or similar)
    """
    try:
        from datasets import load_dataset
        logger.info(f"Loading dataset from HuggingFace: {dataset_name}")
        
        # Load the dataset (streaming=False to get a dataframe easily)
        ds = load_dataset(dataset_name, split="train")
        df = ds.to_pandas()
        
        if subset_size:
            logger.info(f"Limiting dataset to {subset_size} rows")
            df = df.head(subset_size)
        
        return df
    except Exception as e:
        logger.error(f"Failed to load HuggingFace dataset: {e}")
        raise

def load_uci_data(subset_size: Optional[int] = None) -> pd.DataFrame:
    """
    Fallback to UCI dataset.
    Note: This is a fallback if HuggingFace is unavailable.
    """
    try:
        from ucimlrepo import fetch_ucirepo
        logger.info("Loading dataset from UCI (Fallback)")
        
        # The specific ID for SN1 reactions in UCI is not explicitly provided in the prompt,
        # but the task description mentions "UCI ucimlrepo SN subset".
        # We will attempt to fetch a generic reaction dataset or raise a clear error if not found.
        # For this implementation, we assume a hypothetical ID or raise NotImplementedError 
        # if the specific dataset ID is unknown, forcing a failure rather than a fake fallback.
        
        # Attempting to fetch a known reaction kinetics dataset if available, 
        # otherwise raising a clear error to prevent silent failure.
        # Since we cannot guess the ID safely without risking fabrication, 
        # we raise a specific error indicating the fallback requires a known ID.
        raise NotImplementedError(
            "UCI fallback requires a specific dataset ID which is not provided. "
            "Please ensure HuggingFace source 'chemistry/dts-sn1' is accessible."
        )
    except NotImplementedError:
        # Re-raise to fail loudly as per constraints
        raise
    except Exception as e:
        logger.error(f"Failed to load UCI dataset: {e}")
        raise

def map_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Map raw columns to standard schema and handle missing values.
    
    Returns:
        Tuple of (mapped DataFrame, list of exclusion dicts)
    """
    exclusions = []
    original_indices = df.index.tolist()
    
    # Identify SMILES column
    smiles_col = None
    for col in df.columns:
        if 'smiles' in col.lower() or 'sm' in col.lower():
            smiles_col = col
            break
    
    if not smiles_col:
        raise ValueError("No SMILES column found in dataset")
    
    # Identify rate column
    rate_col = None
    for col in df.columns:
        if 'rate' in col.lower():
            rate_col = col
            break
    
    if not rate_col:
        raise ValueError("No rate column found in dataset")
    
    # Identify substrate column
    substrate_col = None
    for col in df.columns:
        if 'substrate' in col.lower():
            substrate_col = col
            break
    
    # Create a copy to avoid modifying original
    df_mapped = df[[smiles_col, rate_col]].copy()
    if substrate_col:
        df_mapped['substrate'] = df[substrate_col]
    
    # Rename columns to standard schema
    df_mapped.rename(columns={
        smiles_col: 'smiles',
        rate_col: 'rate_constant'
    }, inplace=True)
    
    # Handle rate_constant: ensure numeric and absolute
    df_mapped['rate_constant'] = pd.to_numeric(df_mapped['rate_constant'], errors='coerce')
    df_mapped['rate_constant'] = df_mapped['rate_constant'].abs()
    
    # Handle missing rate constants
    missing_rate_mask = df_mapped['rate_constant'].isna()
    if missing_rate_mask.any():
        for idx in df_mapped[missing_rate_mask].index:
          exclusions.append({
              'row_index': original_indices.index(idx),
              'reason': 'missing_rate_constant',
              'original_smiles': df_mapped.loc[idx, 'smiles']
          })
    df_mapped = df_mapped.dropna(subset=['rate_constant'])
    
    # Handle substrate class
    if substrate_col:
        df_mapped['substrate_class'] = df_mapped['substrate'].astype(str).str.lower()
        df_mapped.drop(columns=['substrate'], inplace=True)
    else:
        # Default if not found, though task implies it exists
        df_mapped['substrate_class'] = 'unknown'
    
    # Handle missing smiles
    df_mapped = df_mapped[df_mapped['smiles'].notna() & (df_mapped['smiles'] != '')]
    
    # Select final columns
    return df_mapped[['smiles', 'rate_constant', 'substrate_class']], exclusions

def save_exclusion_report(exclusions: List[Dict], output_path: Path):
    """
    Save exclusion report to CSV.
    """
    if not exclusions:
        # Create empty file with headers
        pd.DataFrame(columns=['row_index', 'reason', 'original_smiles']).to_csv(output_path, index=False)
    else:
        df = pd.DataFrame(exclusions)
        df.to_csv(output_path, index=False)
    logger.info(f"Exclusion report saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Ingest SN1 data")
    parser.add_argument("--output", type=str, default="data/raw/sn1_raw.csv", help="Output path for raw CSV")
    parser.add_argument("--exclusion-output", type=str, default="data/processed/exclusion_report.csv", help="Output path for exclusion report")
    parser.add_argument("--subset", type=int, default=None, help="Limit number of rows for testing")
    args = parser.parse_args()

    ensure_dirs()
    
    # Try HuggingFace first
    df = None
    try:
        df = load_huggingface_data(subset_size=args.subset)
    except Exception as e:
        logger.warning(f"HuggingFace load failed: {e}. Attempting fallback...")
        try:
            df = load_uci_data(subset_size=args.subset)
        except Exception as e2:
            logger.critical(f"All data sources failed. HuggingFace: {e}, UCI: {e2}")
            raise SystemExit(1)
    
    if df is None or df.empty:
        logger.critical("No data loaded from any source.")
        raise SystemExit(1)
    
    # Map columns and handle missing values
    df_mapped, exclusions = map_columns(df)
    
    # Save raw data
    df_mapped.to_csv(args.output, index=False)
    logger.info(f"Raw data saved to {args.output} with {len(df_mapped)} rows")
    
    # Save exclusion report
    save_exclusion_report(exclusions, Path(args.exclusion_output))

if __name__ == "__main__":
    main()