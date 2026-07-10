"""
Statistical Analysis Module for Code Maintainability Impact Study.

This module implements statistical analysis tasks including Wilcoxon Signed-Rank tests
and Benjamini-Hochberg correction for multiple comparisons.
"""
import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
from scipy import stats

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import get_logger

# Configure logging
logger = get_logger(__name__)

class AnalysisError(Exception):
    """Custom exception for analysis-related errors."""
    pass

def setup_output_directories():
    """Ensure required output directories exist."""
    directories = [
        "data/processed",
        "data/logs",
        "docs/paper"
    ]
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {dir_path}")

def load_matched_pairs(filepath: str = "data/processed/matched_pairs.csv") -> List[Dict[str, Any]]:
    """
    Load matched pairs from CSV file.

    Args:
        filepath: Path to the matched pairs CSV file.

    Returns:
        List of dictionaries representing matched pairs.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Matched pairs file not found: {filepath}")

    pairs = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pairs.append(row)

    logger.info(f"Loaded {len(pairs)} matched pairs from {filepath}")
    return pairs

def load_metrics_longitudinal(filepath: str = "data/processed/metrics_longitudinal.csv") -> List[Dict[str, Any]]:
    """
    Load longitudinal metrics from CSV file.

    Args:
        filepath: Path to the metrics CSV file.

    Returns:
        List of dictionaries representing metrics.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Metrics file not found: {filepath}")

    metrics = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            metrics.append(row)

    logger.info(f"Loaded {len(metrics)} metric records from {filepath}")
    return metrics

def join_metrics_with_pairs(pairs: List[Dict], metrics: List[Dict]) -> List[Dict]:
    """
    Join matched pairs with their longitudinal metrics.

    Args:
        pairs: List of matched pairs.
        metrics: List of longitudinal metrics.

    Returns:
        Joined list of dictionaries with pair and metric information.
    """
    # Create a lookup dictionary for metrics by pair_id
    metrics_lookup = {}
    for m in metrics:
        pair_id = m.get('pair_id')
        if pair_id:
            if pair_id not in metrics_lookup:
                metrics_lookup[pair_id] = []
            metrics_lookup[pair_id].append(m)

    joined_data = []
    for pair in pairs:
        pair_id = pair.get('pair_id')
        pair_metrics = metrics_lookup.get(pair_id, [])
        for metric in pair_metrics:
            combined = {**pair, **metric}
            joined_data.append(combined)

    logger.info(f"Joined {len(joined_data)} records")
    return joined_data

def save_joined_data(data: List[Dict], filepath: str = "data/processed/joined_analysis_data.csv"):
    """
    Save joined data to CSV file.

    Args:
        data: List of dictionaries to save.
        filepath: Output file path.
    """
    if not data:
        logger.warning("No data to save")
        return

    fieldnames = list(data[0].keys())
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    logger.info(f"Saved {len(data)} records to {filepath}")

def run_wilcoxon_tests(data: List[Dict]) -> Dict[str, Any]:
    """
    Perform Wilcoxon Signed-Rank tests on matched pairs for maintainability metrics.

    Compares LLM vs Human generated code for:
    - Code churn (lines changed)
    - Bug fix latency (days to fix)

    Args:
        data: Joined data containing matched pairs with metrics.

    Returns:
        Dictionary containing test results (statistic, p-value) for each metric.
    """
    # Separate LLM and Human blocks by pair_id
    pair_data = {}
    for row in data:
        pair_id = row.get('pair_id')
        if not pair_id:
            continue

        if pair_id not in pair_data:
            pair_data[pair_id] = {'llm': {}, 'human': {}}

        block_type = row.get('block_type', '').lower()
        if block_type not in ['llm', 'human']:
            continue

        # Extract metrics
        churn = row.get('churn_lines')
        latency = row.get('days_to_fix')

        if churn is not None and churn != '':
            try:
                pair_data[pair_id][block_type]['churn'] = float(churn)
            except ValueError:
                pass

        if latency is not None and latency != '':
            try:
                pair_data[pair_id][block_type]['latency'] = float(latency)
            except ValueError:
                pass

    # Prepare arrays for paired tests
    churn_llm = []
    churn_human = []
    latency_llm = []
    latency_human = []

    for pair_id, blocks in pair_data.items():
        llm_block = blocks.get('llm', {})
        human_block = blocks.get('human', {})

        # Churn comparison
        if 'churn' in llm_block and 'churn' in human_block:
            churn_llm.append(llm_block['churn'])
            churn_human.append(human_block['churn'])

        # Latency comparison (only if both have valid latency)
        if 'latency' in llm_block and 'latency' in human_block:
            latency_llm.append(llm_block['latency'])
            latency_human.append(human_block['latency'])

    results = {}

    # Wilcoxon test for churn
    if len(churn_llm) >= 2:
        try:
            stat, pval = stats.wilcoxon(churn_llm, churn_human)
            results['churn'] = {
                'statistic': float(stat),
                'p_value': float(pval),
                'n_pairs': len(churn_llm),
                'method': 'wilcoxon_signed_rank'
            }
            logger.info(f"Churn Wilcoxon: statistic={stat:.4f}, p-value={pval:.4f}, n={len(churn_llm)}")
        except Exception as e:
            logger.error(f"Wilcoxon test failed for churn: {e}")
            results['churn'] = {
                'error': str(e),
                'n_pairs': len(churn_llm)
            }
    else:
        logger.warning(f"Not enough pairs for churn test: {len(churn_llm)}")
        results['churn'] = {
            'error': 'Insufficient data',
            'n_pairs': len(churn_llm)
        }

    # Wilcoxon test for latency
    if len(latency_llm) >= 2:
        try:
            stat, pval = stats.wilcoxon(latency_llm, latency_human)
            results['latency'] = {
                'statistic': float(stat),
                'p_value': float(pval),
                'n_pairs': len(latency_llm),
                'method': 'wilcoxon_signed_rank'
            }
            logger.info(f"Latency Wilcoxon: statistic={stat:.4f}, p-value={pval:.4f}, n={len(latency_llm)}")
        except Exception as e:
            logger.error(f"Wilcoxon test failed for latency: {e}")
            results['latency'] = {
                'error': str(e),
                'n_pairs': len(latency_llm)
            }
    else:
        logger.warning(f"Not enough pairs for latency test: {len(latency_llm)}")
        results['latency'] = {
            'error': 'Insufficient data',
            'n_pairs': len(latency_llm)
        }

    return results

