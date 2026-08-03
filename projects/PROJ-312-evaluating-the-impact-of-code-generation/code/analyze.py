import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Ensure logging is configured
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SampleSizeError(Exception):
    """Raised when sample size is insufficient for statistical analysis."""
    pass


class SignificanceError(Exception):
    """Raised when statistical significance threshold is not met and power check fails."""
    pass


def load_processed_data(filepath: str = "data/processed/processed_pr_data.csv") -> pd.DataFrame:
    """Load the processed PR data from CSV."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found at {filepath}")
    
    logger.info(f"Loading processed data from {filepath}")
    df = pd.read_csv(path)
    
    # Ensure turnaround_hours is numeric
    if 'turnaround_hours' in df.columns:
        df['turnaround_hours'] = pd.to_numeric(df['turnaround_hours'], errors='coerce')
        df = df.dropna(subset=['turnaround_hours'])
    
    return df


def filter_excluded_repos(df: pd.DataFrame, excluded_repos: List[str] = None) -> pd.DataFrame:
    """Filter out repositories that were skipped during data acquisition."""
    if excluded_repos is None:
        # Default to empty list if no exclusions provided
        return df
    
    logger.info(f"Filtering out {len(excluded_repos)} excluded repositories")
    return df[~df['repo_name'].isin(excluded_repos)]


def calculate_descriptive_statistics(df: pd.DataFrame, group_col: str = 'is_ai_assisted') -> Dict[str, Dict[str, float]]:
    """Calculate descriptive statistics for AI and non-AI groups."""
    results = {}
    
    for group in df[group_col].unique():
        group_name = "AI" if group else "Non-AI"
        group_data = df[df[group_col] == group]['turnaround_hours']
        
        results[group_name] = {
            'count': len(group_data),
            'mean': float(group_data.mean()),
            'median': float(group_data.median()),
            'std': float(group_data.std()),
            'q1': float(group_data.quantile(0.25)),
            'q3': float(group_data.quantile(0.75))
        }
        
        logger.info(f"{group_name} Group - Count: {results[group_name]['count']}, "
                   f"Mean: {results[group_name]['mean']:.2f}, Median: {results[group_name]['median']:.2f}")
    
    return results


def calculate_distribution_characteristics(df: pd.DataFrame, group_col: str = 'is_ai_assisted') -> Dict[str, Dict[str, float]]:
    """Calculate skewness and kurtosis for both groups."""
    results = {}
    
    for group in df[group_col].unique():
        group_name = "AI" if group else "Non-AI"
        group_data = df[df[group_col] == group]['turnaround_hours']
        
        results[group_name] = {
            'skewness': float(group_data.skew()),
            'kurtosis': float(group_data.kurtosis())
        }
        
        logger.info(f"{group_name} Group - Skewness: {results[group_name]['skewness']:.4f}, "
                   f"Kurtosis: {results[group_name]['kurtosis']:.4f}")
    
    return results


def calculate_shapiro_wilk(df: pd.DataFrame, group_col: str = 'is_ai_assisted') -> Dict[str, float]:
    """Perform Shapiro-Wilk test for normality on both groups."""
    results = {}
    
    for group in df[group_col].unique():
        group_name = "AI" if group else "Non-AI"
        group_data = df[df[group_col] == group]['turnaround_hours']
        
        # Shapiro-Wilk test requires at least 3 samples
        if len(group_data) >= 3:
            stat, p_value = stats.shapiro(group_data)
            results[group_name] = float(p_value)
            logger.info(f"{group_name} Group - Shapiro-Wilk p-value: {p_value:.4f}")
        else:
            results[group_name] = None
            logger.warning(f"{group_name} Group has fewer than 3 samples, skipping Shapiro-Wilk test")
    
    return results


def calculate_iqr_outliers(df: pd.DataFrame, group_col: str = 'is_ai_assisted') -> Dict[str, List[int]]:
    """Calculate IQR outliers for each group. Returns indices of outliers."""
    outlier_indices = {}
    
    for group in df[group_col].unique():
        group_name = "AI" if group else "Non-AI"
        group_data = df[df[group_col] == group]
        turnaround = group_data['turnaround_hours']
        
        q1 = turnaround.quantile(0.25)
        q3 = turnaround.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = group_data[(turnaround < lower_bound) | (turnaround > upper_bound)].index.tolist()
        outlier_indices[group_name] = outliers
        
        logger.info(f"{group_name} Group - Outliers identified: {len(outliers)} (bounds: [{lower_bound:.2f}, {upper_bound:.2f}])")
    
    return outlier_indices


def save_outlier_indices(outlier_indices: Dict[str, List[int]], filepath: str = "data/processed/outlier_indices.json"):
    """Save outlier indices to JSON file."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(outlier_indices, f, indent=2)
    logger.info(f"Outlier indices saved to {filepath}")


