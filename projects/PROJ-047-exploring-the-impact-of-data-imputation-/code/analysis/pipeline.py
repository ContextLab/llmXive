from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
from .imputation import apply_mean_imputation, apply_knn_imputation, apply_mice_imputation
from .causal_estimation import estimate_ate_ipw, estimate_ate_psm
from .entities import SyntheticDataset, CausalEstimate, ImputationResult

def run_imputation_and_estimation(data: SyntheticDataset) -> Dict[str, Any]:
    """
    Orchestrate imputation and causal estimation pipeline.
    
    Input: Incomplete SyntheticDataset
    Output: Dictionary containing ATE estimates, standard errors, and status flags
            for all method/estimator combinations.
    
    Error Handling:
    - Detects non-convergent imputation runs (e.g., MICE max iterations reached)
    - Flags infinite or NaN estimates
    - Gracefully handles extreme missingness scenarios
    """
    results = {
        "status": "success",
        "warnings": [],
        "errors": [],
        "estimates": {}
    }
    
    # Define imputation methods
    imputation_methods = {
        "mean": apply_mean_imputation,
        "knn": apply_knn_imputation,
        "mice": apply_mice_imputation
    }
    
    # Define estimation methods
    estimation_methods = {
        "ipw": estimate_ate_ipw,
        "psm": estimate_ate_psm
    }
    
    # Track if any method failed
    has_failure = False
    
    for method_name, impute_func in imputation_methods.items():
        try:
            # Apply imputation
            imputed_data = impute_func(data)
            
            # Check for convergence issues in MICE
            if method_name == "mice" and hasattr(imputed_data, 'metadata'):
                if imputed_data.metadata.get('convergence_status') == 'failed':
                    results["warnings"].append(
                        f"MICE imputation did not converge for {method_name} method"
                    )
                    has_failure = True
            
            # Check for infinite or NaN values in imputed data
            if np.any(~np.isfinite(imputed_data.X.values)) or np.any(~np.isfinite(imputed_data.Y.values)):
                results["warnings"].append(
                    f"Imputed data contains non-finite values for {method_name} method"
                )
                has_failure = True
                continue
            
            # Store imputed result
            results["estimates"][method_name] = {}
            
            for est_name, est_func in estimation_methods.items():
                try:
                    # Apply causal estimation
                    estimate = est_func(
                        imputed_data,
                        treatment_col='T',
                        outcome_col='Y'
                    )
                    
                    # Check for infinite or NaN estimates
                    if not np.isfinite(estimate.ate):
                        results["warnings"].append(
                            f"Estimate {est_name} for {method_name} is non-finite: {estimate.ate}"
                        )
                        has_failure = True
                        results["estimates"][method_name][est_name] = {
                            "status": "failed",
                            "reason": "non_finite_estimate",
                            "ate": float('nan')
                        }
                        continue
                    
                    if not np.isfinite(estimate.se):
                        results["warnings"].append(
                            f"Standard error {est_name} for {method_name} is non-finite: {estimate.se}"
                        )
                        has_failure = True
                        results["estimates"][method_name][est_name] = {
                            "status": "failed",
                            "reason": "non_finite_se",
                            "ate": estimate.ate,
                            "se": float('nan')
                        }
                        continue
                    
                    # Store successful estimate
                    results["estimates"][method_name][est_name] = {
                        "status": "success",
                        "ate": float(estimate.ate),
                        "se": float(estimate.se),
                        "ci_lower": float(estimate.ci_lower),
                        "ci_upper": float(estimate.ci_upper)
                    }
                    
                except Exception as e:
                    error_msg = f"{est_name} estimation failed for {method_name}: {str(e)}"
                    results["errors"].append(error_msg)
                    results["estimates"][method_name][est_name] = {
                        "status": "failed",
                        "reason": "estimation_error",
                        "error_message": str(e)
                    }
                    has_failure = True
                    
        except Exception as e:
            error_msg = f"Imputation method {method_name} failed: {str(e)}"
            results["errors"].append(error_msg)
            results["estimates"][method_name] = {
                "status": "failed",
                "reason": "imputation_error",
                "error_message": str(e)
            }
            has_failure = True
    
    # Update overall status
    if has_failure:
        results["status"] = "partial_failure"
        results["summary"] = {
            "total_methods": len(imputation_methods) * len(estimation_methods),
            "successful": sum(
                1 for method in results["estimates"].values() 
                for est in method.values() 
                if est.get("status") == "success"
            ),
            "failed": sum(
                1 for method in results["estimates"].values() 
                for est in method.values() 
                if est.get("status") != "success"
            )
        }
    
    return results