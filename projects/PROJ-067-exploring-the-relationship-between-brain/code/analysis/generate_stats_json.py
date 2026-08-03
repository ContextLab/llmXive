import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from analysis.stats import calculate_spearman_correlation, apply_fdr_correction, load_metrics_and_dream_recall
from analysis.permutation_test import run_permutation_test
from analysis.power_analysis import run_post_hoc_power_analysis

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_analysis_results(metrics_path: str = "data/metrics/subject_metrics.csv") -> Dict[str, Any]:
    """
    Loads metrics and dream recall frequency, calculates Spearman correlations,
    and returns the raw results dictionary.
    """
    logger.info(f"Loading analysis data from {metrics_path}")
    metrics_df, dream_recall_df = load_metrics_and_dream_recall(metrics_path)
    
    results = {}
    metrics_columns = [col for col in metrics_df.columns if col != 'subject_id']
    
    for metric_name in metrics_columns:
        logger.info(f"Calculating Spearman correlation for {metric_name}")
        rho, p_uncorrected = calculate_spearman_correlation(metrics_df[metric_name], dream_recall_df['dream_recall_frequency'])
        results[metric_name] = {
            'rho': float(rho),
            'p_uncorrected': float(p_uncorrected)
        }
    
    return results

def apply_fdr_and_permutation(results: Dict[str, Any], n_permutations: int = 1000, seed: int = 42) -> Dict[str, Any]:
    """
    Applies FDR correction and runs permutation tests for all metrics.
    Updates the results dictionary in-place.
    """
    logger.info("Applying FDR correction...")
    p_values = [results[m]['p_uncorrected'] for m in results]
    corrected_p_values = apply_fdr_correction(p_values)
    
    for i, metric_name in enumerate(results):
        results[metric_name]['p_fdr_corrected'] = float(corrected_p_values[i])
    
    logger.info(f"Running permutation tests ({n_permutations} iterations)...")
    # Assuming metrics_df and dream_recall_df are accessible or passed. 
    # We need to reload them here or pass them. For simplicity, reloading from standard path.
    metrics_path = "data/metrics/subject_metrics.csv"
    metrics_df, dream_recall_df = load_metrics_and_dream_recall(metrics_path)
    
    for metric_name in results:
        logger.info(f"  Permutation test for {metric_name}...")
        p_perm = run_permutation_test(
            metrics_df[metric_name].values, 
            dream_recall_df['dream_recall_frequency'].values, 
            n_permutations=n_permutations, 
            seed=seed
        )
        results[metric_name]['p_permutation'] = float(p_perm)
    
    return results

def add_power_analysis(results: Dict[str, Any], n_subjects: int = 50, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Adds post-hoc power analysis results to the metrics.
    """
    logger.info("Calculating post-hoc power analysis...")
    power_results = {}
    
    for metric_name, stats in results.items():
        rho = stats['rho']
        power_info = run_post_hoc_power_analysis(rho, n_subjects, alpha)
        power_results[metric_name] = power_info
    
    results['_power_analysis'] = power_results
    return results

def main():
    """
    Main entry point for generating the stats.json file.
    Orchestrates loading, correlation, FDR, permutation, and power analysis.
    """
    logger.info("Starting stats.json generation (T042)...")
    
    # 1. Load data and calculate raw correlations
    raw_results = load_analysis_results()
    
    # 2. Apply FDR and Permutation tests
    enriched_results = apply_fdr_and_permutation(raw_results)
    
    # 3. Add Power Analysis
    final_results = add_power_analysis(enriched_results)
    
    # 4. Write to results/stats.json
    output_path = Path("results/stats.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Successfully wrote results to {output_path}")
    return final_results

if __name__ == "__main__":
    main()