def calculate_effect_size_r(u_statistic: float, n1: int, n2: int) -> float:
    """Calculate effect size r for Mann-Whitney U test.
    
    r = Z / sqrt(N)
    where Z is approximated from U statistic
    """
    n = n1 + n2
    # Approximate Z from U statistic
    # U = n1*n2 + n1*(n1+1)/2 - R1
    # Z = (U - mean_U) / std_U
    mean_u = (n1 * n2) / 2
    std_u = np.sqrt((n1 * n2 * (n1 + n2 + 1)) / 12)
    
    if std_u == 0:
        return 0.0
    
    z = (u_statistic - mean_u) / std_u
    r = z / np.sqrt(n)
    
    return float(r)


def perform_stratified_mwu_test(df: pd.DataFrame, 
                               group_col: str = 'is_ai_assisted',
                               stratify_cols: List[str] = None) -> Dict[str, Any]:
    """
    Execute Stratified Mann-Whitney U test comparing AI vs non-AI groups.
    
    Stratification is performed by PR size and author activity.
    Returns U statistic, p-value, and effect size (r).
    
    Note: This uses the FULL dataset (not cleaned of outliers) as per Plan Phase 1.
    """
    if stratify_cols is None:
        # Default stratification columns based on task requirements
        stratify_cols = ['pr_size_category', 'author_activity_level']
    
    # Check if stratification columns exist, if not, create simple stratification
    available_cols = [col for col in stratify_cols if col in df.columns]
    
    if not available_cols:
        logger.warning("Stratification columns not found. Using simple stratification by repo_name.")
        # Create a simple stratification if specific columns don't exist
        df['_stratum'] = df['repo_name'].astype(str) + "_" + df['pr_size_category'].astype(str)
        available_cols = ['_stratum']
    else:
        df['_stratum'] = df[available_cols].astype(str).agg('_'.join, axis=1)
    
    # Separate groups
    ai_group = df[df[group_col] == True]['turnaround_hours'].values
    non_ai_group = df[df[group_col] == False]['turnaround_hours'].values
    
    logger.info(f"AI group size: {len(ai_group)}, Non-AI group size: {len(non_ai_group)}")
    
    # Check sample size requirements
    if len(ai_group) < 30:
        raise SampleSizeError(f"Sample size too small: AI group has {len(ai_group)} samples (minimum 30 required)")
    
    if len(non_ai_group) < 30:
        raise SampleSizeError(f"Sample size too small: Non-AI group has {len(non_ai_group)} samples (minimum 30 required)")
    
    # Perform stratified analysis
    # For each stratum, we calculate the contribution to the overall test
    # We'll use a weighted approach based on stratum sizes
    
    stratum_results = []
    total_weight = 0
    
    for stratum in df['_stratum'].unique():
        stratum_df = df[df['_stratum'] == stratum]
        stratum_ai = stratum_df[stratum_df[group_col] == True]['turnaround_hours'].values
        stratum_non_ai = stratum_df[stratum_df[group_col] == False]['turnaround_hours'].values
        
        if len(stratum_ai) > 0 and len(stratum_non_ai) > 0:
            # Perform MWU test for this stratum
            u_stat, p_val = stats.mannwhitneyu(stratum_ai, stratum_non_ai, alternative='two-sided')
            
            # Weight by stratum sample size
            weight = len(stratum_ai) + len(stratum_non_ai)
            stratum_results.append({
                'stratum': stratum,
                'u_stat': u_stat,
                'p_val': p_val,
                'weight': weight,
                'n_ai': len(stratum_ai),
                'n_non_ai': len(stratum_non_ai)
            })
            total_weight += weight
    
    # Calculate weighted overall statistics
    if not stratum_results:
        # Fallback to simple MWU if no strata found
        logger.warning("No valid strata found. Performing simple Mann-Whitney U test.")
        u_stat, p_val = stats.mannwhitneyu(ai_group, non_ai_group, alternative='two-sided')
    else:
        # Weighted average of U statistics (approximation for stratified test)
        # Note: This is a simplified approach; a full stratified test would use Cochran-Mantel-Haenszel
        weighted_u = sum(r['u_stat'] * (r['weight'] / total_weight) for r in stratum_results)
        weighted_p = sum(r['p_val'] * (r['weight'] / total_weight) for r in stratum_results)
        
        u_stat = weighted_u
        p_val = weighted_p
    
    # Calculate effect size
    effect_size_r = calculate_effect_size_r(u_stat, len(ai_group), len(non_ai_group))
    
    result = {
        'test_type': 'Stratified Mann-Whitney U',
        'u_statistic': float(u_stat),
        'p_value': float(p_val),
        'effect_size_r': effect_size_r,
        'sample_sizes': {
            'ai': len(ai_group),
            'non_ai': len(non_ai_group),
            'total': len(ai_group) + len(non_ai_group)
        },
        'stratification_method': 'weighted_average',
        'stratum_count': len(stratum_results) if stratum_results else 1,
        'stratum_details': stratum_results if stratum_results else None
    }
    
    logger.info(f"Stratified MWU Test Results:")
    logger.info(f"  U statistic: {u_stat:.4f}")
    logger.info(f"  p-value: {p_val:.4f}")
    logger.info(f"  Effect size (r): {effect_size_r:.4f}")
    logger.info(f"  Sample sizes - AI: {len(ai_group)}, Non-AI: {len(non_ai_group)}")
    
    return result


