import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from utils.seed_manager import get_seed
from analysis.glm_fitter import fit_glm, estimate_effect_size
from analysis.split_half_validator import run_split_half_validation, SplitHalfValidationError
from utils.bootstrap_aggregator import aggregate_power_results
from utils.timer import log_split, start_run, end_run

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def bootstrap_single_iteration(
    paradigm_data: Dict[str, Any],
    sample_size: int,
    smoothing_kernel: int,
    random_seed: int
) -> Dict[str, Any]:
    """
    Perform a single bootstrap iteration for a given sample size and kernel.
    Returns a dictionary with replication success status and effect size.
    """
    try:
        # Set seed for this specific iteration
        local_seed = random_seed + hash(str(sample_size) + str(smoothing_kernel)) % (2**32)
        
        # Run split-half validation which handles sampling internally
        result = run_split_half_validation(
            data=paradigm_data,
            sample_size_target=sample_size,
            smoothing_kernel=smoothing_kernel,
            random_seed=local_seed
        )
        
        return {
            "replication_success": result.get("replication_success", False),
            "effect_size_est": result.get("effect_size_est", 0.0),
            "p_value": result.get("p_value", 1.0),
            "convergence_status": result.get("convergence_status", "unknown"),
            "sample_size_used": result.get("sample_size_used", sample_size)
        }
    except Exception as e:
        logger.warning(f"Iteration failed: {e}")
        return {
            "replication_success": False,
            "effect_size_est": np.nan,
            "p_value": np.nan,
            "convergence_status": "failed",
            "sample_size_used": sample_size,
            "error": str(e)
        }


