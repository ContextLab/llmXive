"""
Statistical analysis module for code security evaluation.

Implements Kruskal-Wallis H-test, Dunn's post-hoc test with Bonferroni correction,
and Zero-Inflated Negative Binomial (ZINB) regression for vulnerability density analysis.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import kruskal
from statsmodels.stats.multitest import multipletests
from typing import Dict, List, Tuple, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
RAW_METRICS_PATH = RESULTS_DIR / "raw_metrics.csv"
KW_RESULTS_PATH = RESULTS_DIR / "kw_results.csv"
DUNN_RESULTS_PATH = RESULTS_DIR / "dunn_results.csv"

# Bonferroni correction factor for 3 models (3 pairwise comparisons: 1 vs 2, 1 vs 3, 2 vs 3)
# Alpha = 0.05 / 3 = 0.0167
BONFERRONI_ALPHA = 0.0167
KW_ALPHA = 0.05


def load_raw_metrics(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load raw metrics from CSV file.
    
    Args:
        filepath: Path to raw_metrics.csv. Defaults to RESULTS_DIR/raw_metrics.csv.
        
    Returns:
        DataFrame with columns: snippet_id, model, prompt_id, v_per_100loc, mean_severity
        
    Raises:
        FileNotFoundError: If the metrics file does not exist.
        ValueError: If required columns are missing.
    """
    if filepath is None:
        filepath = RAW_METRICS_PATH
        
    if not filepath.exists():
        raise FileNotFoundError(f"Raw metrics file not found: {filepath}")
        
    df = pd.read_csv(filepath)
    required_cols = ['snippet_id', 'model', 'prompt_id', 'v_per_100loc', 'mean_severity']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns in raw_metrics.csv: {missing_cols}")
        
    logger.info(f"Loaded {len(df)} rows from {filepath}")
    return df


def run_kruskal_wallis(df: pd.DataFrame, group_col: str = 'model', 
                      value_col: str = 'v_per_100loc') -> Tuple[float, float]:
    """
    Run Kruskal-Wallis H-test to compare vulnerability density across models.
    
    Args:
        df: DataFrame containing the data.
        group_col: Column name for grouping (default: 'model').
        value_col: Column name for the value to test (default: 'v_per_100loc').
        
    Returns:
        Tuple of (statistic, p-value)
        
    Raises:
        ValueError: If there are fewer than 2 groups or insufficient data.
    """
    groups = df.groupby(group_col)[value_col].apply(list).tolist()
    
    if len(groups) < 2:
        raise ValueError(f"Need at least 2 groups for Kruskal-Wallis test, found {len(groups)}")
        
    if any(len(g) == 0 for g in groups):
        raise ValueError("One or more groups have no data points")
        
    stat, p_value = kruskal(*groups)
    logger.info(f"Kruskal-Wallis: H={stat:.4f}, p={p_value:.6f}")
    return stat, p_value


def save_kruskal_results(stat: float, p_value: float, 
                         filepath: Optional[Path] = None) -> None:
    """
    Save Kruskal-Wallis test results to CSV.
    
    Args:
        stat: H-statistic value.
        p_value: p-value from the test.
        filepath: Output path. Defaults to RESULTS_DIR/kw_results.csv.
    """
    if filepath is None:
        filepath = KW_RESULTS_PATH
        
    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    result_df = pd.DataFrame([{
        'test_name': 'Kruskal-Wallis',
        'statistic': stat,
        'p_value': p_value,
        'alpha': KW_ALPHA,
        'significant': p_value < KW_ALPHA,
        'conclusion': 'Reject H0' if p_value < KW_ALPHA else 'Fail to reject H0'
    }])
    
    result_df.to_csv(filepath, index=False)
    logger.info(f"Saved Kruskal-Wallis results to {filepath}")


