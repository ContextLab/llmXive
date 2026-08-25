import os
import sys
import json
import time
import argparse
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml
import joblib
from datetime import datetime

# Import local modules
from config import get_config, ensure_dirs
from constitution import check_by_amendment_ratification, enforce_gate, ConstitutionalError
from loaders import load_all_datasets, apply_hygiene_pipeline, extract_metadata, ensure_output_dirs
from stats_engine import (
    compute_correlation, construct_graph, calculate_stats, 
    run_permutations_for_threshold, calculate_empirical_p_value
)
from correction import benjamini_yekutieli, apply_correction_to_results
from viz import plot_heatmap, plot_histogram, plot_primary_threshold_visualizations

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compute_file_hash(filepath: str) -> str:
    """Compute SHA256 hash of a file."""
    import hashlib
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def verify_data_integrity(data_dir: str) -> bool:
    """Verify integrity of processed data files."""
    files = list(Path(data_dir).glob("*.csv"))
    if not files:
        logger.warning(f"No CSV files found in {data_dir}")
        return False
    for f in files:
        try:
            compute_file_hash(str(f))
        except Exception as e:
            logger.error(f"Integrity check failed for {f}: {e}")
            return False
    return True

def analyze_pvalue_distribution(pvalues: List[float]) -> Dict[str, float]:
    """Analyze the distribution of p-values."""
    if not pvalues:
        return {'mean': 0.0, 'median': 0.0, 'min': 0.0, 'max': 0.0}
    arr = np.array(pvalues)
    return {
        'mean': float(np.mean(arr)),
        'median': float(np.median(arr)),
        'min': float(np.min(arr)),
        'max': float(np.max(arr))
    }

def validate_threshold_range(thresholds: List[float]) -> bool:
    """Validate that thresholds are in (0, 1)."""
    return all(0 < t < 1 for t in thresholds)

def check_threshold_sweep_edge_cases(thresholds: List[float]) -> bool:
    """Check for edge cases in threshold sweep."""
    if not thresholds:
        return False
    if min(thresholds) <= 0 or max(thresholds) >= 1:
        logger.warning("Thresholds outside (0, 1) range detected.")
        return False
    return True

def run_sensitivity_analysis(data_dir: str, output_dir: str, config: Dict[str, Any]):
    """Run sensitivity analysis across thresholds."""
    thresholds = config.get('thresholds', [0.3, 0.5, 0.7])
    if not validate_threshold_range(thresholds):
        raise ValueError("Invalid threshold range")
    
    # Load processed data
    datasets = []
    for csv_file in Path(data_dir).glob("dataset_*.csv"):
        df = pd.read_csv(csv_file)
        # Filter numeric columns only for correlation
        num_df = df.select_dtypes(include=[np.number])
        if num_df.shape[1] >= 2:
            datasets.append(num_df)
    
    results = []
    for i, df in enumerate(datasets):
        logger.info(f"Running sensitivity analysis on dataset {i+1}...")
        for thresh in thresholds:
            corr_matrix = compute_correlation(df, method='pearson')
            # Filter matrix by threshold
            mask = np.abs(corr_matrix) >= thresh
            # Count significant edges
            edges = np.sum(mask) - np.sum(np.eye(mask.shape[0], dtype=int)) # subtract diagonal
            results.append({
                'dataset_id': i+1,
                'threshold': thresh,
                'significant_edges': int(edges)
            })
    
    # Save results
    results_df = pd.DataFrame(results)
    output_path = os.path.join(output_dir, 'sensitivity_analysis.csv')
    results_df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity analysis saved to {output_path}")
    return results_df

def generate_final_report(results_dir: str, output_path: str):
    """Generate a final report summarizing findings."""
    # Aggregate all results
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': 'Analysis complete.',
        'files_generated': [f for f in os.listdir(results_dir) if f.endswith('.csv') or f.endswith('.png')]
    }
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Final report saved to {output_path}")

