import os
import sys
import logging
import argparse
import pandas as pd
from pathlib import Path
from config import ensure_dirs, DataConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def setup_mapping_logger(log_path: Path) -> logging.Logger:
    """Setup a logger that writes to a file and console."""
    ensure_dirs(log_path.parent)
    logger = logging.getLogger('mapping')
    logger.setLevel(logging.INFO)
    
    # File handler
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)
    
    return logger

def load_raw_data(input_path: Path, logger: logging.Logger) -> pd.DataFrame:
    """Load the raw merged parquet file."""
    logger.info(f"Loading raw data from {input_path}")
    if not input_path.exists():
        logger.error(f"Raw data file not found: {input_path}")
        raise FileNotFoundError(f"Raw data file not found: {input_path}")
    
    try:
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        raise

def map_columns(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """Map raw column names to standardized schema."""
    # Define mapping from raw columns to standard schema
    # Based on the dataset schema: smiles, rate_constant, substrate_class, 
    # gasteiger_charges, topological_indices, source_id
    # We assume the raw data has columns that need mapping.
    # Common raw column names might be: 'SMILES', 'Rate', 'Class', etc.
    
    # Let's assume a generic mapping strategy based on the schema
    # If the raw data already has the correct names, this is a no-op.
    # We'll create a new DataFrame with the standard column names.
    
    standard_columns = ['smiles', 'rate_constant', 'substrate_class', 'source_id']
    
    # Attempt to map common variations
    column_mapping = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if 'smiles' in col_lower:
            column_mapping[col] = 'smiles'
        elif 'rate' in col_lower or 'k' in col_lower:
            column_mapping[col] = 'rate_constant'
        elif 'class' in col_lower or 'substrate' in col_lower:
            column_mapping[col] = 'substrate_class'
        elif 'source' in col_lower or 'id' in col_lower:
            column_mapping[col] = 'source_id'
    
    # Apply mapping
    df_mapped = df.rename(columns=column_mapping)
    
    # Check for missing required columns
    missing = [c for c in standard_columns if c not in df_mapped.columns]
    if missing:
        logger.warning(f"Missing required columns after mapping: {missing}")
        # We proceed anyway, letting downstream tasks handle missing data
    
    logger.info(f"Mapped columns: {list(df_mapped.columns)}")
    return df_mapped

def clean_and_log_exclusions(df: pd.DataFrame, exclusion_log_path: Path, logger: logging.Logger) -> pd.DataFrame:
    """
    Clean data and log rows with missing rate/SMILES to exclusion log.
    Appends to existing log (created by T011d).
    """
    if not exclusion_log_path.exists():
        logger.error(f"Exclusion log not found: {exclusion_log_path}")
        raise FileNotFoundError(f"Exclusion log not found: {exclusion_log_path}. T011d must have created it.")
    
    exclusions = []
    valid_rows = []
    
    for idx, row in df.iterrows():
        is_excluded = False
        reason = None
        
        # Check for missing SMILES
        if pd.isna(row.get('smiles')) or str(row.get('smiles')).strip() == '':
            is_excluded = True
            reason = 'missing_smiles'
        
        # Check for missing rate constant
        elif pd.isna(row.get('rate_constant')):
            is_excluded = True
            reason = 'missing_rate_constant'
        
        if is_excluded:
            exclusions.append({
                'row_index': idx,
                'reason': reason,
                'original_smiles': row.get('smiles', '')
            })
            logger.debug(f"Excluding row {idx}: {reason}")
        else:
            valid_rows.append(row)
    
    # Append exclusions to log file
    if exclusions:
        exclusions_df = pd.DataFrame(exclusions)
        exclusions_df.to_csv(exclusion_log_path, mode='a', header=False, index=False)
        logger.info(f"Appended {len(exclusions)} exclusions to {exclusion_log_path}")
    
    if not valid_rows:
        logger.warning("No valid rows remaining after cleaning.")
        return pd.DataFrame(columns=df.columns)
    
    return pd.DataFrame(valid_rows)

def save_intermediate_dataset(df: pd.DataFrame, output_path: Path, logger: logging.Logger):
    """Save the intermediate cleaned dataset to CSV."""
    ensure_dirs(output_path.parent)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Map columns and clean initial SN1 data.')
    parser.add_argument('--input', type=str, required=True, help='Path to input raw parquet file')
    parser.add_argument('--output', type=str, required=True, help='Path to output intermediate CSV file')
    parser.add_argument('--exclusion-log', type=str, required=True, help='Path to exclusion log file')
    parser.add_argument('--log-file', type=str, default='data/processed/mapping.log', help='Path to mapping log file')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    exclusion_log_path = Path(args.exclusion_log)
    log_path = Path(args.log_file)
    
    logger = setup_mapping_logger(log_path)
    logger.info("Starting mapping and cleaning process...")
    
    try:
        # 1. Load raw data
        df = load_raw_data(input_path, logger)
        
        # 2. Map columns
        df_mapped = map_columns(df, logger)
        
        # 3. Clean and log exclusions
        df_clean = clean_and_log_exclusions(df_mapped, exclusion_log_path, logger)
        
        # 4. Save intermediate dataset
        save_intermediate_dataset(df_clean, output_path, logger)
        
        logger.info("Mapping and cleaning completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Mapping failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()