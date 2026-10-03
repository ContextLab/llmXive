import os
import sys
import logging
import argparse
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs, DataConfig
from utils.logger import get_logger

logger = get_logger(__name__)

def setup_mapping_logger():
    """Setup logging for mapping process."""
    return get_logger(__name__)

def load_raw_data(file_path: str):
    """Load raw data from parquet file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Raw data file not found: {file_path}")
    return pd.read_parquet(file_path)

def map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map columns to standard names."""
    mapping = {
        'smiles': 'smiles',
        'rate': 'rate_constant',
        'substrate_class': 'substrate_class',
        'temperature': 'temperature',
        'solvent': 'solvent'
    }
    
    # Filter to only existing columns
    existing_mapping = {k: v for k, v in mapping.items() if k in df.columns}
    df = df.rename(columns=existing_mapping)
    
    return df

def clean_and_log_exclusions(df: pd.DataFrame, exclusion_log_path: str):
    """Clean data and log exclusions."""
    exclusions = []
    
    # Check for missing rate_constant or smiles
    for idx, row in df.iterrows():
        rate_val = row.get('rate_constant')
        smiles_val = row.get('smiles')
        
        if pd.isna(rate_val):
            exclusions.append({
                'row_index': idx,
                'reason': 'Missing rate constant',
                'original_smiles': str(smiles_val) if smiles_val is not None else ''
            })
        elif pd.isna(smiles_val) or str(smiles_val).strip() == '':
            exclusions.append({
                'row_index': idx,
                'reason': 'Missing SMILES',
                'original_smiles': ''
            })
    
    # Remove excluded rows
    mask = df['rate_constant'].notna() & df['smiles'].notna() & (df['smiles'].astype(str).str.strip() != '')
    cleaned_df = df[mask].reset_index(drop=True)
    
    # Log exclusions
    if exclusions:
        exclusion_df = pd.DataFrame(exclusions)
        # Ensure header is written only if file is new, otherwise append
        file_exists = os.path.exists(exclusion_log_path)
        exclusion_df.to_csv(exclusion_log_path, mode='a', header=not file_exists, index=False)
        logger.info(f"Logged {len(exclusions)} exclusions to {exclusion_log_path}")
    
    return cleaned_df

def save_intermediate_dataset(df: pd.DataFrame, output_path: str):
    """Save intermediate dataset to CSV."""
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Intermediate dataset saved to {output_path} ({len(df)} rows)")

def main():
    parser = argparse.ArgumentParser(description="Map and clean raw data")
    parser.add_argument("--input", type=str, default="data/raw/sn1_raw.parquet", help="Input file path")
    parser.add_argument("--output", type=str, default="data/processed/intermediate_sn1.csv", help="Output file path")
    parser.add_argument("--exclusion-log", type=str, default="data/processed/exclusion_raw.log", help="Exclusion log path")
    args = parser.parse_args()

    ensure_dirs()
    
    # Guard Clause: Check if exclusion log exists
    if not os.path.exists(args.exclusion_log):
        logger.error(f"Exclusion log not found: {args.exclusion_log}. T011d must run first.")
        sys.exit(1)
    
    try:
        # Load raw data
        df = load_raw_data(args.input)
        logger.info(f"Loaded {len(df)} rows from {args.input}")
        
        # Map columns
        df = map_columns(df)
        logger.info(f"Mapped columns")
        
        # Clean and log exclusions
        cleaned_df = clean_and_log_exclusions(df, args.exclusion_log)
        logger.info(f"Cleaned data: {len(cleaned_df)} rows remaining")
        
        # Save intermediate dataset
        save_intermediate_dataset(cleaned_df, args.output)
        
    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Mapping failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()