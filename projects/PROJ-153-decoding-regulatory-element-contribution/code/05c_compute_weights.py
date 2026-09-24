"""
T013c: Compute CRE weights based on validation flags and apply to delta peak signal.

This script implements the core weighting logic for User Story 1:
1. Joins motif, Hi-C, and VIF validation flags.
2. Filters CREs based on inclusive OR of motif/Hi-C validation and excludes collinear CREs.
3. Computes weights: -log10(motif_score) if motif validated, else log10(hic_score + 1) if Hi-C validated.
4. Applies weights to delta peak signal.
5. Outputs the final weighted signal table.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_cre_validation_flags(motif_path: str, hic_path: str) -> pd.DataFrame:
    """
    Load and join motif and Hi-C validation flags.
    
    Args:
        motif_path: Path to motif_validation_flags.tsv
        hic_path: Path to hic_validation_flags.tsv
        
    Returns:
        DataFrame with merged validation flags.
    """
    logger.info(f"Loading motif validation flags from {motif_path}")
    if not os.path.exists(motif_path):
        raise FileNotFoundError(f"Motif validation file not found: {motif_path}")
    df_motif = pd.read_csv(motif_path, sep='\t')
    
    logger.info(f"Loading Hi-C validation flags from {hic_path}")
    if not os.path.exists(hic_path):
        raise FileNotFoundError(f"Hi-C validation file not found: {hic_path}")
    df_hic = pd.read_csv(hic_path, sep='\t')
    
    # Merge on cre_id using outer join to see all CREs first
    # Then we will filter based on logic
    df_merged = pd.merge(
        df_motif[['cre_id', 'motif_validated', 'motif_score']],
        df_hic[['cre_id', 'hic_validated', 'hic_score']],
        on='cre_id',
        how='outer'
    )
    
    # Fill missing values with False/0.0 for boolean/numeric logic
    df_merged['motif_validated'] = df_merged['motif_validated'].fillna(False).astype(bool)
    df_merged['hic_validated'] = df_merged['hic_validated'].fillna(False).astype(bool)
    df_merged['motif_score'] = df_merged['motif_score'].fillna(1.0) # Default to non-significant if missing
    df_merged['hic_score'] = df_merged['hic_score'].fillna(0.0)
    
    return df_merged

def load_vif_flags(vif_path: str) -> pd.DataFrame:
    """
    Load VIF flags.
    
    Args:
        vif_path: Path to vif_flags.tsv
        
    Returns:
        DataFrame with VIF flags.
    """
    logger.info(f"Loading VIF flags from {vif_path}")
    if not os.path.exists(vif_path):
        raise FileNotFoundError(f"VIF flags file not found: {vif_path}")
    df_vif = pd.read_csv(vif_path, sep='\t')
    return df_vif[['cre_id', 'vif_score', 'is_collinear']]

def load_delta_peak_signal(delta_path: str) -> pd.DataFrame:
    """
    Load delta peak signal.
    
    Args:
        delta_path: Path to delta_peak_signal.tsv
        
    Returns:
        DataFrame with delta peak signal.
    """
    logger.info(f"Loading delta peak signal from {delta_path}")
    if not os.path.exists(delta_path):
        raise FileNotFoundError(f"Delta peak signal file not found: {delta_path}")
    df_delta = pd.read_csv(delta_path, sep='\t')
    return df_delta[['cre_id', 'gene_id', 'delta_peak_signal']]

def compute_weights_and_apply(
    df_flags: pd.DataFrame,
    df_vif: pd.DataFrame,
    df_delta: pd.DataFrame
) -> pd.DataFrame:
    """
    Apply filtering and weighting logic.
    
    Logic:
    1. Retain CRE if (motif_validated OR hic_validated) is TRUE.
    2. Exclude if is_collinear is TRUE.
    3. Compute weight:
       - if motif_validated: weight = -log10(motif_score)
       - else if hic_validated: weight = log10(hic_score + 1)
       - else: exclude (should not happen due to step 1)
    4. Apply weight to delta_peak_signal.
    
    Args:
        df_flags: Merged motif/Hi-C flags
        df_vif: VIF flags
        df_delta: Delta peak signal
        
    Returns:
        DataFrame with weighted delta peak signal.
    """
    logger.info("Applying filtering and weighting logic...")
    
    # Join all data on cre_id
    df_combined = pd.merge(df_flags, df_vif, on='cre_id', how='inner')
    df_combined = pd.merge(df_combined, df_delta, on='cre_id', how='inner')
    
    # Step 1: Filter for (motif_validated OR hic_validated)
    mask_validated = df_combined['motif_validated'] | df_combined['hic_validated']
    df_filtered = df_combined[mask_validated].copy()
    logger.info(f"Filtered to {len(df_filtered)} CREs with valid motif OR Hi-C evidence.")
    
    if len(df_filtered) == 0:
        logger.warning("No CREs passed validation. Output will be empty.")
        return pd.DataFrame(columns=['cre_id', 'gene_id', 'weighted_delta_peak_signal', 'weight_source'])

    # Step 2: Exclude collinear CREs
    mask_collinear = ~df_filtered['is_collinear']
    df_final = df_filtered[mask_collinear].copy()
    excluded_collinear = len(df_filtered) - len(df_final)
    logger.info(f"Excluded {excluded_collinear} collinear CREs. Remaining: {len(df_final)}")
    
    if len(df_final) == 0:
        logger.warning("No CREs remained after excluding collinear ones. Output will be empty.")
        return pd.DataFrame(columns=['cre_id', 'gene_id', 'weighted_delta_peak_signal', 'weight_source'])

    # Step 3 & 4: Compute weights and apply
    def calculate_weight(row):
        if row['motif_validated']:
            # Avoid log10(0) or log10(negative) if score is weird, though score should be p-value < 1
            score = row['motif_score']
            if score <= 0:
                score = 1e-300 # Fallback to avoid log domain error, though p-values should be > 0
            weight = -np.log10(score)
            return weight, 'motif'
        elif row['hic_validated']:
            score = row['hic_score']
            weight = np.log10(score + 1)
            return weight, 'hic'
        else:
            # Should not be reached due to mask_validated
            return 0.0, 'none'

    weights_sources = df_final.apply(calculate_weight, axis=1)
    df_final['weight'] = [w[0] for w in weights_sources]
    df_final['weight_source'] = [w[1] for w in weights_sources]
    
    df_final['weighted_delta_peak_signal'] = df_final['delta_peak_signal'] * df_final['weight']
    
    # Select output columns
    df_output = df_final[['cre_id', 'gene_id', 'weighted_delta_peak_signal', 'weight_source']]
    
    logger.info(f"Computed weights for {len(df_output)} CREs.")
    return df_output

def write_output(df: pd.DataFrame, output_path: str):
    """
    Write the final weighted table to disk.
    
    Args:
        df: DataFrame to write
        output_path: Path to output file
    """
    logger.info(f"Writing output to {output_path}")
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    df.to_csv(output_path, sep='\t', index=False)
    logger.info("Output written successfully.")

def main():
    parser = argparse.ArgumentParser(description='Compute CRE weights and apply to delta signal.')
    parser.add_argument('--motif-flags', type=str, required=True, help='Path to motif_validation_flags.tsv')
    parser.add_argument('--hic-flags', type=str, required=True, help='Path to hic_validation_flags.tsv')
    parser.add_argument('--vif-flags', type=str, required=True, help='Path to vif_flags.tsv')
    parser.add_argument('--delta-signal', type=str, required=True, help='Path to delta_peak_signal.tsv')
    parser.add_argument('--output', type=str, required=True, help='Path to output weights.tsv')
    
    args = parser.parse_args()
    
    try:
        # Load data
        df_flags = load_cre_validation_flags(args.motif_flags, args.hic_flags)
        df_vif = load_vif_flags(args.vif_flags)
        df_delta = load_delta_peak_signal(args.delta_signal)
        
        # Process
        df_result = compute_weights_and_apply(df_flags, df_vif, df_delta)
        
        # Write
        write_output(df_result, args.output)
        
        logger.info("Task T013c completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
