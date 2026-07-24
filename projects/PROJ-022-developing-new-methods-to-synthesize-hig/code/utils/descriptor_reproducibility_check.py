"""
Descriptor Reproducibility Check

This script re-calculates a random subset of molecular descriptors from the
standardized dataset and verifies bitwise equality with the values stored
in the feature matrix. This ensures the descriptor calculation pipeline
is deterministic and reproducible.

Required for T048 (Constitutional Principle VI).
"""

import os
import sys
import json
import logging
import hashlib
import random
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import setup_pipeline_logger
from utils.errors import DataInsufficientError, PipelineError
from features.calculate_descriptors import calculate_descriptors_for_smiles

# Constants
RANDOM_SEED = 42
SAMPLE_SIZE = 100  # Number of records to re-calculate and verify
FEATURE_MATRIX_PATH = "data/processed/feature_matrix.csv"
REPORT_PATH = "data/reports/descriptor_reproducibility_report.json"
RAW_DATA_PATH = "data/processed/standardized_polymers.csv"

logger = setup_pipeline_logger("descriptor_reproducibility_check")


def load_feature_matrix() -> pd.DataFrame:
    """Load the feature matrix containing calculated descriptors."""
    if not os.path.exists(FEATURE_MATRIX_PATH):
        raise DataInsufficientError(
            f"Feature matrix not found at {FEATURE_MATRIX_PATH}. "
            "Run T026 (save_feature_matrix) first."
        )
    df = pd.read_csv(FEATURE_MATRIX_PATH)
    logger.info(f"Loaded feature matrix with {len(df)} rows.")
    return df


def load_standardized_data() -> pd.DataFrame:
    """Load the standardized data containing SMILES strings."""
    if not os.path.exists(RAW_DATA_PATH):
        raise DataInsufficientError(
            f"Standardized data not found at {RAW_DATA_PATH}. "
            "Run T016 first."
        )
    df = pd.read_csv(RAW_DATA_PATH)
    logger.info(f"Loaded standardized data with {len(df)} rows.")
    return df


