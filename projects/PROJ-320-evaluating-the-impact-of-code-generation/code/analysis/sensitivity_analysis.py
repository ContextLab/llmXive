"""
Sensitivity Analysis: Re-run statistical tests using only the secondary detector cohort.

This module implements FR-008 by filtering the dataset to include only PRs that
were classified as 'llm' by the primary method AND have a high secondary detector score
(indicating strong LLM characteristics), then re-running the statistical tests to
verify robustness of the findings.

Output: data/processed/sensitivity_analysis_results.json
"""
import os
import json
import csv
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Import from existing modules
from data.extract_metrics import load_prs_labeled, load_complexity_scores, join_and_save_metrics
from analysis.statistical_tests import (
    load_metrics_data,
    group_by_source_type,
    calculate_cohens_d,
    verify_alpha_assumption,
    perform_independent_t_test,
    run_analysis_for_metric,
    run_statistical_tests,
    main as statistical_main
)
from utils.logging import get_logger, setup_logging
from utils.config import get_config_summary
from utils.seeds import set_global_seed

# Constants
DETECTOR_THRESHOLD = 0.7  # Threshold for secondary detector score to be considered "strong LLM signal"
ALPHA = 0.05

logger = get_logger(__name__)


def load_metrics_with_detector_scores(metrics_path: Path, labeled_path: Path) -> List[Dict[str, Any]]:
    """
    Load metrics data and join with detector scores from labeled dataset.
    
    Args:
        metrics_path: Path to prs_metrics.csv
        labeled_path: Path to prs_labeled.csv
        
    Returns:
        List of dictionaries containing merged metrics and detector scores
    """
    logger.info(f"Loading metrics from {metrics_path}")
    metrics_data = load_metrics_data(metrics_path)
    
    logger.info(f"Loading labeled data from {labeled_path}")
    labeled_prs = []
    with open(labeled_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            labeled_prs.append(row)
    
    # Create a lookup dictionary for labeled data
    labeled_lookup = {int(pr['pr_id']): pr for pr in labeled_prs}
    
    # Join metrics with detector scores
    merged_data = []
    for metric_row in metrics_data:
        pr_id = int(metric_row['pr_id'])
        if pr_id in labeled_lookup:
            labeled_row = labeled_lookup[pr_id]
            merged_row = metric_row.copy()
            merged_row['detector_score'] = float(labeled_row.get('detector_score', 0.0))
            merged_row['confidence_score'] = float(labeled_row.get('confidence_score', 0.0))
            merged_row['source_type'] = labeled_row['source_type']
            merged_data.append(merged_row)
    
    logger.info(f"Merged {len(merged_data)} records with detector scores")
    return merged_data


def filter_by_detector_cohort(
    data: List[Dict[str, Any]], 
    threshold: float = DETECTOR_THRESHOLD
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter dataset to separate primary cohort (all LLM) from secondary detector cohort
    (LLM with high detector scores).
    
    Args:
        data: Full dataset with detector scores
        threshold: Minimum detector score to be considered "strong LLM signal"
        
    Returns:
        Tuple of (primary_cohort, secondary_cohort)
    """
    primary_llm = [row for row in data if row['source_type'] == 'llm']
    secondary_llm = [row for row in data if row['source_type'] == 'llm' and float(row['detector_score']) >= threshold]
    
    # Human group remains the same for comparison
    human = [row for row in data if row['source_type'] == 'human']
    
    # Create secondary cohort: strong LLM signal vs human
    secondary_cohort = secondary_llm + human
    primary_cohort = primary_llm + human
    
    logger.info(f"Primary LLM cohort: {len(primary_llm)} PRs")
    logger.info(f"Secondary detector cohort (score >= {threshold}): {len(secondary_llm)} PRs")
    logger.info(f"Human cohort: {len(human)} PRs")
    
    return primary_cohort, secondary_cohort


def run_sensitivity_tests(
    primary_cohort: List[Dict[str, Any]],
    secondary_cohort: List[Dict[str, Any]],
    metrics: List[str] = ['comment_count', 'time_to_merge_minutes', 'review_cycles']
) -> Dict[str, Any]:
    """
    Run statistical tests on both cohorts and compare results.
    
    Args:
        primary_cohort: Full LLM + Human dataset
        secondary_cohort: Strong LLM signal + Human dataset
        metrics: List of metrics to test
        
    Returns:
        Dictionary containing results from both analyses
    """
    results = {
        'primary_cohort': {},
        'secondary_cohort': {},
        'comparison': {}
    }
    
    # Run tests on primary cohort
    logger.info("Running statistical tests on primary cohort...")
    primary_results = run_statistical_tests(primary_cohort, metrics, alpha=ALPHA)
    results['primary_cohort'] = primary_results
    
    # Run tests on secondary cohort
    logger.info("Running statistical tests on secondary detector cohort...")
    secondary_results = run_statistical_tests(secondary_cohort, metrics, alpha=ALPHA)
    results['secondary_cohort'] = secondary_results
    
    # Compare results
    for metric in metrics:
        if metric in primary_results and metric in secondary_results:
            primary_p = primary_results[metric].get('p_value', 1.0)
            secondary_p = secondary_results[metric].get('p_value', 1.0)
            
            # Check if significance is preserved
            primary_sig = primary_p < ALPHA
            secondary_sig = secondary_p < ALPHA
            
            results['comparison'][metric] = {
                'primary_p_value': primary_p,
                'secondary_p_value': secondary_p,
                'primary_significant': primary_sig,
                'secondary_significant': secondary_sig,
                'significance_preserved': primary_sig == secondary_sig,
                'p_value_change': abs(secondary_p - primary_p),
                'interpretation': "Significance preserved" if primary_sig == secondary_sig else "Significance changed - results not robust"
            }
    
    return results


def save_sensitivity_results(results: Dict[str, Any], output_path: Path):
    """
    Save sensitivity analysis results to JSON file.
    
    Args:
        results: Dictionary containing all analysis results
        output_path: Path to save the results JSON
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Sensitivity analysis results saved to {output_path}")


def run_sensitivity_analysis(
    metrics_path: Optional[Path] = None,
    labeled_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    detector_threshold: float = DETECTOR_THRESHOLD
):
    """
    Main entry point for sensitivity analysis.
    
    Args:
        metrics_path: Path to prs_metrics.csv (default: data/processed/prs_metrics.csv)
        labeled_path: Path to prs_labeled.csv (default: data/processed/prs_labeled.csv)
        output_path: Path for results JSON (default: data/processed/sensitivity_analysis_results.json)
        detector_threshold: Threshold for secondary detector score
    """
    # Setup paths
    if metrics_path is None:
        metrics_path = Path('data/processed/prs_metrics.csv')
    if labeled_path is None:
        labeled_path = Path('data/processed/prs_labeled.csv')
    if output_path is None:
        output_path = Path('data/processed/sensitivity_analysis_results.json')
    
    # Verify input files exist
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    if not labeled_path.exists():
        raise FileNotFoundError(f"Labeled data file not found: {labeled_path}")
    
    logger.info(f"Starting sensitivity analysis with detector threshold: {detector_threshold}")
    logger.info(f"Input metrics: {metrics_path}")
    logger.info(f"Input labeled data: {labeled_path}")
    logger.info(f"Output results: {output_path}")
    
    # Load and merge data
    data = load_metrics_with_detector_scores(metrics_path, labeled_path)
    
    if len(data) == 0:
        raise ValueError("No data found after merging metrics and labeled datasets")
    
    # Filter into cohorts
    primary_cohort, secondary_cohort = filter_by_detector_cohort(data, detector_threshold)
    
    if len(secondary_cohort) < 20:
        logger.warning(f"Secondary cohort is small ({len(secondary_cohort)} PRs). Results may have low statistical power.")
    
    # Run statistical tests
    results = run_sensitivity_tests(primary_cohort, secondary_cohort)
    
    # Add metadata
    results['metadata'] = {
        'detector_threshold': detector_threshold,
        'alpha': ALPHA,
        'primary_cohort_size': len(primary_cohort),
        'secondary_cohort_size': len(secondary_cohort),
        'config_summary': get_config_summary()
    }
    
    # Save results
    save_sensitivity_results(results, output_path)
    
    # Print summary
    logger.info("=" * 60)
    logger.info("SENSITIVITY ANALYSIS SUMMARY")
    logger.info("=" * 60)
    for metric, comparison in results['comparison'].items():
        logger.info(f"Metric: {metric}")
        logger.info(f"  Primary p-value: {comparison['primary_p_value']:.4f} (significant: {comparison['primary_significant']})")
        logger.info(f"  Secondary p-value: {comparison['secondary_p_value']:.4f} (significant: {comparison['secondary_significant']})")
        logger.info(f"  Significance preserved: {comparison['significance_preserved']}")
        logger.info(f"  Interpretation: {comparison['interpretation']}")
        logger.info("-" * 40)
    
    logger.info(f"Sensitivity analysis complete. Results saved to {output_path}")
    return results


def main():
    """Main entry point for command-line execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run sensitivity analysis on LLM vs Human PR comparison')
    parser.add_argument('--metrics-path', type=str, default='data/processed/prs_metrics.csv',
                      help='Path to metrics CSV file')
    parser.add_argument('--labeled-path', type=str, default='data/processed/prs_labeled.csv',
                      help='Path to labeled PRs CSV file')
    parser.add_argument('--output-path', type=str, default='data/processed/sensitivity_analysis_results.json',
                      help='Path for output results JSON')
    parser.add_argument('--detector-threshold', type=float, default=DETECTOR_THRESHOLD,
                      help='Threshold for secondary detector score (default: 0.7)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_level='INFO')
    
    # Set random seed
    set_global_seed(args.seed)
    
    # Run analysis
    try:
        results = run_sensitivity_analysis(
            metrics_path=Path(args.metrics_path),
            labeled_path=Path(args.labeled_path),
            output_path=Path(args.output_path),
            detector_threshold=args.detector_threshold
        )
        logger.info("Sensitivity analysis completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())