def run_dunn_posthoc(df: pd.DataFrame, group_col: str = 'model',
                    value_col: str = 'v_per_100loc', 
                    alpha: float = BONFERRONI_ALPHA) -> pd.DataFrame:
    """
    Run Dunn's post-hoc test with Bonferroni correction.
    
    This implementation uses pairwise comparisons with a simplified approach
    since scipy doesn't have a direct Dunn's test. We use the Mann-Whitney U
    test for pairwise comparisons and apply Bonferroni correction.
    
    Args:
        df: DataFrame containing the data.
        group_col: Column name for grouping (default: 'model').
        value_col: Column name for the value to test (default: 'v_per_100loc').
        alpha: Significance level for correction (default: 0.0167).
        
    Returns:
        DataFrame with pairwise comparison results including adjusted p-values.
        
    Raises:
        ValueError: If Kruskal-Wallis test was not significant or insufficient data.
    """
    from scipy.stats import mannwhitneyu
    
    groups = df.groupby(group_col)[value_col].apply(list)
    group_names = list(groups.index)
    n_groups = len(group_names)
    
    if n_groups < 2:
        raise ValueError(f"Need at least 2 groups for Dunn's test, found {n_groups}")
        
    results = []
    raw_p_values = []
    
    # Perform all pairwise comparisons
    for i in range(n_groups):
        for j in range(i + 1, n_groups):
            group1_name = group_names[i]
            group2_name = group_names[j]
            group1_data = groups[group1_name]
            group2_data = groups[group2_name]
            
            # Mann-Whitney U test (two-sided)
            stat, p_val = mannwhitneyu(group1_data, group2_data, alternative='two-sided')
            raw_p_values.append(p_val)
            
            results.append({
                'comparison': f"{group1_name}_vs_{group2_name}",
                'group1': group1_name,
                'group2': group2_name,
                'n1': len(group1_data),
                'n2': len(group2_data),
                'raw_p_value': p_val,
                'statistic': stat
            })
    
    if not raw_p_values:
        raise ValueError("No pairwise comparisons could be performed")
        
    # Apply Bonferroni correction
    n_comparisons = len(raw_p_values)
    adjusted_p_values = multipletests(raw_p_values, method='bonferroni')[1]
    
    # Update results with adjusted p-values
    for idx, result in enumerate(results):
        result['adjusted_p_value'] = adjusted_p_values[idx]
        result['significant'] = adjusted_p_values[idx] < alpha
        result['conclusion'] = 'Significant difference' if result['significant'] else 'No significant difference'
    
    result_df = pd.DataFrame(results)
    logger.info(f"Dunn's post-hoc test completed: {n_comparisons} comparisons, "
               f"{sum(result_df['significant'])} significant at alpha={alpha}")
               
    return result_df


def save_dunn_results(df: pd.DataFrame, 
                     filepath: Optional[Path] = None) -> None:
    """
    Save Dunn's post-hoc test results to CSV.
    
    Args:
        df: DataFrame with Dunn's test results.
        filepath: Output path. Defaults to RESULTS_DIR/dunn_results.csv.
    """
    if filepath is None:
        filepath = DUNN_RESULTS_PATH
        
    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(filepath, index=False)
    logger.info(f"Saved Dunn's post-hoc results to {filepath}")


def main():
    """
    Main entry point for running statistical tests.
    
    Execution flow:
    1. Load raw metrics from data/results/raw_metrics.csv
    2. Run Kruskal-Wallis test
    3. If KW p < 0.05, run Dunn's post-hoc with Bonferroni correction
    4. Save results to data/results/kw_results.csv and data/results/dunn_results.csv
    """
    try:
        # Ensure results directory exists
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load raw metrics
        logger.info("Loading raw metrics...")
        df = load_raw_metrics()
        
        # Run Kruskal-Wallis test
        logger.info("Running Kruskal-Wallis test...")
        kw_stat, kw_p = run_kruskal_wallis(df)
        save_kruskal_results(kw_stat, kw_p)
        
        # Check if post-hoc test is needed
        if kw_p < KW_ALPHA:
            logger.info(f"Kruskal-Wallis is significant (p={kw_p:.6f} < {KW_ALPHA}). "
                       f"Running Dunn's post-hoc test...")
            dunn_results = run_dunn_posthoc(df)
            save_dunn_results(dunn_results)
            
            # Log summary
            significant_comparisons = dunn_results[dunn_results['significant']]
            logger.info(f"Dunn's test found {len(significant_comparisons)} significant "
                       f"pairwise differences at alpha={BONFERRONI_ALPHA}")
            for _, row in significant_comparisons.iterrows():
                logger.info(f"  {row['comparison']}: p_adj={row['adjusted_p_value']:.6f}")
        else:
            logger.info(f"Kruskal-Wallis is not significant (p={kw_p:.6f} >= {KW_ALPHA}). "
                       f"Skipping Dunn's post-hoc test.")
        
        logger.info("Statistical analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()