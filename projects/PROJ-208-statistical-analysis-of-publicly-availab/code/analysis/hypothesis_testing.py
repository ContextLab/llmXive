"""
Hypothesis Testing Module for GitHub Issue Resolution Analysis.

Implements non-parametric statistical tests to compare resolution times
across different programming language groups, with multiple comparison correction.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import kruskal, chi2_contingency
from statsmodels.stats.multitest import multipletests

# Import configuration utilities
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.config import get_config, get_path
from utils.validators import validate_dataset_schema

# Setup logging
logger = logging.getLogger(__name__)


def load_cleaned_data() -> pd.DataFrame:
    """
    Load the cleaned dataset from the processed directory.

    Returns:
        pd.DataFrame: The cleaned issues dataset.
    """
    config = get_config()
    data_path = get_path(config, 'cleaned_issues')
    
    if not Path(data_path).exists():
        raise FileNotFoundError(f"Cleaned dataset not found at {data_path}. "
                              "Run the data collection pipeline first.")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} issues from {data_path}")
    return df


def prepare_groups_for_test(df: pd.DataFrame, 
                            resolution_col: str = 'resolution_time_hours',
                            group_col: str = 'primary_language') -> Dict[str, np.ndarray]:
    """
    Prepare data for Kruskal-Wallis test by grouping resolution times by language.
    Filters out groups with insufficient data or missing values.

    Args:
        df: The cleaned dataset.
        resolution_col: Name of the resolution time column.
        group_col: Name of the grouping column (programming language).

    Returns:
        Dict mapping language names to arrays of resolution times.
    """
    # Drop rows with missing resolution times or languages
    valid_df = df[[resolution_col, group_col]].dropna()
    
    # Filter out very small groups (less than 3 samples)
    groups = valid_df.groupby(group_col)[resolution_col].apply(lambda x: x.values)
    groups = {k: v for k, v in groups.items() if len(v) >= 3}
    
    logger.info(f"Prepared {len(groups)} language groups for testing")
    return groups


def perform_kruskal_wallis(groups: Dict[str, np.ndarray]) -> Tuple[float, float]:
    """
    Perform Kruskal-Wallis H-test across all groups.

    The Kruskal-Wallis test is a non-parametric method to determine whether
    there are statistically significant differences between two or more groups
    of an independent variable on a continuous or ordinal dependent variable.

    Args:
        groups: Dictionary mapping group names to data arrays.

    Returns:
        Tuple of (H-statistic, p-value).
    """
    if len(groups) < 2:
        raise ValueError("Kruskal-Wallis test requires at least 2 groups")
    
    data_arrays = list(groups.values())
    h_stat, p_value = kruskal(*data_arrays)
    
    logger.info(f"Kruskal-Wallis H-statistic: {h_stat:.4f}, p-value: {p_value:.6f}")
    return h_stat, p_value


def perform_pairwise_comparisons(df: pd.DataFrame, 
                                 resolution_col: str = 'resolution_time_hours',
                                 group_col: str = 'primary_language',
                                 alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Perform pairwise Mann-Whitney U tests between all language groups
    and apply Holm-Bonferroni correction.

    Args:
        df: The cleaned dataset.
        resolution_col: Name of the resolution time column.
        group_col: Name of the grouping column.
        alpha: Significance level.

    Returns:
        List of dictionaries containing pairwise test results.
    """
    from scipy.stats import mannwhitneyu
    
    valid_df = df[[resolution_col, group_col]].dropna()
    groups = valid_df[group_col].unique()
    
    results = []
    p_values = []
    comparisons = []
    
    # Perform all pairwise comparisons
    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            lang_a = groups[i]
            lang_b = groups[j]
            
            data_a = valid_df[valid_df[group_col] == lang_a][resolution_col].values
            data_b = valid_df[valid_df[group_col] == lang_b][resolution_col].values
            
            # Skip if either group is too small
            if len(data_a) < 3 or len(data_b) < 3:
                continue
            
            stat, p_val = mannwhitneyu(data_a, data_b, alternative='two-sided')
            
            comparisons.append((lang_a, lang_b))
            p_values.append(p_val)
            
            results.append({
                'group_a': lang_a,
                'group_b': lang_b,
                'n_a': len(data_a),
                'n_b': len(data_b),
                'u_statistic': stat,
                'raw_p_value': p_val
            })
    
    if not p_values:
        logger.warning("No valid pairwise comparisons found")
        return results
    
    # Apply Holm-Bonferroni correction
    corrected = multipletests(p_values, alpha=alpha, method='holm')
    
    # Update results with corrected p-values
    for i, result in enumerate(results):
        result['holm_corrected_p_value'] = corrected.pvalues[i]
        result['is_significant'] = corrected.pvalues[i] < alpha
        result['reject_null'] = corrected.rejections[i]
    
    logger.info(f"Performed {len(results)} pairwise comparisons with Holm-Bonferroni correction")
    return results