def select_random_subset(df: pd.DataFrame, n: int, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Select a random subset of rows for reproducibility check."""
    if len(df) < n:
        logger.warning(f"Dataset size ({len(df)}) is smaller than sample size ({n}). Using all rows.")
        return df.copy()
    
    random.seed(seed)
    np.random.seed(seed)
    sampled_df = df.sample(n=n, random_state=seed).reset_index(drop=True)
    logger.info(f"Selected {len(sampled_df)} random rows for verification.")
    return sampled_df


def re_calculate_descriptors(sampled_df: pd.DataFrame) -> pd.DataFrame:
    """Re-calculate descriptors for the sampled SMILES strings."""
    logger.info("Starting descriptor re-calculation...")
    
    calculated_data = []
    failed_indices = []
    
    for idx, row in sampled_df.iterrows():
        smiles = row.get('smiles')
        if not smiles or pd.isna(smiles):
            failed_indices.append(idx)
            continue
        
        try:
            # Re-calculate descriptors using the same function as the original pipeline
            descriptors = calculate_descriptors_for_smiles(smiles)
            calculated_data.append({
                'original_index': idx,
                'smiles': smiles,
                **descriptors
            })
        except Exception as e:
            logger.warning(f"Failed to calculate descriptors for SMILES at index {idx}: {e}")
            failed_indices.append(idx)
    
    if not calculated_data:
        raise PipelineError("No descriptors could be calculated. Check SMILES data validity.")
    
    calc_df = pd.DataFrame(calculated_data)
    logger.info(f"Successfully calculated descriptors for {len(calc_df)} rows.")
    return calc_df


def verify_bitwise_equality(
    original_df: pd.DataFrame, 
    recalculated_df: pd.DataFrame, 
    feature_columns: List[str]
) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify bitwise equality between original and recalculated descriptors.
    
    Returns:
        Tuple of (all_match: bool, details: dict)
    """
    mismatches = []
    match_count = 0
    total_checks = 0
    
    # Create a mapping from original_index in recalculated_df to rows in original_df
    # Note: original_df uses the original row index from the full dataset
    original_index_map = {row['original_index']: row for _, row in recalculated_df.iterrows()}
    
    for _, rec_row in recalculated_df.iterrows():
        orig_idx = rec_row['original_index']
        
        # Find corresponding row in original feature matrix
        # We need to find the row in original_df that corresponds to this index
        # Assuming original_df index matches the original row indices
        if orig_idx >= len(original_df):
            logger.warning(f"Original index {orig_idx} out of bounds for feature matrix.")
            continue
            
        orig_row = original_df.iloc[orig_idx]
        
        for col in feature_columns:
            total_checks += 1
            if col not in orig_row:
                logger.warning(f"Column {col} not found in original feature matrix.")
                continue
                
            orig_val = orig_row[col]
            rec_val = rec_row[col]
            
            # Handle NaN comparisons
            if pd.isna(orig_val) and pd.isna(rec_val):
                match_count += 1
                continue
            elif pd.isna(orig_val) or pd.isna(rec_val):
                mismatches.append({
                    'index': orig_idx,
                    'column': col,
                    'original': str(orig_val),
                    'recalculated': str(rec_val),
                    'reason': 'NaN mismatch'
                })
                continue
            
            # Numeric comparison with floating point tolerance for bitwise check
            # For true bitwise equality, we use exact equality for floats
            if isinstance(orig_val, (int, float)) and isinstance(rec_val, (int, float)):
                # Check for exact bitwise equality
                if orig_val != rec_val:
                    mismatches.append({
                        'index': orig_idx,
                        'column': col,
                        'original': orig_val,
                        'recalculated': rec_val,
                        'reason': 'Value mismatch'
                    })
                else:
                    match_count += 1
            else:
                # For non-numeric types, use string comparison
                if str(orig_val) != str(rec_val):
                    mismatches.append({
                        'index': orig_idx,
                        'column': col,
                        'original': str(orig_val),
                        'recalculated': str(rec_val),
                        'reason': 'Type/Value mismatch'
                    })
                else:
                    match_count += 1
    
    all_match = len(mismatches) == 0
    details = {
        'total_checks': total_checks,
        'match_count': match_count,
        'mismatch_count': len(mismatches),
        'match_rate': match_count / total_checks if total_checks > 0 else 0.0,
        'mismatches': mismatches[:10]  # Limit to first 10 mismatches for report
    }
    
    return all_match, details


def get_feature_columns(feature_df: pd.DataFrame) -> List[str]:
    """Identify descriptor columns in the feature matrix."""
    # Common descriptor names based on calculate_descriptors_for_smiles output
    known_descriptors = [
        'molecular_weight', 'vdw_volume', 'h_bond_donors', 'h_bond_acceptors',
        'logP', 'rotatable_bonds', 'polar_surface_area', 'aromatic_rings',
        'heavy_atom_count', 'ffv'
    ]
    
    # Filter columns that exist in the dataframe and match known descriptors
    feature_cols = [col for col in known_descriptors if col in feature_df.columns]
    
    if not feature_cols:
        # Fallback: assume columns starting with 'desc_' or containing common terms
        feature_cols = [col for col in feature_df.columns 
                       if 'weight' in col.lower() or 'volume' in col.lower() 
                       or 'bond' in col.lower() or 'h_bond' in col.lower()]
    
    if not feature_cols:
        raise PipelineError("Could not identify descriptor columns in feature matrix.")
    
    logger.info(f"Identified descriptor columns: {feature_cols}")
    return feature_cols


def generate_report(
    sample_size: int,
    all_match: bool,
    details: Dict[str, Any],
    failed_indices: List[int]
) -> Dict[str, Any]:
    """Generate the reproducibility check report."""
    report = {
        'status': 'passed' if all_match else 'failed',
        'sample_size': sample_size,
        'verification_timestamp': pd.Timestamp.now().isoformat(),
        'random_seed': RANDOM_SEED,
        'results': {
            'all_bitwise_equal': all_match,
            'total_checks': details['total_checks'],
            'match_count': details['match_count'],
            'mismatch_count': details['mismatch_count'],
            'match_rate': details['match_rate']
        },
        'mismatches': details['mismatches'],
        'failed_calculations': failed_indices,
        'files_verified': {
            'feature_matrix': FEATURE_MATRIX_PATH,
            'standardized_data': RAW_DATA_PATH
        }
    }
    return report


def save_report(report: Dict[str, Any], report_path: str):
    """Save the report to a JSON file."""
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved to {report_path}")


def main():
    """Main entry point for descriptor reproducibility check."""
    logger.info("Starting descriptor reproducibility check (T002d)...")
    
    try:
        # Load data
        feature_df = load_feature_matrix()
        standardized_df = load_standardized_data()
        
        # Select random subset
        sampled_standardized = select_random_subset(standardized_df, SAMPLE_SIZE)
        
        # Re-calculate descriptors
        recalculated_df = re_calculate_descriptors(sampled_standardized)
        
        # Identify feature columns
        feature_columns = get_feature_columns(feature_df)
        
        # Verify bitwise equality
        all_match, details = verify_bitwise_equality(
            feature_df, recalculated_df, feature_columns
        )
        
        # Generate and save report
        report = generate_report(
            len(sampled_standardized),
            all_match,
            details,
            recalculated_df[recalculated_df['smiles'].isna()]['original_index'].tolist()
        )
        save_report(report, REPORT_PATH)
        
        if all_match:
            logger.info("✅ Reproducibility check PASSED: All descriptors match bitwise.")
            return 0
        else:
            logger.error("❌ Reproducibility check FAILED: Mismatches detected.")
            logger.error(f"Details: {details}")
            return 1
            
    except DataInsufficientError as e:
        logger.error(f"Data insufficient: {e}")
        return 2
    except PipelineError as e:
        logger.error(f"Pipeline error: {e}")
        return 3
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 4


if __name__ == "__main__":
    sys.exit(main())