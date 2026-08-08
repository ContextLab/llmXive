"""
Task T071: Confirm Statistical Robustness

Re-runs statistical tests (T028, T029) with zero-variance handling (T060) enabled
to ensure the final report (T031) accurately reflects the significance of the results
without numerical errors.

This script loads the experiment results from the multi-seed runs, performs the
Wilcoxon signed-rank tests with robust handling for zero variance, and updates
the statistical artifacts.
"""
import os
import sys
import json
import logging
import argparse
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy.stats import wilcoxon

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config
from metrics import StatisticalDegeneracyWarning

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RESULTS_DIR = "data/results"
PROCESSED_DIR = "data/processed"

def load_experiment_data() -> Dict[str, Any]:
    """
    Load the experiment results from the multi-seed runs.
    Expects artifacts from T027 (multi-seed execution) and T025d (threshold sweep).
    """
    # Load seeds
    seeds_path = os.path.join(RESULTS_DIR, "seeds.json")
    if not os.path.exists(seeds_path):
        raise FileNotFoundError(f"Required artifact missing: {seeds_path}")
    
    with open(seeds_path, 'r') as f:
        seeds = json.load(f)
    
    # Load baseline and clustering-aided NDCG scores for each seed
    baseline_ndcg = []
    clustering_ndcg = []
    baseline_wasted = []
    clustering_wasted = []
    
    for seed in seeds:
        seed_results_path = os.path.join(RESULTS_DIR, f"seed_{seed}_results.json")
        if not os.path.exists(seed_results_path):
            logger.warning(f"Seed results missing for {seed}, skipping...")
            continue
        
        with open(seed_results_path, 'r') as f:
            seed_data = json.load(f)
        
        # Extract NDCG@10 scores
        if 'baseline_ndcg' in seed_data:
            baseline_ndcg.append(seed_data['baseline_ndcg'])
        if 'clustering_ndcg' in seed_data:
            clustering_ndcg.append(seed_data['clustering_ndcg'])
        
        # Extract wasted call ratios
        if 'baseline_wasted_ratio' in seed_data:
            baseline_wasted.append(seed_data['baseline_wasted_ratio'])
        if 'clustering_wasted_ratio' in seed_data:
            clustering_wasted.append(seed_data['clustering_wasted_ratio'])
    
    if not baseline_ndcg or not clustering_ndcg:
        raise RuntimeError("No valid NDCG data found across seeds. Cannot perform statistical tests.")
    
    return {
        "seeds": seeds,
        "baseline_ndcg": baseline_ndcg,
        "clustering_ndcg": clustering_ndcg,
        "baseline_wasted": baseline_wasted,
        "clustering_wasted": clustering_wasted
    }

def run_wilcoxon_with_handling(
    group1: List[float],
    group2: List[float],
    test_name: str
) -> Dict[str, Any]:
    """
    Run Wilcoxon signed-rank test with explicit zero-variance handling (T060).
    
    If variance is zero (perfect scores or no difference), logs a warning and
    returns a p-value of 1.0 (no significant difference) instead of attempting
    a division-by-zero or returning NaN.
    """
    if len(group1) != len(group2):
        raise ValueError(f"Group sizes mismatch for {test_name}: {len(group1)} vs {len(group2)}")
    
    if len(group1) < 2:
        logger.warning(f"Insufficient data points for {test_name} (n={len(group1)}). Skipping test.")
        return {
            "test_name": test_name,
            "status": "skipped_insufficient_data",
            "p_value": None,
            "statistic": None,
            "message": "Insufficient data points for statistical test"
        }
    
    arr1 = np.array(group1)
    arr2 = np.array(group2)
    
    # Check for zero variance in differences
    differences = arr1 - arr2
    unique_diffs = np.unique(differences)
    
    if len(unique_diffs) == 1 and unique_diffs[0] == 0:
        # All differences are zero - perfect tie
        logger.warning(f"Zero variance detected in {test_name} (all differences are 0).")
        logger.warning("Returning p_value=1.0 (no significant difference) per T060 handling.")
        return {
            "test_name": test_name,
            "status": "zero_variance_detected",
            "p_value": 1.0,
            "statistic": 0.0,
            "message": "Zero variance detected: all differences are zero. No significant difference."
        }
    
    try:
        # Run Wilcoxon test
        statistic, p_value = wilcoxon(group1, group2)
        
        # Handle potential NaN or Inf
        if np.isnan(p_value) or np.isinf(p_value):
            logger.warning(f"Invalid p-value ({p_value}) for {test_name}. Treating as 1.0.")
            p_value = 1.0
        
        return {
            "test_name": test_name,
            "status": "success",
            "p_value": float(p_value),
            "statistic": float(statistic),
            "n_samples": len(group1),
            "message": "Wilcoxon signed-rank test completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Wilcoxon test failed for {test_name}: {str(e)}")
        return {
            "test_name": test_name,
            "status": "error",
            "p_value": None,
            "statistic": None,
            "error": str(e),
            "message": f"Test execution failed: {str(e)}"
        }

