"""
Validation module for statistical analysis and model comparison.
Implements sensitivity analysis, Bonferroni correction, and parameter recovery checks.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from scipy import stats

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path, load_yaml_config
from utils.logging_utils import get_logger, log_pipeline_step

logger = get_logger(__name__)

# Constants for sensitivity analysis
SENSITIVITY_THRESHOLDS = [2, 10, 20]

def apply_bonferroni_correction(p_values: List[float], num_tests: int) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
        num_tests: Number of hypothesis tests performed
        
    Returns:
        List of Bonferroni-corrected p-values
    """
    if not p_values:
        return []
    
    # Cap corrected p-values at 1.0
    corrected = [min(p * num_tests, 1.0) for p in p_values]
    logger.info(f"Applied Bonferroni correction: {len(p_values)} tests, corrected {len(corrected)} p-values")
    return corrected

def check_parameter_recovery(
    posterior_samples: np.ndarray,
    ground_truth: float,
    credible_interval: float = 0.95
) -> Dict[str, Any]:
    """
    Check if the ground truth parameter value falls within the credible interval
    of the posterior distribution.
    
    Args:
        posterior_samples: Array of posterior samples for a parameter
        ground_truth: The known ground truth value
        credible_interval: Credible interval width (default 0.95 for 95% CI)
        
    Returns:
        Dictionary with recovery status and interval bounds
    """
    lower_percentile = (1 - credible_interval) / 2
    upper_percentile = 1 - lower_percentile
    
    ci_lower = np.percentile(posterior_samples, lower_percentile * 100)
    ci_upper = np.percentile(posterior_samples, upper_percentile * 100)
    
    recovered = ci_lower <= ground_truth <= ci_upper
    
    result = {
        "ground_truth": ground_truth,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "recovered": recovered,
        "credible_interval": credible_interval
    }
    
    logger.info(f"Parameter recovery check: recovered={recovered}, CI=[{ci_lower:.4f}, {ci_upper:.4f}]")
    return result

def conduct_sensitivity_analysis(
    model_results: List[Dict[str, Any]],
    thresholds: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Conduct sensitivity analysis by sweeping decision thresholds.
    
    This function evaluates model selection stability across different
    decision thresholds (e.g., for ΔAIC or ΔWAIC). It produces a stability
    matrix showing how often each model is selected at each threshold.
    
    Args:
        model_results: List of model result dictionaries containing:
            - 'model_name': str
            - 'aic': float
            - 'waic': float
            - 'log_likelihood': float (optional)
        thresholds: List of thresholds to evaluate (default: [2, 10, 20])
        
    Returns:
        Dictionary containing:
            - 'stability_matrix': Dict mapping threshold -> selected model counts
            - 'thresholds': List of thresholds used
            - 'model_names': List of model names
            - 'summary': Dict with stability statistics
    """
    if thresholds is None:
        thresholds = SENSITIVITY_THRESHOLDS
    
    if not model_results:
        logger.warning("No model results provided for sensitivity analysis")
        return {
            "stability_matrix": {},
            "thresholds": thresholds,
            "model_names": [],
            "summary": {"total_models": 0, "stable_at_all_thresholds": 0}
        }
    
    # Extract model names and compute AIC differences
    model_names = sorted(list(set(r.get("model_name", f"model_{i}") for i, r in enumerate(model_results))))
    n_models = len(model_names)
    
    # Compute ΔAIC for each model relative to the best model at each threshold
    stability_matrix = {t: {name: 0 for name in model_names} for t in thresholds}
    
    for threshold in thresholds:
        # Calculate AIC for each model
        aic_values = {}
        for result in model_results:
            name = result.get("model_name", f"model_{model_results.index(result)}")
            aic = result.get("aic")
            if aic is not None:
                aic_values[name] = aic
        
        if not aic_values:
            logger.warning(f"No AIC values found for threshold {threshold}")
            continue
        
        min_aic = min(aic_values.values())
        
        # Count models within threshold of best
        for name, aic in aic_values.items():
            delta_aic = aic - min_aic
            if delta_aic <= threshold:
                stability_matrix[threshold][name] += 1
        
        # Normalize to proportions
        total_at_threshold = sum(stability_matrix[threshold].values())
        if total_at_threshold > 0:
            for name in model_names:
                stability_matrix[threshold][name] /= total_at_threshold
    
    # Calculate stability summary
    stable_models = []
    for name in model_names:
        # Check if model is stable (selected > 50% of the time) at all thresholds
        is_stable = all(
            stability_matrix[t].get(name, 0) > 0.5 
            for t in thresholds
        )
        if is_stable:
            stable_models.append(name)
    
    summary = {
        "total_models": n_models,
        "stable_at_all_thresholds": len(stable_models),
        "stable_models": stable_models,
        "thresholds_evaluated": len(thresholds)
    }
    
    logger.info(f"Sensitivity analysis complete: {len(stable_models)} stable models across {len(thresholds)} thresholds")
    
    return {
        "stability_matrix": stability_matrix,
        "thresholds": thresholds,
        "model_names": model_names,
        "summary": summary
    }

def run_validation_pipeline(
    data_path: str,
    model_results_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Run the full validation pipeline including parameter recovery and sensitivity analysis.
    
    Args:
        data_path: Path to preprocessed data
        model_results_path: Path to model results JSON
        output_path: Path to save validation report
        
    Returns:
        Dictionary with validation results
    """
    log_pipeline_step("Starting validation pipeline", logger)
    
    # Load model results
    try:
        with open(model_results_path, 'r') as f:
            model_results = json.load(f)
        if not isinstance(model_results, list):
            model_results = [model_results]
    except FileNotFoundError:
        logger.error(f"Model results file not found: {model_results_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in model results: {e}")
        raise
    
    # Run sensitivity analysis
    sensitivity_results = conduct_sensitivity_analysis(model_results)
    
    # Run parameter recovery if ground truth is available
    parameter_recovery_results = []
    for result in model_results:
        if "ground_truth" in result and "posterior_samples" in result:
            recovery = check_parameter_recovery(
                np.array(result["posterior_samples"]),
                result["ground_truth"]
            )
            parameter_recovery_results.append({
                "model_name": result.get("model_name", "unknown"),
                "recovery": recovery
            })
    
    # Compile final validation report
    validation_report = {
        "sensitivity_analysis": sensitivity_results,
        "parameter_recovery": parameter_recovery_results,
        "thresholds_used": SENSITIVITY_THRESHOLDS,
        "status": "PASSED" if sensitivity_results["summary"]["stable_at_all_thresholds"] > 0 else "NEEDS_REVIEW"
    }
    
    # Save report
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(validation_report, f, indent=2)
    
    logger.info(f"Validation report saved to {output_path}")
    log_pipeline_step("Validation pipeline complete", logger)
    
    return validation_report

def main():
    """Main entry point for validation analysis."""
    # Default paths
    data_path = get_path("data/processed/merged_data.csv")
    model_results_path = get_path("data/processed/model_results.json")
    output_path = get_path("data/processed/validation_report.json")
    
    # Check if required files exist
    if not os.path.exists(data_path):
        logger.warning(f"Data file not found: {data_path}. Skipping parameter recovery.")
    
    if not os.path.exists(model_results_path):
        logger.error(f"Model results file not found: {model_results_path}")
        sys.exit(1)
    
    # Run validation
    try:
        results = run_validation_pipeline(data_path, model_results_path, output_path)
        print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"Validation pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()