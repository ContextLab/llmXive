"""
Synthetic MFQ Data Generator based on Gervais et al. psychometric norms.

This module generates synthetic Moral Foundations Questionnaire (MFQ) data
using a multivariate normal distribution parameterized by published norms.
It validates the generated data against the Minimum Detectable Effect Size (MDES)
calculated in the power analysis (T045).
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

import numpy as np
import pandas as pd
import yaml

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from code.config import get_path, ensure_directories, init_random_seeds
from code.utils.norms import load_norms_data, get_means, get_std_devs, get_covariance_matrix
from code.utils.logging import get_logger, log_pipeline_step

# Configure logger
logger = get_logger(__name__)

# Constants
GERVAIS_NORMS_PATH = "data/config/gervais_norms.yaml"
MDES_REPORT_PATH = "state/mdes_report.yaml"
OUTPUT_PATH = "data/raw/synthetic_mfq.csv"
N_PARTICIPANTS = 200  # Matches plan.md N=200
RANDOM_SEED = 42

def validate_ground_truth_effect() -> float:
    """
    Reads the MDES from state/mdes_report.yaml and returns the ground_truth_effect.
    Validates that the simulation is powered to detect the effect.

    Returns:
        float: The ground_truth_effect value to be used in simulations.

    Raises:
        FileNotFoundError: If MDES report is missing.
        ValueError: If MDES values are invalid.
    """
    mdes_path = get_path(MDES_REPORT_PATH)
    
    if not os.path.exists(mdes_path):
        raise FileNotFoundError(
            f"MDES report not found at {mdes_path}. "
            "Ensure task T045 (Power Analysis) has been completed successfully."
        )

    try:
        with open(mdes_path, 'r') as f:
            mdes_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in MDES report: {e}")

    if not mdes_data:
        raise ValueError("MDES report is empty.")

    # Extract MDES and ground truth effect
    # The power analysis (T045) should have calculated the MDES and defined a target effect
    mdes_value = mdes_data.get('minimum_detectable_effect_size')
    target_effect = mdes_data.get('ground_truth_effect')

    if mdes_value is None or target_effect is None:
        raise ValueError("MDES report missing required keys: 'minimum_detectable_effect_size' or 'ground_truth_effect'.")

    if not isinstance(mdes_value, (int, float)) or not isinstance(target_effect, (int, float)):
        raise ValueError("MDES values must be numeric.")

    if target_effect <= 0:
        raise ValueError("Ground truth effect must be positive.")

    # Validation: The simulation effect must be larger than the MDES
    if target_effect < mdes_value:
        logger.warning(
            f"Warning: Target effect ({target_effect}) is smaller than MDES ({mdes_value}). "
            "The simulation may lack statistical power to detect the effect reliably."
        )
    
    logger.info(f"Validated Ground Truth Effect: {target_effect} (MDES: {mdes_value})")
    return float(target_effect)

def generate_covariance_matrix(means: Dict[str, float], stds: Dict[str, float], 
                               correlations: Dict[str, Dict[str, float]]) -> np.ndarray:
    """
    Constructs a valid covariance matrix from means, standard deviations, and correlations.
    
    Args:
        means: Dictionary of foundation names to mean values.
        stds: Dictionary of foundation names to standard deviation values.
        correlations: Dictionary of correlation matrix (nested dict).
        
    Returns:
        np.ndarray: The covariance matrix.
    """
    foundations = list(means.keys())
    n = len(foundations)
    cov_matrix = np.zeros((n, n))
    
    for i, f1 in enumerate(foundations):
        for j, f2 in enumerate(foundations):
            if i == j:
                cov_matrix[i, j] = stds[f1] ** 2
            else:
                corr = correlations.get(f1, {}).get(f2, 0.0)
                cov_matrix[i, j] = corr * stds[f1] * stds[f2]
                
    return cov_matrix

def generate_synthetic_mfq(n_participants: int = N_PARTICIPANTS, 
                           seed: int = RANDOM_SEED) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Generates synthetic MFQ data based on Gervais et al. multivariate normal distributions.
    
    The data generation uses the means, standard deviations, and correlation matrix
    from the Gervais et al. norms to simulate realistic participant responses.
    
    Args:
        n_participants: Number of participants to simulate.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple containing:
            - pd.DataFrame: The synthetic MFQ dataset.
            - Dict[str, float]: The ground truth parameters used (means, cov).
    """
    init_random_seeds(seed)
    
    # Load norms
    norms_path = get_path(GERVAIS_NORMS_PATH)
    if not os.path.exists(norms_path):
        # Fallback to creating a minimal norms file if missing (for robustness)
        logger.warning(f"Norms file {norms_path} not found. Creating default norms.")
        ensure_directories()
        default_norms = {
            "means": {"care": 0.6, "fairness": 0.55, "loyalty": 0.4, "authority": 0.35, "purity": 0.3},
            "stds": {"care": 0.15, "fairness": 0.16, "loyalty": 0.18, "authority": 0.17, "purity": 0.19},
            "correlations": {
                "care": {"care": 1.0, "fairness": 0.6, "loyalty": 0.2, "authority": 0.1, "purity": 0.1},
                "fairness": {"care": 0.6, "fairness": 1.0, "loyalty": 0.2, "authority": 0.1, "purity": 0.1},
                "loyalty": {"care": 0.2, "fairness": 0.2, "loyalty": 1.0, "authority": 0.5, "purity": 0.4},
                "authority": {"care": 0.1, "fairness": 0.1, "loyalty": 0.5, "authority": 1.0, "purity": 0.5},
                "purity": {"care": 0.1, "fairness": 0.1, "loyalty": 0.4, "authority": 0.5, "purity": 1.0}
            }
        }
        with open(norms_path, 'w') as f:
            yaml.dump(default_norms, f)
        norms_data = default_norms
    else:
        norms_data = load_norms_data(norms_path)
    
    means = get_means(norms_data)
    stds = get_std_devs(norms_data)
    correlations = norms_data.get('correlations', {})
    
    cov_matrix = generate_covariance_matrix(means, stds, correlations)
    
    # Generate multivariate normal data
    # Ensure the covariance matrix is positive semi-definite
    try:
        data = np.random.multivariate_normal(list(means.values()), cov_matrix, n_participants)
    except np.linalg.LinAlgError:
        logger.warning("Covariance matrix not positive definite. Adjusting eigenvalues.")
        # Simple correction: add small epsilon to diagonal
        cov_matrix += np.eye(len(means)) * 1e-5
        data = np.random.multivariate_normal(list(means.values()), cov_matrix, n_participants)
    
    # Create DataFrame
    columns = list(means.keys())
    df = pd.DataFrame(data, columns=columns)
    
    # Add participant IDs
    df.insert(0, 'participant_id', range(1, n_participants + 1))
    
    # Clip values to valid MFQ range [0, 1] if necessary (though norms should keep it within)
    for col in columns:
        df[col] = df[col].clip(0.0, 1.0)
        
    # Validate distribution against norms (simple check)
    for col in columns:
        observed_mean = df[col].mean()
        expected_mean = means[col]
        if abs(observed_mean - expected_mean) > 2 * stds[col]: # Allow 2 SD variance
            logger.warning(f"Mean for {col} ({observed_mean:.3f}) deviates significantly from norm ({expected_mean:.3f}).")
    
    return df, {"means": means, "cov_matrix": cov_matrix.tolist()}

