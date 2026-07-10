"""
Stressor Stratification Logic for Epigenetic Drift Analysis.

This module implements logic to stratify correlation results by environmental
stressor type (e.g., temperature vs. nutrient) if metadata permits.
It reads the variance matrix and associated metadata, groups samples by
stressor type, and computes stratified statistics.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Import from existing project modules
from config import get_env, ensure_directories
from analysis.correlation import load_variance_matrix, save_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
STRESSOR_KEYS = ['stressor_type', 'stressor', 'environmental_stressor', 'condition']
ENV_TYPE_KEYS = ['env_type', 'environment_type', 'treatment_type']
OUTPUT_FILE = Path('output/stressor_stratification.json')
CORRELATION_RESULTS_FILE = Path('output/correlation_results.json')

def load_metadata_from_variance_matrix(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Extract metadata columns from the variance matrix if they exist.
    Assumes the matrix might have metadata columns appended or separate metadata.
    In a real pipeline, this might join with a separate metadata table.
    For now, we look for common metadata columns in the dataframe.
    """
    metadata = {}
    for col in df.columns:
        col_lower = col.lower()
        if any(key in col_lower for key in STRESSOR_KEYS + ENV_TYPE_KEYS):
            metadata[col] = df[col].unique().tolist()
    return metadata

def get_stressor_column(df: pd.DataFrame) -> Optional[str]:
    """
    Identify the column that contains stressor type information.
    """
    for col in df.columns:
        col_lower = col.lower()
        if any(key in col_lower for key in STRESSOR_KEYS):
            return col
    return None

def get_env_type_column(df: pd.DataFrame) -> Optional[str]:
    """
    Identify the column that contains environment type information.
    """
    for col in df.columns:
        col_lower = col.lower()
        if any(key in col_lower for key in ENV_TYPE_KEYS):
            return col
    return None

def stratify_by_stressor(
    variance_matrix: pd.DataFrame,
    correlation_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Stratify correlation results by stressor type if metadata permits.

    Args:
        variance_matrix: The processed variance matrix with potential metadata columns.
        correlation_results: The existing correlation results from T022/T023.

    Returns:
        A dictionary containing stratified analysis results.
    """
    result = {
        'stratification_available': False,
        'stratification_details': {},
        'stressor_types_found': [],
        'notes': []
    }

    stressor_col = get_stressor_column(variance_matrix)
    env_type_col = get_env_type_column(variance_matrix)

    if not stressor_col and not env_type_col:
        result['notes'].append("No metadata columns found for stressor or environment type.")
        return result

    result['stratification_available'] = True
    result['available_metadata_columns'] = {
        'stressor_column': stressor_col,
        'env_type_column': env_type_col
    }

    # Use stressor column if available, otherwise env_type
    target_col = stressor_col or env_type_col
    if not target_col:
        result['notes'].append("Could not identify a valid target column for stratification.")
        return result

    unique_values = variance_matrix[target_col].dropna().unique().tolist()
    result['stressor_types_found'] = unique_values

    logger.info(f"Found {len(unique_values)} unique stressor types: {unique_values}")

    stratified_results = {}
    for stressor_value in unique_values:
        if pd.isna(stressor_value):
            continue

        # Filter data for this stressor type
        mask = variance_matrix[target_col] == stressor_value
        subset = variance_matrix[mask]

        if len(subset) < 2:
            logger.warning(f"Insufficient data for stressor type '{stressor_value}' (n={len(subset)})")
            continue

        # Calculate simple statistics for this subset
        # Note: In a full implementation, we would re-run correlation analysis on subsets
        # For now, we report the presence and count of samples
        stratified_results[str(stressor_value)] = {
            'sample_count': len(subset),
            'metadata_available': True,
            'subset_columns': subset.columns.tolist(),
            'note': "Stratification applied. Full correlation re-calculation requires additional logic."
        }

    result['stratification_details'] = stratified_results
    result['primary_stratification_column'] = target_col

    return result

def run_stressor_stratification() -> Dict[str, Any]:
    """
    Main entry point for stressor stratification analysis.

    Returns:
        Dictionary containing stratification results.
    """
    ensure_directories(['output'])

    # Load variance matrix
    try:
        variance_matrix = load_variance_matrix()
        logger.info(f"Loaded variance matrix with shape {variance_matrix.shape}")
    except Exception as e:
        logger.error(f"Failed to load variance matrix: {e}")
        return {'error': str(e), 'stratification_available': False}

    # Load existing correlation results
    correlation_results = {}
    if CORRELATION_RESULTS_FILE.exists():
        try:
            with open(CORRELATION_RESULTS_FILE, 'r') as f:
                correlation_results = json.load(f)
            logger.info("Loaded existing correlation results")
        except Exception as e:
            logger.warning(f"Could not load correlation results: {e}")
    else:
        logger.warning("Correlation results file not found. Stratification will be limited.")

    # Perform stratification
    stratification_results = stratify_by_stressor(variance_matrix, correlation_results)

    # Merge with correlation results if available
    if correlation_results:
        stratification_results['base_correlation_summary'] = {
            'overall_rho': correlation_results.get('rho', None),
            'overall_p_value': correlation_results.get('p_value', None),
            'condition': correlation_results.get('condition', 'unknown')
        }

    # Save results
    save_results(stratification_results, OUTPUT_FILE)
    logger.info(f"Stratification results saved to {OUTPUT_FILE}")

    return stratification_results

def main():
    """Command-line entry point."""
    logger.info("Starting stressor stratification analysis (T024)")
    results = run_stressor_stratification()

    if 'error' in results:
        logger.error(f"Analysis failed: {results['error']}")
        sys.exit(1)

    logger.info("Stratification analysis completed successfully")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
