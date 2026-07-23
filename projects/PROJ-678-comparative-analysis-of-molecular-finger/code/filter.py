import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional
import os

from utils import setup_logging, get_logger
from constants import SMARTS_PATTERN

logger = get_logger(__name__)

def load_compounds(input_path: str) -> pd.DataFrame:
    """Load compounds from a CSV file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading compounds from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} compounds")
    return df

def apply_smarts_filter(df: pd.DataFrame, smarts: str = SMARTS_PATTERN) -> pd.DataFrame:
    """Apply SMARTS pattern filter to the dataframe."""
    logger.info(f"Applying SMARTS pattern: {smarts}")
    
    pattern = Chem.MolFromSmarts(smarts)
    if pattern is None:
        raise ValueError(f"Invalid SMARTS pattern: {smarts}")
    
    def matches_pattern(smiles: str) -> bool:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False
        return mol.HasSubstructMatch(pattern)
    
    # Log download size if available (from metadata or row count)
    total_rows = len(df)
    logger.info(f"Dataset download size (row count): {total_rows}")
    
    filtered_df = df[df['smiles'].apply(matches_pattern)]
    filter_count = len(filtered_df)
    
    logger.info(f"Filter counts: Original={total_rows}, Filtered={filter_count}, Removed={total_rows - filter_count}")
    
    return filtered_df

def validate_endpoints(df: pd.DataFrame, log_path: str) -> None:
    """Validate endpoint distributions and log results."""
    logger.info("Validating endpoint distributions")
    
    endpoint_cols = [col for col in df.columns if col.startswith('NR-')]
    if not endpoint_cols:
        # Fallback for different column naming if necessary, though Tox21 usually uses NR-
        endpoint_cols = [col for col in df.columns if col != 'smiles' and col != 'ID']
    
    log_lines = []
    log_lines.append(f"Validation Log - {datetime.now().isoformat()}")
    log_lines.append(f"Total rows: {len(df)}")
    log_lines.append("-" * 40)
    
    low_sample_warning = False
    
    for endpoint in endpoint_cols:
        if endpoint in df.columns:
            count = df[endpoint].notna().sum()
            log_lines.append(f"Endpoint: {endpoint} -> Count: {count}")
            if count < 50:
                log_lines.append(f"  WARNING: Low sample size ({count} < 50) for {endpoint}. Statistical tests skipped.")
                low_sample_warning = True
        else:
            log_lines.append(f"Endpoint: {endpoint} -> NOT FOUND")
    
    if low_sample_warning:
        log_lines.append("-" * 40)
        log_lines.append("LIMITATION: Some endpoints have < 50 samples. Statistical significance cannot be guaranteed.")
    
    # Write to log file
    log_path_obj = Path(log_path)
    log_path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path_obj, 'w') as f:
        f.write('\n'.join(log_lines))
    
    logger.info(f"Validation log written to {log_path}")

def save_filtered_data(df: pd.DataFrame, output_path: str, log_path: str) -> None:
    """Save filtered data and update log."""
    logger.info(f"Saving filtered data to {output_path}")
    
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")
    
    # Update log with endpoint distribution
    validate_endpoints(df, log_path)

def main():
    """Main entry point for filtering."""
    setup_logging()
    
    input_path = "data/raw/tox21.csv" # Expected path from download.py
    output_path = "data/processed/organophosphates_filtered.csv"
    log_path = "data/processed/filter_log.txt"
    
    # Check if input exists (if download.py hasn't run yet, this will fail loudly)
    if not os.path.exists(input_path):
        logger.error(f"Input file {input_path} not found. Please run download.py first.")
        raise FileNotFoundError(f"Input file {input_path} not found")
    
    try:
        df = load_compounds(input_path)
        filtered_df = apply_smarts_filter(df)
        save_filtered_data(filtered_df, output_path, log_path)
        logger.info("Filtering completed successfully")
    except Exception as e:
        logger.error(f"Filtering failed: {e}")
        raise

if __name__ == "__main__":
    main()
