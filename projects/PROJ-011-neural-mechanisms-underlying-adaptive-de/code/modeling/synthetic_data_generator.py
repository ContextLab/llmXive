"""
Synthetic Data Generator for Belief Updating Model Validation.

This module generates ground-truth behavioral data based on a Rescorla-Wagner
learning model to validate the hierarchical Bayesian belief updating model.

The generated data simulates participants making choices based on internal
belief states that are updated after receiving social feedback.
"""

import argparse
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Import from project utilities
from utils.config import get_config, set_seed
from utils.io import ensure_dir, save_csv, save_json
from utils.logger import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants for data generation
DEFAULT_N_PARTICIPANTS = 50
DEFAULT_N_TRIALS = 100
DEFAULT_ALPHA_TRUE = 0.3  # True learning rate
DEFAULT_BETA_TRUE = 5.0   # True inverse temperature (decision noise)
DEFAULT_SIGMA_TRUE = 0.5  # True observation noise


def generate_trial_data(
    n_trials: int,
    alpha: float,
    beta: float,
    rng: np.random.Generator
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate a single participant's trial sequence.
    
    Simulates a Rescorla-Wagner learning process with:
    - Binary choices (0 or 1)
    - Binary feedback (0 or 1)
    - Belief updates based on prediction error
    
    Args:
        n_trials: Number of trials to simulate
        alpha: Learning rate (how much beliefs update)
        beta: Inverse temperature (decision noise; higher = more deterministic)
        rng: NumPy random generator for reproducibility
        
    Returns:
        Tuple of (choices, feedback, beliefs, prediction_errors)
        - choices: Array of binary choices (0 or 1)
        - feedback: Array of binary feedback received (0 or 1)
        - beliefs: Array of belief states at each trial (before choice)
        - prediction_errors: Array of prediction errors after feedback
    """
    # Initialize belief state (probability that option 1 is better)
    beliefs = np.zeros(n_trials)
    beliefs[0] = 0.5  # Start with neutral belief
    
    # Initialize arrays
    choices = np.zeros(n_trials, dtype=int)
    feedback = np.zeros(n_trials, dtype=int)
    prediction_errors = np.zeros(n_trials)
    
    for t in range(n_trials):
        # Current belief about option 1 being better
        belief = beliefs[t]
        
        # Generate choice based on belief and inverse temperature
        # P(choose 1) = sigmoid(beta * (2*belief - 1))
        prob_choice_1 = 1 / (1 + np.exp(-beta * (2 * belief - 1)))
        choices[t] = 1 if rng.random() < prob_choice_1 else 0
        
        # Generate true outcome probability (simulated environment)
        # Option 1 has 60% chance of being correct, option 0 has 40%
        true_prob_1 = 0.6
        actual_outcome = 1 if rng.random() < true_prob_1 else 0
        feedback[t] = 1 if choices[t] == actual_outcome else 0
        
        # Compute prediction error
        # PE = feedback - (2 * belief - 1)  [scaled to [-1, 1]]
        expected_outcome = 2 * belief - 1  # Map [0,1] to [-1,1]
        pe = feedback[t] - (1 if choices[t] == 1 else 0) * 2 + 1  # Simplified
        # Actually: PE = feedback - (choice * 2 - 1) * belief? 
        # Standard RW: PE = outcome - belief
        # Here: outcome is binary (0/1), belief is probability (0-1)
        pe = feedback[t] - belief
        prediction_errors[t] = pe
        
        # Update belief for next trial
        if t < n_trials - 1:
            beliefs[t + 1] = belief + alpha * pe
            # Clamp belief to [0, 1]
            beliefs[t + 1] = np.clip(beliefs[t + 1], 0, 1)
    
    return choices, feedback, beliefs, prediction_errors


def generate_synthetic_dataset(
    n_participants: int = DEFAULT_N_PARTICIPANTS,
    n_trials: int = DEFAULT_N_TRIALS,
    alpha_true: float = DEFAULT_ALPHA_TRUE,
    beta_true: float = DEFAULT_BETA_TRUE,
    sigma_true: float = DEFAULT_SIGMA_TRUE,
    seed: Optional[int] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, pd.DataFrame]:
    """
    Generate a complete synthetic dataset for model validation.
    
    Creates data for multiple participants with individual variations
    in learning rates and decision noise, drawn from a group-level distribution.
    
    Args:
        n_participants: Number of participants to simulate
        n_trials: Number of trials per participant
        alpha_true: Group mean learning rate
        beta_true: Group mean inverse temperature
        sigma_true: Group-level standard deviation for alpha
        seed: Random seed for reproducibility
        output_dir: Directory to save output files (if provided)
        
    Returns:
        Dictionary containing:
        - 'behavioral': DataFrame with all trial data
        - 'params': DataFrame with ground-truth parameters per participant
        - 'metadata': Dictionary with generation parameters
    """
    if seed is not None:
        set_seed(seed)
    
    rng = np.random.default_rng(seed)
    
    # Generate group-level parameters with individual variations
    # Individual alphas drawn from normal distribution around alpha_true
    individual_alphas = np.random.normal(alpha_true, sigma_true, n_participants)
    individual_alphas = np.clip(individual_alphas, 0.05, 0.95)  # Clamp to valid range
    
    # Individual betas drawn from log-normal distribution (positive skew)
    individual_betas = np.random.lognormal(np.log(beta_true), 0.5, n_participants)
    individual_betas = np.clip(individual_betas, 1.0, 20.0)  # Clamp to reasonable range
    
    # Generate data for each participant
    all_rows = []
    participant_ids = []
    true_alphas = []
    true_betas = []
    
    for p_idx in range(n_participants):
        p_id = f"sub-{p_idx + 1:03d}"
        participant_ids.append(p_id)
        true_alphas.append(individual_alphas[p_idx])
        true_betas.append(individual_betas[p_idx])
        
        choices, feedback, beliefs, prediction_errors = generate_trial_data(
            n_trials=n_trials,
            alpha=individual_alphas[p_idx],
            beta=individual_betas[p_idx],
            rng=rng
        )
        
        for t_idx in range(n_trials):
            all_rows.append({
                'participant_id': p_id,
                'trial': t_idx + 1,
                'choice': choices[t_idx],
                'feedback': feedback[t_idx],
                'belief': beliefs[t_idx],
                'prediction_error': prediction_errors[t_idx],
                'alpha_true': individual_alphas[p_idx],
                'beta_true': individual_betas[p_idx]
            })
    
    # Create DataFrames
    behavioral_df = pd.DataFrame(all_rows)
    params_df = pd.DataFrame({
        'participant_id': participant_ids,
        'alpha_true': true_alphas,
        'beta_true': true_betas
    })
    
    metadata = {
        'n_participants': n_participants,
        'n_trials_per_participant': n_trials,
        'group_alpha_mean': alpha_true,
        'group_alpha_std': sigma_true,
        'group_beta_mean': beta_true,
        'generation_seed': seed,
        'data_type': 'synthetic_ground_truth'
    }
    
    logger.info(f"Generated synthetic dataset: {n_participants} participants, {n_trials} trials each")
    
    if output_dir:
        ensure_dir(output_dir)
        
        # Save behavioral data
        behavioral_path = output_dir / "synthetic_behavioral.csv"
        save_csv(behavioral_df, str(behavioral_path))
        logger.info(f"Saved behavioral data to {behavioral_path}")
        
        # Save ground truth parameters
        params_path = output_dir / "synthetic_params.csv"
        save_csv(params_df, str(params_path))
        logger.info(f"Saved ground truth parameters to {params_path}")
        
        # Save metadata
        metadata_path = output_dir / "synthetic_metadata.json"
        save_json(metadata, str(metadata_path))
        logger.info(f"Saved metadata to {metadata_path}")
    
    return {
        'behavioral': behavioral_df,
        'params': params_df,
        'metadata': metadata
    }


def main():
    """Main entry point for synthetic data generation."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic behavioral data for model validation"
    )
    parser.add_argument(
        "--n-participants",
        type=int,
        default=DEFAULT_N_PARTICIPANTS,
        help=f"Number of participants (default: {DEFAULT_N_PARTICIPANTS})"
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=DEFAULT_N_TRIALS,
        help=f"Trials per participant (default: {DEFAULT_N_TRIALS})"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=DEFAULT_ALPHA_TRUE,
        help=f"Group mean learning rate (default: {DEFAULT_ALPHA_TRUE})"
    )
    parser.add_argument(
        "--beta",
        type=float,
        default=DEFAULT_BETA_TRUE,
        help=f"Group mean inverse temperature (default: {DEFAULT_BETA_TRUE})"
    )
    parser.add_argument(
        "--sigma",
        type=float,
        default=DEFAULT_SIGMA_TRUE,
        help=f"Group-level std for alpha (default: {DEFAULT_SIGMA_TRUE})"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/synthetic",
        help="Output directory for generated data"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger.info("Starting synthetic data generation")
    logger.info(f"Parameters: n_participants={args.n_participants}, "
               f"n_trials={args.n_trials}, alpha={args.alpha}, "
               f"beta={args.beta}, sigma={args.sigma}")
    
    # Generate data
    output_path = Path(args.output_dir)
    result = generate_synthetic_dataset(
        n_participants=args.n_participants,
        n_trials=args.n_trials,
        alpha_true=args.alpha,
        beta_true=args.beta,
        sigma_true=args.sigma,
        seed=args.seed,
        output_dir=output_path
    )
    
    logger.info("Synthetic data generation completed successfully")
    
    # Print summary
    print(f"\nGenerated {args.n_participants} participants with {args.n_trials} trials each")
    print(f"Output saved to: {output_path}")
    print(f"Files created:")
    print(f"  - {output_path}/synthetic_behavioral.csv")
    print(f"  - {output_path}/synthetic_params.csv")
    print(f"  - {output_path}/synthetic_metadata.json")


if __name__ == "__main__":
    main()