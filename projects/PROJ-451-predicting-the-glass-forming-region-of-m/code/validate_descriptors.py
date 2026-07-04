"""
Validation script for descriptor completeness in the engineered dataset.

This script ensures that >=95% of descriptors are present for each composition
and drops compositions with missing elemental properties.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_data_path, ensure_data_directories
from features.descriptors import compute_all_descriptors, get_element_properties

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the expected descriptors based on T012
EXPECTED_DESCRIPTORS = [
    'atomic_radius',
    'electronegativity',
    'valence_electron_concentration',
    'atomic_size_mismatch',
    'mixing_enthalpy',
    'atomic_size_difference',
    'valence_electron_size_mismatch',
    'electron_atom_ratio',
    'miedema_heat_of_formation',
    'atomic_packing_factor'
]

def load_engineered_dataset(data_path: str) -> pd.DataFrame:
    """Load the engineered dataset from CSV."""
    input_file = Path(data_path) / "processed" / "engineered_dataset.csv"
    
    if not input_file.exists():
        raise FileNotFoundError(f"Engineered dataset not found at {input_file}")
    
    logger.info(f"Loading dataset from {input_file}")
    df = pd.read_csv(input_file)
    logger.info(f"Loaded {len(df)} compositions with columns: {list(df.columns)}")
    return df

def validate_descriptor_completeness(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validate descriptor completeness and drop compositions with missing properties.
    
    Args:
        df: DataFrame with composition data and descriptors
        
    Returns:
        Tuple of (cleaned DataFrame, validation statistics)
    """
    logger.info("Validating descriptor completeness...")
    
    # Check which descriptor columns exist
    existing_descriptors = [col for col in EXPECTED_DESCRIPTORS if col in df.columns]
    missing_descriptors = [col for col in EXPECTED_DESCRIPTORS if col not in df.columns]
    
    if missing_descriptors:
        logger.warning(f"Missing descriptor columns: {missing_descriptors}")
        # If descriptors are missing, we can't validate completeness properly
        # But we should still check for NaN values in existing descriptor columns
        logger.info("Using only existing descriptor columns for completeness check")
    
    # Use existing descriptor columns for validation
    descriptor_cols = existing_descriptors if existing_descriptors else EXPECTED_DESCRIPTORS
    
    # Calculate completeness for each row
    # A row is complete if it has non-null values for all descriptor columns
    completeness_stats = {}
    
    for col in descriptor_cols:
        if col in df.columns:
            non_null_count = df[col].notna().sum()
            total_count = len(df)
            completeness_pct = (non_null_count / total_count) * 100 if total_count > 0 else 0
            completeness_stats[col] = {
                'non_null': int(non_null_count),
                'total': int(total_count),
                'completeness_pct': round(completeness_pct, 2)
            }
        else:
            completeness_stats[col] = {
                'non_null': 0,
                'total': len(df),
                'completeness_pct': 0.0
            }
    
    # Calculate row-wise completeness (percentage of descriptors present per row)
    if descriptor_cols:
        df['descriptor_completeness'] = df[descriptor_cols].notna().sum(axis=1) / len(descriptor_cols) * 100
    else:
        df['descriptor_completeness'] = 0.0
    
    # Check overall dataset completeness
    total_rows = len(df)
    if total_rows > 0:
        avg_completeness = df['descriptor_completeness'].mean()
        rows_above_95 = (df['descriptor_completeness'] >= 95.0).sum()
        rows_below_95 = total_rows - rows_above_95
        
        completeness_stats['overall'] = {
            'total_rows': int(total_rows),
            'avg_completeness_pct': round(avg_completeness, 2),
            'rows_above_95_pct': int(rows_above_95),
            'rows_below_95_pct': int(rows_below_95),
            'completeness_threshold_met': avg_completeness >= 95.0
        }
    else:
        completeness_stats['overall'] = {
            'total_rows': 0,
            'avg_completeness_pct': 0.0,
            'rows_above_95_pct': 0,
            'rows_below_95_pct': 0,
            'completeness_threshold_met': False
        }
    
    logger.info(f"Average descriptor completeness: {completeness_stats['overall']['avg_completeness_pct']}%")
    logger.info(f"Rows meeting >=95% completeness: {completeness_stats['overall']['rows_above_95_pct']}")
    
    # Drop rows with <95% descriptor completeness
    df_cleaned = df[df['descriptor_completeness'] >= 95.0].copy()
    
    # Also drop rows with any NaN in the descriptor columns (stricter check)
    if descriptor_cols:
        initial_count = len(df_cleaned)
        df_cleaned = df_cleaned.dropna(subset=descriptor_cols)
        dropped_count = initial_count - len(df_cleaned)
        if dropped_count > 0:
            logger.info(f"Dropped {dropped_count} rows with NaN values in descriptor columns")
    
    # Clean up temporary column
    if 'descriptor_completeness' in df_cleaned.columns:
        df_cleaned = df_cleaned.drop(columns=['descriptor_completeness'])
    
    completeness_stats['final'] = {
        'initial_rows': int(total_rows),
        'final_rows': int(len(df_cleaned)),
        'rows_dropped': int(total_rows - len(df_cleaned))
    }
    
    logger.info(f"Final dataset size: {len(df_cleaned)} compositions")
    
    return df_cleaned, completeness_stats

def save_validation_results(stats: Dict[str, Any], output_path: Path):
    """Save validation statistics to JSON file."""
    output_file = output_path / "descriptor_validation_stats.json"
    
    with open(output_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Validation statistics saved to {output_file}")

def save_cleaned_dataset(df: pd.DataFrame, output_path: Path):
    """Save the cleaned dataset to CSV."""
    output_file = output_path / "processed" / "engineered_dataset_validated.csv"
    
    df.to_csv(output_file, index=False)
    logger.info(f"Cleaned dataset saved to {output_file}")

def main():
    """Main execution function."""
    logger.info("Starting descriptor validation for T017")
    
    # Ensure data directories exist
    data_path = get_data_path()
    ensure_data_directories()
    
    try:
        # Load the engineered dataset
        df = load_engineered_dataset(data_path)
        
        # Validate and clean the dataset
        df_cleaned, stats = validate_descriptor_completeness(df)
        
        # Save results
        data_path_obj = Path(data_path)
        save_validation_results(stats, data_path_obj)
        save_cleaned_dataset(df_cleaned, data_path_obj)
        
        # Print summary
        logger.info("=" * 50)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Initial rows: {stats['final']['initial_rows']}")
        logger.info(f"Final rows: {stats['final']['final_rows']}")
        logger.info(f"Rows dropped: {stats['final']['rows_dropped']}")
        logger.info(f"Average completeness: {stats['overall']['avg_completeness_pct']}%")
        logger.info(f"Threshold met (>=95%): {stats['overall']['completeness_threshold_met']}")
        logger.info("=" * 50)
        
        # Return success code
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during validation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
