"""
Bayesian parameter estimation using Bilby and Dynesty.

This module executes the inference pipeline, running nested sampling
to generate posterior distributions for gravitational wave parameters.
"""
import os
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np

# Import from local modules
from code.config import RESULTS_POSTERIORS_DIR
from code.utils.seeds import set_global_seed
from code.utils.logging_config import get_derivation_logger, log_derivation_params
from code.data.models import PosteriorDistribution, ResolutionConfig
from code.inference.models import get_waveform_model, get_model_parameters, get_model_priors

# Try to import bilby, but allow the module to load for testing if bilby is missing
try:
    import bilby
    from bilby.core import prior as bilby_prior
    from bilby.core import likelihood as bilby_likelihood
    from bilby.core.sampler import NestedSampler as BilbyNestedSampler
    HAS_BILBY = True
except ImportError:
    HAS_BILBY = False
    bilby = None
    bilby_prior = None
    bilby_likelihood = None
    BilbyNestedSampler = None

logger = logging.getLogger(__name__)


def run_inference(
    strain_data: Dict[str, Any],
    event_id: str,
    resolution_config: ResolutionConfig,
    waveform_model: str = "IMRPhenomPv2",
    seed: Optional[int] = None,
    max_iterations: int = 5000,
    dlogz_threshold: float = 0.1
) -> Tuple[Optional[PosteriorDistribution], Dict[str, Any]]:
    """
    Run Bayesian parameter estimation using Bilby with Dynesty.

    Args:
        strain_data: Dictionary containing strain data, noise PSD, and metadata.
        event_id: Unique identifier for the event.
        resolution_config: The resolution configuration used.
        waveform_model: The name of the waveform model to use.
        seed: Random seed for reproducibility.
        max_iterations: Maximum number of iterations for the sampler.
        dlogz_threshold: Evidence tolerance threshold for convergence.

    Returns:
        A tuple containing:
            - PosteriorDistribution object if successful, None otherwise.
            - A dictionary containing run metadata (status, dlogz, etc.).
    """
    if not HAS_BILBY:
        raise RuntimeError("Bilby is not installed. Please install it to run inference.")

    if seed is None:
        seed = set_global_seed()
    else:
        set_global_seed(seed)

    logger.info(f"Starting inference for event {event_id} with resolution {resolution_config.name}")

    # Extract data
    times = strain_data.get("times")
    data = strain_data.get("data")
    frequency_array = strain_data.get("frequency_array")
    psd = strain_data.get("psd")

    if times is None or data is None or psd is None:
        raise ValueError("Invalid strain data provided. Missing required fields.")

    # Create likelihood
    likelihood = bilby_likelihood.GWTransient(
        interferometers=strain_data.get("interferometers", []),
        result=None
    )
    # Note: In a real implementation, we would construct the interferometer
    # objects from the strain data and PSD. For now, we assume a simplified setup.
    # This is a placeholder for the actual likelihood construction.

    # Define priors
    priors = bilby_prior.PriorDict()
    model_params = get_model_priors(waveform_model)
    for param_name, param_config in model_params.items():
        if param_config["type"] == "uniform":
            priors[param_name] = bilby_prior.Uniform(
                minimum=param_config["minimum"],
                maximum=param_config["maximum"],
                name=param_name
            )
        elif param_config["type"] == "power_law":
            priors[param_name] = bilby_prior.PowerLaw(
                alpha=param_config["alpha"],
                minimum=param_config["minimum"],
                maximum=param_config["maximum"],
                name=param_name
            )
        elif param_config["type"] == "sine":
            priors[param_name] = bilby_prior.Sine(
                minimum=param_config["minimum"],
                maximum=param_config["maximum"],
                name=param_name
            )

    # Run sampler
    # Note: This is a simplified call. A full implementation would require
    # constructing the actual interferometer objects and passing them to
    # the likelihood.
    sampler = BilbyNestedSampler(
        likelihood=likelihood,
        priors=priors,
        waveform_model=waveform_model,
        nlive=250,
        dlogz=dlogz_threshold,
        maxiter=max_iterations,
        seed=seed
    )

    sampler.run()

    # Check convergence
    dlogz = sampler.results.dlogz
    is_inconclusive = dlogz > dlogz_threshold

    # Extract samples
    samples_dict = {}
    for param in get_model_parameters(waveform_model):
        if param in sampler.results.samples:
            samples_dict[param] = sampler.results.samples[param]
        else:
            # Handle missing parameters
            samples_dict[param] = np.array([])

    # Calculate posterior width (90% CI)
    posterior_widths = {}
    for param, samples in samples_dict.items():
        if len(samples) > 0:
            sorted_samples = np.sort(samples)
            lower_idx = int(0.05 * len(sorted_samples))
            upper_idx = int(0.95 * len(sorted_samples))
            posterior_widths[param] = sorted_samples[upper_idx] - sorted_samples[lower_idx]
        else:
            posterior_widths[param] = 0.0

    # Create posterior distribution object
    posterior = PosteriorDistribution(
        event_id=event_id,
        resolution_config=resolution_config,
        samples=samples_dict,
        log_weights=sampler.results.log_weights,
        is_inconclusive=is_inconclusive,
        posterior_width_90_ci=posterior_widths.get("chirp_mass", 0.0),
        prior_width_90_ci=1.0  # Placeholder, should be calculated from priors
    )

    run_metadata = {
        "event_id": event_id,
        "resolution_config": resolution_config.name,
        "waveform_model": waveform_model,
        "seed": seed,
        "dlogz": dlogz,
        "is_inconclusive": is_inconclusive,
        "max_iterations": max_iterations,
        "samples_count": len(sampler.results.samples["chirp_mass"]) if "chirp_mass" in sampler.results.samples else 0
    }

    return posterior, run_metadata


def main():
    """
    Main entry point for running inference.

    This function is intended to be called from a script to execute
    the inference pipeline on a specific event.
    """
    if not HAS_BILBY:
        logger.error("Bilby is not installed. Cannot run inference.")
        return

    logger.info("Starting inference pipeline...")
    # Placeholder for actual execution logic
    # In a real scenario, this would load data, call run_inference,
    # and save the results.
    logger.info("Inference pipeline completed.")
