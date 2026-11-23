import os
import sys
import json
import pickle
import argparse
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

# Import from existing API surface
from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

def load_processed_data(filepath: str) -> List[Dict[str, Any]]:
    """Load processed descriptor data from CSV (handled by pandas in other modules, 
    but we assume results are already aggregated for this test)."""
    # This function is a placeholder as the actual data loading for the test
    # relies on the LOSO results which contain the aggregated metrics.
    # The actual CSV loading is done in T018/T021.
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    # In a real scenario, we might load the raw data here if needed for re-calculation,
    # but T025 operates on the fold-level MAE differences derived in T021/T024.
    return []

def load_loso_results(filepath: str) -> List[Dict[str, Any]]:
    """Load LOSO cross-validation results containing fold-level metrics."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"LOSO results file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Expected structure based on T021/T024 output:
    # { "folds": [ { "fold_id": "...", "rf_mae": float, "null_mae": float, ... }, ... ] }
    if "folds" not in data:
        raise ValueError("LOSO results missing 'folds' key")
    
    return data["folds"]

def load_null_results(filepath: str) -> List[Dict[str, Any]]:
    """Load null baseline comparison results."""
    # T024 generates baseline_comparison.json, but for the permutation test
    # we need per-fold data which should be in the LOSO results or a specific
    # per-fold baseline file. We assume T024 populated the fold-level data
    # into the LOSO results or a companion file.
    # If T024 only produced an aggregate, we might need to re-calculate or
    # assume the LOSO results from T021 include the null baseline per fold.
    # Based on T024 description: "Per-Fold Baseline... Generate data/artifacts/baseline_comparison.json"
    # We will assume the LOSO results file (from T021) now includes null_mae per fold
    # or we load a specific per-fold baseline file if it exists.
    # For robustness, let's try to load a specific per-fold baseline if available,
    # otherwise rely on the LOSO results.
    
    per_fold_baseline_path = os.path.join(os.path.dirname(filepath), "per_fold_baseline.json")
    if os.path.exists(per_fold_baseline_path):
        with open(per_fold_baseline_path, 'r') as f:
            return json.load(f)["folds"]
    
    # Fallback: if T021/T024 merged them, return the folds from the main LOSO file
    # This assumes the caller passed the correct LOSO file to both loaders or
    # we are re-using the same data structure.
    return []

def run_permutation_test(
    fold_results: List[Dict[str, Any]], 
    n_permutations: int = 1000, 
    seed: int = 42
) -> Tuple[float, float, float]:
    """
    Perform a permutation test on fold-level MAE differences.
    
    Algorithm:
    1. Calculate observed statistic: mean(abs(RF_MAE - Null_MAE)) or mean(RF_MAE - Null_MAE).
       The task asks to shuffle fold-level MAE differences.
       Let's define the difference D_i = Null_MAE_i - RF_MAE_i (positive means RF is better).
       Observed statistic: mean(D).
    2. Shuffle the differences D_i many times.
    3. Calculate the permuted statistic: mean(D_permuted).
    4. P-value = (count of permuted stats >= observed stat) / n_permutations.
       Note: If we are testing if RF is better (D > 0), we check if permuted mean >= observed mean.
       The task says: "Calculate the p-value as the fraction of permuted statistics (absolute mean difference) 
       that are >= the observed statistic."
       This implies the statistic is |mean(D)| or just mean(|D|)? 
       Re-reading: "Shuffle the fold-level MAE differences... fraction of permuted statistics (absolute mean difference) 
       that are >= the observed statistic."
       Let's interpret "absolute mean difference" as |mean(D)|.
       Observed: |mean(D_obs)|.
       Permuted: |mean(D_perm)|.
       P-value = count(|mean(D_perm)| >= |mean(D_obs)|) / n.
    
    Returns:
        p_value (float), observed_stat (float), mean_improvement (float)
    """
    if not fold_results or len(fold_results) < 2:
        raise ValueError("Insufficient fold results for permutation test. Need at least 2 folds.")

    # Extract differences: Null_MAE - RF_MAE (Positive = RF is better)
    differences = []
    for fold in fold_results:
        if "rf_mae" not in fold or "null_mae" not in fold:
            raise ValueError(f"Fold {fold.get('fold_id', 'unknown')} missing 'rf_mae' or 'null_mae'")
        diff = fold["null_mae"] - fold["rf_mae"]
        differences.append(diff)
    
    differences = np.array(differences)
    
    # Observed statistic: Absolute mean of differences
    observed_stat = np.abs(np.mean(differences))
    mean_improvement = np.mean(differences)
    
    np.random.seed(seed)
    count_extreme = 0
    
    for _ in range(n_permutations):
        # Shuffle the differences
        shuffled = np.random.permutation(differences)
        # Calculate permuted statistic: Absolute mean
        perm_stat = np.abs(np.mean(shuffled))
        if perm_stat >= observed_stat:
            count_extreme += 1
    
    p_value = count_extreme / n_permutations
    
    return p_value, observed_stat, mean_improvement

def main(args: Optional[argparse.Namespace] = None):
    if args is None:
        parser = argparse.ArgumentParser(description="Run Permutation Test for Model Significance (SC-008)")
        parser.add_argument("--loso-results", type=str, default="data/artifacts/loso_results.json",
                            help="Path to LOSO results JSON")
        parser.add_argument("--n-permutations", type=int, default=1000,
                            help="Number of permutations")
        parser.add_argument("--seed", type=int, default=42,
                            help="Random seed")
        parser.add_argument("--output", type=str, default="data/artifacts/permutation_pvalue.txt",
                            help="Output path for p-value")
        args = parser.parse_args()

    try:
        log_info("Loading LOSO results...")
        fold_results = load_loso_results(args.loso_results)
        
        log_info(f"Running permutation test with {args.n_permutations} permutations...")
        p_value, obs_stat, mean_imp = run_permutation_test(
            fold_results, 
            n_permutations=args.n_permutations, 
            seed=args.seed
        )
        
        log_info(f"Observed Statistic (|Mean Diff|): {obs_stat:.6f}")
        log_info(f"Mean Improvement (Null - RF): {mean_imp:.6f}")
        log_info(f"P-value: {p_value:.6f}")
        
        # Write output file
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(args.output, 'w') as f:
            f.write(f"{p_value:.10f}")
        
        log_info(f"P-value written to {args.output}")
        
        # Verification: Assert p < 0.05
        if p_value >= 0.05:
            log_warning(f"SC-008 NOT MET: p-value ({p_value:.4f}) >= 0.05. Model improvement may not be statistically significant.")
        else:
            log_info(f"SC-008 MET: p-value ({p_value:.4f}) < 0.05. Model improvement is statistically significant.")
            
        return p_value

    except FileNotFoundError as e:
        log_error(str(e), code=ErrorCode.DATA_SOURCE_MISSING)
        sys.exit(1)
    except ValueError as e:
        log_error(str(e), code=ErrorCode.INVALID_DATA_SCHEMA)
        sys.exit(1)
    except Exception as e:
        log_error(f"Permutation test failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()