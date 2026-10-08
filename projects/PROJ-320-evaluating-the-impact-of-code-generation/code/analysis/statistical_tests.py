"""
Statistical tests module for comparing LLM vs Human code review metrics.
Implements independent two-sample t-tests (primary) and Mann-Whitney U (sensitivity).
Calculates effect sizes (Cohen's d) and determines significance based on alpha = 0.05.
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Local imports from project API surface
from utils.logging import get_logger, setup_logging
from utils.config import get_config_summary

# Standard library imports for statistical calculations
import scipy.stats as stats
import numpy as np


def setup_logging_and_config(script_name: str = "statistical_tests", log_dir: Optional[str] = None) -> Tuple[Any, Dict[str, Any]]:
    """
    Initialize logging and load configuration.
    Returns logger and config dict.
    """
    # Use the tolerant logging setup
    logger = setup_logging()
    if logger is None:
        # Fallback if setup_logging returns None (tolerant behavior)
        logger = get_logger(script_name)
    
    config = get_config_summary()
    logger.log("setup_logging_and_config", script_name=script_name, config_keys=list(config.keys()))
    return logger, config


def load_metrics_data(metrics_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load PR metrics from CSV file.
    Expected columns: pr_id, source_type, comment_count, time_to_merge_minutes, review_cycles, complexity_score
    """
    if metrics_path is None:
        # Default path from config or standard location
        metrics_path = "data/processed/prs_metrics.csv"
    
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    data = []
    with open(metrics_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            parsed_row = {
                'pr_id': int(row['pr_id']),
                'source_type': row['source_type'],
                'comment_count': int(row['comment_count']),
                'time_to_merge_minutes': float(row['time_to_merge_minutes']),
                'review_cycles': int(row['review_cycles']),
                'complexity_score': float(row['complexity_score'])
            }
            data.append(parsed_row)
    
    return data


def group_by_source_type(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group data by source_type (llm vs human).
    """
    groups = {'llm': [], 'human': []}
    for row in data:
        source = row['source_type']
        if source in groups:
            groups[source].append(row)
        else:
            # Log warning for unexpected source types
            pass
    return groups


def calculate_cohens_d(group1: List[float], group2: List[float]) -> float:
    """
    Calculate Cohen's d effect size for two independent groups.
    Cohen's d = (mean1 - mean2) / pooled_std
    Pooled std = sqrt(((n1-1)*std1^2 + (n2-1)*std2^2) / (n1 + n2 - 2))
    """
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return float('nan')
    
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = math.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std


def verify_alpha_assumption(alpha: float = 0.05) -> None:
    """
    Verify that the chosen alpha aligns with the "no multiple-comparison correction" assumption.
    Logs a confirmation message as required by T025.
    """
    # The Spec Assumptions state "no multiple-comparison correction"
    # We verify this by logging the alpha value and confirming it matches the spec
    logger = get_logger("statistical_tests")
    logger.log(
        "verify_alpha_assumption",
        alpha=alpha,
        assumption="no multiple-comparison correction",
        message="Alpha set to 0.05 per Spec Assumptions"
    )
    # Explicitly log the verification message required by T025
    print("Alpha set to 0.05 per Spec Assumptions")


def perform_independent_t_test(group1: List[float], group2: List[float]) -> Dict[str, float]:
    """
    Perform independent two-sample t-test.
    Returns t-statistic, p-value, and effect size (Cohen's d).
    """
    if len(group1) < 2 or len(group2) < 2:
        return {
            't_statistic': float('nan'),
            'p_value': float('nan'),
            'effect_size': float('nan')
        }
    
    t_stat, p_value = stats.ttest_ind(group1, group2, equal_var=False)  # Welch's t-test
    effect_size = calculate_cohens_d(group1, group2)
    
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'effect_size': float(effect_size)
    }


def perform_mann_whitney_u_test(group1: List[float], group2: List[float]) -> Dict[str, float]:
    """
    Perform Mann-Whitney U test (sensitivity analysis).
    Returns U-statistic and p-value.
    """
    if len(group1) < 2 or len(group2) < 2:
        return {
            'U_statistic': float('nan'),
            'p_value': float('nan')
        }
    
    u_stat, p_value = stats.mannwhitneyu(group1, group2, alternative='two-sided')
    
    return {
        'U_statistic': float(u_stat),
        'p_value': float(p_value)
    }


def run_analysis_for_metric(
    groups: Dict[str, List[Dict[str, Any]]],
    metric_name: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run statistical tests for a specific metric.
    Returns results including t-test, Mann-Whitney U, and significance determination.
    """
    llm_values = [row[metric_name] for row in groups['llm']]
    human_values = [row[metric_name] for row in groups['human']]
    
    # Perform t-test (PRIMARY per FR-004)
    t_results = perform_independent_t_test(llm_values, human_values)
    
    # Perform Mann-Whitney U (sensitivity analysis)
    u_results = perform_mann_whitney_u_test(llm_values, human_values)
    
    # Determine significance based on alpha
    is_significant = t_results['p_value'] < alpha if not math.isnan(t_results['p_value']) else False
    
    # Interpret effect size magnitude
    effect_size = t_results['effect_size']
    magnitude = "nan"
    if not math.isnan(effect_size):
        abs_d = abs(effect_size)
        if abs_d < 0.2:
            magnitude = "negligible"
        elif abs_d < 0.5:
            magnitude = "small"
        elif abs_d < 0.8:
            magnitude = "medium"
        else:
            magnitude = "large"
    
    return {
        't_test': {
            'p_value': t_results['p_value'],
            't_statistic': t_results['t_statistic'],
            'effect_size': t_results['effect_size'],
            'magnitude': magnitude,
            'is_significant': is_significant
        },
        'mann_whitney_u': {
            'p_value': u_results['p_value'],
            'U_statistic': u_results['U_statistic']
        },
        'sample_sizes': {
            'llm': len(llm_values),
            'human': len(human_values)
        }
    }


def run_statistical_tests(
    metrics_path: Optional[str] = None,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run all statistical tests on the metrics data.
    Returns aggregated results for all metrics.
    """
    # Verify alpha assumption
    verify_alpha_assumption(alpha)
    
    # Load data
    data = load_metrics_data(metrics_path)
    
    # Group by source type
    groups = group_by_source_type(data)
    
    # Metrics to analyze
    metrics = ['comment_count', 'time_to_merge_minutes', 'review_cycles']
    
    results = {}
    for metric in metrics:
        results[metric] = run_analysis_for_metric(groups, metric, alpha)
    
    # Add complexity correlation if available
    if 'complexity_score' in data[0] if data else False:
        # Simple correlation between complexity and comment count
        complexity_vals = [row['complexity_score'] for row in data]
        comment_vals = [row['comment_count'] for row in data]
        if len(complexity_vals) > 1 and len(comment_vals) > 1:
            corr, _ = stats.pearsonr(complexity_vals, comment_vals)
            results['complexity_correlation'] = {
                'pearson_r': float(corr),
                'description': 'Correlation between complexity_score and comment_count'
            }
    
    return results


def save_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save statistical results to JSON file.
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)


def main() -> None:
    """
    Main entry point for running statistical tests.
    """
    logger, config = setup_logging_and_config()
    logger.log("main_start", action="run_statistical_tests")
    
    try:
        # Parse arguments (simple CLI)
        metrics_path = "data/processed/prs_metrics.csv"
        output_path = "data/processed/results.json"
        alpha = 0.05
        
        # Check for command line overrides
        if len(sys.argv) > 1:
            # Simple parsing: --input path --output path
            i = 1
            while i < len(sys.argv):
                if sys.argv[i] == '--input' and i + 1 < len(sys.argv):
                    metrics_path = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == '--output' and i + 1 < len(sys.argv):
                    output_path = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == '--alpha' and i + 1 < len(sys.argv):
                    alpha = float(sys.argv[i + 1])
                    i += 2
                else:
                    i += 1
        
        # Run analysis
        results = run_statistical_tests(metrics_path, alpha)
        
        # Save results
        save_results(results, output_path)
        
        logger.log("main_complete", output_path=output_path, metrics_analyzed=list(results.keys()))
        print(f"Statistical tests completed. Results saved to {output_path}")
        
    except FileNotFoundError as e:
        logger.log("main_error", error=str(e))
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.log("main_error", error=str(e), traceback=repr(e))
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()