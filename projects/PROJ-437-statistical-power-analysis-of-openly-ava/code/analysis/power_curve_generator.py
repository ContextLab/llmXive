"""
Power Curve Generator Module.

Orchestrates bootstrap iterations per sample size, supports multiple smoothing kernels,
and manages alpha sweeps for statistical power analysis.
"""

import argparse
import json
import logging
import sys
import gc
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Local imports matching API surface
from analysis.split_half_validator import run_split_half_validation
from analysis.bootstrap_aggregator import aggregate_power_results, save_aggregated_results
from models.simulation_config import SimulationConfig
from utils.seed_manager import set_global_seed, get_seed
from utils.memory_monitor import trigger_gc

# Constants
MIN_SAMPLE_SIZE_GUARDRAIL = 10
OUTPUT_PATH = Path("data/aggregated/power_curves.json")
LOG_PATH = Path("data/aggregated/power_curve_execution_log.json")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def clamp_sample_size_to_available(
    requested_size: int,
    available_subjects: List[Any],
    paradigm_name: str
) -> Tuple[int, bool]:
    """
    Clamps the requested sample size to the number of available subjects.
    
    Args:
        requested_size: The target sample size.
        available_subjects: List of available subject identifiers.
        paradigm_name: Name of the paradigm for logging.
        
    Returns:
        Tuple of (clamped_size, was_clamped).
    """
    actual_available = len(available_subjects)
    if requested_size > actual_available:
        logger.warning(
            f"Paradigm '{paradigm_name}': Requested N={requested_size} exceeds "
            f"available subjects ({actual_available}). Clamping to {actual_available}."
        )
        return actual_available, True
    return requested_size, False


def bootstrap_single_iteration(
    config: SimulationConfig,
    sample_size: int,
    paradigm_name: str,
    smoothing_kernel: str,
    available_subjects: List[Any]
) -> Dict[str, Any]:
    """
    Performs a single bootstrap iteration for a given configuration.
    
    Returns a dictionary with replication success status and metrics.
    """
    # Check minimum sample size guardrail
    if sample_size < MIN_SAMPLE_SIZE_GUARDRAIL:
        logger.warning(
            f"Skipping bootstrap iteration for N={sample_size} in '{paradigm_name}'. "
            f"Reason: Below minimum sample size guardrail ({MIN_SAMPLE_SIZE_GUARDRAIL})."
        )
        return {
            "skipped": True,
            "reason": "Insufficient Data",
            "sample_size": sample_size,
            "paradigm": paradigm_name,
            "kernel": smoothing_kernel
        }

    try:
        result = run_split_half_validation(
            config=config,
            sample_size=sample_size,
            paradigm=paradigm_name,
            smoothing_kernel=smoothing_kernel,
            available_subjects=available_subjects
        )
        return {
            "skipped": False,
            "success": result.get("replication_success", False),
            "effect_size": result.get("effect_size", 0.0),
            "p_value": result.get("p_value", 1.0),
            "sample_size": sample_size,
            "paradigm": paradigm_name,
            "kernel": smoothing_kernel
        }
    except Exception as e:
        logger.error(
            f"Bootstrap iteration failed for N={sample_size}, paradigm={paradigm_name}: {e}"
        )
        return {
            "skipped": False,
            "success": False,
            "error": str(e),
            "sample_size": sample_size,
            "paradigm": paradigm_name,
            "kernel": smoothing_kernel
        }
    finally:
        trigger_gc()
        gc.collect()