def apply_benjamini_hochberg_correction(p_values: List[Tuple[str, float]], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Benjamini-Hochberg correction for multiple comparisons.

    This method controls the False Discovery Rate (FDR) when performing
    multiple hypothesis tests.

    Args:
        p_values: List of tuples (test_name, p_value).
        alpha: Significance level (default: 0.05).

    Returns:
        Dictionary containing corrected results with significance flags.
    """
    if not p_values:
        return {'error': 'No p-values provided'}

    n_tests = len(p_values)
    logger.info(f"Applying Benjamini-Hochberg correction to {n_tests} tests")

    # Sort p-values by value, keeping track of original indices
    sorted_indices = sorted(range(n_tests), key=lambda i: p_values[i][1])
    sorted_p_values = [(p_values[i][0], p_values[i][1]) for i in sorted_indices]

    # Calculate critical values and determine significance
    results = []
    significant_count = 0

    for i, (test_name, p_val) in enumerate(sorted_p_values):
        # BH critical value: (i+1) * alpha / n
        critical_value = (i + 1) * alpha / n_tests
        is_significant = p_val <= critical_value

        results.append({
            'test_name': test_name,
            'raw_p_value': p_val,
            'critical_value': critical_value,
            'is_significant': is_significant,
            'rank': i + 1
        })

        if is_significant:
            significant_count += 1

    # Sort results back to original order for readability
    results.sort(key=lambda x: x['rank'])

    summary = {
        'alpha': alpha,
        'n_tests': n_tests,
        'significant_tests': significant_count,
        'method': 'benjamini_hochberg_fdr',
        'tests': results
    }

    logger.info(f"BH Correction complete: {significant_count}/{n_tests} tests significant at alpha={alpha}")
    return summary

def run_bh_correction_on_wilcoxon_results(wilcoxon_results: Dict[str, Any], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Benjamini-Hochberg correction to Wilcoxon test results.

    Args:
        wilcoxon_results: Dictionary containing Wilcoxon test results.
        alpha: Significance level (default: 0.05).

    Returns:
        Dictionary containing BH-corrected results.
    """
    # Extract valid p-values from Wilcoxon results
    p_value_pairs = []
    for metric_name, result in wilcoxon_results.items():
        if 'p_value' in result and 'error' not in result:
            p_value_pairs.append((f"wilcoxon_{metric_name}", result['p_value']))
            logger.info(f"Found p-value for {metric_name}: {result['p_value']:.4f}")

    if not p_value_pairs:
        logger.warning("No valid p-values found in Wilcoxon results for BH correction")
        return {
            'error': 'No valid p-values found',
            'original_results': wilcoxon_results
        }

    # Apply BH correction
    bh_results = apply_benjamini_hochberg_correction(p_value_pairs, alpha)

    # Combine with original results
    combined_results = {
        'wilcoxon_results': wilcoxon_results,
        'bh_correction': bh_results,
        'alpha': alpha
    }

    return combined_results

def save_statistical_results(results: Dict[str, Any], filepath: str = "data/processed/statistical_results.json"):
    """
    Save statistical results to JSON file.

    Args:
        results: Dictionary containing all statistical results.
        filepath: Output file path.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Saved statistical results to {filepath}")

def main():
    """
    Main entry point for statistical analysis pipeline.

    Executes:
    1. Load matched pairs and metrics
    2. Join data
    3. Run Wilcoxon Signed-Rank tests
    4. Apply Benjamini-Hochberg correction
    5. Save results
    """
    logger.info("Starting statistical analysis pipeline")
    setup_output_directories()

    try:
        # Load data
        pairs = load_matched_pairs()
        metrics = load_metrics_longitudinal()

        if not pairs:
            raise AnalysisError("No matched pairs found")
        if not metrics:
            raise AnalysisError("No longitudinal metrics found")

        # Join data
        joined_data = join_metrics_with_pairs(pairs, metrics)
        save_joined_data(joined_data)

        # Run Wilcoxon tests
        wilcoxon_results = run_wilcoxon_tests(joined_data)

        # Apply Benjamini-Hochberg correction
        bh_results = run_bh_correction_on_wilcoxon_results(wilcoxon_results)

        # Save all results
        save_statistical_results(bh_results)

        logger.info("Statistical analysis pipeline completed successfully")
        return bh_results

    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()