import os
import json
import csv
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Standard library stats for t-test
from statistics import mean, stdev
from scipy import stats as scipy_stats

# Project imports
from utils.logging import get_logger, setup_logging
from utils.config import get_path, get_classification_thresholds

logger = get_logger(__name__)

# Constants
DEFAULT_ALPHA = 0.05
DATA_PROCESSED_DIR = "data/processed"

def load_metrics_data() -> List[Dict[str, Any]]:
    """Load processed metrics from prs_metrics.csv."""
    metrics_path = get_path("processed_metrics")
    if not os.path.exists(metrics_path):
        logger.error(f"Metrics file not found: {metrics_path}")
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    data = []
    with open(metrics_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'pr_id': int(row['pr_id']),
                'source_type': row['source_type'],
                'comment_count': int(row['comment_count']),
                'time_to_merge_minutes': float(row['time_to_merge_minutes']),
                'review_cycles': int(row['review_cycles']),
                'complexity_score': float(row['complexity_score'])
            })
    return data

def group_by_source_type(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group data by source_type (llm vs human)."""
    groups = {'llm': [], 'human': []}
    for row in data:
        source = row['source_type']
        if source in groups:
            groups[source].append(row)
        else:
            logger.warning(f"Unknown source type: {source}, skipping.")
    return groups

def calculate_cohens_d(group1: List[float], group2: List[float]) -> float:
    """
    Calculate Cohen's d effect size.
    d = (mean1 - mean2) / pooled_std
    """
    if not group1 or not group2:
        return 0.0
    
    mean1 = mean(group1)
    mean2 = mean(group2)
    
    n1 = len(group1)
    n2 = len(group2)
    
    if n1 < 2 or n2 < 2:
        return 0.0
    
    var1 = sum((x - mean1) ** 2 for x in group1) / (n1 - 1)
    var2 = sum((x - mean2) ** 2 for x in group2) / (n2 - 1)
    
    # Pooled standard deviation
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    pooled_std = math.sqrt(pooled_var)
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def verify_alpha_assumption(alpha: float = DEFAULT_ALPHA) -> bool:
    """
    Verify that the chosen alpha aligns with the 'no multiple-comparison correction' assumption.
    
    This function checks if the alpha value is the standard 0.05 used in the project's 
    statistical analysis plan which explicitly states no multiple-comparison correction.
    
    Args:
        alpha: The significance level to verify (default 0.05).
    
    Returns:
        bool: True if the assumption is satisfied, False otherwise.
    
    Raises:
        ValueError: If the alpha value does not match the project's assumption.
    """
    # The project plan explicitly states "no multiple-comparison correction"
    # and uses the standard alpha = 0.05.
    if abs(alpha - DEFAULT_ALPHA) > 1e-9:
        error_msg = f"Alpha {alpha} does not align with the 'no multiple-comparison correction' assumption (expected {DEFAULT_ALPHA})."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Alpha assumption verified: {alpha} aligns with 'no multiple-comparison correction'.")
    return True

def perform_independent_t_test(group1: List[float], group2: List[float]) -> Dict[str, float]:
    """
    Perform an independent two-sample t-test.
    
    Returns:
        Dict containing t-statistic, p-value, and effect size (Cohen's d).
    """
    if not group1 or not group2:
        return {
            't_statistic': 0.0,
            'p_value': 1.0,
            'effect_size': 0.0,
            'is_significant': False
        }
    
    # Use scipy for robust t-test
    t_stat, p_val = scipy_stats.ttest_ind(group1, group2, equal_var=False)
    
    # Calculate Cohen's d
    d = calculate_cohens_d(group1, group2)
    
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_val),
        'effect_size': float(d),
        'is_significant': p_val < DEFAULT_ALPHA
    }

def run_analysis_for_metric(
    data: List[Dict[str, Any]], 
    metric_name: str, 
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """
    Run statistical analysis for a specific metric.
    
    Args:
        data: List of PR metrics.
        metric_name: Name of the metric column (e.g., 'comment_count', 'time_to_merge_minutes').
        alpha: Significance level.
    
    Returns:
        Dictionary with t-statistic, p-value, effect size, and significance.
    """
    # Verify alpha assumption
    verify_alpha_assumption(alpha)
    
    groups = group_by_source_type(data)
    llm_values = [row[metric_name] for row in groups['llm']]
    human_values = [row[metric_name] for row in groups['human']]
    
    logger.info(f"Analyzing {metric_name}: LLM (n={len(llm_values)}), Human (n={len(human_values)})")
    
    if not llm_values or not human_values:
        logger.warning(f"Insufficient data for {metric_name} analysis.")
        return {
            'p_value': 1.0,
            't_statistic': 0.0,
            'effect_size': 0.0,
            'is_significant': False
        }
    
    results = perform_independent_t_test(llm_values, human_values)
    results['alpha'] = alpha
    results['metric'] = metric_name
    
    return results

def run_statistical_tests(
    data: Optional[List[Dict[str, Any]]] = None,
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """
    Run all statistical tests for the project metrics.
    
    Args:
        data: Optional pre-loaded data. If None, loads from file.
        alpha: Significance level (default 0.05).
    
    Returns:
        Dictionary containing results for all metrics.
    """
    if data is None:
        data = load_metrics_data()
    
    # Verify alpha assumption globally
    verify_alpha_assumption(alpha)
    
    results = {}
    
    # Analyze comment density (comment_count)
    results['comment_density'] = run_analysis_for_metric(data, 'comment_count', alpha)
    
    # Analyze time to merge
    results['time_to_merge'] = run_analysis_for_metric(data, 'time_to_merge_minutes', alpha)
    
    # Analyze review cycles
    results['review_cycles'] = run_analysis_for_metric(data, 'review_cycles', alpha)
    
    logger.info("Statistical analysis completed.")
    return results

def main():
    """Main entry point for statistical tests module."""
    setup_logging()
    logger.info("Starting statistical tests analysis.")
    
    try:
        results = run_statistical_tests()
        
        # Save results to JSON
        output_path = get_path("results_json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        return results
    except Exception as e:
        logger.error(f"Error during statistical analysis: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()