def update_statistical_artifacts(
    ndcg_result: Dict[str, Any],
    wasted_result: Dict[str, Any]
) -> None:
    """
    Update the statistical result artifacts with the new robust test results.
    """
    # Update NDCG result
    ndcg_path = os.path.join(RESULTS_DIR, "wilcoxon_ndcg.json")
    with open(ndcg_path, 'w') as f:
        json.dump(ndcg_result, f, indent=2)
    logger.info(f"Updated NDCG statistical results: {ndcg_path}")
    
    # Update wasted ratio result
    wasted_path = os.path.join(RESULTS_DIR, "wilcoxon_wasted.json")
    with open(wasted_path, 'w') as f:
        json.dump(wasted_result, f, indent=2)
    logger.info(f"Updated wasted ratio statistical results: {wasted_path}")

def main():
    """
    Main entry point for T071: Confirm Statistical Robustness.
    """
    parser = argparse.ArgumentParser(description="Confirm Statistical Robustness (T071)")
    parser.add_argument("--force", action="store_true", help="Force re-run even if artifacts exist")
    args = parser.parse_args()
    
    logger.info("Starting T071: Confirm Statistical Robustness")
    logger.info("Loading experiment data...")
    
    try:
        data = load_experiment_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("Cannot proceed without experiment data. Ensure T027 (multi-seed execution) has completed.")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    
    logger.info(f"Loaded data for {len(data['seeds'])} seeds")
    logger.info(f"Baseline NDCG samples: {len(data['baseline_ndcg'])}")
    logger.info(f"Clustering NDCG samples: {len(data['clustering_ndcg'])}")
    
    # Run Wilcoxon test for NDCG@10 (T028)
    logger.info("Running Wilcoxon test for NDCG@10 (T028)...")
    ndcg_result = run_wilcoxon_with_handling(
        data['baseline_ndcg'],
        data['clustering_ndcg'],
        "NDCG@10 comparison"
    )
    
    # Run Wilcoxon test for wasted call ratios (T029)
    logger.info("Running Wilcoxon test for wasted call ratios (T029)...")
    wasted_result = run_wilcoxon_with_handling(
        data['baseline_wasted'],
        data['clustering_wasted'],
        "Wasted call ratio comparison"
    )
    
    # Update artifacts
    logger.info("Updating statistical artifacts...")
    update_statistical_artifacts(ndcg_result, wasted_result)
    
    # Log summary
    logger.info("=" * 60)
    logger.info("T071 STATISTICAL ROBUSTNESS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"NDCG Test: {ndcg_result['status']}")
    if ndcg_result['p_value'] is not None:
        logger.info(f"  P-value: {ndcg_result['p_value']:.6f}")
        logger.info(f"  Significant (p<0.05): {ndcg_result['p_value'] < 0.05}")
    logger.info(f"Wasted Ratio Test: {wasted_result['status']}")
    if wasted_result['p_value'] is not None:
        logger.info(f"  P-value: {wasted_result['p_value']:.6f}")
        logger.info(f"  Significant (p<0.05): {wasted_result['p_value'] < 0.05}")
    logger.info("=" * 60)
    
    if ndcg_result['status'] == 'error' or wasted_result['status'] == 'error':
        logger.error("One or more statistical tests failed. Review logs above.")
        sys.exit(1)
    
    logger.info("T071 completed successfully. Statistical robustness confirmed.")
    sys.exit(0)

if __name__ == "__main__":
    main()