def save_statistical_results(results: Dict[str, Any], 
                            filepath: str = "data/processed/statistical_results.json"):
    """Save statistical results to JSON file."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Statistical results saved to {filepath}")


def main():
    """Main execution function for stratified Mann-Whitney U test."""
    logger.info("Starting stratified Mann-Whitney U test analysis")
    
    try:
        # Load processed data
        df = load_processed_data("data/processed/processed_pr_data.csv")
        
        # Filter excluded repos if needed (pass empty list if no exclusions)
        # In a real pipeline, this would come from T014
        excluded_repos = []  # Placeholder - would be populated from pipeline state
        df = filter_excluded_repos(df, excluded_repos)
        
        # Calculate descriptive statistics
        desc_stats = calculate_descriptive_statistics(df)
        
        # Calculate distribution characteristics
        dist_chars = calculate_distribution_characteristics(df)
        
        # Calculate Shapiro-Wilk test results
        shapiro_results = calculate_shapiro_wilk(df)
        
        # Calculate IQR outliers (for visualization only, not for primary test)
        outlier_indices = calculate_iqr_outliers(df)
        save_outlier_indices(outlier_indices)
        
        # Perform stratified Mann-Whitney U test on FULL dataset
        mwu_results = perform_stratified_mwu_test(df)
        
        # Check significance threshold
        alpha = 0.05
        if mwu_results['p_value'] < alpha:
            logger.info(f"Significant difference found (p < {alpha})")
        else:
            logger.info(f"No significant difference found (p >= {alpha})")
            
            # Power check would go here - if power is insufficient, raise SignificanceError
            # For now, we just log the condition
            if mwu_results['sample_sizes']['ai'] < 30:
                raise SignificanceError(f"Power check failed: AI group size {mwu_results['sample_sizes']['ai']} is below threshold")
        
        # Save results
        save_statistical_results(mwu_results)
        
        logger.info("Stratified Mann-Whitney U test analysis completed successfully")
        
    except SampleSizeError as e:
        logger.error(f"Sample size error: {e}")
        raise
    except SignificanceError as e:
        logger.error(f"Significance error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        raise


if __name__ == "__main__":
    main()