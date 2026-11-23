"""
T029: Generate final summary table with all statistical results.

This script aggregates results from the physics analysis (T025, T026, T027)
and the scaling analysis (T020) into a single summary CSV file.

It reads:
1. data/processed/scaling_results.csv (from T020)
2. data/processed/physics_metrics.csv (from T026/T025)
3. data/processed/statistical_tests.json (from T027)

It outputs:
- data/processed/final_analysis.csv
"""

import os
import sys
import logging
import json
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

# Add project root to path to allow imports from sibling modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_config
from utils.logging_config import setup_logging, get_logger

logger = get_logger(__name__)

def load_scaling_results(config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Load scaling results from T020."""
    scaling_path = Path(config['data_dir']) / 'processed' / 'scaling_results.csv'
    
    if not scaling_path.exists():
        logger.error(f"Scaling results file not found: {scaling_path}")
        return None
    
    try:
        df = pd.read_csv(scaling_path)
        logger.info(f"Loaded {len(df)} scaling results from {scaling_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load scaling results: {e}")
        return None

def load_physics_metrics(config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Load physics metrics from T026/T025."""
    physics_path = Path(config['data_dir']) / 'processed' / 'physics_metrics.csv'
    
    if not physics_path.exists():
        logger.warning(f"Physics metrics file not found: {physics_path}. "
                     "Proceeding without physics correlations.")
        return None
    
    try:
        df = pd.read_csv(physics_path)
        logger.info(f"Loaded {len(df)} physics metrics from {physics_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load physics metrics: {e}")
        return None

def load_statistical_tests(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Load statistical test results from T027."""
    stats_path = Path(config['data_dir']) / 'processed' / 'statistical_tests.json'
    
    if not stats_path.exists():
        logger.warning(f"Statistical tests file not found: {stats_path}. "
                     "Proceeding without permutation test results.")
        return None
    
    try:
        with open(stats_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded statistical test results from {stats_path}")
        return data
    except Exception as e:
        logger.error(f"Failed to load statistical tests: {e}")
        return None

def merge_results(scaling_df: pd.DataFrame, 
                 physics_df: Optional[pd.DataFrame],
                 stats_data: Optional[Dict[str, Any]]) -> pd.DataFrame:
    """Merge all results into a final summary dataframe."""
    
    # Start with scaling results
    final_df = scaling_df.copy()
    
    # Merge physics metrics if available
    if physics_df is not None:
        # Ensure we have the right columns for merging
        if 'property_name' in physics_df.columns:
            # Rename columns to avoid conflicts if any
            physics_cols = ['property_name', 'spatial_locality', 'symmetry_sensitivity', 
                          'valence_electron_variance', 'correlation_spatial', 
                          'correlation_symmetry', 'p_value_spatial', 'p_value_symmetry']
            
            # Only keep existing columns
            existing_cols = [c for c in physics_cols if c in physics_df.columns]
            if 'property_name' not in existing_cols:
                existing_cols.insert(0, 'property_name')
            
            physics_subset = physics_df[existing_cols].copy()
            
            # Merge on property_name
            final_df = pd.merge(final_df, physics_subset, on='property_name', how='left')
            logger.info(f"Merged {len(final_df.columns)} columns from physics metrics")
        else:
            logger.warning("Physics metrics missing 'property_name' column, skipping merge")
    else:
        # Add placeholder columns if physics data is missing
        placeholder_cols = ['spatial_locality', 'symmetry_sensitivity', 'valence_electron_variance',
                          'correlation_spatial', 'correlation_symmetry', 'p_value_spatial', 'p_value_symmetry']
        for col in placeholder_cols:
            final_df[col] = np.nan
        logger.info("Added placeholder columns for missing physics metrics")
    
    # Add statistical test results as a summary row or column
    if stats_data is not None:
        # Extract key statistics
        permutation_p_value = stats_data.get('permutation_test', {}).get('p_value', np.nan)
        class_comparison = stats_data.get('comparison', 'unknown')
        
        # Add as a new column for the summary
        final_df['permutation_test_p_value'] = permutation_p_value
        final_df['class_comparison'] = class_comparison
        
        logger.info(f"Included permutation test p-value: {permutation_p_value}")
    else:
        final_df['permutation_test_p_value'] = np.nan
        final_df['class_comparison'] = 'N/A'
    
    # Ensure consistent column order
    desired_order = [
        'property_name', 'exponent_b', 'intercept_a', 'r_squared', 'fit_status',
        'spatial_locality', 'symmetry_sensitivity', 'valence_electron_variance',
        'correlation_spatial', 'correlation_symmetry', 'p_value_spatial', 'p_value_symmetry',
        'permutation_test_p_value', 'class_comparison'
    ]
    
    # Reorder columns, putting missing ones at the end
    existing_cols = [c for c in desired_order if c in final_df.columns]
    missing_cols = [c for c in desired_order if c not in final_df.columns]
    
    # Add missing columns with NaN
    for col in missing_cols:
        final_df[col] = np.nan
    
    final_df = final_df[desired_order]
    
    # Sort by property name for consistent output
    final_df = final_df.sort_values('property_name').reset_index(drop=True)
    
    return final_df

def save_final_summary(df: pd.DataFrame, config: Dict[str, Any]) -> Path:
    """Save the final summary to CSV."""
    output_path = Path(config['data_dir']) / 'processed' / 'final_analysis.csv'
    
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Saved final summary to {output_path} with {len(df)} rows and {len(df.columns)} columns")
        return output_path
    except Exception as e:
        logger.error(f"Failed to save final summary: {e}")
        raise

def main():
    """Main entry point for T029."""
    logger.info("Starting T029: Generate final summary table")
    
    try:
        # Load configuration
        config = get_config()
        
        # Load all required data
        scaling_results = load_scaling_results(config)
        if scaling_results is None:
            logger.error("Cannot proceed without scaling results (T020)")
            sys.exit(1)
        
        physics_metrics = load_physics_metrics(config)
        stats_results = load_statistical_tests(config)
        
        # Merge all results
        final_df = merge_results(scaling_results, physics_metrics, stats_results)
        
        # Save final output
        output_path = save_final_summary(final_df, config)
        
        # Log summary statistics
        logger.info("Final Summary Statistics:")
        logger.info(f"  - Total properties: {len(final_df)}")
        logger.info(f"  - Properties with valid fits: {final_df['fit_status'].eq('power-law').sum()}")
        logger.info(f"  - Properties with non-power-law fits: {final_df['fit_status'].eq('non-power-law').sum()}")
        
        if 'permutation_test_p_value' in final_df.columns:
            p_val = final_df['permutation_test_p_value'].iloc[0]
            if not pd.isna(p_val):
                logger.info(f"  - Permutation test p-value: {p_val:.4f}")
        
        logger.info(f"  - Output file: {output_path}")
        
        logger.info("T029 completed successfully")
        
    except Exception as e:
        logger.error(f"T029 failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    setup_logging()
    main()