"""
Compute Delta Peak Signal (ΔPeakSignal) for CREs.

This script calculates the difference between the signal in regulatory elements (CREs)
and the signal in null regions (distal background). This metric is used to normalize
CRE signal against local genomic background.

Inputs:
    - data/processed/CRE_merged.bed: Merged CRE annotations with signal columns
    - data/processed/null_region_signal.bed: Null region signal measurements

Output:
    - data/processed/delta_peak_signal.tsv: Table of CRE signals, null signals, and delta
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_bed_line(line: str) -> Dict:
    """
    Parse a BED line into a dictionary.
    
    Args:
        line: A single line from a BED file (tab-separated)
        
    Returns:
        Dictionary with keys: chrom, start, end, name, score, strand, etc.
    """
    parts = line.strip().split('\t')
    if len(parts) < 4:
        raise ValueError(f"Invalid BED line (expected >= 4 fields): {line}")
    
    result = {
        'chrom': parts[0],
        'start': int(parts[1]),
        'end': int(parts[2]),
        'name': parts[3] if len(parts) > 3 else None,
    }
    
    # Optional fields
    if len(parts) > 4:
        result['score'] = parts[4]
    if len(parts) > 5:
        result['strand'] = parts[5]
    if len(parts) > 6:
        result['thickStart'] = parts[6]
    if len(parts) > 7:
        result['thickEnd'] = parts[7]
    if len(parts) > 8:
        result['itemRgb'] = parts[8]
    if len(parts) > 9:
        result['blockCount'] = parts[9]
    if len(parts) > 10:
        result['blockSizes'] = parts[10]
    if len(parts) > 11:
        result['blockStarts'] = parts[11]
        
    return result


def load_cre_signal(cre_file: Path) -> pd.DataFrame:
    """
    Load CRE signal data from the merged CRE BED file.
    
    Expected columns in CRE_merged.bed (after processing):
        - chrom, start, end, name (cre_id)
        - Additional columns: signal values per TF/condition
        
    Args:
        cre_file: Path to data/processed/CRE_merged.bed
        
    Returns:
        DataFrame with CRE signal data
    """
    if not cre_file.exists():
        raise FileNotFoundError(f"CRE signal file not found: {cre_file}")
    
    logger.info(f"Loading CRE signal data from {cre_file}")
    
    # Try to read as BED with potential extra columns
    # First, try to detect if there's a header
    with open(cre_file, 'r') as f:
        first_line = f.readline()
        
    # Check if first line looks like a header (contains non-integer in position 1,2)
    parts = first_line.strip().split('\t')
    has_header = False
    try:
        int(parts[1])
        int(parts[2])
    except ValueError:
        has_header = True
    
    # Read the file
    if has_header:
        df = pd.read_csv(cre_file, sep='\t', header=0)
    else:
        df = pd.read_csv(cre_file, sep='\t', header=None, 
                       names=['chrom', 'start', 'end', 'cre_id'] + 
                             [f'col{i}' for i in range(4, 100)])
        
        # Clean up column names - keep only those that look like signal values
        # or standard BED columns
        signal_cols = []
        for col in df.columns:
            if col in ['chrom', 'start', 'end', 'cre_id']:
                continue
            # Check if column name is numeric or looks like a signal column
            try:
                float(df[col].iloc[0])
                signal_cols.append(col)
            except (ValueError, TypeError):
                pass
        
        # Keep cre_id and signal columns
        if signal_cols:
            df = df[['cre_id'] + signal_cols]
        else:
            # If no signal columns found, assume all columns after cre_id are signals
            df = df[['cre_id'] + [col for col in df.columns if col != 'cre_id']]
    
    # Validate required columns
    if 'cre_id' not in df.columns:
        raise ValueError("CRE signal file must contain 'cre_id' column")
        
    logger.info(f"Loaded {len(df)} CREs with {len(df.columns) - 1} signal columns")
    return df


def load_null_signal(null_file: Path) -> pd.DataFrame:
    """
    Load null region signal data from the null region BED file.
    
    Expected columns in null_region_signal.bed:
        - chrom, start, end, name (region_id or similar identifier)
        - Signal values (e.g., mean_signal, or per-condition signals)
        
    Args:
        null_file: Path to data/processed/null_region_signal.bed
        
    Returns:
        DataFrame with null region signal data
    """
    if not null_file.exists():
        raise FileNotFoundError(f"Null signal file not found: {null_file}")
    
    logger.info(f"Loading null signal data from {null_file}")
    
    # Read the file
    with open(null_file, 'r') as f:
        first_line = f.readline()
        
    parts = first_line.strip().split('\t')
    has_header = False
    try:
        int(parts[1])
        int(parts[2])
    except ValueError:
        has_header = True
    
    if has_header:
        df = pd.read_csv(null_file, sep='\t', header=0)
    else:
        df = pd.read_csv(null_file, sep='\t', header=None,
                       names=['chrom', 'start', 'end', 'region_id'] +
                             [f'col{i}' for i in range(4, 100)])
        
        # Identify signal columns
        signal_cols = []
        for col in df.columns:
            if col in ['chrom', 'start', 'end', 'region_id']:
                continue
            try:
                float(df[col].iloc[0])
                signal_cols.append(col)
            except (ValueError, TypeError):
                pass
        
        if signal_cols:
            df = df[['region_id'] + signal_cols]
        else:
            df = df[['region_id'] + [col for col in df.columns if col != 'region_id']]
    
    # Determine the ID column name
    id_col = 'region_id' if 'region_id' in df.columns else df.columns[3]
    
    # Rename to standard 'cre_id' for joining
    df = df.rename(columns={id_col: 'cre_id'})
    
    logger.info(f"Loaded {len(df)} null regions")
    return df


def compute_delta_signal(cre_df: pd.DataFrame, null_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Delta Peak Signal (ΔPeakSignal) = CRE signal - null signal.
    
    This function joins CRE signals with null signals and computes the difference.
    For multiple signal columns, it computes the delta for each.
    
    Args:
        cre_df: DataFrame with CRE signal data
        null_df: DataFrame with null region signal data
        
    Returns:
        DataFrame with cre_id, signal columns, null columns, and delta columns
    """
    if cre_df.empty or null_df.empty:
        raise ValueError("Input dataframes cannot be empty")
    
    # Merge on cre_id
    # Note: This assumes cre_id in null_df represents the matched null region for each CRE
    merged = cre_df.merge(null_df, on='cre_id', how='left', suffixes=('_cre', '_null'))
    
    if merged.empty:
        logger.warning("No matching CREs found between CRE and null signal files")
        # Return CRE data with NaN for null and delta
        merged = cre_df.copy()
        for col in cre_df.columns:
            if col != 'cre_id':
                merged[f'{col}_null'] = np.nan
                merged[f'{col}_delta'] = np.nan
        return merged
    
    # Identify signal columns (non-ID columns)
    signal_cols = [col for col in cre_df.columns if col != 'cre_id']
    
    # Compute delta for each signal column
    for col in signal_cols:
        cre_col = f'{col}_cre'
        null_col = f'{col}_null'
        delta_col = f'{col}_delta'
        
        # Ensure columns exist
        if cre_col in merged.columns and null_col in merged.columns:
            merged[delta_col] = merged[cre_col] - merged[null_col]
        else:
            # If merge didn't create expected columns, handle gracefully
            if col in merged.columns:
                merged[delta_col] = merged[col] - merged.get(null_col, np.nan)
    
    logger.info(f"Computed delta signal for {len(signal_cols)} signal columns")
    logger.info(f"Resulting dataframe has {len(merged)} rows")
    
    return merged


