"""
Psychometric Norms Module for Gervais et al. MFQ Data.

This module handles loading, saving, and validating Moral Foundations Questionnaire (MFQ)
data against established psychometric norms from Gervais et al.

It provides functions to:
1. Load norms from a YAML configuration file.
2. Generate synthetic MFQ data based on these norms (multivariate normal).
3. Validate generated data against the norms (mean/SD/Correlation checks).
4. Save updated norms or generated data.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
import yaml
from scipy import stats

# Import project utilities
# Note: Using relative imports where possible, falling back to absolute if needed for execution context
try:
    from config import get_path, load_yaml_config
    from utils.schema import MFQResponse, MFQDataset
except ImportError:
    # Fallback for direct execution or different import contexts
    from code.config import get_path, load_yaml_config
    from code.utils.schema import MFQResponse, MFQDataset

# Constants
NORMS_CONFIG_PATH = "data/config/gervais_norms.yaml"
DEFAULT_MEANS = {
    "care_relevance": 4.2,
    "fairness_relevance": 4.1,
    "loyalty_relevance": 3.8,
    "authority_relevance": 3.5,
    "purity_relevance": 3.6,
    "care_justification": 3.9,
    "fairness_justification": 3.8,
    "loyalty_justification": 3.4,
    "authority_justification": 3.1,
    "purity_justification": 3.2
}
DEFAULT_STD_DEVS = {
    "care_relevance": 0.8,
    "fairness_relevance": 0.9,
    "loyalty_relevance": 1.0,
    "authority_relevance": 1.1,
    "purity_relevance": 1.0,
    "care_justification": 0.9,
    "fairness_justification": 0.9,
    "loyalty_justification": 1.0,
    "authority_justification": 1.1,
    "purity_justification": 1.0
}
# Simplified correlation structure (identity for robustness, can be expanded)
DEFAULT_CORRELATIONS = {
    "care_relevance": {"care_justification": 0.6},
    "fairness_relevance": {"fairness_justification": 0.6},
    "loyalty_relevance": {"loyalty_justification": 0.5},
    "authority_relevance": {"authority_justification": 0.5},
    "purity_relevance": {"purity_justification": 0.5}
}

logger = logging.getLogger(__name__)


def load_norms_data(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load psychometric norms from a YAML configuration file.

    Args:
        config_path: Path to the YAML config file. Defaults to NORMS_CONFIG_PATH.

    Returns:
        Dictionary containing means, std_devs, and correlation matrix.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the config file is malformed.
    """
    if config_path is None:
        config_path = get_path(NORMS_CONFIG_PATH)
    else:
        config_path = get_path(config_path)

    if not os.path.exists(config_path):
        logger.warning(f"Norms config file not found at {config_path}. Using defaults.")
        return {
            "means": DEFAULT_MEANS,
            "std_devs": DEFAULT_STD_DEVS,
            "correlations": DEFAULT_CORRELATIONS
        }

    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        logger.info(f"Loaded norms from {config_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading norms config: {e}")
        raise


def save_norms_data(data: Dict[str, Any], config_path: Optional[str] = None) -> None:
    """
    Save psychometric norms to a YAML configuration file.

    Args:
        data: Dictionary containing means, std_devs, and correlations.
        config_path: Path to the output YAML file.
    """
    if config_path is None:
        config_path = get_path(NORMS_CONFIG_PATH)
    else:
        config_path = get_path(config_path)

    # Ensure directory exists
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    with open(config_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)
    logger.info(f"Saved norms to {config_path}")