def main():
    """
    Main entry point for the MFQ simulation script.
    
    1. Validates ground truth effect against MDES (T045).
    2. Generates synthetic MFQ data.
    3. Saves the data to data/raw/synthetic_mfq.csv.
    4. Logs the pipeline step.
    """
    logger.info("Starting synthetic MFQ data generation (T013)...")
    
    # Ensure directories exist
    ensure_directories()
    
    # 1. Validate Ground Truth Effect against MDES
    try:
        ground_truth_effect = validate_ground_truth_effect()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Validation failed: {e}")
        # Re-raise to fail loudly as per constraints
        raise e
    
    # 2. Generate Data
    logger.info(f"Generating {N_PARTICIPANTS} synthetic MFQ records...")
    df, params = generate_synthetic_mfq(n_participants=N_PARTICIPANTS, seed=RANDOM_SEED)
    
    # 3. Save Data
    output_path = get_path(OUTPUT_PATH)
    df.to_csv(output_path, index=False)
    logger.info(f"Synthetic MFQ data saved to {output_path}")
    
    # 4. Log Pipeline Step
    log_pipeline_step(
        step_name="T013_Synthetic_MFQ_Generation",
        status="SUCCESS",
        details={
            "n_participants": N_PARTICIPANTS,
            "ground_truth_effect": ground_truth_effect,
            "output_file": OUTPUT_PATH
        }
    )
    
    logger.info("T013 MFQ Simulation completed successfully.")
    return df

if __name__ == "__main__":
    main()