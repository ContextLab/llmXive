"""
Sensitivity analysis sweep for BINARY metrics using McNemar's test.

Analyzes recovery_success and task_success across significance levels (alpha)
to determine robustness of the Foundation Protocol vs. Native Direct Communication.

Generates: results/sensitivity_binary.csv
"""
import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
from scipy.stats import mcnemar
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Binary metrics to analyze
BINARY_METRICS = ['recovery_success', 'task_success']

# Significance levels to sweep
ALPHA_LEVELS = [0.01, 0.05, 0.10]

def load_experiment_data(data_path: str) -> List[Dict[str, Any]]:
    """
    Load experiment results from JSON file.
    
    Args:
        data_path: Path to the JSON file containing experiment results
        
    Returns:
        List of metric records from the experiment
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    return data.get('results', [])

def prepare_contingency_table(
    records: List[Dict[str, Any]], 
    metric: str
) -> Tuple[int, int, int, int]:
    """
    Prepare 2x2 contingency table for McNemar's test.
    
    Compares Foundation Protocol vs. Native Direct Communication outcomes.
    Table structure:
        |           | Direct: Success | Direct: Fail |
        |-----------|-----------------|--------------|
        | Foundation: Success | a             | b            |
        | Foundation: Fail    | c             | d            |
    
    Args:
        records: List of metric records
        metric: Name of the binary metric to analyze
        
    Returns:
        Tuple (a, b, c, d) representing the contingency table counts
    """
    a = b = c = d = 0
    
    # Group by seed to get paired comparisons
    seed_data: Dict[int, Dict[str, bool]] = {}
    
    for record in records:
        seed = record.get('seed')
        protocol = record.get('protocol')
        value = record.get(metric)
        
        if seed is None or protocol is None or value is None:
            continue
        
        if seed not in seed_data:
            seed_data[seed] = {}
        
        seed_data[seed][protocol] = bool(value)
    
    # Build contingency table from paired data
    for seed, outcomes in seed_data.items():
        foundation_success = outcomes.get('Foundation', False)
        direct_success = outcomes.get('Native Direct', False)
        
        if foundation_success and direct_success:
            a += 1  # Both success
        elif foundation_success and not direct_success:
            b += 1  # Foundation success, Direct fail
        elif not foundation_success and direct_success:
            c += 1  # Foundation fail, Direct success
        else:
            d += 1  # Both fail
    
    return a, b, c, d

def run_mcnemar_sweep(
    records: List[Dict[str, Any]],
    metrics: List[str],
    alphas: List[float]
) -> List[Dict[str, Any]]:
    """
    Run McNemar's test sweep across metrics and significance levels.
    
    Args:
        records: Experiment results
        metrics: List of binary metrics to analyze
        alphas: List of significance levels to test
        
    Returns:
        List of results with p-values and significance
    """
    results = []
    
    for metric in metrics:
        logger.info(f"Analyzing metric: {metric}")
        
        # Prepare contingency table
        a, b, c, d = prepare_contingency_table(records, metric)
        
        logger.info(f"  Contingency table: a={a}, b={b}, c={c}, d={d}")
        
        # Check if McNemar's test is applicable
        # Need at least some discordant pairs (b + c > 0)
        discordant = b + c
        
        if discordant == 0:
            logger.warning(f"  No discordant pairs for {metric}. Skipping test.")
            # Add results for all alphas as not significant (no difference detected)
            for alpha in alphas:
                results.append({
                    'alpha': alpha,
                    'metric': metric,
                    'p_value': 1.0,
                    'significant': False
                })
            continue
        
        # Run McNemar's test
        # Using exact method for small samples, chi2 for larger
        try:
            # scipy.stats.mcnemar returns (statistic, pvalue)
            # exact=True uses binomial distribution, exact=False uses chi2
            result = mcnemar((b, c), exact=(discordant < 25))
            p_value = result.pvalue
        except Exception as e:
            logger.error(f"  McNemar's test failed for {metric}: {e}")
            p_value = 1.0
        
        logger.info(f"  McNemar p-value: {p_value:.6f}")
        
        # Test against each alpha level
        for alpha in alphas:
            significant = p_value < alpha
            results.append({
                'alpha': alpha,
                'metric': metric,
                'p_value': p_value,
                'significant': significant
            })
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save sensitivity analysis results to CSV.
    
    Args:
        results: List of result dictionaries
        output_path: Path to output CSV file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    df = pd.DataFrame(results)
    df.to_csv(path, index=False)
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for sensitivity analysis sweep."""
    parser = argparse.ArgumentParser(
        description='Sensitivity analysis for binary metrics using McNemar\'s test'
    )
    parser.add_argument(
        '--data',
        type=str,
        default='data/experiment_results.json',
        help='Path to experiment results JSON file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/sensitivity_binary.csv',
        help='Path to output CSV file'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Loading data from {args.data}")
    
    try:
        records = load_experiment_data(args.data)
        logger.info(f"Loaded {len(records)} records")
        
        logger.info(f"Running McNemar sweep for metrics: {BINARY_METRICS}")
        logger.info(f"Across alpha levels: {ALPHA_LEVELS}")
        
        results = run_mcnemar_sweep(records, BINARY_METRICS, ALPHA_LEVELS)
        
        logger.info(f"Generated {len(results)} result entries")
        
        save_results(results, args.output)
        
        # Print summary
        df = pd.DataFrame(results)
        logger.info("Summary:")
        for metric in BINARY_METRICS:
            metric_df = df[df['metric'] == metric]
            sig_count = metric_df['significant'].sum()
            logger.info(f"  {metric}: {sig_count}/{len(ALPHA_LEVELS)} alpha levels show significance")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        logger.error("Please run experiments first to generate data/experiment_results.json")
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == '__main__':
    main()
