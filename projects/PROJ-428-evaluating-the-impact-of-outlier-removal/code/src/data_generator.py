import numpy as np
import pandas as pd
from pathlib import Path
import json
from typing import Dict, Any, Tuple, List, Optional
import os
import logging
from src.checkpoint import CheckpointManager

logger = logging.getLogger(__name__)

def generate_normal_distribution(mean: float, std_dev: float, size: int) -> np.ndarray:
    """Generates a normal distribution."""
    return np.random.normal(mean, std_dev, size)

def generate_lognormal_distribution(mean: float, sigma: float, size: int) -> np.ndarray:
    """Generates a log-normal distribution."""
    return np.random.lognormal(mean, sigma, size)

def generate_exponential_distribution(scale: float, size: int) -> np.ndarray:
    """Generates an exponential distribution."""
    return np.random.exponential(scale, size)

def generate_beta_distribution(a: float, b: float, size: int) -> np.ndarray:
    """Generates a beta distribution."""
    return np.random.beta(a, b, size)

def generate_gamma_distribution(shape: float, scale: float, size: int) -> np.ndarray:
    """Generates a gamma distribution."""
    return np.random.gamma(shape, scale, size)

def save_ground_truth_params(params: Dict[str, Any], filepath: Path) -> None:
    """Saves ground truth parameters to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(params, f)

def generate_and_save_distribution(
    distribution_type: str, params: Dict[str, Any], filepath: Path, size: int
) -> None:
    """Generates and saves a distribution to a CSV file."""
    if distribution_type == "normal":
        data = generate_normal_distribution(params["mean"], params["std_dev"], size)
    elif distribution_type == "lognormal":
        data = generate_lognormal_distribution(params["mean"], params["sigma"], size)
    elif distribution_type == "exponential":
        data = generate_exponential_distribution(params["scale"], size)
    elif distribution_type == "beta":
        data = generate_beta_distribution(params["a"], params["b"], size)
    elif distribution_type == "gamma":
        data = generate_gamma_distribution(params["shape"], params["scale"], size)
    else:
        raise ValueError(f"Unsupported distribution type: {distribution_type}")

    df = pd.DataFrame(data, columns=[distribution_type])
    df.to_csv(filepath, index=False)

def inject_outliers(data: pd.DataFrame, contamination_rate: float, outlier_type: str) -> pd.DataFrame:
    """Injects outliers into a DataFrame."""
    if outlier_type == "cauchy":
        num_outliers = int(len(data) * contamination_rate)
        outliers = np.random.standard_cauchy(num_outliers)
        data.iloc[np.random.choice(len(data), num_outliers, replace=False)] = outliers
    elif outlier_type == "extreme_scaling":
      num_outliers = int(len(data) * contamination_rate)
      indices = np.random.choice(len(data), num_outliers, replace=False)
      data.iloc[indices] = data.iloc[indices] * np.random.choice([-10, 10], size=num_outliers)
    else:
        raise ValueError(f"Unsupported outlier type: {outlier_type}")
    return data


def main():
    """Main function to generate contaminated data."""
    data_dir = Path("data/processed")
    data_dir.mkdir(parents=True, exist_ok=True)

    contamination_rates = [0.0, 0.05, 0.1, 0.2]
    outlier_types = ["cauchy", "extreme_scaling"]
    distribution_types = ["normal", "lognormal"]

    for dist_type in distribution_types:
        for rate in contamination_rates:
            for outlier_type in outlier_types:
                # Generate clean data
                if dist_type == "normal":
                    params = {"mean": 0, "std_dev": 1}
                elif dist_type == "lognormal":
                    params = {"mean": 0, "sigma": 1}
                else:
                    raise ValueError(f"Unsupported distribution type: {dist_type}")

                clean_filepath = data_dir / f"{dist_type}_clean_{rate}.csv"
                generate_and_save_distribution(dist_type, params, clean_filepath, 1000)

                # Load clean data
                clean_data = pd.read_csv(clean_filepath)

                # Inject outliers
                contaminated_data = inject_outliers(clean_data.copy(), rate, outlier_type)

                # Save contaminated data
                contaminated_filepath = data_dir / f"{dist_type}_contaminated_{rate}_{outlier_type}.csv"
                contaminated_data.to_csv(contaminated_filepath, index=False)

                # Save injection profile
                injection_profile = {
                    "distribution_type": dist_type,
                    "contamination_rate": rate,
                    "outlier_type": outlier_type,
                }
                injection_profile_filepath = data_dir / "injection_profile.json"
                save_ground_truth_params(injection_profile, injection_profile_filepath)

                logger.info(f"Generated and saved contaminated data: {contaminated_filepath}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()