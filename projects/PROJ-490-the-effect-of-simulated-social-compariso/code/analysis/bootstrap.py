import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd

from data.config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)

def run_single_bootstrap_iteration(
    data: pd.DataFrame,
    outcome_col: str,
    covariate_col: str,
    predictor_col: str,
    interaction_col: str,
    rng: np.random.Generator
) -> Tuple[float, float]:
    """
    Run a single bootstrap iteration:
    1. Resample rows with replacement.
    2. Fit a linear model (OLS) to estimate coefficients.
    3. Return the interaction coefficient and its standard error.
    
    Returns:
        Tuple (interaction_coef, interaction_se)
    """
    import statsmodels.api as sm
    
    # Resample
    sample_indices = rng.choice(len(data), size=len(data), replace=True)
    boot_data = data.iloc[sample_indices].reset_index(drop=True)
    
    # Prepare features
    # We need: covariate, predictor, interaction
    X = boot_data[[covariate_col, predictor_col, interaction_col]].values
    y = boot_data[outcome_col].values
    
    # Add constant
    X = sm.add_constant(X)
    
    # Fit OLS
    model = sm.OLS(y, X)
    results = model.fit()
    
    # Extract interaction coefficient (index 3) and its SE
    # Assuming order: const, covariate, predictor, interaction
    interaction_coef = results.params[3]
    interaction_se = results.bse[3]
    
    return interaction_coef, interaction_se

