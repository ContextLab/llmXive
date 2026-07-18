"""
code/utils/norms.py

Module for loading, managing, and validating against psychometric norms
(specifically Gervais et al. Moral Foundations Questionnaire norms).

Provides utilities to:
1. Load standard norm data from YAML/JSON configuration.
2. Calculate statistical moments (mean, std, covariance).
3. Generate synthetic data that matches these norms (for simulation).
4. **Validate** that a dataset (e.g., from simulation) falls within acceptable
   statistical bounds (e.g., within 1 SD of the published mean).
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from scipy import stats

# Project root for relative imports if needed, though we assume standard path structure
ROOT_DIR = Path(__file__).parent.parent.parent
CONFIG_DIR = ROOT_DIR / "data" / "config"
LOG_DIR = ROOT_DIR / "data" / "logs"

# Ensure directories exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

def load_norms_data(norms_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the Gervais et al. psychometric norms from a YAML/JSON file.

    Args:
        norms_file: Path to the norms file. Defaults to data/config/gervais_norms.yaml.

    Returns:
        Dictionary containing means, stds, and optionally covariance/correlation matrices.

    Raises:
        FileNotFoundError: If the norms file does not exist.
    """
    if norms_file is None:
        norms_file = CONFIG_DIR / "gervais_norms.yaml"

    if not norms_file.exists():
        logger.error(f"Norms file not found at {norms_file}")
        raise FileNotFoundError(f"Norms file not found: {norms_file}")

    logger.info(f"Loading norms from {norms_file}")
    with open(norms_file, 'r') as f:
        # Simple YAML-like parsing if pyyaml is not strictly enforced, 
        # but assuming standard library + requests + yaml in requirements
        try:
            import yaml
            data = yaml.safe_load(f)
        except ImportError:
            # Fallback to JSON if YAML library missing, though spec implies yaml
            f.seek(0)
            data = json.load(f)
    
    return data

def save_norms_data(data: Dict[str, Any], norms_file: Optional[Path] = None) -> None:
    """
    Save norm data to a file.
    """
    if norms_file is None:
        norms_file = CONFIG_DIR / "gervais_norms.yaml"
    
    with open(norms_file, 'w') as f:
        import yaml
        yaml.dump(data, f)

def get_means(norms_data: Dict[str, Any]) -> np.ndarray:
    """
    Extract the vector of means from the norms data.
    Expected keys: 'means' (dict or list)
    """
    means = norms_data.get('means', {})
    if isinstance(means, dict):
        return np.array(list(means.values()))
    return np.array(means)

def get_std_devs(norms_data: Dict[str, Any]) -> np.ndarray:
    """
    Extract the vector of standard deviations from the norms data.
    Expected keys: 'stds' or 'std_devs'
    """
    stds = norms_data.get('stds', norms_data.get('std_devs', {}))
    if isinstance(stds, dict):
        return np.array(list(stds.values()))
    return np.array(stds)

def get_correlation_matrix(norms_data: Dict[str, Any]) -> np.ndarray:
    """
    Extract the correlation matrix from norms data.
    """
    corr = norms_data.get('correlation_matrix', norms_data.get('corr', None))
    if corr is None:
        # Default to identity if not provided
        n = len(get_means(norms_data))
        return np.eye(n)
    return np.array(corr)

def get_covariance_matrix(norms_data: Dict[str, Any]) -> np.ndarray:
    """
    Compute the covariance matrix from std devs and correlation matrix.
    Cov = diag(std) * Corr * diag(std)
    """
    stds = get_std_devs(norms_data)
    corr = get_correlation_matrix(norms_data)
    D = np.diag(stds)
    return D @ corr @ D

