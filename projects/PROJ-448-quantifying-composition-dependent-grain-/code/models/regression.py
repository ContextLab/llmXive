"""
Regression module for fitting linear models with interaction terms.

Implements multivariate linear regression to model segregation energy as a function
of bulk composition and interaction terms (e.g., Cr*Mo, Cr*V).
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

from code.config import PROCESSED_PATH, get_logger
from code.errors import RegressionError

logger = get_logger(__name__)


def load_interaction_terms(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load interaction terms from the generated CSV file.

    Args:
        filepath: Path to the interaction terms CSV. Defaults to
                  data/processed/interaction_terms.csv.

    Returns:
        DataFrame with composition and interaction term columns.

    Raises:
        RegressionError: If the file is missing or malformed.
    """
    if filepath is None:
        filepath = PROCESSED_PATH / "interaction_terms.csv"

    if not filepath.exists():
        raise RegressionError(f"Interaction terms file not found: {filepath}")

    try:
        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df)} rows of interaction terms from {filepath}")
        return df
    except Exception as e:
        raise RegressionError(f"Failed to load interaction terms: {e}")


def prepare_features_and_target(
    df: pd.DataFrame,
    target_col: str = "segregation_energy_eV",
    composition_cols: List[str] = ["Cr", "Mo", "V", "W"],
    interaction_cols: List[str] = None
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare feature matrix X and target vector y for regression.

    Args:
        df: DataFrame containing composition, interaction terms, and target.
        target_col: Name of the target column (segregation energy).
        composition_cols: List of base composition column names.
        interaction_cols: List of interaction term column names. If None,
                          inferred from df columns.

    Returns:
        Tuple of (X, y, feature_names) where:
            X: Feature matrix (base compositions + interactions)
            y: Target vector (segregation energies)
            feature_names: List of column names used in X
    """
    if interaction_cols is None:
        # Identify interaction columns by looking for underscore-separated
        # pairs of composition elements
        interaction_cols = [
            col for col in df.columns
            if "_" in col and col != target_col
            and all(part in composition_cols for part in col.split("_"))
        ]
        logger.info(f"Auto-detected interaction columns: {interaction_cols}")

    feature_cols = composition_cols + interaction_cols
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise RegressionError(f"Missing required columns: {missing_cols}")

    if target_col not in df.columns:
        raise RegressionError(f"Target column '{target_col}' not found in data")

    X = df[feature_cols].values
    y = df[target_col].values

    logger.info(f"Prepared feature matrix with shape {X.shape} and target shape {y.shape}")
    return X, y, feature_cols


def fit_linear_model_with_interactions(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    fit_intercept: bool = True
) -> Dict[str, Any]:
    """
    Fit a linear regression model and return results.

    Args:
        X: Feature matrix.
        y: Target vector.
        feature_names: Names of features corresponding to X columns.
        fit_intercept: Whether to fit an intercept term.

    Returns:
        Dictionary containing:
            - model: Fitted LinearRegression instance
            - coefficients: Dict mapping feature names to coefficients
            - intercept: Model intercept
            - r2_score: R^2 score on training data
            - mse: Mean squared error on training data
    """
    if X.shape[0] < X.shape[1]:
        logger.warning(f"More features ({X.shape[1]}) than samples ({X.shape[0]}). "
                     "Model may be overfitting.")

    model = LinearRegression(fit_intercept=fit_intercept)
    model.fit(X, y)

    coefficients = dict(zip(feature_names, model.coef_))
    if fit_intercept:
        coefficients["intercept"] = model.intercept_

    y_pred = model.predict(X)
    mse = np.mean((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    ss_res = np.sum((y - y_pred) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    logger.info(f"Model fitted: R² = {r2:.4f}, MSE = {mse:.6f}")
    logger.info(f"Coefficients: {coefficients}")

    return {
        "model": model,
        "coefficients": coefficients,
        "intercept": model.intercept_ if fit_intercept else 0.0,
        "r2_score": r2,
        "mse": mse,
        "feature_names": feature_names
    }


def generate_polynomial_features(
    df: pd.DataFrame,
    composition_cols: List[str],
    degree: int = 2,
    include_bias: bool = False
) -> pd.DataFrame:
    """
    Generate interaction terms using sklearn PolynomialFeatures.

    Args:
        df: DataFrame with composition columns.
        composition_cols: List of composition column names to use.
        degree: Degree of polynomial features (2 for interactions).
        include_bias: Whether to include bias column.

    Returns:
        DataFrame with original composition columns and new interaction columns.
    """
    X = df[composition_cols].values
    poly = PolynomialFeatures(degree=degree, include_bias=include_bias, interaction_only=True)
    X_poly = poly.fit_transform(X)

    feature_names = poly.get_feature_names_out(composition_cols)

    # Filter to keep only interaction terms (containing spaces)
    interaction_mask = [" " in name for name in feature_names]
    interaction_names = [name.replace(" ", "_") for i, name in enumerate(feature_names) if interaction_mask[i]]
    interaction_data = X_poly[:, interaction_mask]

    interaction_df = pd.DataFrame(interaction_data, columns=interaction_names, index=df.index)

    # Combine with original data
    result = pd.concat([df.reset_index(drop=True), interaction_df], axis=1)
    logger.info(f"Generated {len(interaction_names)} interaction terms: {interaction_names}")
    return result


def run_regression_analysis(
    input_df: Optional[pd.DataFrame] = None,
    target_col: str = "segregation_energy_eV",
    composition_cols: List[str] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main entry point for running regression analysis on segregation data.

    Args:
        input_df: DataFrame with segregation profiles. If None, loads from
                  interaction_terms.csv.
        target_col: Name of target column.
        composition_cols: Base composition columns. Defaults to ["Cr", "Mo", "V", "W"].
        output_path: Path to save results JSON. Defaults to
                    data/processed/regression_results.json.

    Returns:
        Dictionary with regression results.
    """
    if composition_cols is None:
        composition_cols = ["Cr", "Mo", "V", "W"]

    if input_df is None:
        input_df = load_interaction_terms()

    X, y, feature_names = prepare_features_and_target(
        input_df, target_col, composition_cols
    )

    results = fit_linear_model_with_interactions(X, y, feature_names)

    if output_path is None:
        output_path = PROCESSED_PATH / "regression_results.json"

    # Convert numpy types to Python native types for JSON serialization
    serializable_results = {
        "r2_score": float(results["r2_score"]),
        "mse": float(results["mse"]),
        "intercept": float(results["intercept"]),
        "coefficients": {k: float(v) for k, v in results["coefficients"].items() if k != "intercept"},
        "feature_names": results["feature_names"]
    }

    # Save to file
    import json
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(serializable_results, f, indent=2)

    logger.info(f"Regression results saved to {output_path}")
    return serializable_results


def main():
    """Main entry point for the regression module."""
    logger.info("Starting regression analysis with interaction terms")
    results = run_regression_analysis()
    logger.info(f"Analysis complete. R²: {results['r2_score']:.4f}, MSE: {results['mse']:.6f}")
    return results


if __name__ == "__main__":
    main()