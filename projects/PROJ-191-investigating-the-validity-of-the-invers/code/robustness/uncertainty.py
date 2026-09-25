import os
import sys
import json
import logging
import time
from pathlib import Path
import numpy as np
from scipy.linalg import cholesky, cho_solve

# Import from project API surface
from config import ProjectConfig, get_logger
from models.likelihood import load_covariance_matrix, compute_cholesky_decomposition, log_likelihood_yukawa, log_likelihood_newtonian
from inference.nested import load_harmonized_data, run_nested_sampling

def inflate_covariance(cov_matrix: np.ndarray, inflation_factor: float) -> np.ndarray:
    """
    Applies a multiplicative inflation factor to the covariance matrix.
    
    Args:
        cov_matrix: The original covariance matrix (N x N).
        inflation_factor: The factor by which to multiply the matrix elements.
        
    Returns:
        The inflated covariance matrix.
    """
    if inflation_factor <= 0:
        raise ValueError("Inflation factor must be positive.")
    
    return cov_matrix * inflation_factor

def compute_bayes_factor(config: ProjectConfig, logger: logging.Logger, inflation_factor: float = 1.0) -> dict:
    """
    Computes the Bayes factor for the Yukawa model vs Newtonian model
    with an inflated covariance matrix.
    
    Args:
        config: Project configuration object.
        logger: Logger instance.
        inflation_factor: Factor to inflate the covariance matrix.
        
    Returns:
        Dictionary containing Bayes factor and related metrics.
    """
    logger.info(f"Computing Bayes factor with covariance inflation factor: {inflation_factor}")
    
    # Load harmonized data
    data = load_harmonized_data(config)
    
    if data is None:
        logger.error("Failed to load harmonized data. Cannot proceed with Bayes factor computation.")
        return {"error": "Failed to load data"}
    
    # Load original covariance matrix
    cov_matrix_path = config.data_processed / "covariance_matrix.npy"
    if not cov_matrix_path.exists():
        logger.error(f"Covariance matrix not found at {cov_matrix_path}")
        return {"error": "Covariance matrix not found"}
        
    original_cov = load_covariance_matrix(cov_matrix_path)
    
    # Inflate covariance
    inflated_cov = inflate_covariance(original_cov, inflation_factor)
    
    # Save inflated covariance temporarily for inference modules
    inflated_cov_path = config.data_processed / "inflated_covariance_matrix.npy"
    np.save(inflated_cov_path, inflated_cov)
    
    # Run nested sampling for both models with the inflated covariance
    # Note: The nested sampling function needs to be updated to accept a custom covariance path
    # For now, we assume it reads from the standard path, so we temporarily swap files
    # A more robust solution would be to refactor the inference module to accept covariance as an argument
    
    # Backup original covariance
    backup_path = config.data_processed / "covariance_matrix_backup.npy"
    os.rename(cov_matrix_path, backup_path)
    os.rename(inflated_cov_path, cov_matrix_path)
    
    try:
        # Run nested sampling for Yukawa model
        logger.info("Running nested sampling for Yukawa model with inflated covariance...")
        yukawa_result = run_nested_sampling(config, model="yukawa")
        
        # Run nested sampling for Newtonian model
        logger.info("Running nested sampling for Newtonian model with inflated covariance...")
        newtonian_result = run_nested_sampling(config, model="newtonian")
        
        # Calculate Bayes factor (log evidence difference)
        log_evidence_yukawa = yukawa_result.get('log_evidence', -np.inf)
        log_evidence_newtonian = newtonian_result.get('log_evidence', -np.inf)
        
        log_bayes_factor = log_evidence_yukawa - log_evidence_newtonian
        bayes_factor = np.exp(log_bayes_factor)
        
        result = {
            "log_evidence_yukawa": float(log_evidence_yukawa),
            "log_evidence_newtonian": float(log_evidence_newtonian),
            "log_bayes_factor": float(log_bayes_factor),
            "bayes_factor": float(bayes_factor),
            "inflation_factor": float(inflation_factor),
            "status": "success"
        }
        
        logger.info(f"Bayes factor (Yukawa vs Newtonian) with {inflation_factor}x inflation: {bayes_factor:.4f} (log: {log_bayes_factor:.4f})")
        
    finally:
        # Restore original covariance
        os.rename(cov_matrix_path, inflated_cov_path)
        os.rename(backup_path, cov_matrix_path)
        
        # Clean up inflated covariance file
        if inflated_cov_path.exists():
            os.remove(inflated_cov_path)
    
    return result

def main():
    """
    Main function to run the systematic uncertainty inflation test.
    """
    config = ProjectConfig()
    logger = get_logger(__name__)
    
    # Read inflation factor from config or use default
    # In a real implementation, this would be read from a config file
    inflation_factor = 1.5  # Example: 50% increase in uncertainty
    
    logger.info("Starting systematic uncertainty inflation test")
    start_time = time.time()
    
    # Compute Bayes factor with inflated covariance
    result = compute_bayes_factor(config, logger, inflation_factor)
    
    if "error" in result:
        logger.error(f"Test failed: {result['error']}")
        sys.exit(1)
    
    # Check if Bayes factor change is within threshold
    # We need to compare with the baseline (inflation_factor = 1.0)
    baseline_result = compute_bayes_factor(config, logger, 1.0)
    
    if "error" in baseline_result:
        logger.error(f"Baseline computation failed: {baseline_result['error']}")
        sys.exit(1)
    
    baseline_log_bf = baseline_result['log_bayes_factor']
    inflated_log_bf = result['log_bayes_factor']
    
    log_change = abs(inflated_log_bf - baseline_log_bf)
    threshold = 0.1  # log-units
    
    result["baseline_log_bayes_factor"] = float(baseline_log_bf)
    result["log_change"] = float(log_change)
    result["threshold"] = float(threshold)
    result["pass"] = log_change < threshold
    
    if result["pass"]:
        logger.info(f"SUCCESS: Bayes factor change ({log_change:.4f}) is within threshold ({threshold})")
    else:
        logger.warning(f"WARNING: Bayes factor change ({log_change:.4f}) exceeds threshold ({threshold})")
    
    # Save results
    output_path = config.data_results / "uncertainty_inflation_report.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    logger.info(f"Total execution time: {time.time() - start_time:.2f} seconds")
    
    return result

if __name__ == "__main__":
    main()