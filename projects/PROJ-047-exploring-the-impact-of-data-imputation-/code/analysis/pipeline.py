"""
Pipeline module for running imputation and causal estimation.
Orchestrates the full workflow from incomplete data to ATE estimates.
"""
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
import warnings
import logging
from datetime import datetime
import json
import os

# Import from local analysis modules
from .imputation import apply_mean_imputation, apply_knn_imputation, apply_mice_imputation
from .causal_estimation import estimate_ate_ipw, estimate_ate_psm
from .se_combination import apply_bootstrap_ci, apply_rubins_rules
from .entities import ImputationResult, CausalEstimate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Error log file path
ERROR_LOG_PATH = "data/results/run_errors.log"

def _ensure_error_log_exists():
    """Ensure the error log directory and file exist."""
    os.makedirs(os.path.dirname(ERROR_LOG_PATH), exist_ok=True)
    if not os.path.exists(ERROR_LOG_PATH):
        with open(ERROR_LOG_PATH, 'w') as f:
            f.write("Convergence Failure Log\n")
            f.write("=" * 50 + "\n")

def _log_error(run_id: str, method: str, estimator: str, error_msg: str):
    """Log a convergence or estimation failure to the error log file."""
    _ensure_error_log_exists()
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "run_id": run_id,
        "method": method,
        "estimator": estimator,
        "error": error_msg
    }
    with open(ERROR_LOG_PATH, 'a') as f:
        f.write(json.dumps(log_entry) + "\n")
    logger.warning(f"Logged error for run {run_id}: {error_msg}")

def run_imputation_and_estimation(
    data: Dict[str, Any],
    run_id: str,
    beta: float
) -> List[Dict[str, Any]]:
    """
    Run the full imputation and estimation pipeline on the provided data.
    
    Args:
        data: Dictionary containing 'X', 'T', 'Y', 'mask' keys with incomplete data.
        run_id: Unique identifier for this simulation run.
        beta: The MNAR parameter used for this run.
    
    Returns:
        List of dictionaries containing ATE estimates, standard errors, and metadata.
        Each dictionary corresponds to a (imputation_method, estimator) combination.
        If a run fails, the entry will have status='failed' and NaN metrics.
    """
    results = []
    
    # Define imputation methods and their wrappers
    imputation_methods = [
        ("mean", apply_mean_imputation),
        ("knn", lambda d: apply_knn_imputation(d, k=5)),
        ("mice", apply_mice_imputation)
    ]
    
    # Define causal estimators
    estimators = [
        ("ipw", estimate_ate_ipw),
        ("psm", estimate_ate_psm)
    ]
    
    for method_name, impute_func in imputation_methods:
        imputed_data = None
        imputation_status = "success"
        imputation_error = None
        
        try:
            logger.info(f"Run {run_id}: Applying {method_name} imputation...")
            imputed_data = impute_func(data)
            
            # Check for convergence warnings or failures in MICE
            if method_name == "mice":
                if imputed_data.get('status') == 'failed':
                    imputation_status = "failed"
                    imputation_error = f"MICE failed to converge after max iterations"
                    logger.warning(f"Run {run_id}: {imputation_error}")
                    
        except Exception as e:
            imputation_status = "failed"
            imputation_error = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Run {run_id}: Imputation failed with {imputation_error}")
            _log_error(run_id, method_name, "all", imputation_error)
        
        if imputation_status == "failed":
            # Create failed result entries for all estimators
            for est_name, _ in estimators:
                results.append({
                    "run_id": run_id,
                    "beta": beta,
                    "method": method_name,
                    "estimator": est_name,
                    "ate": np.nan,
                    "se": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "status": "failed",
                    "error": imputation_error
                })
            continue
        
        # If imputation succeeded, proceed with estimation
        df_imputed = imputed_data.get('df', imputed_data) if isinstance(imputed_data, dict) else imputed_data
        
        for est_name, est_func in estimators:
            est_result = None
            est_status = "success"
            est_error = None
            
            try:
                logger.info(f"Run {run_id}: Applying {est_name} estimation...")
                
                # Run estimation
                est_result = est_func(
                    df_imputed,
                    treatment_col='T',
                    outcome_col='Y'
                )
                
                # Check for infinite or NaN results
                if est_result is None or not isinstance(est_result, dict):
                    raise ValueError("Estimation returned invalid result format")
                    
                ate = est_result.get('ate', np.nan)
                se = est_result.get('se', np.nan)
                
                if np.isinf(ate) or np.isnan(ate) or np.isinf(se) or np.isnan(se):
                    est_status = "failed"
                    est_error = f"Invalid estimate: ate={ate}, se={se}"
                    logger.warning(f"Run {run_id}: {est_error}")
                    
            except Exception as e:
                est_status = "failed"
                est_error = f"{type(e).__name__}: {str(e)}"
                logger.error(f"Run {run_id}: Estimation failed with {est_error}")
                _log_error(run_id, method_name, est_name, est_error)
            
            if est_status == "failed":
                results.append({
                    "run_id": run_id,
                    "beta": beta,
                    "method": method_name,
                    "estimator": est_name,
                    "ate": np.nan,
                    "se": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "status": "failed",
                    "error": est_error
                })
            else:
                # Calculate confidence intervals
                ate_val = est_result['ate']
                se_val = est_result['se']
                
                # Use bootstrap CI for non-MICE methods, Rubins for MICE
                if method_name == "mice":
                    # For MICE, we would use Rubins rules if we had multiple imputations
                    # For now, use bootstrap as fallback
                    ci_lower, ci_upper = apply_bootstrap_ci([ate_val], n_boot=100)
                else:
                    ci_lower, ci_upper = apply_bootstrap_ci([ate_val], n_boot=100)
                
                results.append({
                    "run_id": run_id,
                    "beta": beta,
                    "method": method_name,
                    "estimator": est_name,
                    "ate": float(ate_val),
                    "se": float(se_val),
                    "ci_lower": float(ci_lower[0]) if hasattr(ci_lower, '__len__') else float(ci_lower),
                    "ci_upper": float(ci_upper[0]) if hasattr(ci_upper, '__len__') else float(ci_upper),
                    "status": "success",
                    "error": None
                })
    
    return results

def main():
    """
    CLI entry point for testing the pipeline.
    This is primarily for development and testing purposes.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Run imputation and estimation pipeline')
    parser.add_argument('--run-id', type=str, default='test_run', help='Unique run identifier')
    parser.add_argument('--beta', type=float, default=0.5, help='MNAR parameter beta')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    # Generate test data
    from simulation.scm_generator import generate_scm
    from simulation.missingness import inject_mnar, tune_alpha
    
    # Generate complete data
    dataset = generate_scm(seed=args.seed, n=1000, tau_true=0.5)
    
    # Inject missingness
    alpha = tune_alpha(beta=args.beta, target_rate=0.3)
    incomplete_data = inject_mnar(dataset, beta=args.beta, target_rate=0.3)
    
    # Run pipeline
    results = run_imputation_and_estimation(
        data=incomplete_data,
        run_id=args.run_id,
        beta=args.beta
    )
    
    # Print results
    print(f"Pipeline completed for run {args.run_id}")
    for res in results:
        print(f"  {res['method']}/{res['estimator']}: {res['status']} - ATE={res['ate']:.4f}")

if __name__ == '__main__':
    main()
