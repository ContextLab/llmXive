"""
Permutation Test Module for Statistical Significance Assessment.

This module implements block permutation tests to generate null distributions
for composition coefficients in the regression model, assessing statistical
significance while preserving temporal autocorrelation structure.
"""

import os
import sys
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import AnalysisError, get_logger, log_duration
from utils.io import load_parquet, save_parquet

logger = get_logger(__name__)


def load_regression_results(results_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load regression results from JSON file.

    Args:
        results_path: Path to regression results JSON file. If None, uses default path.

    Returns:
        Dictionary containing regression results.

    Raises:
        AnalysisError: If results file cannot be loaded or parsed.
    """
    if results_path is None:
        results_path = str(PROJECT_ROOT / "data" / "artifacts" / "regression_results.json")

    try:
        with open(results_path, 'r') as f:
            results = json.load(f)
        logger.info(f"Loaded regression results from {results_path}")
        return results
    except FileNotFoundError:
        raise AnalysisError(f"Regression results file not found: {results_path}")
    except json.JSONDecodeError as e:
        raise AnalysisError(f"Invalid JSON in regression results: {e}")


def get_coefficient_stats(results: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    Extract coefficient statistics from regression results.

    Args:
        results: Regression results dictionary.

    Returns:
        Dictionary mapping predictor names to their coefficient statistics
        (estimate, std_error, p_value).
    """
    coefficient_stats = {}

    for model_name, model_data in results.get("models", {}).items():
        for predictor, stats_data in model_data.get("coefficients", {}).items():
            if predictor not in coefficient_stats:
                coefficient_stats[predictor] = {
                    "estimate": stats_data["estimate"],
                    "std_error": stats_data["std_error"],
                    "p_value": stats_data["p_value"],
                    "model": model_name
                }

    return coefficient_stats


@log_duration(logger)
def generate_null_distribution(
    data: pd.DataFrame,
    target_column: str,
    predictor_columns: List[str],
    n_iterations: int = 1000,
    block_size: int = 24,
    random_state: Optional[int] = None
) -> Dict[str, np.ndarray]:
    """
    Generate null distribution for predictor coefficients using block permutation.

    This function shuffles the target variable in blocks to preserve temporal
    autocorrelation while breaking the relationship with predictors.

    Args:
        data: DataFrame containing the aligned time-series data.
        target_column: Name of the target variable (Dst or Kp).
        predictor_columns: List of predictor variable names.
        n_iterations: Number of permutation iterations.
        block_size: Size of blocks for permutation (in hours).
        random_state: Random seed for reproducibility.

    Returns:
        Dictionary mapping each predictor to its null distribution of coefficients.

    Raises:
        AnalysisError: If data validation fails or permutation process encounters errors.
    """
    if random_state is not None:
        np.random.seed(random_state)

    # Validate inputs
    if target_column not in data.columns:
        raise AnalysisError(f"Target column '{target_column}' not found in data")

    for col in predictor_columns:
        if col not in data.columns:
            raise AnalysisError(f"Predictor column '{col}' not found in data")

    # Remove rows with missing values in target or predictors
    clean_data = data.dropna(subset=[target_column] + predictor_columns)

    if len(clean_data) < block_size * 2:
        raise AnalysisError(
            f"Insufficient data for block permutation: "
            f"need at least {block_size * 2} rows, got {len(clean_data)}"
        )

    n_samples = len(clean_data)
    n_blocks = n_samples // block_size
    remaining = n_samples % block_size

    # Create block indices
    block_indices = []
    for i in range(n_blocks):
        start_idx = i * block_size
        end_idx = start_idx + block_size
        block_indices.append(np.arange(start_idx, end_idx))

    # Handle remaining samples by distributing them across blocks
    if remaining > 0:
        for i in range(remaining):
            block_idx = i % n_blocks
            last_idx = block_indices[block_idx][-1] + 1
            if last_idx < n_samples:
                block_indices[block_idx] = np.append(block_indices[block_idx], last_idx)

    # Initialize null distributions
    null_distributions = {col: [] for col in predictor_columns}

    logger.info(f"Starting block permutation test with {n_iterations} iterations")
    logger.info(f"Block size: {block_size} hours, Number of blocks: {len(block_indices)}")

    for iteration in range(n_iterations):
        if (iteration + 1) % 100 == 0:
            logger.info(f"Permutation iteration {iteration + 1}/{n_iterations}")

        # Shuffle block indices
        shuffled_block_order = np.random.permutation(len(block_indices))

        # Create shuffled index array
        shuffled_indices = []
        for block_idx in shuffled_block_order:
            shuffled_indices.extend(block_indices[block_idx])

        # Ensure we have exactly n_samples indices
        shuffled_indices = shuffled_indices[:n_samples]

        # Shuffle target variable
        shuffled_target = clean_data[target_column].values[shuffled_indices]

        # Fit regression model with shuffled target
        X = clean_data[predictor_columns].values
        y = shuffled_target

        # Check for multicollinearity issues
        try:
            # Use numpy's lstsq for coefficient estimation
            # Add intercept term
            X_with_intercept = np.column_stack([np.ones(len(X)), X])
            coefficients, residuals, rank, s = np.linalg.lstsq(X_with_intercept, y, rcond=None)

            # Extract coefficients for predictors (excluding intercept)
            for i, col in enumerate(predictor_columns):
                null_distributions[col].append(coefficients[i + 1])

        except np.linalg.LinAlgError as e:
            logger.warning(f"Linear algebra error at iteration {iteration}: {e}")
            # Skip this iteration if matrix is singular
            continue

    # Convert lists to numpy arrays
    result = {col: np.array(dist) for col, dist in null_distributions.items()}

    logger.info(f"Generated null distributions for {len(predictor_columns)} predictors")

    return result


@log_duration(logger)
def run_permutation_tests(
    data: pd.DataFrame,
    target_column: str,
    predictor_columns: List[str],
    n_iterations: int = 1000,
    block_size: int = 24,
    random_state: Optional[int] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run full permutation test analysis for all predictors.

    This function:
    1. Generates null distributions via block permutation
    2. Calculates observed coefficients from original data
    3. Computes p-values by comparing observed vs null distributions
    4. Calculates confidence intervals for null distributions

    Args:
        data: DataFrame containing the aligned time-series data.
        target_column: Name of the target variable (Dst or Kp).
        predictor_columns: List of predictor variable names.
        n_iterations: Number of permutation iterations (minimum 1000).
        block_size: Size of blocks for permutation (in hours).
        random_state: Random seed for reproducibility.
        output_path: Path to save results JSON file.

    Returns:
        Dictionary containing permutation test results including:
        - observed_coefficients: Original regression coefficients
        - null_distributions: Generated null distributions
        - p_values: Two-tailed p-values for each predictor
        - confidence_intervals: 95% confidence intervals for null distributions
        - significance: Boolean flags for statistical significance (alpha=0.05)

    Raises:
        AnalysisError: If permutation test fails or results cannot be computed.
    """
    if n_iterations < 1000:
        logger.warning(f"n_iterations ({n_iterations}) is below recommended minimum of 1000")

    # Generate null distribution
    try:
        null_distributions = generate_null_distribution(
            data=data,
            target_column=target_column,
            predictor_columns=predictor_columns,
            n_iterations=n_iterations,
            block_size=block_size,
            random_state=random_state
        )
    except Exception as e:
        raise AnalysisError(f"Failed to generate null distribution: {e}")

    # Calculate observed coefficients
    clean_data = data.dropna(subset=[target_column] + predictor_columns)
    X = clean_data[predictor_columns].values
    y = clean_data[target_column].values

    try:
        X_with_intercept = np.column_stack([np.ones(len(X)), X])
        coefficients, residuals, rank, s = np.linalg.lstsq(X_with_intercept, y, rcond=None)
        observed_coefficients = {col: coefficients[i + 1] for i, col in enumerate(predictor_columns)}
    except np.linalg.LinAlgError as e:
        raise AnalysisError(f"Failed to compute observed coefficients: {e}")

    # Calculate p-values and confidence intervals
    results = {
        "target": target_column,
        "n_iterations": n_iterations,
        "block_size": block_size,
        "observed_coefficients": observed_coefficients,
        "null_distributions": {},
        "p_values": {},
        "confidence_intervals": {},
        "significance": {}
    }

    alpha = 0.05

    for predictor, null_dist in null_distributions.items():
        observed_coef = observed_coefficients[predictor]

        # Calculate two-tailed p-value
        # Count how many null coefficients are as extreme or more extreme than observed
        positive_extreme = np.sum(null_dist >= abs(observed_coef))
        negative_extreme = np.sum(null_dist <= -abs(observed_coef))
        total_extreme = positive_extreme + negative_extreme

        p_value = total_extreme / len(null_dist)

        # Calculate 95% confidence interval (2.5th to 97.5th percentile)
        ci_lower = np.percentile(null_dist, 2.5)
        ci_upper = np.percentile(null_dist, 97.5)

        # Determine significance
        is_significant = p_value < alpha

        results["null_distributions"][predictor] = {
            "mean": float(np.mean(null_dist)),
            "std": float(np.std(null_dist)),
            "min": float(np.min(null_dist)),
            "max": float(np.max(null_dist)),
            "samples": len(null_dist)
        }

        results["p_values"][predictor] = float(p_value)
        results["confidence_intervals"][predictor] = {
            "lower": float(ci_lower),
            "upper": float(ci_upper)
        }
        results["significance"][predictor] = is_significant

        logger.info(
            f"Predictor {predictor}: "
            f"observed_coef={observed_coef:.4f}, "
            f"p_value={p_value:.4f}, "
            f"significant={is_significant}"
        )

    # Save results if output path provided
    if output_path:
        try:
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            # Convert numpy arrays to lists for JSON serialization
            serializable_results = {
                k: v if not isinstance(v, dict) else {
                    kk: (vv.tolist() if isinstance(vv, np.ndarray) else vv)
                    for kk, vv in v.items()
                } if isinstance(v, dict) else v
                for k, v in results.items()
            }

            with open(output_path, 'w') as f:
                json.dump(serializable_results, f, indent=2)

            logger.info(f"Permutation test results saved to {output_path}")
        except Exception as e:
            logger.warning(f"Failed to save results: {e}")

    return results


def main():
    """
    Main entry point for permutation test execution.

    Reads configuration, loads data, runs permutation tests, and saves results.
    """
    try:
        # Load configuration
        config_path = PROJECT_ROOT / "code" / "config.py"
        if config_path.exists():
            from config import get_config
            config = get_config()
        else:
            config = {
                "data_path": str(PROJECT_ROOT / "data" / "processed" / "aligned_data.parquet"),
                "output_path": str(PROJECT_ROOT / "data" / "artifacts" / "permutation_results.json"),
                "n_iterations": 1000,
                "block_size": 24,
                "random_state": 42,
                "target_columns": ["Dst", "Kp"],
                "composition_predictors": ["O_Fe", "He_H", "C_O"]
            }

        # Load aligned data
        data_path = config.get("data_path", str(PROJECT_ROOT / "data" / "processed" / "aligned_data.parquet"))

        if not os.path.exists(data_path):
            raise AnalysisError(f"Aligned data file not found: {data_path}")

        logger.info(f"Loading data from {data_path}")
        data = load_parquet(data_path)

        # Run permutation tests for each target variable
        all_results = {}

        target_columns = config.get("target_columns", ["Dst", "Kp"])
        composition_predictors = config.get("composition_predictors", ["O_Fe", "He_H", "C_O"])

        for target in target_columns:
            if target not in data.columns:
                logger.warning(f"Target column '{target}' not found in data, skipping")
                continue

            logger.info(f"Running permutation test for target: {target}")

            results = run_permutation_tests(
                data=data,
                target_column=target,
                predictor_columns=composition_predictors,
                n_iterations=config.get("n_iterations", 1000),
                block_size=config.get("block_size", 24),
                random_state=config.get("random_state", 42),
                output_path=None  # Save all results at the end
            )

            all_results[target] = results

        # Save combined results
        output_path = config.get("output_path", str(PROJECT_ROOT / "data" / "artifacts" / "permutation_results.json"))

        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(all_results, f, indent=2)

        logger.info(f"All permutation test results saved to {output_path}")

        # Print summary
        print("\n" + "="*60)
        print("PERMUTATION TEST SUMMARY")
        print("="*60)

        for target, results in all_results.items():
            print(f"\nTarget: {target}")
            print("-" * 40)
            for predictor, p_value in results["p_values"].items():
                significance = "YES" if results["significance"][predictor] else "NO"
                print(f"  {predictor}: p={p_value:.4f} (significant={significance})")

        print("\n" + "="*60)

    except Exception as e:
        logger.error(f"Permutation test execution failed: {e}")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()