import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from utils.config import get_permutation_shuffles, get_permutation_seed
from utils.logging import setup_logger

logger = setup_logger(__name__)

def load_null_residuals(file_path: str) -> np.ndarray:
    """Loads null residuals from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        return df.iloc[:, 0].to_numpy()  # Assuming residuals are in the first column
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading null residuals: {e}")
        raise

def run_freedman_lane_permutation(null_residuals: np.ndarray, num_shuffles: int = 1000, seed: int = 42) -> float:
    """Performs Freedman-Lane permutation test."""
    np.random.seed(seed)
    observed_statistic = null_residuals[0]  # Use the first residual as the observed statistic
    permuted_statistics = []
    for _ in range(num_shuffles):
        shuffled_residuals = np.random.permutation(null_residuals)
        permuted_statistics.append(shuffled_residuals[0])
    p_value = np.mean(np.abs(permuted_statistics) >= np.abs(observed_statistic))
    return p_value

def save_permutation_results(results: dict, file_path: str) -> None:
    """Saves permutation results to a JSON file."""
    try:
        with open(file_path, "w") as f:
            json.dump(results, f)
    except Exception as e:
        logger.error(f"Error saving permutation results: {e}")
        raise

def run_validation_analysis(null_residuals_path: str, output_path: str) -> None:
    """Runs the permutation test and saves the results."""
    try:
        null_residuals = load_null_residuals(null_residuals_path)
        num_shuffles = get_permutation_shuffles()
        seed = get_permutation_seed()
        p_value = run_freedman_lane_permutation(null_residuals, num_shuffles, seed)
        results = {"p_value": p_value}
        save_permutation_results(results, output_path)
        logger.info(f"Permutation test completed. P-value: {p_value}")

    except Exception as e:
        logger.error(f"Error running validation analysis: {e}")
        raise

def main():
    """Main function to run the validation analysis."""
    null_residuals_path = "data/processed/validation/null_residuals.csv"
    output_path = "data/processed/validation/permutation_results.json"
    run_validation_analysis(null_residuals_path, output_path)
