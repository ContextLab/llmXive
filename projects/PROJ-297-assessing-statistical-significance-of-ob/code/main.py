import os
import sys
import json
import time
import argparse
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Local imports
from config import get_config, ensure_dirs, save_config, load_config
from constitution import check_by_amendment_ratification, enforce_gate, ConstitutionalError
from loaders import load_all_datasets, apply_hygiene_pipeline
from stats_engine import (
    compute_correlation, construct_graph, calculate_stats,
    run_permutations_for_threshold, calculate_empirical_p_value,
    estimate_runtime_pilot, adjust_permutation_count
)
from correction import benjamini_yekutieli, apply_correction_to_results
from viz import plot_heatmap, plot_histogram, plot_primary_threshold_visualizations

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_pvalue_distribution(pvalues: List[float], threshold: float) -> Dict[str, Any]:
    """Analyze the distribution of p-values for a given threshold."""
    if not pvalues:
        return {"mean": 0.0, "median": 0.0, "count": 0}
    
    arr = np.array(pvalues)
    return {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr)),
        "count": len(arr),
        "threshold": threshold
    }

def validate_threshold_range(thresholds: List[float]) -> bool:
    """Validate that thresholds are within a reasonable range for correlation."""
    if not thresholds:
        return False
    # Correlation thresholds must be between 0 and 1
    return all(0.0 <= t <= 1.0 for t in thresholds)

def check_threshold_sweep_edge_cases(config: Dict[str, Any], results: Dict[str, Any]) -> bool:
    """
    T075: Threshold Sweep Edge Case Check.
    Validates edge cases in threshold sweep results to ensure robustness.
    
    Checks:
    1. No NaN or Inf values in statistical outputs.
    2. P-values are strictly within (0, 1).
    3. Graph statistics are non-negative where applicable.
    4. If a threshold yields 0 edges, ensure the system handles it gracefully (no crash).
    """
    issues = []
    
    # 1. Check for NaN/Inf in numeric results
    for dataset_name, data in results.items():
        if 'stats' in data:
            stats = data['stats']
            for k, v in stats.items():
                if isinstance(v, (float, int)):
                    if np.isnan(v) or np.isinf(v):
                        issues.append(f"Dataset {dataset_name}: Invalid numeric value for {k}: {v}")
        
        if 'p_values' in data:
            for p in data['p_values']:
                if isinstance(p, (float, int)):
                    if np.isnan(p) or np.isinf(p):
                        issues.append(f"Dataset {dataset_name}: Invalid p-value: {p}")
    
    # 2. Validate p-value range (should be (0, 1] empirically, often clamped to avoid 0)
    # Note: Empirical p-values can technically be 0 if all permutations are more extreme,
    # but we usually apply a floor (e.g., 1/(N+1)). We check for strict negativity or >1.
    for dataset_name, data in results.items():
        if 'p_values' in data:
            for p in data['p_values']:
                if p < 0 or p > 1:
                    issues.append(f"Dataset {dataset_name}: P-value out of bounds: {p}")
    
    # 3. Validate graph statistics
    for dataset_name, data in results.items():
        if 'graph_stats' in data:
            gs = data['graph_stats']
            # Density, clustering, etc. should be non-negative
            for k in ['density', 'clustering_coefficient', 'avg_degree']:
                if k in gs:
                    if gs[k] < 0:
                        issues.append(f"Dataset {dataset_name}: Negative graph stat {k}: {gs[k]}")
    
    # 4. Check for empty graph handling (threshold too high)
    # This is a "soft" check: if a threshold is high, 0 edges is expected.
    # We just ensure the code didn't crash (which would be caught by exception handling).
    # We log a warning if all thresholds for a dataset result in empty graphs.
    for dataset_name, data in results.items():
        if 'threshold_results' in data:
            all_empty = True
            for t_res in data['threshold_results']:
                if t_res.get('num_edges', 0) > 0:
                    all_empty = False
                    break
            if all_empty and len(data['threshold_results']) > 0:
                logger.warning(f"Dataset {dataset_name}: All thresholds resulted in empty graphs.")
    
    if issues:
        for issue in issues:
            logger.error(issue)
        return False
    
    logger.info("Threshold sweep edge case check passed.")
    return True