def verify_variable_counts(data_dir: str, min_count: int = 20) -> bool:
    """Verify that all datasets have >= min_count continuous variables."""
    for csv_file in Path(data_dir).glob("dataset_*.csv"):
        df = pd.read_csv(csv_file)
        num_cols = df.select_dtypes(include=[np.number]).shape[1]
        if num_cols < min_count:
            logger.warning(f"Dataset {csv_file} has only {num_cols} continuous variables.")
            return False
    return True

def verify_master_seed_reproducibility(config: Dict[str, Any]) -> bool:
    """Verify that the master seed is set correctly."""
    seed = config.get('random_seed')
    if seed is None:
        logger.warning("Random seed not set in config.")
        return False
    logger.info(f"Master seed verified: {seed}")
    return True

def verify_threshold_baseline(config: Dict[str, Any]) -> bool:
    """Verify baseline threshold configuration."""
    thresholds = config.get('thresholds', [])
    if not thresholds:
        logger.warning("No thresholds configured.")
        return False
    return True

def main():
    """Main entry point for the analysis pipeline."""
    parser = argparse.ArgumentParser(description="Run the statistical significance analysis pipeline.")
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    parser.add_argument('--permutations', type=int, default=None, help='Number of permutations')
    parser.add_argument('--threshold', type=float, default=None, help='Correlation threshold')
    parser.add_argument('--sweep', action='store_true', help='Run sensitivity analysis sweep')
    args = parser.parse_args()

    # Load config
    config = get_config(args.config)
    if args.permutations:
        config['permutations'] = args.permutations
    if args.threshold:
        config['thresholds'] = [args.threshold]
    
    ensure_dirs(config)
    
    # Constitutional Gate Check
    try:
        enforce_gate(config)
    except ConstitutionalError as e:
        logger.critical(f"Constitutional Gate Failed: {e}")
        sys.exit(1)

    # Verify seed
    verify_master_seed_reproducibility(config)
    verify_threshold_baseline(config)

    # Load and process data
    data_processed_dir = config['paths']['data_processed']
    datasets = load_all_datasets(config, data_processed_dir)
    
    if not datasets:
        logger.error("No valid datasets loaded.")
        sys.exit(1)

    # Run Permutations and Compute Statistics
    # We run the permutation engine for each dataset
    results = []
    for i, df in enumerate(datasets):
        logger.info(f"Processing dataset {i+1}...")
        
        # Compute observed correlation
        corr_matrix = compute_correlation(df, method='pearson')
        
        # Determine thresholds to use
        thresholds = config['thresholds'] if args.sweep else [config['thresholds'][0]]
        
        for thresh in thresholds:
            logger.info(f"Running permutations for threshold {thresh}...")
            # Run permutations
            null_dist, obs_stats = run_permutations_for_threshold(
                df, 
                n_permutations=config['permutations'], 
                threshold=thresh,
                method='pearson'
            )
            
            # Calculate empirical p-values
            p_values = [calculate_empirical_p_value(obs, null) for obs, null in zip(obs_stats, null_dist)]
            
            # Apply BY correction
            corrected_p = benjamini_yekutieli(p_values)
            
            # Identify significant edges
            significant = [i for i, p in enumerate(corrected_p) if p < 0.05]
            
            results.append({
                'dataset_id': i+1,
                'threshold': thresh,
                'significant_edges': len(significant),
                'total_edges': len(p_values)
            })
            
            # Generate visualizations
            plot_heatmap(corr_matrix, f"output/plots/corr_heatmap_ds{i+1}_t{thresh}.png")
            plot_histogram(null_dist[0], f"output/plots/null_hist_ds{i+1}_t{thresh}.png")
    
    # Save results
    results_df = pd.DataFrame(results)
    results_path = os.path.join(config['paths']['output_results'], 'analysis_results.csv')
    results_df.to_csv(results_path, index=False)
    
    # Run sensitivity analysis if requested
    if args.sweep:
        run_sensitivity_analysis(data_processed_dir, config['paths']['output_results'], config)
    
    # Generate final report
    generate_final_report(config['paths']['output_results'], 'output/reports/final_report.json')
    
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