def calculate_confidence_intervals(
    coefficients: List[float],
    ci_level: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate confidence intervals from a list of bootstrap coefficients.
    
    Args:
        coefficients: List of bootstrap coefficients.
        ci_level: Confidence level (e.g., 0.95).
        
    Returns:
        Tuple (lower_ci, upper_ci)
    """
    alpha = 1 - ci_level
    lower = np.percentile(coefficients, (alpha / 2) * 100)
    upper = np.percentile(coefficients, (1 - alpha / 2) * 100)
    return lower, upper

def calculate_ci_width_variance(
    coefficients: List[float],
    ci_level: float = 0.95,
    n_iterations: int = 1000,
    seed: Optional[int] = None,
    data: Optional[pd.DataFrame] = None,
    outcome_col: str = "post_self_esteem",
    covariate_col: str = "pre_self_esteem",
    predictor_col: str = "avatar_condition",
    interaction_col: str = "interaction_term"
) -> Dict[str, Any]:
    """
    Calculate the variance of CI widths from bootstrap results.
    
    This function performs bootstrap resampling to generate multiple sets of 
    confidence intervals, then calculates the variance of the CI widths.
    
    Args:
        coefficients: Pre-computed coefficients (if available). If None, 
                    bootstrap will be run.
        ci_level: Confidence level (e.g., 0.95).
        n_iterations: Number of bootstrap iterations.
        seed: Random seed for reproducibility.
        data: DataFrame containing the data. Required if coefficients is None.
        outcome_col: Name of the outcome variable.
        covariate_col: Name of the covariate variable.
        predictor_col: Name of the predictor variable.
        interaction_col: Name of the interaction variable.
        
    Returns:
        Dict containing:
            - ci_width_variance: Variance of CI widths
            - mean_ci_width: Mean CI width
            - ci_lower: Lower bound of CI
            - ci_upper: Upper bound of CI
            - n_iterations: Number of iterations performed
            - flagged: True if variance >= 0.01 (SC-004)
    """
    if seed is None:
        seed = get_config().seed
        
    rng = np.random.default_rng(seed)
    
    if coefficients is None:
        if data is None:
            raise ValueError("Either coefficients or data must be provided")
        
        logger.info(f"Running {n_iterations} bootstrap iterations...")
        interaction_coefs = []
        
        for i in range(n_iterations):
            coef, se = run_single_bootstrap_iteration(
                data, outcome_col, covariate_col, predictor_col, interaction_col, rng
            )
            interaction_coefs.append(coef)
            if (i + 1) % 100 == 0:
                logger.info(f"Completed {i + 1}/{n_iterations} iterations")
        
        coefficients = interaction_coefs
    
    # Calculate CI widths for multiple resamples to get variance
    # We'll do a second-level bootstrap on the CI widths
    ci_widths = []
    n_subsamples = min(100, n_iterations)  # Use a subset for variance estimation
    
    for _ in range(n_subsamples):
        # Resample coefficients
        sample_coefs = rng.choice(coefficients, size=len(coefficients), replace=True)
        lower, upper = calculate_confidence_intervals(sample_coefs, ci_level)
        width = upper - lower
        ci_widths.append(width)
    
    ci_width_variance = np.var(ci_widths)
    mean_ci_width = np.mean(ci_widths)
    
    # Final CI calculation
    final_lower, final_upper = calculate_confidence_intervals(coefficients, ci_level)
    
    flagged = ci_width_variance >= 0.01
    
    result = {
        "ci_width_variance": float(ci_width_variance),
        "mean_ci_width": float(mean_ci_width),
        "ci_lower": float(final_lower),
        "ci_upper": float(final_upper),
        "n_iterations": n_iterations,
        "flagged": flagged,
        "threshold": 0.01
    }
    
    if flagged:
        logger.warning(f"CI width variance ({ci_width_variance:.4f}) >= 0.01. Stability concern (SC-004).")
    else:
        logger.info(f"CI width variance ({ci_width_variance:.4f}) < 0.01. Stability confirmed.")
        
    return result

def run_bootstrap_stability(
    data: pd.DataFrame,
    outcome_col: str = "post_self_esteem",
    covariate_col: str = "pre_self_esteem",
    predictor_col: str = "avatar_condition",
    interaction_col: str = "interaction_term",
    n_iterations: int = 1000,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run full bootstrap stability analysis including CI width variance.
    
    Args:
        data: Input DataFrame.
        outcome_col: Outcome variable name.
        covariate_col: Covariate variable name.
        predictor_col: Predictor variable name.
        interaction_col: Interaction variable name.
        n_iterations: Number of bootstrap iterations.
        seed: Random seed.
        
    Returns:
        Dict with stability analysis results.
    """
    config = get_config()
    if seed is None:
        seed = config.seed
        
    logger.info(f"Starting bootstrap stability analysis with {n_iterations} iterations")
    
    # Calculate CI width variance
    stability_results = calculate_ci_width_variance(
        coefficients=None,
        ci_level=0.95,
        n_iterations=n_iterations,
        seed=seed,
        data=data,
        outcome_col=outcome_col,
        covariate_col=covariate_col,
        predictor_col=predictor_col,
        interaction_col=interaction_col
    )
    
    return stability_results

def run_bootstrap_analysis(
    data_path: str,
    n_iterations: int = 1000,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Main entry point for bootstrap analysis.
    
    Args:
        data_path: Path to the processed data CSV.
        n_iterations: Number of bootstrap iterations.
        seed: Random seed.
        
    Returns:
        Dict with analysis results.
    """
    logger.info(f"Loading data from {data_path}")
    data = pd.read_csv(data_path)
    
    # Ensure required columns exist
    required_cols = ["post_self_esteem", "pre_self_esteem", "avatar_condition", "interaction_term"]
    missing = [col for col in required_cols if col not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    results = run_bootstrap_stability(
        data=data,
        n_iterations=n_iterations,
        seed=seed
    )
    
    return results

def main():
    """
    Command-line entry point for bootstrap analysis.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Bootstrap stability analysis")
    parser.add_argument("--data", type=str, required=True, help="Path to processed data CSV")
    parser.add_argument("--iterations", type=int, default=1000, help="Number of bootstrap iterations")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--output", type=str, default="data/processed/bootstrap_results.json", 
                      help="Output path for results")
    
    args = parser.parse_args()
    
    results = run_bootstrap_analysis(
        data_path=args.data,
        n_iterations=args.iterations,
        seed=args.seed
    )
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    print(json.dumps(results, indent=2))
    
    return results

if __name__ == "__main__":
    main()