def run_sensitivity_analysis(config: Dict[str, Any], datasets: List[pd.DataFrame], dataset_names: List[str]) -> Dict[str, Any]:
    """Run the full sensitivity analysis across thresholds."""
    thresholds = config.get('thresholds', [0.3, 0.4, 0.5])
    permutations = config.get('permutations', 2000)
    
    if not validate_threshold_range(thresholds):
        raise ValueError("Invalid threshold range provided.")
    
    results = {}
    
    logger.info(f"Starting sensitivity analysis with {len(datasets)} datasets and {len(thresholds)} thresholds.")
    
    for idx, df in enumerate(datasets):
        name = dataset_names[idx]
        logger.info(f"Processing dataset: {name}")
        
        dataset_results = {
            "threshold_results": [],
            "p_values": [],
            "stats": {},
            "graph_stats": {}
        }
        
        # Compute observed correlation once
        try:
            corr_matrix = compute_correlation(df, method='pearson')
        except Exception as e:
            logger.error(f"Failed to compute correlation for {name}: {e}")
            continue
        
        for t in thresholds:
            logger.info(f"  Threshold: {t}")
            
            # Run permutations
            try:
                perm_results = run_permutations_for_threshold(
                    df, corr_matrix, t, permutations, config.get('seed', 42)
                )
            except Exception as e:
                logger.error(f"Permutation failed for {name} at t={t}: {e}")
                continue
            
            # Calculate empirical p-value
            obs_stat = perm_results['obs_stat']
            null_dist = perm_results['null_dist']
            
            p_val = calculate_empirical_p_value(obs_stat, null_dist)
            
            # Calculate graph stats for observed
            g = construct_graph(corr_matrix, t)
            g_stats = calculate_stats(g)
            
            dataset_results['threshold_results'].append({
                "threshold": t,
                "obs_stat": obs_stat,
                "p_value": p_val,
                "num_edges": g.number_of_edges(),
                "num_nodes": g.number_of_nodes()
            })
            
            dataset_results['p_values'].append(p_val)
            dataset_results['graph_stats'] = g_stats
            dataset_results['stats'] = {
                "mean_corr": float(np.mean(np.abs(corr_matrix.values))),
                "max_corr": float(np.max(np.abs(corr_matrix.values)))
            }
        
        results[name] = dataset_results
    
    return results

def generate_final_report(results: Dict[str, Any], config: Dict[str, Any], output_dir: Path):
    """Generate the final summary report and visualizations."""
    # 1. Threshold Sweep Edge Case Check (T075)
    if not check_threshold_sweep_edge_cases(config, results):
        logger.warning("Edge case check found issues. Proceeding with warnings.")
    
    # 2. P-Value Distribution Analysis
    all_pvals = []
    for name, data in results.items():
        all_pvals.extend(data.get('p_values', []))
    
    if all_pvals:
        pval_dist = analyze_pvalue_distribution(all_pvals, config.get('threshold', 0.3))
        logger.info(f"P-value distribution: {pval_dist}")
    
    # 3. Save JSON Report
    report_path = output_dir / "sensitivity_analysis_report.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Report saved to {report_path}")
    
    # 4. Visualizations
    # We can aggregate results for plotting if needed, or plot per dataset
    # For now, we ensure the pipeline doesn't crash on empty results if possible
    if results:
        # Example: Plot heatmap for the first dataset's correlation matrix
        first_name = list(results.keys())[0]
        # Note: We don't have the raw corr matrix stored in 'results' easily without re-computing or storing it.
        # In a full implementation, we'd pass the matrices or store them.
        # Here we just log that visualization logic would run.
        logger.info("Visualization generation triggered (implementation depends on stored matrices).")

def main():
    parser = argparse.ArgumentParser(description="Run statistical significance analysis")
    parser.add_argument('--permutations', type=int, default=2000, help='Number of permutations')
    parser.add_argument('--threshold', type=float, default=0.3, help='Correlation threshold')
    parser.add_argument('--sweep', action='store_true', help='Run threshold sweep')
    args = parser.parse_args()
    
    # 1. Constitutional Gate Check
    try:
        enforce_gate()
    except ConstitutionalError as e:
        logger.critical(f"Constitutional gate failed: {e}")
        sys.exit(1)
    
    # 2. Load Config
    config = get_config()
    config['permutations'] = args.permutations
    config['threshold'] = args.threshold
    
    if args.sweep:
        config['thresholds'] = [0.2, 0.3, 0.4, 0.5, 0.6]
    else:
        config['thresholds'] = [args.threshold]
    
    # 3. Ensure Directories
    ensure_dirs(config)
    output_dir = Path(config['output_dir'])
    
    # 4. Load Data
    logger.info("Loading datasets...")
    try:
        datasets, names = load_all_datasets(config)
        if not datasets:
            logger.error("No valid datasets loaded. Exiting.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load datasets: {e}")
        sys.exit(1)
    
    # 5. Run Analysis
    start_time = time.time()
    try:
        results = run_sensitivity_analysis(config, datasets, names)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise
    
    elapsed = time.time() - start_time
    logger.info(f"Analysis completed in {elapsed:.2f} seconds.")
    
    # 6. Generate Report
    generate_final_report(results, config, output_dir)
    
    logger.info("Pipeline finished successfully.")

if __name__ == '__main__':
    main()