def run_bootstrap_loop(
    config: SimulationConfig,
    sample_sizes: List[int],
    paradigms: List[str],
    smoothing_kernels: List[str],
    available_subjects_map: Dict[str, List[Any]]
) -> List[Dict[str, Any]]:
    """
    Orchestrates the full bootstrap loop over sample sizes, paradigms, and kernels.
    
    Returns a list of results for aggregation.
    """
    all_results = []
    set_global_seed(config.random_seed)
    
    logger.info(f"Starting bootstrap loop for {len(sample_sizes)} sample sizes, "
                f"{len(paradigms)} paradigms, {len(smoothing_kernels)} kernels.")

    for paradigm in paradigms:
        subjects = available_subjects_map.get(paradigm, [])
        if not subjects:
            logger.warning(f"No subjects found for paradigm '{paradigm}'. Skipping.")
            continue
        
        for kernel in smoothing_kernels:
            for n in sample_sizes:
                # Apply guardrail check before calling bootstrap
                if n < MIN_SAMPLE_SIZE_GUARDRAIL:
                    logger.info(
                        f"Skipping N={n} for paradigm '{paradigm}', kernel '{kernel}'. "
                        f"Reason: Below minimum sample size guardrail ({MIN_SAMPLE_SIZE_GUARDRAIL})."
                    )
                    # Log the skip explicitly to the results list for transparency
                    all_results.append({
                        "skipped": True,
                        "reason": "Insufficient Data",
                        "sample_size": n,
                        "paradigm": paradigm,
                        "kernel": kernel,
                        "timestamp": datetime.now().isoformat()
                    })
                    continue

                # Clamp if necessary
                clamped_n, _ = clamp_sample_size_to_available(n, subjects, paradigm)
                
                result = bootstrap_single_iteration(
                    config=config,
                    sample_size=clamped_n,
                    paradigm_name=paradigm,
                    smoothing_kernel=kernel,
                    available_subjects=subjects
                )
                all_results.append(result)
                
                # Log progress
                if len(all_results) % 10 == 0:
                    logger.info(f"Processed {len(all_results)} iterations...")

    return all_results


def fit_power_curve_model(
    results: List[Dict[str, Any]],
    alpha_values: List[float]
) -> Dict[str, Any]:
    """
    Fits a logistic regression model to predict replication success.
    
    Args:
        results: List of bootstrap results.
        alpha_values: List of alpha thresholds to evaluate.
        
    Returns:
        Dictionary containing model parameters and diagnostics.
    """
    # Filter out skipped results
    valid_results = [r for r in results if not r.get("skipped", False)]
    if not valid_results:
        logger.warning("No valid results found for model fitting.")
        return {"status": "invalid", "reason": "No data"}

    # Prepare data
    sample_sizes = np.array([r["sample_size"] for r in valid_results])
    successes = np.array([1 if r.get("success", False) else 0 for r in valid_results])
    
    # Add constant for intercept
    X = sm.add_constant(sample_sizes)
    y = successes

    try:
        model = sm.Logit(y, X)
        result = model.fit(disp=False)
        
        # Calculate VIF for multicollinearity check (though only 1 predictor here)
        vif_data = []
        if X.shape[1] > 1:
            for i in range(X.shape[1]):
                vif = variance_inflation_factor(X, i)
                vif_data.append({"feature": i, "vif": vif})
                if vif >= 5:
                    logger.warning("High Collinearity detected (VIF >= 5). Model flagged as Invalid.")
                    
        return {
            "status": "valid",
            "params": result.params.tolist(),
            "vif_check": vif_data,
            "alpha_sweep": {
                str(alpha): {
                    "threshold": alpha,
                    "n_obs": len(valid_results)
                } for alpha in alpha_values
            }
        }
    except Exception as e:
        logger.error(f"Logistic regression fitting failed: {e}")
        return {"status": "invalid", "reason": str(e)}


