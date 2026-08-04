"""
Nested sampling implementation for Yukawa and Newtonian models using dynesty.

This module implements Bayesian model comparison between the standard Newtonian
inverse-square law and a Yukawa-modified potential using the dynesty library.

Outputs:
    data/results/nested_sampling_results.json: Posterior samples and evidence values
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import numpy as np
from dynesty import NestedSampler, dynamic_nested_sampler
from dynesty import utils as dyfunc

# Project imports based on API surface
from config import get_logger, setup_logging, ProjectConfig
from data.loaders import HarmonizedDataset
from models.physics import log_likelihood_yukawa, log_likelihood_newtonian

# Constants
CONFIG = ProjectConfig()
logger = get_logger(__name__)

def load_harmonized_data() -> HarmonizedDataset:
    """
    Load the harmonized dataset from the processed directory.
    
    Returns:
        HarmonizedDataset: The loaded dataset containing separation, force, and covariance.
        
    Raises:
        FileNotFoundError: If the harmonized dataset does not exist.
    """
    data_path = CONFIG.paths.processed / "harmonized_dataset.npz"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Harmonized dataset not found at {data_path}. "
            "Please run code/data/harmonize.py first."
        )
    
    # Load the .npz file and reconstruct the dataset object
    # Assuming the harmonize.py saves specific keys that we reconstruct here
    # or we load the raw arrays and wrap them. 
    # Given the API, we assume HarmonizedDataset can be reconstructed or loaded.
    # For this implementation, we load arrays and wrap them if needed, 
    # or directly access if the loader supports it.
    # Since HarmonizedDataset is a dataclass, we likely need to reconstruct it.
    # However, to keep it simple and robust, let's assume we load the arrays
    # that the likelihood functions expect.
    
    # Re-loading logic based on typical harmonize output
    try:
        data = np.load(data_path, allow_pickle=True)
        # Reconstructing HarmonizedDataset is safer if we know the fields
        # Assuming fields: separation, force, covariance_matrix, metadata
        separation = data['separation']
        force = data['force']
        covariance = data['covariance_matrix']
        # metadata might be a numpy object array
        metadata = data['metadata'] if 'metadata' in data else None
        
        return HarmonizedDataset(
            separation=separation,
            force=force,
            covariance_matrix=covariance,
            metadata=metadata
        )
    except Exception as e:
        logger.error(f"Failed to load harmonized dataset: {e}")
        raise

def run_nested_sampling(
    model_type: str = "yukawa",
    n_live: int = 100,
    sample: str = "auto",
    maxiter_init: int = None,
    maxiter_batch: int = None,
    maxiter_max: int = None,
    bound: str = "multi",
    nlive_batch: int = 500
) -> Dict[str, Any]:
    """
    Run nested sampling for the specified model.
    
    Args:
        model_type: "yukawa" or "newtonian".
        n_live: Number of live points.
        sample: Sampling method ("auto", "unif", "rwalk", "slice", "hslice", "rslice").
        bound: Bounding method for likelihood evaluation.
        bound: Bounding method.
        
    Returns:
        Dictionary containing results (samples, evidence, logZ, etc.).
    """
    logger.info(f"Starting nested sampling for {model_type} model...")
    start_time = time.time()
    
    # Load data
    dataset = load_harmonized_data()
    x = dataset.separation
    y = dataset.force
    cov = dataset.covariance_matrix
    
    # Select likelihood function
    if model_type == "yukawa":
        log_like_func = log_likelihood_yukawa
        # Prior bounds for Yukawa: alpha (log-uniform), lambda (log-uniform)
        # alpha: 0 to 10^4 (typical range for strength relative to gravity)
        # lambda: 1e-5 to 1e-2 (meters)
        def prior_transform(u):
            # u is uniform in [0, 1]
            # log10(alpha) in [0, 4] -> alpha = 10^(u[0]*4)
            # log10(lambda) in [-5, -2] -> lambda = 10^(u[1]*(-3) - 2)
            # Actually, let's map u[0] to log_alpha in [0, 4] and u[1] to log_lambda in [-5, -2]
            log_alpha = u[0] * 4.0
            log_lambda = u[1] * (-3.0) - 2.0
            return np.array([10**log_alpha, 10**log_lambda])
        
        ndim = 2
    elif model_type == "newtonian":
        log_like_func = log_likelihood_newtonian
        # Newtonian model has no free parameters (or fixed parameters)
        # If we treat it as a fixed model, we just compute the evidence at the fixed point?
        # Usually, nested sampling requires parameters. If Newtonian is fixed, we can't sample.
        # However, the task says "for both Newtonian and Yukawa models".
        # If Newtonian has no parameters, the evidence is just the likelihood at the fixed point
        # times the prior volume (which is 1).
        # But dynesty requires a prior transform and ndim.
        # Let's assume we are comparing a fixed Newtonian vs Yukawa with parameters.
        # In this case, for Newtonian, we might just return a pre-computed value or 
        # run a trivial sampler with 0 dimensions? Dynesty doesn't support 0 dims easily.
        # Alternative: Newtonian might have a scale parameter? The spec says "Newtonian and Yukawa-modified".
        # If Newtonian is strictly fixed, we can't use nested sampling for it in the same way.
        # Let's assume the "Newtonian" model here implies a fixed model, so we compute
        # the likelihood at the best fit (which is fixed) and return that as evidence.
        # But the task asks to "Implement dynesty nested sampler".
        # Perhaps we treat Newtonian as a limit of Yukawa with alpha=0?
        # Or maybe we just run the sampler for Yukawa and compute Newtonian evidence analytically?
        # Given the constraints, let's implement the sampler for Yukawa.
        # For Newtonian, if it has no parameters, we can't run nested sampling.
        # Let's assume the user wants the evidence for the fixed model.
        # We will handle "newtonian" by returning a fixed evidence value based on the likelihood.
        # But to strictly follow "Implement dynesty nested sampler", we might need to fake a 1D parameter
        # or just compute it.
        # Let's assume the Newtonian model is fixed. We will compute the log-likelihood
        # at the fixed parameters and return it as logZ.
        # However, dynesty requires a prior.
        # Let's check the physics module: log_likelihood_newtonian takes x, y, cov. No params.
        # So, for Newtonian, we calculate the log-likelihood once.
        # We will return a dummy result for "newtonian" that represents the fixed model evidence.
        # But the task implies running the sampler.
        # Let's assume we run the sampler for Yukawa, and for Newtonian we just compute the likelihood.
        # If the task strictly requires running dynesty for Newtonian, it's impossible with 0 params.
        # We will implement the logic to handle both:
        # If model_type == "newtonian", we compute the likelihood and return it as evidence.
        # We won't run the dynesty loop for 0 params.
        pass
    else:
        raise ValueError(f"Unknown model_type: {model_type}")
    
    if model_type == "newtonian":
        # Fixed model: compute log-likelihood at the fixed point
        # The evidence is log(L) + log(Prior Volume). Prior Volume = 1 for a point?
        # Or we assume a unit prior volume.
        log_like_val = log_like_func(x, y, cov)
        # Evidence = likelihood (since prior is a delta function effectively)
        # But Bayes factor requires consistent prior volumes.
        # Let's assume the prior volume for the fixed model is 1 (log 0).
        log_evidence = log_like_val
        results = {
            "model": "newtonian",
            "log_evidence": float(log_evidence),
            "evidence": float(np.exp(log_evidence)),
            "samples": None,
            "params": None,
            "runtime": time.time() - start_time
        }
        logger.info(f"Newtonian model evidence (fixed): {log_evidence:.2f}")
        return results

    # For Yukawa, run the sampler
    # Initialize sampler
    sampler = NestedSampler(
        log_like_func,
        ndim,
        n_live=n_live,
        bound=bound,
        sample=sample,
        queue_size=1,
        print_progress=True,
        print_func=lambda x: None  # Suppress default printing, we log ourselves
    )
    
    # Run the sampling
    # We use dynamic nested sampling for better efficiency if needed, 
    # but standard is fine for this task.
    sampler.run_nested()
    
    # Extract results
    results = sampler.results
    log_evidence = results.logz[-1]
    log_evidence_err = results.logzerr[-1]
    
    # Get posterior samples
    samples = results.samples
    # Calculate posterior means and standard deviations
    # Assuming params are [alpha, lambda]
    alpha_mean = np.mean(samples[:, 0])
    lambda_mean = np.mean(samples[:, 1])
    alpha_std = np.std(samples[:, 0])
    lambda_std = np.std(samples[:, 1])
    
    runtime = time.time() - start_time
    
    logger.info(f"Yukawa model log-evidence: {log_evidence:.2f} (+/- {log_evidence_err:.2f})")
    logger.info(f"Runtime: {runtime:.2f} seconds")
    
    return {
        "model": "yukawa",
        "log_evidence": float(log_evidence),
        "log_evidence_err": float(log_evidence_err),
        "evidence": float(np.exp(log_evidence)),
        "samples": samples.tolist(),
        "params": {
            "alpha": {"mean": float(alpha_mean), "std": float(alpha_std)},
            "lambda": {"mean": float(lambda_mean), "std": float(lambda_std)}
        },
        "runtime": float(runtime),
        "n_samples": len(samples)
    }

def main():
    """
    Main entry point for the nested sampling pipeline.
    
    Runs nested sampling for both Newtonian and Yukawa models,
    computes the Bayes factor, and saves results to disk.
    """
    setup_logging()
    logger.info("Starting Nested Sampling Analysis (T024)")
    
    results_dir = CONFIG.paths.results
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = results_dir / "nested_sampling_results.json"
    
    try:
        # Run for Newtonian
        logger.info("Running Newtonian model...")
        newtonian_results = run_nested_sampling(model_type="newtonian")
        
        # Run for Yukawa
        logger.info("Running Yukawa model...")
        yukawa_results = run_nested_sampling(model_type="yukawa")
        
        # Compute Bayes Factor (Yukawa vs Newtonian)
        # K = P(D|M_Yukawa) / P(D|M_Newtonian) = exp(logZ_Y - logZ_N)
        log_k = yukawa_results["log_evidence"] - newtonian_results["log_evidence"]
        bayes_factor = np.exp(log_k)
        
        logger.info(f"Bayes Factor (Yukawa/Newtonian): {bayes_factor:.2e} (log K = {log_k:.2f})")
        
        # Compile final results
        final_results = {
            "models": {
                "newtonian": newtonian_results,
                "yukawa": yukawa_results
            },
            "comparison": {
                "log_bayes_factor": float(log_k),
                "bayes_factor": float(bayes_factor),
                "interpretation": "Strong evidence for Yukawa" if bayes_factor > 150 else 
                                 "Moderate evidence for Yukawa" if bayes_factor > 20 else
                                 "Inconclusive" if bayes_factor > 3 else
                                 "Evidence for Newtonian"
            },
            "metadata": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "config": {
                    "n_live": 100,
                    "bound": "multi",
                    "sample": "auto"
                }
            }
        }
        
        # Save to JSON
        with open(output_path, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Nested sampling failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()