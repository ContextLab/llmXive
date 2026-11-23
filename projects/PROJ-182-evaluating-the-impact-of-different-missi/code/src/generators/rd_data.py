"""
Synthetic Regression Discontinuity (RD) Data Generator.

Generates synthetic RD datasets with known ground truth parameters and
applies missingness mechanisms.

Model: Y = beta0 + beta1*X + beta2*Z + tau*D + epsilon
Where:
  - X ~ Uniform(-1, 1) (Running variable)
  - Z ~ Normal(0, 1) (Covariate)
  - D = (X > 0) (Treatment indicator)
  - epsilon ~ Normal(0, sigma)
  - Z* ~ Normal(0, 1) (Exclusion restriction, independent of X, affects missingness)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from pathlib import Path

# Import from existing project modules
from src.logging_config import get_logger
from src.models import SimulationConfig

logger = get_logger(__name__)


def generate_rd_data(
    sample_size: int,
    beta0: float = 0.0,
    beta1: float = 1.0,
    beta2: float = 0.5,
    tau: float = 2.0,
    sigma: float = 1.0,
    seed: Optional[int] = None
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Generate synthetic RD data according to the linear model.

    Args:
        sample_size: Number of observations to generate.
        beta0: Intercept.
        beta1: Coefficient for running variable X.
        beta2: Coefficient for covariate Z.
        tau: Treatment effect (jump at X=0).
        sigma: Standard deviation of error term.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (DataFrame with columns X, Z, Z_star, D, Y, Y_true, and dict of ground truth params).
    """
    if seed is not None:
        np.random.seed(seed)
        logger.info(f"Set random seed to {seed} for data generation")

    # Generate running variable X ~ Uniform(-1, 1)
    X = np.random.uniform(-1, 1, size=sample_size)

    # Generate covariate Z ~ Normal(0, 1)
    Z = np.random.normal(0, 1, size=sample_size)

    # Generate exclusion restriction Z* ~ Normal(0, 1)
    # Independent of X, affects missingness (used in MAR/MNAR mechanisms)
    Z_star = np.random.normal(0, 1, size=sample_size)

    # Treatment indicator D = (X > 0)
    D = (X > 0).astype(float)

    # Generate error term epsilon ~ Normal(0, sigma)
    epsilon = np.random.normal(0, sigma, size=sample_size)

    # Calculate true outcome Y (before any missingness)
    # Y = beta0 + beta1*X + beta2*Z + tau*D + epsilon
    Y_true = beta0 + beta1 * X + beta2 * Z + tau * D + epsilon

    # Create DataFrame
    df = pd.DataFrame({
        'X': X,
        'Z': Z,
        'Z_star': Z_star,
        'D': D,
        'Y': Y_true,  # Will be masked later by missingness generator
        'Y_true': Y_true  # Keep true value for validation/bias calculation
    })

    ground_truth = {
        'beta0': beta0,
        'beta1': beta1,
        'beta2': beta2,
        'tau': tau,
        'sigma': sigma
    }

    logger.info(f"Generated {sample_size} RD observations with treatment effect tau={tau}")
    return df, ground_truth


def load_simulation_config_from_dict(config_dict: Dict[str, Any]) -> SimulationConfig:
    """
    Helper to create SimulationConfig from a dictionary (e.g., loaded from YAML).
    This bridges the gap between YAML config and the data generator.
    """
    return SimulationConfig(
        sample_size=config_dict.get('sample_size', 1000),
        true_effect=config_dict.get('true_effect', 2.0),
        seed=config_dict.get('seed', 42),
        exclusion_restriction=config_dict.get('exclusion_restriction', 0.0),
        beta0=config_dict.get('beta0', 0.0),
        beta1=config_dict.get('beta1', 1.0),
        beta2=config_dict.get('beta2', 0.5),
        sigma=config_dict.get('sigma', 1.0)
    )


def main():
    """
    Standalone execution to generate and save synthetic RD data.
    Reads configuration from config/simulation.yaml and saves to data/simulated_raw.csv.
    """
    import yaml
    from src.config_loader import load_simulation_config

    # Load configuration
    try:
        sim_config = load_simulation_config()
        logger.info(f"Loaded simulation config: sample_size={sim_config.sample_size}, seed={sim_config.seed}")
    except FileNotFoundError:
        logger.warning("config/simulation.yaml not found, using defaults")
        # Fallback defaults if config file is missing (for initial testing)
        sim_config = SimulationConfig(
            sample_size=1000,
            true_effect=2.0,
            seed=42,
            exclusion_restriction=0.0,
            beta0=0.0,
            beta1=1.0,
            beta2=0.5,
            sigma=1.0
        )

    # Generate data
    df, ground_truth = generate_rd_data(
        sample_size=sim_config.sample_size,
        beta0=sim_config.beta0,
        beta1=sim_config.beta1,
        beta2=sim_config.beta2,
        tau=sim_config.true_effect,
        sigma=sim_config.sigma,
        seed=sim_config.seed
    )

    # Save to data/simulated_raw.csv
    output_path = Path("data/simulated_raw.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved simulated RD data to {output_path}")

    # Save ground truth parameters to a separate file for validation
    ground_truth_path = Path("data/ground_truth.json")
    import json
    with open(ground_truth_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    logger.info(f"Saved ground truth parameters to {ground_truth_path}")

    print(f"Successfully generated {len(df)} observations.")
    print(f"Output saved to: {output_path}")
    print(f"Ground truth saved to: {ground_truth_path}")


if __name__ == "__main__":
    main()