def analyze_hypotheses(df: pd.DataFrame,
                      resolution_col: str = 'resolution_time_hours',
                      group_col: str = 'primary_language',
                      alpha: float = 0.05) -> Dict[str, Any]:
    """
    Full hypothesis testing pipeline: Kruskal-Wallis followed by pairwise tests.

    Args:
        df: The cleaned dataset.
        resolution_col: Name of the resolution time column.
        group_col: Name of the grouping column.
        alpha: Significance level.

    Returns:
        Dictionary containing all test results and metrics.
    """
    logger.info("Starting hypothesis testing analysis")
    
    # Prepare groups
    groups = prepare_groups_for_test(df, resolution_col, group_col)
    
    if len(groups) < 2:
        raise ValueError("Insufficient groups for Kruskal-Wallis test (need >= 2)")
    
    # Kruskal-Wallis test
    h_stat, p_value = perform_kruskal_wallis(groups)
    
    # Pairwise comparisons with Holm-Bonferroni
    pairwise_results = perform_pairwise_comparisons(df, resolution_col, group_col, alpha)
    
    # Summary statistics
    summary = {
        'num_groups': len(groups),
        'total_samples': sum(len(v) for v in groups.values()),
        'groups': sorted(groups.keys()),
        'kruskal_wallis': {
            'h_statistic': float(h_stat),
            'p_value': float(p_value),
            'is_significant': p_value < alpha,
            'degrees_of_freedom': len(groups) - 1
        },
        'pairwise_comparisons': pairwise_results,
        'significant_pairs': [
            {
                'group_a': r['group_a'],
                'group_b': r['group_b'],
                'holm_corrected_p_value': r['holm_corrected_p_value']
            }
            for r in pairwise_results if r['is_significant']
        ],
        'alpha': alpha,
        'method': 'Kruskal-Wallis with Holm-Bonferroni correction'
    }
    
    logger.info(f"Analysis complete. Found {len(summary['significant_pairs'])} significant pairs")
    return summary


def save_results(results: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Save hypothesis testing results to a JSON file.

    Args:
        results: Dictionary of test results.
        output_path: Optional path to save results. If None, uses default path.

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        config = get_config()
        output_path = get_path(config, 'hypothesis_results')
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Saved results to {output_path}")
    return str(output_path)


def main():
    """Main entry point for hypothesis testing pipeline."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load data
        df = load_cleaned_data()
        
        # Validate schema
        validate_dataset_schema(df, 'cleaned_issues')
        
        # Run analysis
        results = analyze_hypotheses(df)
        
        # Save results
        output_path = save_results(results)
        
        # Print summary
        print("\n" + "="*60)
        print("HYPOTHESIS TESTING RESULTS SUMMARY")
        print("="*60)
        print(f"Test Method: {results['method']}")
        print(f"Number of Groups: {results['num_groups']}")
        print(f"Total Samples: {results['total_samples']}")
        print(f"Groups: {', '.join(results['groups'])}")
        print("-"*60)
        
        kw = results['kruskal_wallis']
        print(f"Kruskal-Wallis H-statistic: {kw['h_statistic']:.4f}")
        print(f"Kruskal-Wallis p-value: {kw['p_value']:.6f}")
        print(f"Significant (α={kw['alpha']}): {'Yes' if kw['is_significant'] else 'No'}")
        print("-"*60)
        
        if results['significant_pairs']:
            print(f"Significant pairwise differences ({len(results['significant_pairs'])} pairs):")
            for pair in results['significant_pairs']:
                print(f"  {pair['group_a']} vs {pair['group_b']}: p={pair['holm_corrected_p_value']:.6f}")
        else:
            print("No significant pairwise differences found after Holm-Bonferroni correction.")
        
        print("="*60)
        print(f"Results saved to: {output_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during hypothesis testing: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
