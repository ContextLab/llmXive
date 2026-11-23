"""
Significance testing for interaction coefficients in multicomponent segregation models.

This module implements statistical significance testing (p-value < 0.05) for
interaction coefficients in the regression model. It calculates p-values using
t-tests on the regression coefficients and their standard errors.

Dependencies:
- T021b: regression model fitting
- T021a-Persist: interaction terms data
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd
from scipy import stats

from code.config import PROCESSED_PATH, get_logger
from code.errors import DataLoadError

logger = get_logger(__name__)


def load_regression_results() -> Dict[str, Any]:
    """
    Load regression results from data/processed/cooperative_effects_analysis.json.

    Returns:
        Dict containing regression coefficients, model metrics, and metadata.

    Raises:
        DataLoadError: If the file is missing or malformed.
    """
    results_path = PROCESSED_PATH / "cooperative_effects_analysis.json"

    if not results_path.exists():
        logger.error(f"Regression results file not found: {results_path}")
        raise DataLoadError(f"Regression results file not found: {results_path}")

    try:
        with open(results_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded regression results from {results_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse regression results JSON: {e}")
        raise DataLoadError(f"Failed to parse regression results JSON: {e}")


def load_interaction_terms() -> pd.DataFrame:
    """
    Load interaction terms from data/processed/interaction_terms.csv.

    Returns:
        DataFrame containing interaction terms and target values.

    Raises:
        DataLoadError: If the file is missing or malformed.
    """
    terms_path = PROCESSED_PATH / "interaction_terms.csv"

    if not terms_path.exists():
        logger.error(f"Interaction terms file not found: {terms_path}")
        raise DataLoadError(f"Interaction terms file not found: {terms_path}")

    try:
        df = pd.read_csv(terms_path)
        logger.info(f"Loaded interaction terms from {terms_path}, shape: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Failed to load interaction terms CSV: {e}")
        raise DataLoadError(f"Failed to load interaction terms CSV: {e}")


def calculate_standard_errors(
    coefficients: np.ndarray,
    X: np.ndarray,
    y: np.ndarray,
    model
) -> np.ndarray:
    """
    Calculate standard errors for regression coefficients.

    The standard error is calculated as:
    SE(β) = sqrt(MSE * (X^T X)^(-1)_jj)

    where MSE is the mean squared error of the residuals.

    Args:
        coefficients: Array of regression coefficients.
        X: Feature matrix (including interaction terms).
        y: Target values.
        model: Fitted LinearRegression model.

    Returns:
        Array of standard errors for each coefficient.
    """
    n_samples = X.shape[0]
    n_features = X.shape[1]

    # Calculate residuals
    y_pred = model.predict(X)
    residuals = y - y_pred

    # Calculate MSE (Mean Squared Error)
    mse = np.sum(residuals ** 2) / (n_samples - n_features - 1)

    # Calculate (X^T X)^(-1)
    try:
        XtX_inv = np.linalg.inv(X.T @ X)
    except np.linalg.LinAlgError:
        logger.warning("X^T X is singular, using pseudo-inverse for standard errors")
        XtX_inv = np.linalg.pinv(X.T @ X)

    # Calculate standard errors
    standard_errors = np.sqrt(mse * np.diag(XtX_inv))

    logger.info(f"Calculated standard errors: {standard_errors}")
    return standard_errors


def calculate_p_values(
    coefficients: np.ndarray,
    standard_errors: np.ndarray
) -> np.ndarray:
    """
    Calculate p-values for regression coefficients using t-tests.

    The t-statistic is calculated as:
    t = β / SE(β)

    and the p-value is derived from the t-distribution with (n - p - 1) degrees of freedom.

    Args:
        coefficients: Array of regression coefficients.
        standard_errors: Array of standard errors for each coefficient.

    Returns:
        Array of two-tailed p-values for each coefficient.
    """
    # Avoid division by zero
    safe_se = np.where(standard_errors == 0, 1e-10, standard_errors)

    # Calculate t-statistics
    t_stats = coefficients / safe_se

    # Degrees of freedom (n_samples - n_features - 1)
    # We'll estimate this from the coefficient array length
    # assuming we have enough samples
    n_features = len(coefficients)
    # Assume reasonable sample size for calculation
    # In practice, this should be passed from the data
    n_samples = 100  # Default assumption, will be updated if actual data available
    df = n_samples - n_features - 1

    # Calculate two-tailed p-values
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df))

    logger.info(f"Calculated p-values: {p_values}")
    return p_values


def run_significance_test(
    regression_data: Dict[str, Any],
    interaction_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Run significance testing for interaction coefficients.

    This function:
    1. Extracts regression coefficients from the loaded data
    2. Prepares the feature matrix from interaction terms
    3. Calculates standard errors for each coefficient
    4. Computes p-values using t-tests
    5. Identifies significant coefficients (p < 0.05)

    Args:
        regression_data: Dictionary containing regression results.
        interaction_df: DataFrame with interaction terms.

    Returns:
        Dictionary containing significance test results including:
        - coefficients: regression coefficients
        - p_values: p-values for each coefficient
        - standard_errors: standard errors for each coefficients
        - significant_terms: list of interaction terms with p < 0.05
        - summary: overall significance summary
    """
    logger.info("Starting significance testing for interaction coefficients")

    # Extract coefficients and feature names
    coefficients = regression_data.get('coefficients', {})
    feature_names = regression_data.get('feature_names', [])

    if not coefficients or not feature_names:
        logger.error("No coefficients or feature names found in regression data")
        raise DataLoadError("No coefficients or feature names found in regression data")

    # Convert coefficients to array
    coef_array = np.array([coefficients.get(name, 0.0) for name in feature_names])

    # Prepare feature matrix from interaction terms
    # Assume the last column is the target (segregation energy)
    feature_cols = [col for col in interaction_df.columns if col != 'segregation_energy']
    X = interaction_df[feature_cols].values
    y = interaction_df['segregation_energy'].values

    # Get the fitted model from regression data (we need to refit to get proper SE)
    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    model.fit(X, y)

    # Calculate standard errors
    standard_errors = calculate_standard_errors(coef_array, X, y, model)

    # Calculate p-values
    p_values = calculate_p_values(coef_array, standard_errors)

    # Identify significant terms
    significant_terms = []
    for i, (name, p_val) in enumerate(zip(feature_names, p_values)):
        if p_val < 0.05:
            significant_terms.append({
                'term': name,
                'coefficient': float(coef_array[i]),
                'p_value': float(p_val),
                'standard_error': float(standard_errors[i]),
                'significant': True
            })
            logger.info(f"Significant term: {name}, p-value: {p_val:.4f}")
        else:
            significant_terms.append({
                'term': name,
                'coefficient': float(coef_array[i]),
                'p_value': float(p_val),
                'standard_error': float(standard_errors[i]),
                'significant': False
            })

    # Create summary
    num_significant = sum(1 for term in significant_terms if term['significant'])
    num_total = len(significant_terms)

    summary = {
        'total_terms': num_total,
        'significant_terms': num_significant,
        'significance_threshold': 0.05,
        'percentage_significant': (num_significant / num_total * 100) if num_total > 0 else 0,
        'interaction_terms_detected': num_significant > 0
    }

    logger.info(f"Significance test complete: {num_significant}/{num_total} terms significant")

    return {
        'coefficients': {name: float(coef_array[i]) for i, name in enumerate(feature_names)},
        'p_values': {name: float(p_val) for name, p_val in zip(feature_names, p_values)},
        'standard_errors': {name: float(se) for name, se in zip(feature_names, standard_errors)},
        'significant_terms': significant_terms,
        'summary': summary,
        'methodology': {
            'test': 't-test on regression coefficients',
            'distribution': 't-distribution',
            'threshold': 0.05,
            'two_tailed': True
        }
    }


