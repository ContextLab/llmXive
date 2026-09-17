"""
Statistical Testing Module for Cognitive Decline Analysis.

Implements Mann-Whitney U tests for group comparisons (Control vs AD, Control vs MCI)
on extracted linguistic features.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

from config import get_path, get_seed, set_seed
from utils import get_logger

# Configure logging
logger = get_logger(__name__)

def load_feature_matrix(filepath: str) -> pd.DataFrame:
    """
    Load the processed feature matrix from CSV.

    Args:
        filepath: Path to the features CSV file.

    Returns:
        DataFrame containing features and labels.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Feature matrix not found at {filepath}")

    df = pd.read_csv(filepath)
    
    # Validate required columns
    required_cols = ['participant_id', 'label']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    logger.info(f"Loaded feature matrix with {len(df)} records")
    return df

def prepare_group_data(df: pd.DataFrame, feature_col: str, group1_label: str, group2_label: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract feature values for two specific groups.

    Args:
        df: Full dataframe with features and labels.
        feature_col: Name of the feature column to analyze.
        group1_label: Label for the first group (e.g., 'Control').
        group2_label: Label for the second group (e.g., 'AD').

    Returns:
        Tuple of (group1_values, group2_values) as numpy arrays.
    """
    if feature_col not in df.columns:
        raise ValueError(f"Feature column '{feature_col}' not found in dataframe")

    group1 = df[df['label'] == group1_label][feature_col].dropna()
    group2 = df[df['label'] == group2_label][feature_col].dropna()

    if len(group1) == 0 or len(group2) == 0:
        raise ValueError(f"One of the groups has no valid data for feature '{feature_col}'")

    logger.debug(f"Group {group1_label}: n={len(group1)}, Group {group2_label}: n={len(group2)}")
    return group1.values, group2.values

def run_mann_whitney_u(group1: np.ndarray, group2: np.ndarray, alternative: str = 'two-sided') -> Dict[str, float]:
    """
    Perform Mann-Whitney U test between two groups.

    Args:
        group1: Array of values for group 1.
        group2: Array of values for group 2.
        alternative: Type of alternative hypothesis ('two-sided', 'less', 'greater').

    Returns:
        Dictionary with 'statistic' and 'pvalue'.
    """
    if len(group1) < 2 or len(group2) < 2:
        raise ValueError("Both groups must have at least 2 samples for Mann-Whitney U test")

    # Handle constant variance edge case
    if np.std(group1) == 0 or np.std(group2) == 0:
        logger.warning("One or both groups have zero variance. Mann-Whitney U may be undefined.")
        # If all values are identical, U statistic is based on rank sums, but p-value calculation
        # might fail or be trivial. We proceed but log the warning.

    try:
        stat, pval = mannwhitneyu(group1, group2, alternative=alternative)
        return {'statistic': float(stat), 'pvalue': float(pval)}
    except Exception as e:
        logger.error(f"Mann-Whitney U test failed: {e}")
        raise

def run_group_comparisons(df: pd.DataFrame, feature_cols: List[str], 
                          comparisons: List[Tuple[str, str]]) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Run Mann-Whitney U tests for all features across specified group comparisons.

    Args:
        df: Feature dataframe.
        feature_cols: List of feature column names to test.
        comparisons: List of tuples (group1_label, group2_label).

    Returns:
        Nested dictionary: {feature_name: {comparison_key: {statistic, pvalue}}}
    """
    results = {}
    
    for feature in feature_cols:
        results[feature] = {}
        
        for g1_label, g2_label in comparisons:
            comparison_key = f"{g1_label}_vs_{g2_label}"
            try:
                g1_vals, g2_vals = prepare_group_data(df, feature, g1_label, g2_label)
                test_result = run_mann_whitney_u(g1_vals, g2_vals)
                results[feature][comparison_key] = test_result
            except ValueError as e:
                logger.warning(f"Skipping {feature} for {comparison_key}: {e}")
                results[feature][comparison_key] = {'error': str(e)}

    return results

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save statistical results to a JSON file.

    Args:
        results: Dictionary of results to save.
        output_path: Path to the output JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Statistical results saved to {output_path}")

def main() -> None:
    """
    Main entry point for statistical testing.
    Loads features, runs Mann-Whitney U tests for Control vs AD and Control vs MCI,
    and saves results.
    """
    # Set seed for reproducibility
    set_seed(get_seed())

    # Define paths
    features_path = get_path('data/processed/features.csv')
    output_path = get_path('data/results/statistical_metrics.json')

    # Define comparisons
    # Based on task description: Control vs AD and Control vs MCI
    comparisons = [
        ('Control', 'AD'),
        ('Control', 'MCI')
    ]

    logger.info("Starting statistical testing module (T026)")
    
    try:
        # Load data
        df = load_feature_matrix(features_path)
        
        # Identify feature columns (exclude metadata columns)
        exclude_cols = ['participant_id', 'label']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        if not feature_cols:
            raise ValueError("No feature columns found in the dataset")
        
        logger.info(f"Found {len(feature_cols)} features to test")

        # Run comparisons
        results = run_group_comparisons(df, feature_cols, comparisons)

        # Add metadata
        final_results = {
            'metadata': {
                'total_features_tested': len(feature_cols),
                'comparisons_performed': [f"{c[0]}_vs_{c[1]}" for c in comparisons],
                'test_method': 'Mann-Whitney U (two-sided)'
            },
            'results': results
        }

        # Save results
        save_results(final_results, output_path)
        
        logger.info("Statistical testing completed successfully")

    except Exception as e:
        logger.error(f"Statistical testing failed: {e}")
        raise

if __name__ == '__main__':
    main()