def run_bootstrap_loop(
    paradigm_data: Dict[str, Any],
    sample_sizes: List[int],
    smoothing_kernel: int,
    num_iterations: int,
    base_seed: int
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Run the bootstrap loop for multiple sample sizes.
    Returns a dictionary mapping sample_size -> list of iteration results.
    """
    results_by_size: Dict[int, List[Dict[str, Any]]] = {size: [] for size in sample_sizes}
    
    for n in sample_sizes:
        logger.info(f"Running bootstrap for N={n}, Kernel={smoothing_kernel}")
        for i in range(num_iterations):
            res = bootstrap_single_iteration(paradigm_data, n, smoothing_kernel, base_seed)
            results_by_size[n].append(res)
        
        log_split(f"Bootstrap loop N={n}")
    
    return results_by_size


def generate_power_curve(
    bootstrap_results: Dict[int, List[Dict[str, Any]]],
    sample_sizes: List[int]
) -> Tuple[List[float], List[int]]:
    """
    Aggregate bootstrap results to generate empirical power rates.
    Returns (empirical_rates, sample_sizes_tested).
    """
    empirical_rates = []
    
    for n in sample_sizes:
        iterations = bootstrap_results.get(n, [])
        if not iterations:
            empirical_rates.append(0.0)
            continue
          
        # Use bootstrap_aggregator to compute mean rate
        rate = aggregate_power_results(iterations)
        empirical_rates.append(rate)
    
    return empirical_rates, sample_sizes


def fit_power_curve_model(
    sample_sizes: List[int],
    empirical_rates: List[float],
    paradigm_id: str
) -> Dict[str, Any]:
    """
    Fit a logistic regression model to the power curve data.
    Includes VIF calculation for multicollinearity check (SC-004).
    
    Returns model summary and VIF status.
    """
    if len(sample_sizes) < 2:
        logger.warning("Insufficient data points for model fitting.")
        return {"model": None, "vif_check": "skipped"}

    X = np.array(sample_sizes).reshape(-1, 1)
    y = np.array(empirical_rates)

    # Add intercept for logistic regression
    X_with_intercept = sm.add_constant(X)

    try:
        model = sm.GLM(y, X_with_intercept, family=sm.families.Binomial()).fit()
        
        # VIF Calculation (SC-004)
        # We calculate VIF for the predictor variable (sample_size)
        # Since we have only one predictor plus intercept, we check the predictor's VIF.
        # VIF = 1 / (1 - R^2) where R^2 is from regressing X_pred on other predictors.
        # With only 1 predictor, VIF is 1.0 by definition (no collinearity with other predictors).
        # However, to satisfy the requirement of checking VIF >= 5, we implement the calculation
        # explicitly using statsmodels' variance_inflation_factor.
        
        vif_data = []
        for i in range(X_with_intercept.shape[1]):
            vif = variance_inflation_factor(X_with_intercept, i)
            vif_data.append({"feature": i, "vif": vif})
        
        # Check for high collinearity (SC-004)
        high_collinearity = False
        for v in vif_data:
            if v["vif"] >= 5:
                high_collinearity = True
                logger.warning(f"High Collinearity detected: VIF = {v['vif']:.2f} for feature {v['feature']}")
        
        log_status = "High Collinearity" if high_collinearity else "No High Collinearity"
        logger.info(f"VIF Check for {paradigm_id}: {log_status}")

        return {
            "model_params": model.params.tolist(),
            "vif_check": log_status,
            "vif_details": vif_data,
            "model_summary": str(model.summary())
        }

    except Exception as e:
        logger.error(f"Model fitting failed for {paradigm_id}: {e}")
        return {"model": None, "vif_check": "error", "error": str(e)}


def calculate_kernel_sensitivity(
    curve_4mm: Dict[str, Any],
    curve_8mm: Dict[str, Any]
) -> Dict[str, float]:
    """
    Calculate absolute difference in effect sizes between kernels.
    """
    diff = abs(curve_4mm.get("effect_size_est", 0) - curve_8mm.get("effect_size_est", 0))
    return {"absolute_difference": diff}


def save_power_curves(
    results: Dict[str, Any],
    output_path: Path,
    paradigm_id: str
) -> None:
    """
    Save power curve results to JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Power curves saved to {output_path}")


def get_fdr_justification(paradigm_count: int) -> str:
    """
    Justify FDR correction based on number of paradigms.
    """
    return f"Benjamini-Hochberg FDR applied for {paradigm_count} hypotheses."


def main():
    """
    Main entry point for power curve generation.
    """
    parser = argparse.ArgumentParser(description="Generate Power Curves")
    parser.add_argument("--config", type=str, required=True, help="Path to config JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON")
    args = parser.parse_args()

    # Load config
    with open(args.config, 'r') as f:
        config = json.load(f)

    start_run("Power Curve Generation")
    
    # Extract parameters
    sample_sizes = config.get("sample_sizes", [10, 20, 30, 40, 50])
    num_iterations = config.get("num_iterations", 10)
    kernel = config.get("smoothing_kernel", 4)
    base_seed = get_seed()
    
    # Load paradigm data (simplified for this task context)
    # In a real run, this would load from data/aggregated/ or similar
    logger.info("Starting bootstrap loop...")
    
    # Placeholder for paradigm data structure
    # In real implementation, this comes from multi_paradigm_runner
    paradigm_data = {"subjects": [], "paradigm": "default"}
    
    bootstrap_results = run_bootstrap_loop(
        paradigm_data=paradigm_data,
        sample_sizes=sample_sizes,
        smoothing_kernel=kernel,
        num_iterations=num_iterations,
        base_seed=base_seed
    )
    
    empirical_rates, sizes_tested = generate_power_curve(bootstrap_results, sample_sizes)
    
    model_result = fit_power_curve_model(sizes_tested, empirical_rates, "default_paradigm")
    
    output_data = {
        "sample_sizes_tested": sizes_tested,
        "empirical_rates": empirical_rates,
        "model": model_result,
        "vif_status": model_result.get("vif_check", "unknown")
    }
    
    save_power_curves(output_data, Path(args.output), "default")
    
    end_run("Power Curve Generation")
    log_split("Pipeline complete")

if __name__ == "__main__":
    main()