def write_output(df: pd.DataFrame, output_file: Path) -> None:
    """
    Write the delta signal dataframe to a TSV file.
    
    Args:
        df: DataFrame with delta signal results
        output_file: Path to output file
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing output to {output_file}")
    df.to_csv(output_file, sep='\t', index=False)
    
    logger.info(f"Successfully wrote {len(df)} rows to {output_file}")


def main():
    """Main entry point for delta signal computation."""
    parser = argparse.ArgumentParser(
        description='Compute Delta Peak Signal (ΔPeakSignal) for CREs'
    )
    parser.add_argument(
        '--cre-file',
        type=Path,
        default=Path('data/processed/CRE_merged.bed'),
        help='Path to CRE merged BED file with signal data'
    )
    parser.add_argument(
        '--null-file',
        type=Path,
        default=Path('data/processed/null_region_signal.bed'),
        help='Path to null region signal BED file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/processed/delta_peak_signal.tsv'),
        help='Path to output delta signal TSV file'
    )
    
    args = parser.parse_args()
    
    try:
        # Load data
        cre_df = load_cre_signal(args.cre_file)
        null_df = load_null_signal(args.null_file)
        
        # Compute delta signal
        delta_df = compute_delta_signal(cre_df, null_df)
        
        # Write output
        write_output(delta_df, args.output)
        
        logger.info("Delta signal computation completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
