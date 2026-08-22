"""
Permutation test implementation for statistical significance of the association
between cognitive flexibility and RSFC variability.

This module implements a permutation test with 10,000 iterations to generate
a stable null distribution as required by SC-003.
"""
import os
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from scipy import stats

from code.config import get_config, set_seed
from code.data.paths import get_results_path, get_processed_path, ensure_dir
from code.utils.logging import init_logging, log_error, log_warning

# Configure logger
logger = logging.getLogger(__name__)

def calculate_test_statistic(
    variability: np.ndarray,
    flexibility: np.ndarray,
    covariates: Optional[pd.DataFrame] = None
) -> float:
    """
    Calculate the test statistic (t-statistic from linear regression) for the
    association between variability and flexibility.

    Args:
        variability: Array of variability metrics (predictor)
        flexibility: Array of flexibility scores (outcome)
        covariates: Optional DataFrame of covariates (age, sex, FD, scan_time)

    Returns:
        float: The t-statistic for the variability coefficient
    """
    # Build design matrix
    X = np.column_stack([variability])
    if covariates is not None and not covariates.empty:
        # Convert categorical variables to numeric if needed
        numeric_covariates = covariates.copy()
        if 'Sex' in numeric_covariates.columns:
            # Encode Sex: M=0, F=1 (or similar consistent mapping)
            numeric_covariates['Sex'] = numeric_covariates['Sex'].map({'M': 0, 'F': 1, 'Male': 0, 'Female': 1})
        
        for col in numeric_covariates.columns:
            if col not in ['Subject_ID']:
                try:
                    X = np.column_stack([X, numeric_covariates[col].values])
                except (ValueError, TypeError):
                    logger.warning(f"Skipping non-numeric covariate: {col}")

    # Add intercept
    X = np.column_stack([np.ones(X.shape[0]), X])
    y = flexibility

    # Check for sufficient data
    if X.shape[0] < X.shape[1] + 1:
        raise ValueError("Insufficient data points for regression with covariates")

    # Fit linear regression: y = X @ beta + epsilon
    try:
        # Use least squares
        beta, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
        
        # Calculate residuals and standard error
        y_pred = X @ beta
        residuals = y - y_pred
        
        # Degrees of freedom
        n = len(y)
        p = X.shape[1]  # Including intercept
        dof = n - p
        
        if dof <= 0:
            raise ValueError("Degrees of freedom <= 0")
        
        # Mean squared error
        mse = np.sum(residuals**2) / dof
        
        # Covariance matrix of coefficients: sigma^2 * (X'X)^-1
        try:
            XtX_inv = np.linalg.inv(X.T @ X)
        except np.linalg.LinAlgError:
            logger.warning("X'X is singular, using pseudo-inverse")
            XtX_inv = np.linalg.pinv(X.T @ X)
        
        # Standard error of the variability coefficient (first predictor, index 1)
        se_beta = np.sqrt(mse * XtX_inv[1, 1])
        
        if se_beta == 0:
            logger.warning("Standard error is zero, returning large t-stat")
            return np.inf if beta[1] > 0 else -np.inf
        
        # T-statistic for the variability coefficient
        t_stat = beta[1] / se_beta
        
        return t_stat
        
    except Exception as e:
        logger.error(f"Error calculating test statistic: {e}")
        raise

