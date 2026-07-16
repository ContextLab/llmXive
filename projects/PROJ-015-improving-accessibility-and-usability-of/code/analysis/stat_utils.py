import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, List, Optional, Tuple
from utils.logger import get_logger
import os

logger = get_logger(__name__)

def run_anova_pipeline(traditional: np.ndarray, explainable: np.ndarray, metric_name: str) -> Dict[str, Any]:
    """
    Run Repeated Measures ANOVA for within-subjects design.
    Note: Normality-based test selection is bypassed per Constitution Principle VII.
    """
    if len(traditional) != len(explainable):
        # For unequal sample sizes, use standard ANOVA
        f_stat, p_value = stats.f_oneway(traditional, explainable)
    else:
        # For paired data, use paired t-test as approximation for ANOVA
        # In a true repeated measures design with 2 conditions, t-test squared = F-stat
        t_stat, p_value = stats.ttest_rel(traditional, explainable)
        f_stat = t_stat ** 2
    
    return {
        'F': f_stat,
        'p_value': p_value,
        'method': 'Repeated Measures ANOVA (approximated via paired t-test)',
        'metric': metric_name
    }

def run_holm_bonferroni(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Holm-Bonferroni correction for multiple comparisons.
    """
    if 'p_value' not in df.columns or len(df) == 0:
        return df
    
    # Sort by p-value
    df_sorted = df.sort_values('p_value').reset_index(drop=True)
    n_tests = len(df_sorted)
    
    # Calculate adjusted p-values using Holm-Bonferroni
    adjusted_p = np.zeros(n_tests)
    for i in range(n_tests):
        # Holm-Bonferroni: p * (n - i)
        adjusted_p[i] = min(df_sorted.iloc[i]['p_value'] * (n_tests - i), 1.0)
    
    # Ensure monotonicity (adjusted p-values should not decrease)
    for i in range(1, n_tests):
        adjusted_p[i] = max(adjusted_p[i], adjusted_p[i-1])
    
    # Map back to original order
    df['adjusted_p_value'] = adjusted_p
    
    logger.info(f"Holm-Bonferroni correction applied to {n_tests} tests")
    return df

def calculate_effect_size(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d as effect size.
    """
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    
    # Pooled standard deviation
    n1, n2 = len(group1), len(group2)
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    cohens_d = (mean1 - mean2) / pooled_std
    return abs(cohens_d)

def generate_metrics_summary(df: pd.DataFrame, output_path: str) -> pd.DataFrame:
    """
    Generate full metrics summary with ANOVA and effect sizes.
    """
    metrics_to_analyze = ['completion_time', 'error_count', 'sus_score']
    results = []
    
    for metric in metrics_to_analyze:
        if metric not in df.columns:
            continue
        
        traditional = df[df['interface_type'] == 'Traditional'][metric].values
        explainable = df[df['interface_type'] == 'Explainable'][metric].values
        
        if len(traditional) < 2 or len(explainable) < 2:
            logger.warning(f"Insufficient data for {metric}")
            continue
        
        anova_result = run_anova_pipeline(traditional, explainable, metric)
        effect_size = calculate_effect_size(traditional, explainable)
        
        results.append({
            'metric_name': metric,
            'interface_type': 'Comparison',
            'F_statistic': anova_result['F'],
            'p_value': anova_result['p_value'],
            'adjusted_p_value': anova_result['p_value'],  # Will be corrected later
            'effect_size': effect_size,
            'n_traditional': len(traditional),
            'n_explainable': len(explainable)
        })
    
    if not results:
        raise ValueError("No metrics could be analyzed")
    
    summary_df = pd.DataFrame(results)
    summary_df = run_holm_bonferroni(summary_df)
    summary_df.to_csv(output_path, index=False)
    
    return summary_df

def main():
    """Main entry point for statistical utilities."""
    print("Stat utilities module loaded successfully")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())