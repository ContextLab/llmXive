"""
Nested Sampling Implementation for Inverse-Square Law Investigation.

This module implements Bayesian model comparison using the dynesty library
to compute the Bayesian evidence for both Newtonian and Yukawa-modified
gravity models.

It loads the harmonized dataset (separation, force, covariance) and runs
nested sampling to estimate the posterior distributions of parameters
(alpha, lambda) and the model evidence (log_Z).
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
from scipy.linalg import cholesky, cho_solve
import dynesty
from dynesty import nested_sampler
from dynesty.utils import resample_equal

# Project imports based on API surface
from config import get_logger, ProjectConfig
from data.loaders import load_harmonized_data
from models.physics import newtonian_force, yukawa_force
from models.likelihood import load_covariance_matrix

# Ensure we can import from the project root if run as script
if 'code' not in sys.path:
    code_root = Path(__file__).resolve().parent.parent
    if code_root not in sys.path:
        sys.path.insert(0, str(code_root))

# Constants
# Default priors for Yukawa model:
# alpha (strength): Uniform log-uniform between 1e-10 and 1e-2
# lambda (range): Uniform log-uniform between 1e-6 and 1e-3 (micrometers to mm)
# We use log-uniform priors for scale parameters to cover orders of magnitude.
MIN_ALPHA = 1e-10
MAX_ALPHA = 1e-2
MIN_LAMBDA = 1e-6  # 1 micrometer
MAX_LAMBDA = 1e-3  # 1 millimeter

# Newtonian model parameters (fixed alpha=0, effectively)
# We treat Newtonian as a special case of Yukawa with alpha=0, but for nested sampling
# we often run two separate models:
# Model 0: Newtonian (no free parameters for deviation, just noise scale if needed, but here fixed)
# Model 1: Yukawa (alpha, lambda free)

# For this implementation, we will run nested sampling for:
# 1. Yukawa Model: Parameters [log_alpha, log_lambda]
# 2. Newtonian Model: Effectively a single point or a model with alpha=0 fixed.
#    To compute Bayes Factor, we need the evidence Z_Newtonian.
#    Since Newtonian has 0 free parameters (if we assume noise is fixed from data),
#    the evidence is just the likelihood at the single point.
#    However, dynesty expects a distribution. We can run it with 0 dimensions or
#    treat alpha as fixed to 0 and run a 1D sampler for lambda if we want to constrain lambda
#    assuming alpha is known (which is not the case).
#    Standard approach: Run Yukawa sampler. For Newtonian, calculate Likelihood at alpha=0.
#    If we need a full nested sampling run for Newtonian for consistency, we can run a
#    sampler with 0 dimensions (single point).

logger = get_logger(__name__)

def log_prior_newtonian(u: np.ndarray) -> float:
    """
    Log prior for Newtonian model.
    Newtonian model has no free parameters (alpha=0 fixed).
    Returns 0.0 (constant prior) for the single point.
    """
    # Dynesty might call this with 0-dim array or empty.
    return 0.0

def log_likelihood_newtonian(theta: np.ndarray, x: np.ndarray, y: np.ndarray, cov_inv: np.ndarray, chol: np.ndarray) -> float:
    """
    Log likelihood for Newtonian model (alpha=0).
    """
    # Force prediction is just Newtonian
    y_pred = newtonian_force(x)
    residuals = y - y_pred
    # Log likelihood: -0.5 * (residuals^T * Cov^-1 * residuals) - 0.5 * log|Cov|
    # We assume the covariance matrix is fixed and known from data processing.
    # The constant term -0.5 * log|Cov| is the same for both models and cancels in Bayes Factor,
    # but we include it for absolute evidence calculation.
    # Using Cholesky: Cov = L L^T. Cov^-1 = L^-T L^-1.
    # x^T Cov^-1 x = (L^-1 x)^T (L^-1 x) = ||y||^2
    # log|Cov| = 2 * sum(log(diag(L)))
    log_det = 2.0 * np.sum(np.log(np.diag(chol)))
    # Solve L z = residuals for z, then z^T z
    z = cho_solve((chol, True), residuals)
    chi2 = np.dot(residuals, z)
    log_lik = -0.5 * chi2 - 0.5 * log_det - 0.5 * len(y) * np.log(2 * np.pi)
    return log_lik

def log_prior_yukawa(u: np.ndarray) -> float:
    """
    Log prior for Yukawa model.
    u is a vector of uniform random variables in [0, 1].
    We map them to log-uniform distributions for alpha and lambda.
    theta[0] -> log10(alpha)
    theta[1] -> log10(lambda)
    """
    if len(u) != 2:
        return -np.inf
    
    log_alpha_min = np.log10(MIN_ALPHA)
    log_alpha_max = np.log10(MAX_ALPHA)
    log_lambda_min = np.log10(MIN_LAMBDA)
    log_lambda_max = np.log10(MAX_LAMBDA)

    log_alpha = log_alpha_min + u[0] * (log_alpha_max - log_alpha_min)
    log_lambda = log_lambda_min + u[1] * (log_lambda_max - log_lambda_min)

    # Check bounds (should be satisfied by construction)
    if not (log_alpha_min <= log_alpha <= log_alpha_max):
        return -np.inf
    if not (log_lambda_min <= log_lambda <= log_lambda_max):
        return -np.inf

    # Return log prior (uniform in log space implies constant log prior)
    return 0.0

def log_likelihood_yukawa(theta: np.ndarray, x: np.ndarray, y: np.ndarray, cov_inv: np.ndarray, chol: np.ndarray) -> float:
    """
    Log likelihood for Yukawa model.
    theta[0] = log10(alpha)
    theta[1] = log10(lambda)
    """
    if len(theta) != 2:
        return -np.inf

    log_alpha = theta[0]
    log_lambda = theta[1]

    alpha = 10.0 ** log_alpha
    lam = 10.0 ** log_lambda

    # Ensure physical bounds
    if alpha <= 0 or lam <= 0:
        return -np.inf

    y_pred = yukawa_force(x, alpha, lam)
    residuals = y - y_pred

    # Log likelihood calculation using Cholesky
    log_det = 2.0 * np.sum(np.log(np.diag(chol)))
    z = cho_solve((chol, True), residuals)
    chi2 = np.dot(residuals, z)
    log_lik = -0.5 * chi2 - 0.5 * log_det - 0.5 * len(y) * np.log(2 * np.pi)

    return log_lik

def run_nested_sampling(
    model: str = "yukawa",
    data_path: Optional[Path] = None,
    n_live_points: int = 1000,
    nlive: int = 1000,
    maxiter: int = 50000,
    dlogz: float = 0.1
) -> Dict[str, Any]:
    """
    Run nested sampling for the specified model.

    Args:
        model: "yukawa" or "newtonian"
        data_path: Path to the harmonized dataset (JSON/NPY)
        n_live_points: Number of live points
        nlive: Alias for n_live_points (dynesty convention)
        maxiter: Maximum number of iterations
        dlogz: Stopping criterion (delta logZ)

    Returns:
        Dictionary containing results: log_evidence, samples, etc.
    """
    if data_path is None:
        # Default path based on project structure
        data_path = Path("data/processed/harmonized_dataset.json")
    
    if not Path(data_path).exists():
        raise FileNotFoundError(f"Harmonized dataset not found at {data_path}")

    logger.info(f"Loading data from {data_path}")
    dataset = load_harmonized_data(data_path)
    
    x = dataset.separation_m
    y = dataset.force_n
    
    # Load covariance matrix
    # We expect a diagonal or banded covariance matrix in data/processed/
    cov_path = Path("data/processed/covariance_matrix.npy")
    if not cov_path.exists():
        # Fallback to banded if diagonal missing, or raise error
        cov_path = Path("data/processed/covariance_banded.npy")
        if not cov_path.exists():
            raise FileNotFoundError("Covariance matrix not found in data/processed/")
    
    logger.info(f"Loading covariance from {cov_path}")
    cov = np.load(cov_path)
    
    # Cholesky decomposition
    try:
        chol = cholesky(cov, lower=False)
    except np.linalg.LinAlgError as e:
        logger.error(f"Covariance matrix is not positive definite: {e}")
        # Try to regularize if it's slightly non-positive definite
        logger.warning("Attempting to regularize covariance matrix...")
        min_eig = np.linalg.eigvalsh(cov).min()
        if min_eig < 0:
            cov += np.eye(cov.shape[0]) * abs(min_eig) * 1.1
            chol = cholesky(cov, lower=False)
        else:
            raise

    if model == "newtonian":
        # Newtonian model: alpha=0 fixed.
        # We can run a "dummy" nested sampler with 0 dimensions.
        # Or simply compute the likelihood at the single point.
        # dynesty supports 0-dimensional problems.
        
        def prior_newtonian(u):
            return 0.0
        
        def loglike_newtonian(theta):
            return log_likelihood_newtonian(theta, x, y, None, chol)
        
        # Run nested sampler with 0 dimensions
        sampler = nested_sampler.DynamicNestedSampler(
            loglike_newtonian,
            prior_newtonian,
            ndim=0,
            n_live_points=1
        )
        
        logger.info("Running Newtonian nested sampling (0 dimensions)...")
        start_time = time.time()
        sampler.run_nested(dlogz=dlogz, maxiter=maxiter)
        elapsed = time.time() - start_time
        
        results = sampler.results
        log_z = results.logz[-1]
        # For 0-dim, samples is empty or trivial.
        
        logger.info(f"Newtonian logZ: {log_z:.4f} (Time: {elapsed:.2f}s)")
        
        return {
            "model": "newtonian",
            "log_evidence": float(log_z),
            "samples": [],
            "n_iterations": int(results.niter[-1]),
            "elapsed_time": elapsed,
            "logz_error": float(results.logzerr[-1])
        }

    elif model == "yukawa":
        def prior_yukawa(u):
            return log_prior_yukawa(u)
        
        def loglike_yukawa(theta):
            return log_likelihood_yukawa(theta, x, y, None, chol)
        
        # Dynesty expects 2D input for 2 parameters
        sampler = nested_sampler.DynamicNestedSampler(
            loglike_yukawa,
            prior_yukawa,
            ndim=2,
            n_live_points=nlive
        )
        
        logger.info(f"Running Yukawa nested sampling with {nlive} live points...")
        start_time = time.time()
        sampler.run_nested(dlogz=dlogz, maxiter=maxiter)
        elapsed = time.time() - start_time
        
        results = sampler.results
        log_z = results.logz[-1]
        
        # Extract samples
        # samples shape: (n_samples, ndim)
        samples = results.samples
        # weights shape: (n_samples,)
        weights = results.weights
        
        logger.info(f"Yukawa logZ: {log_z:.4f} (Time: {elapsed:.2f}s)")
        
        # Convert log10 parameters back to linear for storage
        # samples[:, 0] is log10(alpha), samples[:, 1] is log10(lambda)
        alpha_samples = 10.0 ** samples[:, 0]
        lambda_samples = 10.0 ** samples[:, 1]
        
        return {
            "model": "yukawa",
            "log_evidence": float(log_z),
            "samples": {
                "alpha": alpha_samples,
                "lambda": lambda_samples,
                "weights": weights
            },
            "n_iterations": int(results.niter[-1]),
            "elapsed_time": elapsed,
            "logz_error": float(results.logzerr[-1]),
            "final_ncall": int(results.ncall[-1])
        }
    else:
        raise ValueError(f"Unknown model: {model}")

def main():
    """
    Main entry point for running nested sampling.
    Executes both Newtonian and Yukawa models and computes Bayes Factor.
    """
    config = ProjectConfig()
    logger.info("Starting Nested Sampling Inference (T024)")
    
    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Run Newtonian
    try:
        newtonian_results = run_nested_sampling(model="newtonian")
    except Exception as e:
        logger.error(f"Newtonian sampling failed: {e}")
        newtonian_results = {"log_evidence": -np.inf, "error": str(e)}
    
    # Run Yukawa
    try:
        yukawa_results = run_nested_sampling(model="yukawa")
    except Exception as e:
        logger.error(f"Yukawa sampling failed: {e}")
        yukawa_results = {"log_evidence": -np.inf, "error": str(e)}
    
    # Compute Bayes Factor
    # K = Z_Yukawa / Z_Newtonian = exp(logZ_Y - logZ_N)
    bayes_factor = None
    log_bayes_factor = None
    if "log_evidence" in newtonian_results and "log_evidence" in yukawa_results:
        log_z_n = newtonian_results["log_evidence"]
        log_z_y = yukawa_results["log_evidence"]
        log_bayes_factor = log_z_y - log_z_n
        bayes_factor = np.exp(log_bayes_factor)
        
        logger.info(f"Bayes Factor (Yukawa vs Newtonian): {bayes_factor:.4e}")
        logger.info(f"Log Bayes Factor: {log_bayes_factor:.4f}")
        
        # Kass-Rafferty Scale Interpretation
        if log_bayes_factor < 0:
            interpretation = "Evidence favors Newtonian"
        elif log_bayes_factor < 1.15:
            interpretation = "Not worth more than a bare mention"
        elif log_bayes_factor < 2.3:
            interpretation = "Substantial evidence for Yukawa"
        elif log_bayes_factor < 4.6:
            interpretation = "Strong evidence for Yukawa"
        else:
            interpretation = "Decisive evidence for Yukawa"
        
        logger.info(f"Interpretation: {interpretation}")
    
    # Save results
    output_file = results_dir / "nested_sampling_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "newtonian": newtonian_results,
            "yukawa": yukawa_results,
            "bayes_factor": bayes_factor,
            "log_bayes_factor": log_bayes_factor,
            "interpretation": interpretation if 'interpretation' in locals() else "N/A"
        }, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    
    # Save posterior samples for Yukawa if available
    if "samples" in yukawa_results and yukawa_results["samples"]:
        samples_file = results_dir / "yukawa_posterior_samples.npy"
        np.savez_compressed(
            samples_file,
            alpha=yukawa_results["samples"]["alpha"],
            lambda_param=yukawa_results["samples"]["lambda"],
            weights=yukawa_results["samples"]["weights"]
        )
        logger.info(f"Posterior samples saved to {samples_file}")

if __name__ == "__main__":
    main()
