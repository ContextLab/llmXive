import os
import json
import csv
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from scipy import stats
from utils.logging import get_logger
from utils.config import get_config_summary

logger = get_logger(__name__)

# Configuration constants
ALPHA = 0.05
NO_MULTIPLE_COMPARISON_CORRECTION = True

def load_metrics_data(metrics_path: str = "data/processed/prs_metrics.csv") -> List[Dict[str, Any]]:
    """Load metrics from the processed CSV file."""
    data = []
    with open(metrics_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def group_by_source_type(data: List[Dict[str, Any]], metric_name: str) -> Tuple[List[float], List[float]]:
    """Split data into llm and human groups based on source_type."""
    llm_values = []
    human_values = []
    
    for row in data:
        source_type = row.get('source_type', '').strip().lower()
        try:
            value = float(row.get(metric_name, 0))
            if source_type == 'llm':
                llm_values.append(value)
            elif source_type == 'human':
                human_values.append(value)
            else:
                logger.warning(f"Unknown source_type '{source_type}' for PR {row.get('pr_id')}")
        except (ValueError, TypeError):
            logger.warning(f"Invalid metric value for {metric_name} in PR {row.get('pr_id')}: {row.get(metric_name)}")
    
    return llm_values, human_values

def calculate_cohens_d(group1: List[float], group2: List[float]) -> float:
    """Calculate Cohen's d effect size."""
    if not group1 or not group2:
        return 0.0
    
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = sum(group1) / n1, sum(group2) / n2
    
    var1 = sum((x - mean1) ** 2 for x in group1) / (n1 - 1) if n1 > 1 else 0
    var2 = sum((x - mean2) ** 2 for x in group2) / (n2 - 1) if n2 > 1 else 0
    
    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def verify_alpha_assumption(alpha: float = ALPHA) -> bool:
    """
    Verify that the chosen alpha aligns with the 'no multiple-comparison correction' assumption.
    
    This function checks:
    1. That alpha is set to the standard 0.05 threshold.
    2. That the global flag NO_MULTIPLE_COMPARISON_CORRECTION is True.
    
    Returns True if the assumption holds, raises ValueError otherwise.
    """
    if alpha != ALPHA:
        raise ValueError(
            f"Alpha must be {ALPHA} for this study design. "
            f"Received {alpha}. The protocol assumes no multiple-comparison correction."
        )
    
    if not NO_MULTIPLE_COMPARISON_CORRECTION:
        raise ValueError(
            "The study design requires NO_MULTIPLE_COMPARISON_CORRECTION to be True. "
            "Current setting is False, which violates the protocol assumption."
        )
    
    logger.info(f"Alpha verification passed: alpha={alpha}, no_correction={NO_MULTIPLE_COMPARISON_CORRECTION}")
    return True

def perform_independent_t_test(group1: List[float], group2: List[float]) -> Dict[str, Any]:
    """Perform independent two-sample t-test and calculate effect size."""
    if len(group1) < 2 or len(group2) < 2:
        return {
            't_statistic': None,
            'p_value': None,
            'effect_size': None,
            'n1': len(group1),
            'n2': len(group2),
            'note': 'Insufficient sample size for t-test'
        }
    
    t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)
    d = calculate_cohens_d(group1, group2)
    
    # Determine significance based on alpha
    is_significant = p_val < ALPHA if p_val is not None else False
    
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_val),
        'effect_size': float(d),
        'n1': len(group1),
        'n2': len(group2),
        'alpha': ALPHA,
        'is_significant': is_significant
    }

def run_analysis_for_metric(
    data: List[Dict[str, Any]], 
    metric_name: str, 
    include_sensitivity: bool = True
) -> Dict[str, Any]:
    """Run both t-test and Mann-Whitney U test for a specific metric."""
    # Verify alpha assumption before running analysis
    verify_alpha_assumption()
    
    llm_vals, human_vals = group_by_source_type(data, metric_name)
    
    logger.info(f"Analyzing {metric_name}: LLM (n={len(llm_vals)}), Human (n={len(human_vals)})")
    
    result = {
        'metric': metric_name,
        'n_llm': len(llm_vals),
        'n_human': len(human_vals),
        't_test': None,
        'mann_whitney': None
    }
    
    # Primary: T-test (FR-004)
    result['t_test'] = perform_independent_t_test(llm_vals, human_vals)
    
    # Sensitivity Analysis: Mann-Whitney U test (FR-008)
    if include_sensitivity:
        if len(llm_vals) >= 2 and len(human_vals) >= 2:
            u_stat, u_pval = stats.mannwhitneyu(llm_vals, human_vals, alternative='two-sided')
            is_sig = u_pval < ALPHA
            result['mann_whitney'] = {
                'u_statistic': float(u_stat),
                'p_value': float(u_pval),
                'n1': len(llm_vals),
                'n2': len(human_vals),
                'alpha': ALPHA,
                'is_significant': is_sig,
                'method': 'Mann-Whitney U (Sensitivity Analysis)'
            }
        else:
            result['mann_whitney'] = {
                'u_statistic': None,
                'p_value': None,
                'note': 'Insufficient sample size for Mann-Whitney U'
            }
    
    return result

def run_statistical_tests(
    metrics_path: str = "data/processed/prs_metrics.csv",
    output_path: str = "data/processed/results.json"
) -> Dict[str, Any]:
    """Run all statistical tests and save results."""
    # Verify alpha assumption at the start of the pipeline
    verify_alpha_assumption()
    
    logger.info(f"Loading metrics from {metrics_path}")
    data = load_metrics_data(metrics_path)
    
    if not data:
        raise ValueError("No data loaded from metrics file")
    
    metrics_to_test = ['comment_count', 'time_to_merge_minutes', 'review_cycles']
    all_results = {}
    
    for metric in metrics_to_test:
        logger.info(f"Running analysis for {metric}")
        all_results[metric] = run_analysis_for_metric(data, metric)
    
    # Add summary metadata
    all_results['metadata'] = {
        'total_prs': len(data),
        'alpha': ALPHA,
        'no_multiple_comparison_correction': NO_MULTIPLE_COMPARISON_CORRECTION,
        'primary_test': 'Independent T-Test',
        'sensitivity_test': 'Mann-Whitney U',
        'timestamp': str(os.popen('date -u +"%Y-%m-%dT%H:%M:%SZ"').read().strip())
    }
    
    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return all_results

def main():
    """Main entry point for statistical tests."""
    config = get_config_summary()
    logger.info("Starting statistical analysis pipeline")
    logger.info(f"Config: {config}")
    
    try:
        results = run_statistical_tests()
        print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()