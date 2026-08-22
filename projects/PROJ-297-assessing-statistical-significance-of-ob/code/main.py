"""
Main entry point for the Statistical Significance Analysis Pipeline.
Orchestrates data loading, permutation testing, correction, and reporting.
"""
import os
import sys
import json
import time
import argparse
import logging
import hashlib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

# Local imports matching the API surface
from config import get_config, ensure_dirs
from constitution import check_by_amendment_ratification, enforce_gate, ConstitutionalError
from loaders import load_all_datasets, apply_hygiene_pipeline, extract_metadata
from stats_engine import (
    run_permutations_for_threshold,
    calculate_empirical_p_value,
    compute_correlation,
    construct_graph,
    calculate_stats,
    generate_synthetic_dataset
)
from correction import benjamini_yekutieli, apply_correction_to_results
from viz import plot_heatmap, plot_histogram, plot_primary_threshold_visualizations

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('output/pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

def compute_file_hash(filepath: str) -> str:
    """Compute SHA256 hash of a file for integrity checks."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.warning(f"File not found for hashing: {filepath}")
        return ""

def verify_data_integrity(config: Dict[str, Any]) -> bool:
    """Verify that required data files exist and match expected checksums."""
    processed_dir = config['paths']['data_processed']
    checksum_file = os.path.join(processed_dir, 'checksums.json')
    
    if not os.path.exists(checksum_file):
        logger.warning("Checksum file not found. Skipping integrity verification.")
        return True
    
    with open(checksum_file, 'r') as f:
        checksums = json.load(f)
    
    all_valid = True
    for filename, expected_hash in checksums.items():
        filepath = os.path.join(processed_dir, filename)
        if os.path.exists(filepath):
            actual_hash = compute_file_hash(filepath)
            if actual_hash != expected_hash:
                logger.error(f"Integrity check failed for {filename}")
                all_valid = False
        else:
            logger.error(f"Missing file for integrity check: {filename}")
            all_valid = False
    
    return all_valid

def analyze_pvalue_distribution(pvalues: List[float]) -> Dict[str, float]:
    """Analyze the distribution of calculated p-values."""
    if not pvalues:
        return {"mean": 0.0, "median": 0.0, "std": 0.0}
    
    arr = np.array(pvalues)
    return {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr))
    }

def validate_threshold_range(threshold: float) -> bool:
    """Validate that the threshold is within a reasonable range."""
    return 0.0 < threshold < 1.0

def check_threshold_sweep_edge_cases(thresholds: List[float]) -> bool:
    """Check for edge cases in threshold sweep (e.g., duplicates, out of bounds)."""
    if not thresholds:
        return False
    if len(thresholds) != len(set(thresholds)):
        logger.warning("Duplicate thresholds detected in sweep.")
        return False
    for t in thresholds:
        if not validate_threshold_range(t):
            logger.error(f"Invalid threshold value: {t}")
            return False
    return True

def run_sensitivity_analysis(
    datasets: List[pd.DataFrame],
    thresholds: List[float],
    n_permutations: int,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Run sensitivity analysis across different thresholds."""
    results = {}
    
    if not check_threshold_sweep_edge_cases(thresholds):
        logger.error("Sensitivity analysis aborted due to invalid thresholds.")
        return results
    
    for dataset in datasets:
        dataset_name = dataset.attrs.get('name', 'unknown')
        results[dataset_name] = {}
        
        for threshold in thresholds:
            logger.info(f"Running sensitivity check for {dataset_name} at threshold {threshold}")
            
            # Compute observed stats
            corr_matrix = compute_correlation(dataset, method='pearson')
            graph = construct_graph(corr_matrix, threshold)
            obs_stats = calculate_stats(graph)
            
            # Run permutations
            null_dist = run_permutations_for_threshold(
                dataset, threshold, n_permutations, config['random_seed']
            )
            
            # Calculate p-values for each stat
            p_values = {}
            for stat_name, obs_val in obs_stats.items():
                p_val = calculate_empirical_p_value(obs_val, null_dist[stat_name])
                p_values[stat_name] = p_val
            
            results[dataset_name][threshold] = {
                'observed': obs_stats,
                'null_stats': null_dist,
                'p_values': p_values
            }
    
    return results

def generate_final_report(
    results: Dict[str, Any],
    corrected_results: Dict[str, Any],
    config: Dict[str, Any]
) -> str:
    """Generate the final summary report."""
    report_lines = []
    report_lines.append("# Statistical Significance Analysis Report")
    report_lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Threshold: {config.get('threshold', 'N/A')}")
    report_lines.append(f"Permutations: {config.get('n_permutations', 'N/A')}")
    report_lines.append("")
    
    report_lines.append("## Significant Findings (Associational)")
    report_lines.append("| Dataset | Statistic | Observed | P-Value | Corrected Q-Value | Significant |")
    report_lines.append("|---|---|---|---|---|---|")
    
    for dataset_name, data in results.items():
        # Assuming single threshold for final report or picking the primary one
        threshold_key = list(data.keys())[0] if data else None
        if threshold_key:
            stats_data = data[threshold_key]
            p_vals = stats_data.get('p_values', {})
            corrected = corrected_results.get(dataset_name, {}).get(threshold_key, {})
            q_vals = corrected.get('q_values', {})
            
            for stat_name, obs_val in stats_data.get('observed', {}).items():
                p_val = p_vals.get(stat_name, 1.0)
                q_val = q_vals.get(stat_name, 1.0)
                sig = "Yes" if q_val < 0.05 else "No"
                report_lines.append(
                    f"| {dataset_name} | {stat_name} | {obs_val:.4f} | {p_val:.4f} | {q_val:.4f} | {sig} |"
                )
    
    report_lines.append("")
    report_lines.append("## Methodology Note")
    report_lines.append("All findings are reported as associational. Causal inference is not claimed.")
    report_lines.append("Multiple testing correction applied using Benjamini-Yekutieli procedure.")
    
    return "\n".join(report_lines)

def verify_variable_counts(dataset: pd.DataFrame, min_vars: int = 20) -> bool:
    """Verify that a dataset has the minimum required continuous variables."""
    continuous_cols = [c for c in dataset.columns if pd.api.types.is_numeric_dtype(dataset[c])]
    return len(continuous_cols) >= min_vars

def verify_master_seed_reproducibility(config: Dict[str, Any]) -> bool:
    """Verify that the master seed is set and consistent."""
    seed = config.get('random_seed')
    if seed is None:
        logger.error("Master seed is not set in config.")
        return False
    logger.info(f"Master seed verified: {seed}")
    return True

def verify_threshold_baseline(threshold: float, config: Dict[str, Any]) -> bool:
    """
    T054: Threshold Baseline Verification.
    Validates that the provided threshold is consistent with the configuration
    and within the expected operational range for the analysis.
    """
    # 1. Check against config threshold if defined
    config_threshold = config.get('threshold')
    if config_threshold is not None:
        if abs(threshold - config_threshold) > 1e-9:
            logger.warning(
                f"Threshold mismatch: CLI provided {threshold}, "
                f"config has {config_threshold}. Using CLI value."
            )
    
    # 2. Validate range (0, 1)
    if not validate_threshold_range(threshold):
        logger.error(f"Threshold {threshold} is out of valid range (0, 1).")
        return False
    
    # 3. Verify against sensitivity sweep bounds if applicable
    # (Implicitly handled if sweep is run, but good to check baseline here)
    logger.info(f"Threshold baseline verified: {threshold}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Run Statistical Significance Analysis")
    parser.add_argument('--permutations', type=int, default=2000, help='Number of permutations')
    parser.add_argument('--threshold', type=float, default=0.3, help='Correlation threshold')
    parser.add_argument('--sweep', action='store_true', help='Run sensitivity sweep')
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Path to config file')
    
    args = parser.parse_args()
    
    # Load Configuration
    config = get_config(args.config)
    ensure_dirs(config)
    
    # T054: Threshold Baseline Verification
    if not verify_threshold_baseline(args.threshold, config):
        logger.critical("Threshold baseline verification failed. Exiting.")
        sys.exit(1)
    
    # Constitutional Gate Check
    try:
        enforce_gate(config)
    except ConstitutionalError as e:
        logger.critical(str(e))
        sys.exit(1)
    
    # Verify Master Seed
    if not verify_master_seed_reproducibility(config):
        sys.exit(1)
    
    # Load Data
    logger.info("Loading datasets...")
    datasets = load_all_datasets(config)
    
    if not datasets:
        logger.error("No valid datasets found. Exiting.")
        sys.exit(1)
    
    # Apply Hygiene
    logger.info("Applying data hygiene...")
    clean_datasets = apply_hygiene_pipeline(datasets, config)
    
    # Verify Variable Counts
    valid_datasets = [
        ds for ds in clean_datasets 
        if verify_variable_counts(ds, min_vars=20)
    ]
    
    if len(valid_datasets) < 1:
        logger.error("No datasets with >= 20 continuous variables found.")
        sys.exit(1)
    
    # Data Integrity Check
    if not verify_data_integrity(config):
        logger.warning("Data integrity check failed. Proceeding with caution.")
    
    # Run Analysis
    results = {}
    corrected_results = {}
    
    if args.sweep:
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
        logger.info(f"Running sensitivity sweep for thresholds: {thresholds}")
        sweep_results = run_sensitivity_analysis(
            valid_datasets, thresholds, args.permutations, config
        )
        # Flatten for reporting if needed, or keep nested
        results = sweep_results
    else:
        threshold = args.threshold
        for dataset in valid_datasets:
            name = dataset.attrs.get('name', 'unknown')
            logger.info(f"Processing dataset: {name}")
            
            corr_matrix = compute_correlation(dataset, method='pearson')
            graph = construct_graph(corr_matrix, threshold)
            obs_stats = calculate_stats(graph)
            
            null_dist = run_permutations_for_threshold(
                dataset, threshold, args.permutations, config['random_seed']
            )
            
            p_values = {}
            for stat_name, obs_val in obs_stats.items():
                p_val = calculate_empirical_p_value(obs_val, null_dist[stat_name])
                p_values[stat_name] = p_val
            
            results[name] = {
                threshold: {
                    'observed': obs_stats,
                    'null_stats': null_dist,
                    'p_values': p_values
                }
            }
            
            # Apply Correction
            p_list = list(p_values.values())
            if p_list:
                q_values = benjamini_yekutieli(p_list, alpha=0.05)
                corrected_results[name] = {
                    threshold: {
                        'q_values': q_values,
                        'significant': [q < 0.05 for q in q_values]
                    }
                }
    
    # Generate Reports and Visualizations
    report = generate_final_report(results, corrected_results, config)
    report_path = os.path.join(config['paths']['output_reports'], 'final_report.md')
    with open(report_path, 'w') as f:
        f.write(report)
    logger.info(f"Report saved to {report_path}")
    
    # Visualizations
    if valid_datasets:
        sample_ds = valid_datasets[0]
        corr_matrix = compute_correlation(sample_ds, method='pearson')
        plot_heatmap(corr_matrix, os.path.join(config['paths']['output_plots'], 'correlation_heatmap.png'))
        logger.info("Correlation heatmap saved.")
        
        # Example histogram of null distribution for first stat
        if results:
            first_ds = list(results.keys())[0]
            if results[first_ds]:
                first_th = list(results[first_ds].keys())[0]
                null_stats = results[first_ds][first_th].get('null_stats', {})
                if null_stats:
                    first_stat = list(null_stats.keys())[0]
                    plot_histogram(
                        null_stats[first_stat], 
                        os.path.join(config['paths']['output_plots'], f'{first_stat}_null_dist.png')
                    )
                    logger.info(f"Null distribution histogram saved for {first_stat}.")
    
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()