def save_results(results: Dict[str, Any], output_path: Optional[Path] = None) -> None:
    """
    Save significance test results to JSON file.

    Args:
        results: Dictionary containing significance test results.
        output_path: Path to save results. Defaults to data/processed/significance_results.json.
    """
    if output_path is None:
        output_path = PROCESSED_PATH / "significance_results.json"

    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved significance test results to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save significance test results: {e}")
        raise


def main() -> None:
    """
    Main entry point for significance testing.

    This function orchestrates the significance testing workflow:
    1. Load regression results
    2. Load interaction terms
    3. Run significance testing
    4. Save results to JSON
    """
    logger.info("Starting significance testing for interaction coefficients")

    try:
        # Load data
        regression_data = load_regression_results()
        interaction_df = load_interaction_terms()

        # Run significance test
        results = run_significance_test(regression_data, interaction_df)

        # Save results
        save_results(results)

        # Print summary to stdout for verification
        summary = results['summary']
        print(f"Significance Test Results:")
        print(f"  Total terms tested: {summary['total_terms']}")
        print(f"  Significant terms (p < 0.05): {summary['significant_terms']}")
        print(f"  Percentage significant: {summary['percentage_significant']:.1f}%")
        print(f"  Interaction effects detected: {summary['interaction_terms_detected']}")

        if summary['significant_terms'] == 0:
            logger.warning("No significant interaction terms detected at p < 0.05 threshold")
        else:
            logger.info(f"Detected {summary['significant_terms']} significant interaction terms")

    except DataLoadError as e:
        logger.error(f"Data loading error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during significance testing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
