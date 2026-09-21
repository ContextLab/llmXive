"""
Synthetic Data Generator for Belief Updating Model Validation.

This module generates ground-truth behavioral data for validation purposes.
It creates synthetic datasets where the true parameters (alpha, precision)
are known, allowing verification that the model (T024) can recover these
parameters within a defined error margin.

The generator creates realistic choice sequences based on a Rescorla-Wagner
learning model with noise, simulating the behavioral data structure expected
from the OpenNeuro ds003694 dataset.

Outputs:
    data/synthetic/ground_truth.csv: CSV with columns subject_id, true_alpha,
        true_precision, generated_choices (JSON-encoded list of choices).
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.config import get_config, set_seed
from utils.logger import get_logger
from utils.io import ensure_dir, save_csv

logger = get_logger(__name__)


def generate_trial_data(
    true_alpha: float,
    true_precision: float,
    n_trials: int = 100,
    seed: Optional[int] = None
) -> Tuple[List[int], List[float], List[float]]:
    """
    Generate a single subject's trial-by-trial behavioral data.

    Simulates a Rescorla-Wagner learning process where the subject updates
    belief values based on feedback discrepancy, then makes stochastic choices.

    Args:
        true_alpha: Ground-truth learning rate (0.0 to 1.0).
        true_precision: Ground-truth inverse temperature for choice stochasticity.
        n_trials: Number of trials to simulate.
        seed: Random seed for reproducibility of this subject's data.

    Returns:
        Tuple of (choices, values, discrepancies).
        - choices: List of 0 or 1 indicating the chosen option.
        - values: List of learned values for the chosen option.
        - discrepancies: List of feedback discrepancies (outcome - expected).
    """
    if seed is not None:
        np.random.seed(seed)

    # Initialize values for two options
    value_0 = 0.5
    value_1 = 0.5

    choices = []
    values = []
    discrepancies = []

    for t in range(n_trials):
        # Compute choice probability using softmax
        # P(choose 1) = 1 / (1 + exp(-precision * (value_1 - value_0)))
        diff = value_1 - value_0
        prob_1 = 1.0 / (1.0 + np.exp(-true_precision * diff))

        # Make choice
        choice = 1 if np.random.random() < prob_1 else 0
        choices.append(choice)

        # Store value of chosen option
        current_value = value_1 if choice == 1 else value_0
        values.append(current_value)

        # Simulate outcome (binary reward: 0 or 1)
        # True probability of reward for option 0 is 0.3, for option 1 is 0.7
        # This creates a non-stationary environment where option 1 is generally better
        true_prob_reward = 0.7 if choice == 1 else 0.3
        outcome = 1 if np.random.random() < true_prob_reward else 0

        # Calculate discrepancy (prediction error)
        discrepancy = outcome - current_value
        discrepancies.append(discrepancy)

        # Update value of chosen option using Rescorla-Wagner rule
        if choice == 0:
            value_0 += true_alpha * discrepancy
        else:
            value_1 += true_alpha * discrepancy

        # Clamp values to [0, 1]
        value_0 = np.clip(value_0, 0.0, 1.0)
        value_1 = np.clip(value_1, 0.0, 1.0)

    return choices, values, discrepancies


def generate_synthetic_dataset(
    n_participants: int = 50,
    n_trials: int = 100,
    output_path: Optional[str] = None,
    seed: Optional[int] = 42
) -> pd.DataFrame:
    """
    Generate a complete synthetic dataset for model validation.

    Creates multiple subjects with varying ground-truth parameters to test
    the model's ability to recover individual differences.

    Args:
        n_participants: Number of synthetic subjects to generate.
        n_trials: Number of trials per subject.
        output_path: Path to save the CSV output. If None, no file is saved.
        seed: Random seed for reproducibility of the dataset generation.

    Returns:
        DataFrame with columns: subject_id, true_alpha, true_precision, generated_choices.

    Raises:
        ValueError: If n_participants or n_trials are invalid.
    """
    if n_participants <= 0:
        raise ValueError("n_participants must be positive")
    if n_trials <= 0:
        raise ValueError("n_trials must be positive")

    if seed is not None:
        np.random.seed(seed)

    logger.info(f"Generating synthetic dataset for {n_participants} participants")

    data = []

    # Generate ground-truth parameters from a realistic distribution
    # Alpha: Beta distribution skewed towards moderate learning rates
    # Precision: Log-normal distribution for inverse temperature
    true_alphas = np.random.beta(2, 2, n_participants)  # Mean ~0.5
    true_precisions = np.random.lognormal(mean=0.5, sigma=0.5, size=n_participants)

    for i in range(n_participants):
        subject_id = f"syn_sub_{i:03d}"
        alpha = float(true_alphas[i])
        precision = float(true_precisions[i])

        # Generate trial data for this subject
        # Use a unique seed for each subject based on the main seed
        subject_seed = None if seed is None else seed + i
        choices, _, _ = generate_trial_data(alpha, precision, n_trials, subject_seed)

        # Store choices as a JSON string to fit in CSV
        choices_json = json.dumps(choices)

        data.append({
            "subject_id": subject_id,
            "true_alpha": round(alpha, 4),
            "true_precision": round(precision, 4),
            "generated_choices": choices_json
        })

        if (i + 1) % 10 == 0:
            logger.info(f"Generated {i + 1}/{n_participants} subjects")

    df = pd.DataFrame(data)

    if output_path:
        ensure_dir(output_path)
        save_csv(df, output_path)
        logger.info(f"Saved synthetic dataset to {output_path}")

    return df


def main():
    """
    Main entry point for synthetic data generation.

    Command-line arguments:
        --n-participants: Number of synthetic subjects (default: 50)
        --n-trials: Number of trials per subject (default: 100)
        --output: Output CSV path (default: data/synthetic/ground_truth.csv)
        --seed: Random seed (default: 42)
    """
    parser = argparse.ArgumentParser(
        description="Generate synthetic behavioral data for model validation."
    )
    parser.add_argument(
        "--n-participants",
        type=int,
        default=50,
        help="Number of synthetic participants to generate (default: 50)"
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=100,
        help="Number of trials per participant (default: 100)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/synthetic/ground_truth.csv",
        help="Output CSV file path (default: data/synthetic/ground_truth.csv)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("Starting synthetic data generation")

    try:
        df = generate_synthetic_dataset(
            n_participants=args.n_participants,
            n_trials=args.n_trials,
            output_path=args.output,
            seed=args.seed
        )

        logger.info(f"Synthetic data generation completed successfully.")
        logger.info(f"Generated {len(df)} subjects with {args.n_trials} trials each.")
        logger.info(f"Output saved to: {args.output}")

        # Verify the output file exists and is non-empty
        if os.path.exists(args.output) and os.path.getsize(args.output) > 0:
            logger.info("Output file verification passed.")
        else:
            logger.error("Output file verification failed: file missing or empty.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Synthetic data generation failed: {e}")
        raise


if __name__ == "__main__":
    main()