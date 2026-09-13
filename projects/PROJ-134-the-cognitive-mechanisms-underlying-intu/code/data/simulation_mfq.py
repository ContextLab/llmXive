from __future__ import annotations
import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple

def load_mdes_report(mdes_report_path: str = "state/mdes_report.yaml") -> Dict[str, Any]:
    """Loads the MDES report from the specified YAML file."""
    try:
        with open(mdes_report_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"MDES report missing at {mdes_report_path}. Ensure T045 (Power Analysis) is complete before running this task."
        ) from None

def validate_ground_truth_effect(ground_truth_effect: float, mdes_report: Dict[str, Any]) -> bool:
    """Validates that the ground truth effect is within the acceptable range based on the MDES report."""
    n_required = mdes_report["n_required"]
    effect_size = mdes_report["effect_size"]
    # Add a check if the ground truth effect is within a reasonable range
    if abs(ground_truth_effect) > effect_size * 2:
        logging.warning(
            f"Ground truth effect ({ground_truth_effect}) is significantly larger than the expected effect size ({effect_size})."
        )
        return False
    return True

def get_correlation_matrix(num_factors: int = 6) -> np.ndarray:
    """Generates a correlation matrix for the MFQ factors."""
    np.random.seed(42)  # for reproducibility
    correlation_matrix = np.random.rand(num_factors, num_factors)
    correlation_matrix = np.triu(correlation_matrix, k=1)  # upper triangle
    correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2  # make symmetric
    np.fill_diagonal(correlation_matrix, 1)
    return correlation_matrix

def generate_covariance_matrix(correlation_matrix: np.ndarray, variances: list[float]) -> np.ndarray:
    """Generates a covariance matrix from the correlation matrix and variances."""
    std_devs = np.sqrt(variances)
    covariance_matrix = np.outer(std_devs, std_devs) * correlation_matrix
    return covariance_matrix

def generate_synthetic_mfq(
    n_samples: int = 100,
    ground_truth_effect: float = 0.5,
    mdes_report: Dict[str, Any] = None,
) -> pd.DataFrame:
    """Generates synthetic MFQ data based on the specified parameters."""

    if mdes_report is None:
        raise ValueError("MDES report must be provided.")

    if not validate_ground_truth_effect(ground_truth_effect, mdes_report):
        logging.warning("Ground truth effect is outside the acceptable range. Proceeding with caution.")

    # Load the means and standard deviations from the Gervais norms
    norms = load_yaml_config("data/config/gervais_norms.yaml")
    means = [norms[factor]["mean"] for factor in norms]
    variances = [norms[factor]["std"] ** 2 for factor in norms]

    # Generate the correlation matrix
    correlation_matrix = get_correlation_matrix()

    # Generate the covariance matrix
    covariance_matrix = generate_covariance_matrix(correlation_matrix, variances)

    # Generate the data
    np.random.seed(42)
    data = np.random.multivariate_normal(means, covariance_matrix, n_samples)
    df = pd.DataFrame(data, columns=["care", "fairness", "loyalty", "authority", "purity", "total_score"])
    df["participant_id"] = range(n_samples)

    # Add the ground truth effect
    df["total_score"] = df["total_score"] + ground_truth_effect

    return df

def save_synthetic_mfq(df: pd.DataFrame, output_path: str = "data/processed/synthetic_mfq.csv"):
    """Saves the synthetic MFQ data to a CSV file."""
    df.to_csv(output_path, index=False)

def update_artifact_hash(file_path: str):
    """Updates the artifact hash in the state file."""
    import hashlib

    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    # Load existing hashes
    try:
        with open("state/artifact_hashes.yaml", "r") as f:
            hashes = yaml.safe_load(f)
    except FileNotFoundError:
        hashes = {}

    # Update the hash
    hashes[file_path] = file_hash

    # Save the updated hashes
    with open("state/artifact_hashes.yaml", "w") as f:
        yaml.dump(hashes, f)

def log_pipeline_step(logger, step_name: str, message: str):
    logger.info(f"Pipeline Step: {step_name} - {message}")

def main():
    """Main function to run the synthetic MFQ data generation pipeline."""
    import yaml

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    try:
        # Load the MDES report
        mdes_report = load_mdes_report()

        # Generate the synthetic MFQ data
        synthetic_mfq_data = generate_synthetic_mfq(
            n_samples=100, ground_truth_effect=0.5, mdes_report=mdes_report
        )

        # Save the synthetic MFQ data
        output_path = "data/processed/synthetic_mfq.csv"
        save_synthetic_mfq(synthetic_mfq_data, output_path)
        logging.info(f"Synthetic MFQ data saved to {output_path}")

        # Update the artifact hash
        update_artifact_hash(output_path)
        logging.info(f"Artifact hash updated for {output_path}")

    except Exception as e:
        logging.error(f"An error occurred during synthetic MFQ data generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()