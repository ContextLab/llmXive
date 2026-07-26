"""
Belief Updater Model Implementation

Implements a hierarchical Bayesian model using PyMC with the NumPyro CPU backend
to estimate individual belief-updating rates (alpha) and group-level hyperparameters.

This module respects runtime constraints enforced by runtime_enforcer.py.
"""
import os
import sys
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd

# PyMC imports
import pymc as pm
from pymc.backends import NDArray

# Local imports
from utils.config import get_config, set_seed, get_seed
from utils.logger import get_logger, setup_file_logging
from utils.io import ensure_dir, load_json, save_json, load_csv, save_csv
from modeling.runtime_enforcer import RuntimeEnforcer, RuntimeLimitExceeded, SampleSizeReductionRequired

# Configure logging
logger = get_logger(__name__)


def load_behavioral_data(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load preprocessed behavioral data from the data/processed directory.

    Args:
        config: Configuration dictionary containing data paths

    Returns:
        DataFrame with columns: participant_id, trial, choice, feedback, discrepancy
    """
    data_path = Path(config["paths"]["processed_behavioral"])
    if not data_path.exists():
        raise FileNotFoundError(f"Behavioral data not found at {data_path}")

    df = load_csv(data_path)
    logger.info(f"Loaded {len(df)} behavioral trials from {data_path}")
    return df


def prepare_model_data(df: pd.DataFrame) -> Dict[str, np.ndarray]:
    """
    Prepare data for the hierarchical Bayesian model.

    Args:
        df: DataFrame with behavioral data

    Returns:
        Dictionary containing model inputs:
            - n_participants: int
            - n_trials: int
            - participant_idx: array of participant indices for each trial
            - choices: array of binary choices (0 or 1)
            - feedback: array of feedback values
            - discrepancy: array of prediction errors
    """
    participants = df["participant_id"].unique()
    n_participants = len(participants)
    n_trials = len(df)

    # Map participant IDs to indices
    participant_to_idx = {p: i for i, p in enumerate(participants)}
    participant_idx = np.array([participant_to_idx[p] for p in df["participant_id"]])

    # Convert categorical choices to binary if needed
    choices = np.array(df["choice"].astype(int))
    feedback = np.array(df["feedback"].astype(float))
    discrepancy = np.array(df["discrepancy"].astype(float))

    logger.info(f"Prepared data for {n_participants} participants, {n_trials} trials")

    return {
        "n_participants": n_participants,
        "n_trials": n_trials,
        "participant_idx": participant_idx,
        "choices": choices,
        "feedback": feedback,
        "discrepancy": discrepancy
    }


def build_hierarchical_model(data: Dict[str, np.ndarray]) -> pm.Model:
    """
    Build a hierarchical Bayesian model for belief updating.

    Model structure:
      - Individual alpha (learning rate) parameters drawn from a group-level Beta distribution
      - Individual beta (inverse temperature) parameters drawn from a group-level HalfNormal
      - Choice probability modeled via logistic function of prediction error

    Args:
        data: Dictionary containing prepared model data

    Returns:
        PyMC model instance
    """
    n_participants = data["n_participants"]
    n_trials = data["n_trials"]
    participant_idx = data["participant_idx"]
    choices = data["choices"]
    discrepancy = data["discrepancy"]

    with pm.Model() as model:
        # Group-level hyperparameters for alpha (learning rate)
        # Beta distribution constrained to [0, 1]
        alpha_mu = pm.Normal("alpha_mu", mu=0.5, sigma=0.2)
        alpha_sigma = pm.HalfNormal("alpha_sigma", sigma=0.2)

        # Individual alpha parameters (hierarchical)
        alpha_raw = pm.Normal("alpha_raw", mu=0, sigma=1, shape=n_participants)
        alpha = pm.Deterministic("alpha", alpha_mu + alpha_sigma * alpha_raw)
        alpha = pm.Bound(pm.Normal, lower=0, upper=1)("alpha_transformed",
                                                     mu=alpha_mu + alpha_sigma * alpha_raw,
                                                     sigma=alpha_sigma)

        # Group-level hyperparameters for beta (inverse temperature)
        beta_mu = pm.Normal("beta_mu", mu=2.0, sigma=1.0)
        beta_sigma = pm.HalfNormal("beta_sigma", sigma=1.0)

        # Individual beta parameters (hierarchical)
        beta_raw = pm.Normal("beta_raw", mu=0, sigma=1, shape=n_participants)
        beta = pm.Deterministic("beta", pm.math.exp(beta_mu + beta_sigma * beta_raw))

        # Expected choice probability based on belief updating
        # p(choice=1) = sigmoid(beta * (discrepancy * alpha))
        # This models how individuals update beliefs based on feedback discrepancy

        # Linear predictor
        linear_predictor = beta[participant_idx] * discrepancy * alpha[participant_idx]

        # Convert to probability via logistic function
        p_choice = pm.math.sigmoid(linear_predictor)

        # Likelihood
        obs = pm.Bernoulli("obs", p=p_choice, observed=choices)

    return model


def run_mcmc_sampling(
    model: pm.Model,
    data: Dict[str, np.ndarray],
    config: Dict[str, Any],
    runtime_enforcer: Optional[RuntimeEnforcer] = None
) -> Tuple[pm.backends.base.MultiTrace, Dict[str, Any]]:
    """
    Run MCMC sampling with runtime constraints.

    Args:
        model: PyMC model instance
        data: Dictionary containing prepared model data
        config: Configuration dictionary with sampling parameters
        runtime_enforcer: Optional runtime enforcer for constraint checking

    Returns:
        Tuple of (trace, sampling_metadata)
    """
    n_chains = config["modeling"].get("n_chains", 4)
    draws = config["modeling"].get("draws", 2000)
    tune = config["modeling"].get("tune", 1000)
    target_accept = config["modeling"].get("target_accept", 0.9)

    logger.info(f"Starting MCMC sampling: {n_chains} chains, {draws} draws, {tune} tune")

    # Set up sampling context
    sampling_start_time = time.time()
    metadata = {
        "start_time": sampling_start_time,
        "n_chains": n_chains,
        "draws": draws,
        "tune": tune,
        "target_accept": target_accept
    }

    with model:
        try:
            # Use NumPyro backend for CPU-only execution
            sampler = pm.sample(
                draws=draws,
                tune=tune,
                chains=n_chains,
                target_accept=target_accept,
                random_seed=get_seed(),
                progressbar=False,
                return_inferencedata=False,
                nuts_sampler="numpyro",
                init="adapt_diag"
            )

            sampling_time = time.time() - sampling_start_time
            metadata["sampling_time"] = sampling_time
            metadata["status"] = "completed"

            # Check runtime constraints
            if runtime_enforcer:
                remaining_time = runtime_enforcer.get_remaining_time()
                if remaining_time <= 0:
                    raise RuntimeLimitExceeded("Sampling exceeded time limit")

            logger.info(f"Sampling completed in {sampling_time:.2f} seconds")

            return sampler, metadata

        except Exception as e:
            metadata["status"] = "failed"
            metadata["error"] = str(e)
            logger.error(f"Sampling failed: {e}")
            raise


def extract_posterior_samples(trace: pm.backends.base.MultiTrace) -> Dict[str, np.ndarray]:
    """
    Extract posterior samples for individual parameters.

    Args:
        trace: MCMC trace from sampling

    Returns:
        Dictionary with posterior samples for alpha and beta per participant
    """
    # Extract alpha and beta samples
    alpha_samples = trace["alpha_transformed"]
    beta_samples = trace["beta"]

    # Compute posterior means for each participant
    alpha_mean = np.mean(alpha_samples, axis=(0, 1))
    beta_mean = np.mean(beta_samples, axis=(0, 1))

    # Compute posterior standard deviations
    alpha_std = np.std(alpha_samples, axis=(0, 1))
    beta_std = np.std(beta_samples, axis=(0, 1))

    return {
        "alpha_mean": alpha_mean,
        "alpha_std": alpha_std,
        "beta_mean": beta_mean,
        "beta_std": beta_std,
        "alpha_samples": alpha_samples,
        "beta_samples": beta_samples
    }


def save_model_results(
    results: Dict[str, np.ndarray],
    participants: List[str],
    config: Dict[str, Any],
    metadata: Dict[str, Any]
) -> Path:
    """
    Save model results to disk.

    Args:
        results: Dictionary containing posterior samples and statistics
        participants: List of participant IDs
        config: Configuration dictionary
        metadata: Sampling metadata

    Returns:
        Path to saved results file
    """
    output_path = Path(config["paths"]["model_output"])
    ensure_dir(output_path)

    # Create results DataFrame
    df_results = pd.DataFrame({
        "participant_id": participants,
        "alpha_mean": results["alpha_mean"],
        "alpha_std": results["alpha_std"],
        "beta_mean": results["beta_mean"],
        "beta_std": results["beta_std"]
    })

    # Save individual parameters
    output_file = output_path / "individual_parameters.csv"
    save_csv(output_file, df_results)
    logger.info(f"Saved individual parameters to {output_file}")

    # Save metadata
    metadata_file = output_path / "sampling_metadata.json"
    save_json(metadata_file, metadata)
    logger.info(f"Saved sampling metadata to {metadata_file}")

    return output_file


def main():
    """
    Main entry point for belief updater model.
    """
    parser = argparse.ArgumentParser(description="Run hierarchical belief updating model")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--max-runtime", type=float, default=21600, help="Max runtime in seconds (6h default)")
    parser.add_argument("--target-n", type=int, default=30, help="Target sample size")
    args = parser.parse_args()

    # Setup logging
    log_path = Path("logs/belief_updater.log")
    ensure_dir(log_path.parent)
    setup_file_logging(log_path)
    logger.info("Starting belief updater model")

    # Load configuration
    config = get_config(args.config)
    set_seed(config["modeling"].get("seed", 42))

    # Initialize runtime enforcer
    runtime_enforcer = RuntimeEnforcer(
        max_runtime=args.max_runtime,
        target_n=args.target_n,
        logger=logger
    )

    try:
        # Load and prepare data
        df = load_behavioral_data(config)
        data = prepare_model_data(df)

        # Check if we need to reduce sample size
        if data["n_participants"] > args.target_n:
            logger.warning(f"Participant count ({data['n_participants']}) exceeds target ({args.target_n})")
            # Reduce to target N while maintaining participant diversity
            participants = df["participant_id"].unique()[:args.target_n]
            df = df[df["participant_id"].isin(participants)]
            data = prepare_model_data(df)
            logger.info(f"Reduced to {data['n_participants']} participants")

        # Build model
        model = build_hierarchical_model(data)
        logger.info("Model built successfully")

        # Run sampling
        trace, metadata = run_mcmc_sampling(model, data, config, runtime_enforcer)

        # Extract results
        participants = df["participant_id"].unique()
        results = extract_posterior_samples(trace)

        # Save results
        output_path = save_model_results(results, participants, config, metadata)

        logger.info(f"Belief updater completed. Results saved to {output_path}")
        return 0

    except RuntimeLimitExceeded as e:
        logger.error(f"Runtime limit exceeded: {e}")
        return 1
    except Exception as e:
        logger.error(f"Belief updater failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