def generate_synthetic_mfq_from_norms(
    norms_data: Dict[str, Any], 
    n_samples: int, 
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate synthetic MFQ data that follows the multivariate normal distribution
    defined by the provided norms.
    """
    if seed is not None:
        np.random.seed(seed)

    means = get_means(norms_data)
    cov = get_covariance_matrix(norms_data)
    
    # Generate multivariate normal data
    data = np.random.multivariate_normal(means, cov, size=n_samples)
    
    # Create DataFrame with appropriate column names if available
    columns = list(norms_data.get('means', {}).keys())
    if not columns:
        columns = [f"mfq_{i}" for i in range(len(means))]
    
    return pd.DataFrame(data, columns=columns)

def validate_against_norms(
    df: pd.DataFrame, 
    norms_data: Dict[str, Any], 
    tolerance_sd: float = 1.0,
    alpha: float = 0.05
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that the input DataFrame's distribution matches the published norms.
    
    This function performs two checks:
    1. **Mean Check**: For each dimension, checks if the sample mean is within 
       `tolerance_sd` standard deviations of the population mean.
    2. **Distribution Check (Optional)**: Performs a Kolmogorov-Smirnov test 
       against a theoretical normal distribution defined by the norms.

    Args:
        df: DataFrame containing the synthetic or real data to validate.
        norms_data: Dictionary containing the reference norms (means, stds).
        tolerance_sd: Number of standard deviations allowed for the mean check.
        alpha: Significance level for KS test (if performed).

    Returns:
        Tuple of (is_valid, details_dict)
        - is_valid: True if all checks pass.
        - details_dict: Contains per-dimension statistics and pass/fail status.
    """
    means = get_means(norms_data)
    stds = get_std_devs(norms_data)
    
    # Ensure columns match
    if df.shape[1] != len(means):
        raise ValueError(f"DataFrame columns ({df.shape[1]}) do not match norms dimensions ({len(means)})")
    
    column_names = list(df.columns)
    
    results = {
        "mean_checks": [],
        "ks_tests": [],
        "overall_pass": True
    }

    all_passed = True

    for i, col in enumerate(column_names):
        sample_mean = df[col].mean()
        sample_std = df[col].std()
        pop_mean = means[i]
        pop_std = stds[i]

        # Check 1: Mean within tolerance
        # Z-score of the sample mean relative to population mean
        # We check if |sample_mean - pop_mean| <= tolerance_sd * pop_std
        diff = abs(sample_mean - pop_mean)
        allowed_diff = tolerance_sd * pop_std
        mean_pass = diff <= allowed_diff
        
        mean_result = {
            "column": col,
            "sample_mean": float(sample_mean),
            "pop_mean": float(pop_mean),
            "diff": float(diff),
            "allowed_diff": float(allowed_diff),
            "pass": mean_pass
        }
        results["mean_checks"].append(mean_result)

        if not mean_pass:
            all_passed = False
            logger.warning(f"Mean check failed for {col}: diff={diff:.4f} > allowed={allowed_diff:.4f}")

        # Check 2: Distribution shape (KS Test)
        # We compare the sample distribution to a Normal(pop_mean, pop_std)
        try:
            ks_stat, p_value = stats.kstest(df[col].dropna(), 'norm', args=(pop_mean, pop_std))
            ks_pass = p_value > alpha
            ks_result = {
                "column": col,
                "ks_statistic": float(ks_stat),
                "p_value": float(p_value),
                "pass": ks_pass
            }
            results["ks_tests"].append(ks_result)
            
            if not ks_pass:
                # Note: KS test can be sensitive to large N. We might warn but not fail hard
                # depending on strictness. Here we log but rely on mean check for hard fail.
                logger.info(f"KS test p-value for {col} is {p_value:.4f} (alpha={alpha})")
        except Exception as e:
            logger.warning(f"Could not perform KS test for {col}: {e}")
            results["ks_tests"].append({"column": col, "error": str(e)})

    results["overall_pass"] = all_passed
    return all_passed, results

def run_validation_pipeline(
    synthetic_data_path: Path, 
    norms_file: Optional[Path] = None,
    output_log: Optional[Path] = None
) -> bool:
    """
    Main entry point to validate a generated dataset against norms.
    
    Reads the synthetic data from disk, loads norms, runs validation,
    and logs the results.
    """
    if not synthetic_data_path.exists():
        raise FileNotFoundError(f"Synthetic data file not found: {synthetic_data_path}")
    
    logger.info(f"Starting validation pipeline for {synthetic_data_path}")
    
    # Load data
    df = pd.read_csv(synthetic_data_path)
    
    # Load norms
    norms_data = load_norms_data(norms_file)
    
    # Run validation
    is_valid, details = validate_against_norms(df, norms_data)
    
    # Log results
    if output_log is None:
        output_log = LOG_DIR / "norm_validation_report.json"
    
    report = {
        "source_file": str(synthetic_data_path),
        "norms_file": str(norms_file) if norms_file else "default",
        "validation_passed": is_valid,
        "details": details,
        "timestamp": str(pd.Timestamp.now())
    }
    
    with open(output_log, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation {'PASSED' if is_valid else 'FAILED'}. Report saved to {output_log}")
    
    return is_valid

def main():
    """
    CLI entry point for validation.
    Usage: python -m code.utils.norms --data data/processed/synthetic_mfq.csv
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate synthetic MFQ data against norms.")
    parser.add_argument("--data", type=str, required=True, help="Path to synthetic data CSV")
    parser.add_argument("--norms", type=str, default=None, help="Path to norms YAML (optional)")
    parser.add_argument("--output", type=str, default=None, help="Path to output report JSON (optional)")
    
    args = parser.parse_args()
    
    data_path = Path(args.data)
    norms_path = Path(args.norms) if args.norms else None
    output_path = Path(args.output) if args.output else None
    
    success = run_validation_pipeline(data_path, norms_path, output_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()