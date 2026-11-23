"""
Script to save Leave-One-Out (LOO) Jackknife results and stability metrics to artifacts.
This script executes the final step of User Story 3 (T032).
"""
import os
import sys
import json
import logging
from pathlib import Path
import numpy as np

# Add project root to path if running directly
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from robustness import load_loo_results, calculate_stability_metrics, load_fpca_results
from config import get_artifacts_dir
from update_state import update_state, load_current_state
from logging_config import setup_logging, get_logger

def save_loo_results_and_metrics():
    """
    Loads LOO results, calculates final stability metrics, saves artifacts,
    and updates the project state hash.
    """
    logger = get_logger(__name__)
    artifacts_dir = get_artifacts_dir()
    
    # Ensure artifacts directory exists
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading LOO Jackknife results from data/processed...")
    try:
        loo_results = load_loo_results()
    except FileNotFoundError:
        logger.error("LOO results file not found. Ensure T028-T031 have been run.")
        raise

    if not loo_results:
        logger.warning("No LOO results found. Saving empty metrics.")
        loo_results = {}

    logger.info(f"Processing {len(loo_results)} LOO iterations.")

    # Calculate stability metrics if not already present in the loaded results
    # The robustness module should have done this, but we ensure the final aggregation here.
    # We expect loo_results to contain 'full_fpca' and 'loo_runs' (list of dicts)
    full_fpca = loo_results.get('full_fpca')
    loo_runs = loo_results.get('loo_runs', [])

    stability_summary = {
        "total_iterations": len(loo_runs),
        "metrics": [],
        "unstable_modes": [],
        "mean_correlation": 0.0,
        "std_correlation": 0.0
    }

    if full_fpca and loo_runs:
        correlations = []
        for run_idx, run_data in enumerate(loo_runs):
            # Calculate correlation between full and LOO eigenfunctions for each component
            # Assuming run_data contains 'eigenfunctions' or 'loadings'
            # We need to align them first (Procrustes) - usually done in robustness.py calculate_stability_metrics
            # Here we assume the robustness module already did the heavy lifting and we are aggregating.
            
            # If the robustness module stored detailed metrics per run:
            run_correlations = run_data.get('correlations', [])
            if run_correlations:
                mean_run_corr = np.mean(run_correlations)
                correlations.append(mean_run_corr)
                
                # Identify unstable modes for this run (correlation < 0.95)
                for comp_idx, corr in enumerate(run_correlations):
                    if corr < 0.95:
                        stability_summary["unstable_modes"].append({
                            "iteration": run_idx,
                            "component": comp_idx,
                            "correlation": float(corr),
                            "removed_model": run_data.get('removed_model', 'unknown')
                        })

        if correlations:
            stability_summary["mean_correlation"] = float(np.mean(correlations))
            stability_summary["std_correlation"] = float(np.std(correlations))
            stability_summary["metrics"] = correlations

    # Save stability metrics summary
    metrics_path = artifacts_dir / "stability_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(stability_summary, f, indent=2)
    logger.info(f"Saved stability metrics to {metrics_path}")

    # Save full LOO results (raw data)
    loo_full_path = artifacts_dir / "loo_results_full.json"
    # Convert numpy types to native python types for JSON serialization
    def convert_numpy(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        if isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        if isinstance(obj, dict):
            return {k: convert_numpy(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert_numpy(i) for i in obj]
        return obj

    loo_serializable = convert_numpy(loo_results)
    with open(loo_full_path, 'w') as f:
        json.dump(loo_serializable, f, indent=2)
    logger.info(f"Saved full LOO results to {loo_full_path}")

    # Update project state hash to include new artifacts
    logger.info("Updating project state hash...")
    try:
        update_state()
        logger.info("State hash updated successfully.")
    except Exception as e:
        logger.error(f"Failed to update state hash: {e}")
        # Do not fail the script if state update fails, but log it

    return stability_summary

def main():
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Starting T032: Save LOO results and stability metrics.")
    
    try:
        results = save_loo_results_and_metrics()
        logger.info(f"Completed. Mean correlation: {results['mean_correlation']:.4f}, Std: {results['std_correlation']:.4f}")
        logger.info(f"Unstable modes identified: {len(results['unstable_modes'])}")
    except Exception as e:
        logger.critical(f"Task T032 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
