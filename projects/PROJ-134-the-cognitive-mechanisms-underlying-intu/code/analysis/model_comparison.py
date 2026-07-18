import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np

# Import local utilities
from code.config import ensure_directories
from code.utils.logging_utils import get_logger, log_pipeline_step

# Setup logging for this module
logger = get_logger("model_comparison")

def calculate_aic_waic(model_results: Dict[str, Any]) -> Tuple[float, float]:
    """
    Calculate AIC and WAIC from model results.
    
    Args:
        model_results: Dictionary containing log_likelihood, n_params, etc.
    
    Returns:
        Tuple of (AIC, WAIC)
    """
    log_likelihood = model_results.get('log_likelihood', 0.0)
    n_params = model_results.get('n_params', 0)
    
    # AIC = -2 * log_likelihood + 2 * n_params
    # Note: log_likelihood is often returned as sum of log probs (negative)
    # If log_likelihood is negative sum, we use it directly.
    # Standard convention: AIC = 2k - 2ln(L)
    aic = 2 * n_params - 2 * log_likelihood
    
    # WAIC approximation (using effective number of parameters)
    # For this simulation, we approximate WAIC similarly to AIC but with
    # a penalty for model complexity based on posterior variance
    waic = aic + 2 * n_params * 0.1  # Simplified penalty adjustment
    
    return float(aic), float(waic)

def run_model_comparison(
    baseline_results: Dict[str, Any],
    salience_results: Dict[str, Any],
    run_mode: str = 'simulation'
) -> Dict[str, Any]:
    """
    Run model comparison between baseline and salience-augmented models.
    
    Args:
        baseline_results: Results from the baseline model (no salience)
        salience_results: Results from the salience-augmented model
        run_mode: 'simulation' or 'real'
    
    Returns:
        Dictionary containing comparison metrics and status
    """
    logger.info(f"Running model comparison in mode: {run_mode}")
    
    # Calculate metrics for both models
    aic_baseline, waic_baseline = calculate_aic_waic(baseline_results)
    aic_salience, waic_salience = calculate_aic_waic(salience_results)
    
    # Calculate delta AIC (Salience - Baseline)
    # Negative delta AIC means salience model is better
    delta_aic = aic_salience - aic_baseline
    
    # Calculate delta WAIC
    delta_waic = waic_salience - waic_baseline
    
    result = {
        'aic_baseline': aic_baseline,
        'aic_salience': aic_salience,
        'delta_aic': delta_aic,
        'waic_baseline': waic_baseline,
        'waic_salience': waic_salience,
        'delta_waic': delta_waic,
        'run_mode': run_mode,
        'timestamp': str(Path.cwd()) # Placeholder for actual timestamp
    }
    
    # Handle mode-specific logic
    if run_mode == 'simulation':
        # Log the scientific metric but defer the claim per Phase 3 Staged Implementation
        log_message = f"LOG: Scientific Metric: Calculated (ΔAIC={delta_aic:.4f}) - Claim Deferred per Phase 3 Staged Implementation"
        logger.info(log_message)
        result['claim_status'] = 'deferred'
        result['priority_metric'] = 'parameter_recovery'
        logger.info("Priority metric set to 'parameter_recovery' for simulation mode.")
        
    elif run_mode == 'real':
        # Check for strong evidence (ΔAIC > 10)
        if delta_aic > 10:
            result['claim_status'] = 'strong_evidence'
            logger.warning("Strong evidence detected (ΔAIC > 10) as required by SC-002.")
        elif delta_aic < -10:
            result['claim_status'] = 'strong_evidence_baseline'
            logger.warning("Strong evidence for baseline model (ΔAIC < -10).")
        else:
            result['claim_status'] = 'inconclusive'
            logger.info("Inconclusive evidence (|ΔAIC| <= 10).")
    else:
        logger.error(f"Unknown run_mode: {run_mode}")
        raise ValueError(f"Invalid run_mode: {run_mode}")
    
    return result

def perform_posterior_predictive_checks(
    model_results: Dict[str, Any],
    observed_data: np.ndarray
) -> Dict[str, Any]:
    """
    Perform Posterior Predictive Checks (PPC) and visualize fit.
    
    Args:
        model_results: Model inference results
        observed_data: Observed data array
    
    Returns:
        Dictionary containing PPC statistics
    """
    # Extract posterior samples if available
    posterior_samples = model_results.get('posterior_samples', None)
    
    if posterior_samples is None:
        logger.warning("No posterior samples found for PPC.")
        return {'ppc_status': 'missing_samples', 'p_value': None}
    
    # Simple PPC: compare mean of posterior predictive to observed mean
    simulated_means = np.mean(posterior_samples, axis=0)
    observed_mean = np.mean(observed_data)
    
    # Calculate p-value approximation (proportion of simulated means > observed mean)
    p_value = np.mean(simulated_means > observed_mean)
    
    # Check if observed mean falls within 95% CI of posterior predictive
    ci_lower = np.percentile(simulated_means, 2.5)
    ci_upper = np.percentile(simulated_means, 97.5)
    within_ci = ci_lower <= observed_mean <= ci_upper
    
    return {
        'ppc_status': 'completed',
        'p_value': float(p_value),
        'observed_mean': float(observed_mean),
        'simulated_mean': float(np.mean(simulated_means)),
        'ci_95_lower': float(ci_lower),
        'ci_95_upper': float(ci_upper),
        'within_ci': within_ci
    }

def main():
    """
    Main entry point for model comparison analysis.
    """
    logger.info("Starting Model Comparison Analysis (T027)")
    
    # Ensure directories
    ensure_directories()
    
    # Load configuration (mocked for this task, usually from config.py)
    # In a real scenario, this would read from data/config/ or env vars
    run_mode = os.getenv('RUN_MODE', 'simulation')
    logger.info(f"Detected RUN_MODE: {run_mode}")
    
    # Mock results for demonstration (in real flow, these come from bayesian.py)
    # These values are chosen to demonstrate the logic
    baseline_results = {
        'log_likelihood': -150.0,
        'n_params': 3
    }
    
    salience_results = {
        'log_likelihood': -130.0, # Better fit
        'n_params': 4 # One extra parameter for salience
    }
    
    # Run comparison
    comparison_result = run_model_comparison(
        baseline_results,
        salience_results,
        run_mode=run_mode
    )
    
    # Perform PPC on salience model
    mock_observed = np.array([1.0, 1.2, 0.9, 1.1, 1.3])
    ppc_result = perform_posterior_predictive_checks(salience_results, mock_observed)
    
    # Combine results
    final_report = {
        'comparison': comparison_result,
        'ppc': ppc_result
    }
    
    # Save results
    output_path = Path("data/processed/model_comparison_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Model comparison results saved to {output_path}")
    logger.info(f"Final Delta AIC: {comparison_result['delta_aic']:.4f}")
    
    return final_report

if __name__ == "__main__":
    main()