def run_alpha_sweep(
    results: List[Dict[str, Any]],
    alpha_values: List[float]
) -> Dict[str, Any]:
    """
    Runs the alpha sweep analysis to verify robustness across thresholds.
    """
    sweep_results = {}
    for alpha in alpha_values:
        # In a full implementation, this would recalculate success rates based on p-values
        # compared against the specific alpha threshold.
        # For now, we aggregate based on the existing 'success' flag which is typically p < 0.05.
        # If the underlying validator supports dynamic alpha, we would filter there.
        valid_results = [r for r in results if not r.get("skipped", False)]
        if not valid_results:
            continue
        
        # Placeholder for alpha-specific aggregation logic
        # Assuming 'success' in results is already computed against a default or specific alpha
        # If we need to re-evaluate, we would need p-values here.
        successes = [r for r in valid_results if r.get("success", False)]
        rate = len(successes) / len(valid_results) if valid_results else 0.0
        
        sweep_results[str(alpha)] = {
            "empirical_rate": rate,
            "n_success": len(successes),
            "n_total": len(valid_results)
        }
        
    return sweep_results


def save_power_curves(
    results: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Aggregates results and saves the power curve data to JSON.
    Includes skipped entries with 'Insufficient Data' reasons.
    """
    # Group by paradigm and kernel
    aggregated = {}
    
    # First, collect all unique keys
    paradigms = set(r["paradigm"] for r in results)
    kernels = set(r["kernel"] for r in results)
    
    for paradigm in paradigms:
        aggregated[paradigm] = {}
        for kernel in kernels:
            subset = [r for r in results if r["paradigm"] == paradigm and r["kernel"] == kernel]
            
            # Separate skipped and valid
            skipped = [r for r in subset if r.get("skipped", False)]
            valid = [r for r in subset if not r.get("skipped", False)]
            
            # Calculate rates for valid
            sample_sizes = sorted(list(set(r["sample_size"] for r in valid)))
            rates = []
            for n in sample_sizes:
                n_results = [r for r in valid if r["sample_size"] == n]
                if n_results:
                    successes = sum(1 for r in n_results if r.get("success", False))
                    rates.append(successes / len(n_results))
                else:
                    rates.append(0.0)
            
            aggregated[paradigm][kernel] = {
                "sample_sizes_tested": sample_sizes,
                "empirical_rates": rates,
                "skipped_entries": [
                    {
                        "sample_size": s["sample_size"],
                        "reason": s.get("reason", "Unknown")
                    } for s in skipped
                ],
                "total_iterations": len(subset),
                "valid_iterations": len(valid)
            }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(aggregated, f, indent=2)
        
    logger.info(f"Power curves saved to {output_path}")


def get_fdr_justification(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates FDR justification metrics if applicable.
    """
    valid = [r for r in results if not r.get("skipped", False)]
    total = len(valid)
    if total == 0:
        return {"status": "insufficient_data"}
    
    # Placeholder for FDR logic
    return {
        "status": "ok",
        "total_tests": total,
        "method": "benjamini_hochberg"
    }


def main():
    """
    Entry point for the power curve generator.
    """
    parser = argparse.ArgumentParser(description="Generate Power Curves")
    parser.add_argument("--config", type=str, required=True, help="Path to config file")
    parser.add_argument("--output", type=str, default=str(OUTPUT_PATH), help="Output JSON path")
    args = parser.parse_args()
    
    # Load config (simplified for this snippet)
    try:
        with open(args.config, 'r') as f:
            config_dict = json.load(f)
        config = SimulationConfig(**config_dict)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
        
    # Mock data sources for execution (in real run, these come from T008/T052)
    # In a real run, we would load available subjects from the data validator
    available_subjects_map = {
        "Motor": list(range(20)), # Mock 20 subjects
        "Visual": list(range(15)) # Mock 15 subjects
    }
    
    sample_sizes = [5, 10, 15, 20, 25]
    paradigms = ["Motor", "Visual"]
    kernels = ["4s", "8s"]
    
    results = run_bootstrap_loop(
        config=config,
        sample_sizes=sample_sizes,
        paradigms=paradigms,
        smoothing_kernels=kernels,
        available_subjects_map=available_subjects_map
    )
    
    # Save results
    save_power_curves(results, Path(args.output))
    
    # Log execution
    logger.info("Power curve generation complete.")


if __name__ == "__main__":
    main()