def run_permutation_test(
    df: pd.DataFrame,
    variability_col: str = "Variability_Metric",
    flexibility_col: str = "Flexibility_Score",
    n_permutations: int = 10000,
    covariate_cols: Optional[List[str]] = None,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run a permutation test to assess the significance of the association
    between variability and flexibility.

    Args:
        df: DataFrame containing variability, flexibility, and covariates
        variability_col: Column name for variability metric
        flexibility_col: Column name for flexibility score
        n_permutations: Number of permutation iterations (default: 10000)
        covariate_cols: List of covariate column names to control for
        seed: Random seed for reproducibility

    Returns:
        Dict containing:
            - observed_stat: The observed test statistic
            - p_value: Two-tailed p-value from permutation test
            - null_distribution: Array of permuted test statistics
            - n_permutations: Number of permutations run
    """
    set_seed(seed)
    
    # Extract data
    variability = df[variability_col].values
    flexibility = df[flexibility_col].values
    
    # Prepare covariates
    covariates = None
    if covariate_cols:
        available_covariates = [col for col in covariate_cols if col in df.columns]
        if available_covariates:
            covariates = df[available_covariates].copy()
            if covariates.empty:
                covariates = None
    
    logger.info(f"Running permutation test with {n_permutations} iterations")
    logger.info(f"Sample size: {len(df)}")
    if covariates is not None:
        logger.info(f"Covariates: {list(covariates.columns)}")
    
    # Calculate observed test statistic
    try:
        observed_stat = calculate_test_statistic(variability, flexibility, covariates)
    except Exception as e:
        logger.error(f"Failed to calculate observed statistic: {e}")
        raise
    
    logger.info(f"Observed test statistic: {observed_stat:.4f}")
    
    # Initialize null distribution
    null_distribution = np.zeros(n_permutations)
    
    # Run permutations
    logger.info("Starting permutation loop...")
    for i in range(n_permutations):
        # Permute the outcome (flexibility) while keeping predictors fixed
        # This tests the null hypothesis that there is no association
        permuted_flexibility = np.random.permutation(flexibility)
        
        try:
            perm_stat = calculate_test_statistic(variability, permuted_flexibility, covariates)
            null_distribution[i] = perm_stat
        except Exception as e:
            logger.warning(f"Permutation {i} failed: {e}. Skipping.")
            null_distribution[i] = np.nan
    
    # Remove NaN values from null distribution
    valid_null = null_distribution[~np.isnan(null_distribution)]
    
    if len(valid_null) == 0:
        raise RuntimeError("All permutations failed. Cannot compute p-value.")
    
    # Calculate two-tailed p-value
    # p = proportion of null statistics with absolute value >= |observed|
    abs_observed = np.abs(observed_stat)
    abs_null = np.abs(valid_null)
    
    # Count how many null statistics are as extreme or more extreme than observed
    extreme_count = np.sum(abs_null >= abs_observed)
    p_value = (extreme_count + 1) / (len(valid_null) + 1)  # Add 1 for observed statistic
    
    logger.info(f"Permutation test complete. P-value: {p_value:.6f}")
    logger.info(f"Null distribution mean: {np.mean(valid_null):.4f}, std: {np.std(valid_null):.4f}")
    
    return {
        "observed_stat": float(observed_stat),
        "p_value": float(p_value),
        "null_distribution": valid_null,
        "n_permutations": len(valid_null),
        "extreme_count": int(extreme_count),
        "total_permutations": n_permutations
    }

def run_permutation_pipeline(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    n_permutations: int = 10000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run the full permutation test pipeline:
    1. Load the processed results data
    2. Run the permutation test
    3. Save results to JSON

    Args:
        input_path: Path to final_results.csv (if None, uses default path)
        output_path: Path to save results JSON (if None, uses default path)
        n_permutations: Number of permutation iterations
        seed: Random seed

    Returns:
        Dict containing permutation test results
    """
    # Initialize logging
    init_logging()
    
    # Set default paths
    if input_path is None:
        input_path = os.path.join(get_processed_path(), "final_results.csv")
    
    if output_path is None:
        output_path = os.path.join(get_results_path(), "permutation_results.json")
    
    ensure_dir(output_path)
    
    logger.info(f"Loading data from: {input_path}")
    
    # Load data
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading input file: {e}")
        raise
    
    # Validate required columns
    required_cols = ["Variability_Metric", "Flexibility_Score"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Drop rows with missing values in key columns
    initial_count = len(df)
    df = df.dropna(subset=required_cols)
    if len(df) < initial_count:
        logger.warning(f"Dropped {initial_count - len(df)} rows with missing values")
    
    if len(df) < 10:
        raise ValueError(f"Insufficient data after dropping missing values: {len(df)} subjects")
    
    # Define covariates
    possible_covariates = ["Age", "Sex", "Mean_FD", "Total_Scan_Time"]
    available_covariates = [col for col in possible_covariates if col in df.columns]
    
    logger.info(f"Running permutation test on {len(df)} subjects")
    logger.info(f"Covariates used: {available_covariates}")
    
    # Run permutation test
    results = run_permutation_test(
        df=df,
        variability_col="Variability_Metric",
        flexibility_col="Flexibility_Score",
        n_permutations=n_permutations,
        covariate_cols=available_covariates if available_covariates else None,
        seed=seed
    )
    
    # Prepare output (exclude large null distribution from JSON for size)
    output_results = {
        "observed_statistic": results["observed_stat"],
        "p_value": results["p_value"],
        "n_permutations_run": results["n_permutations"],
        "n_permutations_requested": results["total_permutations"],
        "extreme_count": results["extreme_count"],
        "covariates_used": available_covariates,
        "seed": seed,
        "sample_size": len(df)
    }
    
    # Save results to JSON
    try:
        with open(output_path, 'w') as f:
            import json
            json.dump(output_results, f, indent=2)
        logger.info(f"Results saved to: {output_path}")
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        raise
    
    # Optionally save null distribution as CSV for further analysis
    null_csv_path = output_path.replace('.json', '_null_distribution.csv')
    try:
        pd.DataFrame({"null_statistic": results["null_distribution"]}).to_csv(
            null_csv_path, index=False
        )
        logger.info(f"Null distribution saved to: {null_csv_path}")
    except Exception as e:
        logger.warning(f"Could not save null distribution CSV: {e}")
    
    return output_results

def main():
    """Main entry point for running the permutation test from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run permutation test for RSFC variability vs flexibility")
    parser.add_argument("--input", type=str, default=None, help="Path to input CSV (default: data/processed/final_results.csv)")
    parser.add_argument("--output", type=str, default=None, help="Path to output JSON (default: data/results/permutation_results.json)")
    parser.add_argument("--n-permutations", type=int, default=10000, help="Number of permutations (default: 10000)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    
    args = parser.parse_args()
    
    try:
        results = run_permutation_pipeline(
            input_path=args.input,
            output_path=args.output,
            n_permutations=args.n_permutations,
            seed=args.seed
        )
        
        print(f"\nPermutation Test Results:")
        print(f"  Observed Statistic: {results['observed_statistic']:.4f}")
        print(f"  P-value: {results['p_value']:.6f}")
        print(f"  Permutations Run: {results['n_permutations_run']}")
        print(f"  Sample Size: {results['sample_size']}")
        
        if results['p_value'] < 0.05:
            print(f"  Significance: YES (p < 0.05)")
        else:
            print(f"  Significance: NO (p >= 0.05)")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()