"""
Data Generation Module for Simulated Social Status Study.

This module provides functionality to generate synthetic research data
simulating the influence of social status on risk-taking behavior.
It supports between-subjects experimental designs with randomized
assignment to status and observed behavior conditions.

The generated data adheres to the project's design constraints:
- Random assignment to High/Low status conditions
- Random assignment to Risky/Conservative behavior conditions
- Risk-taking scores derived from meta-analytic effect sizes
- Strict validation of experimental integrity

Attributes:
    logger (logging.Logger): Module-level logger for tracking execution.
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime

# Ensure code is in path for imports if running as script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from logger import setup_logger, get_logger
from utils import set_seed, ensure_directory
from config import load_decision_record

logger = setup_logger("generate_data", "logs/generate_data.log")


def generate_synthetic_data(n: int = 800, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic dataset for the social status risk-taking study.

    Creates a between-subjects experimental dataset with randomized
    assignment to status and behavior conditions, simulating risk-taking
    scores based on meta-analytic effect sizes.

    Args:
        n (int): Number of participants to generate. Default is 800.
        seed (int): Random seed for reproducibility. Default is 42.

    Returns:
        pd.DataFrame: DataFrame containing:
            - participant_id: Unique identifier for each participant
            - status_level: Categorical variable (High/Low)
            - observed_behavior: Categorical variable (Risky/Conservative)
            - risk_taking_score: Continuous measure of risk-taking behavior

    Raises:
        SystemExit: If status_level lacks variance (experimental integrity violation)
        SystemExit: If duplicate participant IDs are detected (design violation)

    Example:
        >>> df = generate_synthetic_data(n=100, seed=123)
        >>> print(df.shape)
        (100, 4)
    """
    logger.info(f"Generating synthetic data with N={n} and seed={seed}")
    set_seed(seed)

    participant_ids = [f"sub_{i:04d}" for i in range(n)]

    # Between-subjects design: 2 levels of status, 2 levels of behavior
    status_levels = np.random.choice(["High", "Low"], size=n)
    observed_behaviors = np.random.choice(["Risky", "Conservative"], size=n)

    # Generate risk taking score based on simulated effect
    # Base score + effect of status + effect of behavior + interaction + noise
    base_score = 50.0
    status_effect = np.where(status_levels == "High", 5.0, 0.0)
    behavior_effect = np.where(observed_behaviors == "Risky", 10.0, 0.0)
    interaction_effect = np.where((status_levels == "High") & (observed_behaviors == "Risky"), 8.0, 0.0)
    noise = np.random.normal(0, 10, size=n)

    risk_taking_scores = base_score + status_effect + behavior_effect + interaction_effect + noise

    df = pd.DataFrame({
        "participant_id": participant_ids,
        "status_level": status_levels,
        "observed_behavior": observed_behaviors,
        "risk_taking_score": risk_taking_scores
    })

    # Validation: Check for variance in status_level
    if df["status_level"].nunique() < 2:
        logger.error("Error: status_level has no variance. Experimental condition integrity violated.")
        sys.exit(1)

    # Validation: Check between-subjects design (one observation per participant_id)
    if df["participant_id"].duplicated().any():
        logger.error("Error: Duplicate participant IDs detected. Between-subjects design violated.")
        sys.exit(1)

    return df


def main():
    """
    Command-line entry point for synthetic data generation.

    Parses arguments for sample size, random seed, and output path.
    Generates the synthetic dataset and saves it to the specified CSV file.
    Logs the generation process and confirms successful output.

    Args:
        --n (int): Number of participants (default: 800)
        --seed (int): Random seed for reproducibility (default: 42)
        --output (str): Required path for output CSV file

    Example:
        python code/generate_data.py --n 1000 --seed 123 --output data/raw/simulated_data.csv
    """
    parser = argparse.ArgumentParser(description="Generate synthetic research data")
    parser.add_argument("--n", type=int, default=800, help="Number of participants")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, required=True, help="Output CSV path")
    args = parser.parse_args()

    df = generate_synthetic_data(n=args.n, seed=args.seed)
    ensure_directory(os.path.dirname(args.output))
    df.to_csv(args.output, index=False)
    logger.info(f"Saved {len(df)} rows to {args.output}")
    print(f"Generated {len(df)} rows. Saved to {args.output}")


if __name__ == "__main__":
    main()