def get_means(norms: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """
    Extract means from norms data.

    Args:
        norms: Norms dictionary. If None, loads defaults.

    Returns:
        Dictionary of mean values for each MFQ dimension.
    """
    if norms is None:
        norms = load_norms_data()
    return norms.get("means", DEFAULT_MEANS)


def get_std_devs(norms: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """
    Extract standard deviations from norms data.

    Args:
        norms: Norms dictionary. If None, loads defaults.

    Returns:
        Dictionary of standard deviation values for each MFQ dimension.
    """
    if norms is None:
        norms = load_norms_data()
    return norms.get("std_devs", DEFAULT_STD_DEVS)


def get_correlation_matrix(norms: Optional[Dict[str, Any]] = None) -> np.ndarray:
    """
    Construct a correlation matrix from the norms data.

    Args:
        norms: Norms dictionary.

    Returns:
        Numpy array representing the correlation matrix.
    """
    if norms is None:
        norms = load_norms_data()

    means = get_means(norms)
    keys = list(means.keys())
    n = len(keys)
    corr_matrix = np.eye(n)

    correlations = norms.get("correlations", DEFAULT_CORRELATIONS)
    for var1, pairs in correlations.items():
        for var2, corr_val in pairs.items():
            if var1 in keys and var2 in keys:
                idx1 = keys.index(var1)
                idx2 = keys.index(var2)
                corr_matrix[idx1, idx2] = corr_val
                corr_matrix[idx2, idx1] = corr_val

    return corr_matrix


def get_covariance_matrix(norms: Optional[Dict[str, Any]] = None) -> np.ndarray:
    """
    Construct a covariance matrix from means, std_devs, and correlations.

    Args:
        norms: Norms dictionary.

    Returns:
        Numpy array representing the covariance matrix.
    """
    std_devs = get_std_devs(norms)
    corr_matrix = get_correlation_matrix(norms)
    keys = list(get_means(norms).keys())

    cov_matrix = np.zeros((len(keys), len(keys)))
    for i, var1 in enumerate(keys):
        for j, var2 in enumerate(keys):
            cov_matrix[i, j] = std_devs[var1] * std_devs[var2] * corr_matrix[i, j]

    return cov_matrix


def generate_synthetic_mfq_from_norms(
    n_samples: int,
    norms: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate synthetic MFQ data based on Gervais et al. norms.

    Uses a multivariate normal distribution with means and covariance derived
    from the provided norms.

    Args:
        n_samples: Number of participants to simulate.
        norms: Norms dictionary. If None, loads defaults.
        seed: Random seed for reproducibility.

    Returns:
        Pandas DataFrame with synthetic MFQ responses.
    """
    if seed is not None:
        np.random.seed(seed)

    if norms is None:
        norms = load_norms_data()

    means = get_means(norms)
    cov_matrix = get_covariance_matrix(norms)
    keys = list(means.keys())

    # Ensure covariance matrix is positive semi-definite
    try:
        data = np.random.multivariate_normal(list(means.values()), cov_matrix, n_samples)
    except np.linalg.LinAlgError:
        logger.warning("Covariance matrix not positive definite. Adjusting for stability.")
        # Simple adjustment: add small diagonal jitter
        cov_matrix += np.eye(len(keys)) * 1e-4
        data = np.random.multivariate_normal(list(means.values()), cov_matrix, n_samples)

    df = pd.DataFrame(data, columns=keys)

    # Clip values to realistic range (0-6 for Likert scale, though norms might be 1-5)
    # Assuming 0-6 range based on typical MFQ scoring
    df = df.clip(lower=0, upper=6)

    return df


def validate_against_norms(
    data: pd.DataFrame,
    norms: Optional[Dict[str, Any]] = None,
    tolerance: float = 1.0,
    alpha: float = 0.05
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate a dataset against psychometric norms.

    Checks if the sample means and standard deviations are within `tolerance`
    standard errors of the population norms. Also performs a Kolmogorov-Smirnov
    test for distribution shape.

    Args:
        data: DataFrame containing MFQ data to validate.
        norms: Norms dictionary. If None, loads defaults.
        tolerance: Number of standard errors allowed for deviation (default 1.0 SD).
        alpha: Significance level for KS test (default 0.05).

    Returns:
        Tuple of (is_valid, details_dict).
        details_dict contains stats for each dimension and overall KS p-values.
    """
    if norms is None:
        norms = load_norms_data()

    means = get_means(norms)
    std_devs = get_std_devs(norms)
    keys = list(means.keys())

    validation_results = {
        "means_valid": True,
        "std_devs_valid": True,
        "distribution_valid": True,
        "details": {}
    }

    n = len(data)
    if n == 0:
        return False, {"error": "Empty dataset"}

    all_means_pass = True
    all_stds_pass = True
    all_ks_pass = True

    for key in keys:
        if key not in data.columns:
            validation_results["details"][key] = {"error": "Missing column"}
            all_means_pass = False
            continue

        sample = data[key].dropna()
        if len(sample) == 0:
            validation_results["details"][key] = {"error": "No valid data"}
            all_means_pass = False
            continue

        sample_mean = sample.mean()
        sample_std = sample.std()
        pop_mean = means[key]
        pop_std = std_devs[key]

        # Standard Error of the Mean
        se = sample_std / np.sqrt(len(sample))

        # Check Mean
        mean_diff = abs(sample_mean - pop_mean)
        mean_pass = mean_diff <= (tolerance * se)
        if not mean_pass:
            all_means_pass = False

        # Check Std Dev (approximate test)
        # Using a simple heuristic: sample std should be within tolerance * (pop_std / sqrt(2n))
        # More robust would be chi-squared test, but keeping it simple for now
        std_diff = abs(sample_std - pop_std)
        std_se = pop_std / np.sqrt(2 * len(sample))
        std_pass = std_diff <= (tolerance * std_se)
        if not std_pass:
            all_stds_pass = False

        # KS Test
        # Compare sample distribution to normal distribution with population parameters
        ks_stat, ks_p = stats.kstest(sample, 'norm', args=(pop_mean, pop_std))
        ks_pass = ks_p > alpha

        if not ks_pass:
            all_ks_pass = False

        validation_results["details"][key] = {
            "sample_mean": float(sample_mean),
            "pop_mean": float(pop_mean),
            "mean_diff": float(mean_diff),
            "mean_pass": mean_pass,
            "sample_std": float(sample_std),
            "pop_std": float(pop_std),
            "std_pass": std_pass,
            "ks_statistic": float(ks_stat),
            "ks_p_value": float(ks_p),
            "ks_pass": ks_pass
        }

    validation_results["means_valid"] = all_means_pass
    validation_results["std_devs_valid"] = all_stds_pass
    validation_results["distribution_valid"] = all_ks_pass

    overall_valid = all_means_pass and all_stds_pass and all_ks_pass

    return overall_valid, validation_results


def run_validation_pipeline(data: pd.DataFrame, norms_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full validation pipeline: load norms, validate data, and report.

    Args:
        data: DataFrame of MFQ data.
        norms_path: Optional path to norms config.

    Returns:
        Dictionary with validation status and details.
    """
    norms = load_norms_data(norms_path)
    is_valid, details = validate_against_norms(data, norms)

    result = {
        "status": "PASS" if is_valid else "FAIL",
        "timestamp": str(pd.Timestamp.now()),
        "norms_source": norms_path or NORMS_CONFIG_PATH,
        "details": details
    }

    if is_valid:
        logger.info("Validation PASSED: Data matches psychometric norms.")
    else:
        logger.warning("Validation FAILED: Data deviates from psychometric norms.")
        for key, res in details.get("details", {}).items():
            if "error" not in res:
                if not res.get("mean_pass"):
                    logger.warning(f"  - Mean mismatch for {key}: {res['sample_mean']:.2f} vs {res['pop_mean']:.2f}")
                if not res.get("std_pass"):
                    logger.warning(f"  - Std Dev mismatch for {key}: {res['sample_std']:.2f} vs {res['pop_std']:.2f}")
                if not res.get("ks_pass"):
                    logger.warning(f"  - Distribution mismatch for {key}: p={res['ks_p_value']:.4f}")

    return result


def main():
    """
    Main entry point for testing the norms module.
    Generates synthetic data and validates it against norms.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Norms Module Validation...")

    # 1. Load Norms
    norms = load_norms_data()
    logger.info(f"Loaded norms: {list(norms.get('means', {}).keys())}")

    # 2. Generate Synthetic Data
    n_participants = 200
    logger.info(f"Generating {n_participants} synthetic participants...")
    synthetic_data = generate_synthetic_mfq_from_norms(n_participants, norms, seed=42)

    # 3. Validate
    logger.info("Validating generated data against norms...")
    is_valid, details = validate_against_norms(synthetic_data, norms, tolerance=2.0)

    logger.info(f"Validation Status: {'PASS' if is_valid else 'FAIL'}")

    # Save a sample of the generated data for other modules to use
    output_path = get_path("data/raw/synthetic_mfq_norms_sample.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    synthetic_data.to_csv(output_path, index=False)
    logger.info(f"Saved synthetic data sample to {output_path}")

    # Save validation report
    report = run_validation_pipeline(synthetic_data)
    report_path = get_path("data/logs/norms_validation_report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Saved validation report to {report_path}")

    return is_valid


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
