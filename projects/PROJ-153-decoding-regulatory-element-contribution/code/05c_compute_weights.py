"""
T013c: Compute weights for CREs and apply them to delta peak signal.

This script implements FR-015:
1. Join validation flags (motif/Hi-C) and VIF flags.
2. Exclude collinear CREs (VIF > 5).
3. Compute weights based on validation source.
4. Apply weights to delta peak signal.
5. Output weighted delta peak signal to data/processed/weights.tsv.
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)

def load_cre_validation_flags(filepath: str) -> pd.DataFrame:
    """
    Load CRE validation flags from T013a output.
    Expected columns: cre_id, motif_validated, hic_validated, validation_score
    """
    logger.info(f"Loading CRE validation flags from {filepath}")
    df = pd.read_csv(filepath, sep='\t')
    
    required_cols = {'cre_id', 'motif_validated', 'hic_validated', 'validation_score'}
    if not required_cols.issubset(set(df.columns)):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns in validation flags: {missing}")
    
    # Ensure boolean columns are properly typed
    df['motif_validated'] = df['motif_validated'].astype(bool)
    df['hic_validated'] = df['hic_validated'].astype(bool)
    
    logger.info(f"Loaded {len(df)} CREs with validation flags")
    return df

def load_vif_flags(filepath: str) -> pd.DataFrame:
    """
    Load VIF flags from T013b output.
    Expected columns: cre_id, vif_score, is_collinear
    """
    logger.info(f"Loading VIF flags from {filepath}")
    df = pd.read_csv(filepath, sep='\t')
    
    required_cols = {'cre_id', 'vif_score', 'is_collinear'}
    if not required_cols.issubset(set(df.columns)):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns in VIF flags: {missing}")
    
    df['is_collinear'] = df['is_collinear'].astype(bool)
    
    logger.info(f"Loaded {len(df)} CREs with VIF scores")
    return df

def load_delta_peak_signal(filepath: str) -> pd.DataFrame:
    """
    Load delta peak signal from T043 output.
    Expected columns: cre_id, gene_id, delta_signal (or similar)
    """
    logger.info(f"Loading delta peak signal from {filepath}")
    df = pd.read_csv(filepath, sep='\t')
    
    # Check for required columns
    if 'cre_id' not in df.columns:
        raise ValueError("Missing 'cre_id' column in delta peak signal file")
    
    # Identify the signal column (could be 'delta_signal', 'signal', etc.)
    signal_cols = [col for col in df.columns if 'signal' in col.lower() and col != 'cre_id']
    if not signal_cols:
        raise ValueError("No signal column found in delta peak signal file")
    
    # Use the first matching signal column
    signal_col = signal_cols[0]
    logger.info(f"Using signal column: {signal_col}")
    
    logger.info(f"Loaded {len(df)} delta peak signal entries")
    return df, signal_col

def compute_weights_and_apply(
    validation_df: pd.DataFrame,
    vif_df: pd.DataFrame,
    delta_df: pd.DataFrame,
    signal_col: str
) -> pd.DataFrame:
    """
    Join datasets, filter collinear CREs, compute weights, and apply to delta signal.
    
    Weight logic (FR-015):
    - If motif_validated is true: weight = -log10(motif_score)
    - Else if hic_validated is true: weight = log10(hi_c_score + 1)
    - Else: exclude
    """
    logger.info("Joining validation, VIF, and delta signal datasets")
    
    # Merge validation and VIF flags on cre_id
    merged_df = pd.merge(
        validation_df,
        vif_df,
        on='cre_id',
        how='inner',
        suffixes=('_val', '_vif')
    )
    logger.info(f"After join with VIF: {len(merged_df)} CREs")
    
    # Exclude collinear CREs (VIF > 5)
    non_collinear_df = merged_df[~merged_df['is_collinear']].copy()
    excluded_collinear = len(merged_df) - len(non_collinear_df)
    logger.info(f"Excluded {excluded_collinear} collinear CREs (VIF > 5)")
    
    # Merge with delta signal
    final_df = pd.merge(
        non_collinear_df,
        delta_df[['cre_id', 'gene_id', signal_col]],
        on='cre_id',
        how='inner'
    )
    logger.info(f"After join with delta signal: {len(final_df)} CREs")
    
    # Compute weights and apply
    def compute_weight(row):
        motif_validated = row['motif_validated']
        hic_validated = row['hic_validated']
        validation_score = row['validation_score']
        
        if motif_validated:
            # Weight = -log10(motif_score)
            # Ensure validation_score is positive (motif p-value)
            if validation_score <= 0:
                return None, 'invalid_motif_score'
            weight = -np.log10(validation_score)
            return weight, 'motif'
        elif hic_validated:
            # Weight = log10(hi_c_score + 1)
            weight = np.log10(validation_score + 1)
            return weight, 'hic'
        else:
            return None, 'no_validation'
    
    # Apply weight computation
    weight_results = final_df.apply(compute_weight, axis=1)
    final_df['weight'] = [w[0] for w in weight_results]
    final_df['weight_source'] = [w[1] for w in weight_results]
    
    # Filter out CREs without valid weights
    valid_weights_df = final_df[final_df['weight'].notna()].copy()
    excluded_no_weight = len(final_df) - len(valid_weights_df)
    logger.info(f"Excluded {excluded_no_weight} CREs with no valid weight")
    
    # Compute weighted delta signal
    valid_weights_df['weighted_delta_peak_signal'] = (
        valid_weights_df['weight'] * valid_weights_df[signal_col]
    )
    
    # Select output columns
    output_df = valid_weights_df[[
        'cre_id', 
        'gene_id', 
        'weighted_delta_peak_signal', 
        'weight_source'
    ]].copy()
    
    logger.info(f"Final output: {len(output_df)} weighted CREs")
    return output_df

def write_output(df: pd.DataFrame, filepath: str):
    """Write the weighted delta peak signal to TSV file."""
    logger.info(f"Writing output to {filepath}")
    df.to_csv(filepath, sep='\t', index=False)
    logger.info(f"Successfully wrote {len(df)} rows to {filepath}")

def main():
    parser = argparse.ArgumentParser(
        description='Compute weights for CREs and apply to delta peak signal (T013c)'
    )
    parser.add_argument(
        '--validation-flags',
        type=str,
        default='data/processed/cre_validation_flags.tsv',
        help='Path to CRE validation flags from T013a'
    )
    parser.add_argument(
        '--vif-flags',
        type=str,
        default='data/processed/vif_flags.tsv',
        help='Path to VIF flags from T013b'
    )
    parser.add_argument(
        '--delta-signal',
        type=str,
        default='data/processed/delta_peak_signal.tsv',
        help='Path to delta peak signal from T043'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed/weights.tsv',
        help='Path for output weights file'
    )
    
    args = parser.parse_args()
    
    # Validate input files exist
    input_files = [
        args.validation_flags,
        args.vif_flags,
        args.delta_signal
    ]
    
    for filepath in input_files:
        if not os.path.exists(filepath):
            logger.error(f"Input file not found: {filepath}")
            sys.exit(1)
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        validation_df = load_cre_validation_flags(args.validation_flags)
        vif_df = load_vif_flags(args.vif_flags)
        delta_df, signal_col = load_delta_peak_signal(args.delta_signal)
        
        # Compute weights and apply
        weighted_df = compute_weights_and_apply(
            validation_df,
            vif_df,
            delta_df,
            signal_col
        )
        
        # Write output
        write_output(weighted_df, args.output)
        
        logger.info("T013c completed successfully")
        
    except Exception as e:
        logger.error(f"Error during weight computation: {e}")
        raise

if __name__ == '__main__':
    main()