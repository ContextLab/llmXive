"""
Regression analysis module for computing goodness-of-fit metrics for knot complexity models.

This module implements regression model fitting (linear, polynomial, logarithmic) and
computes goodness-of-fit metrics (R², AIC, BIC, MAE) as per FR-005.

The regression analysis tests linear vs. non-linear relationships for associating
hyperbolic volume from crossing number and braid index.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import warnings

# Suppress warnings for cleaner output during computation
warnings.filterwarnings('ignore', category=RuntimeWarning)

from reproducibility.logs import log_operation, get_logger


@dataclass
class RegressionMetrics:
    """Container for goodness-of-fit metrics of a regression model."""
    model_type: str
    r_squared: float
    aic: float
    bic: float
    mae: float
    rmse: float
    n_samples: int
    n_parameters: int
    formula: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'model_type': self.model_type,
            'r_squared': self.r_squared,
            'aic': self.aic,
            'bic': self.bic,
            'mae': self.mae,
            'rmse': self.rmse,
            'n_samples': self.n_samples,
            'n_parameters': self.n_parameters,
            'formula': self.formula
        }


@dataclass
class RegressionResult:
    """Container for complete regression analysis results."""
    model_type: str
    coefficients: Dict[str, float]
    metrics: RegressionMetrics
    predictions: np.ndarray
    residuals: np.ndarray
    fitted_values: np.ndarray

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'model_type': self.model_type,
            'coefficients': self.coefficients,
            'metrics': self.metrics.to_dict(),
            'predictions': self.predictions.tolist(),
            'residuals': self.residuals.tolist(),
            'fitted_values': self.fitted_values.tolist()
        }


@dataclass
class RegressionAnalysisReport:
    """Container for complete regression analysis report."""
    analysis_timestamp: str
    dataset_summary: Dict[str, Any]
    model_results: List[RegressionResult]
    best_model: Optional[str]
    best_model_r_squared: float
    comparison_summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'analysis_timestamp': self.analysis_timestamp,
            'dataset_summary': self.dataset_summary,
            'model_results': [r.to_dict() for r in self.model_results],
            'best_model': self.best_model,
            'best_model_r_squared': self.best_model_r_squared,
            'comparison_summary': self.comparison_summary
        }


def calculate_r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate the coefficient of determination (R²).

    R² = 1 - SS_res / SS_tot
    where:
        SS_res = sum of squared residuals
        SS_tot = total sum of squares

    Args:
        y_true: Actual values
        y_pred: Predicted values

    Returns:
        R² value between 0 and 1 (can be negative for poor models)
    """
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0

    return 1.0 - (ss_res / ss_tot)


def calculate_aic(n_samples: int, n_parameters: int, rss: float) -> float:
    """
    Calculate the Akaike Information Criterion (AIC).

    AIC = 2k - 2ln(L)
    For linear regression with normal errors:
    AIC = n * ln(RSS/n) + 2k

    where:
        n = number of samples
        k = number of parameters
        RSS = residual sum of squares

    Args:
        n_samples: Number of data points
        n_parameters: Number of model parameters
        rss: Residual sum of squares

    Returns:
        AIC value (lower is better)
    """
    if rss <= 0:
        rss = 1e-10  # Avoid log(0)

    return n_samples * np.log(rss / n_samples) + 2 * n_parameters


def calculate_bic(n_samples: int, n_parameters: int, rss: float) -> float:
    """
    Calculate the Bayesian Information Criterion (BIC).

    BIC = k * ln(n) - 2ln(L)
    For linear regression with normal errors:
    BIC = n * ln(RSS/n) + k * ln(n)

    where:
        n = number of samples
        k = number of parameters
        RSS = residual sum of squares

    Args:
        n_samples: Number of data points
        n_parameters: Number of model parameters
        rss: Residual sum of squares

    Returns:
        BIC value (lower is better)
    """
    if rss <= 0:
        rss = 1e-10  # Avoid log(0)

    return n_samples * np.log(rss / n_samples) + n_parameters * np.log(n_samples)


def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate the Mean Absolute Error (MAE).

    MAE = (1/n) * sum(|y_true - y_pred|)

    Args:
        y_true: Actual values
        y_pred: Predicted values

    Returns:
        Mean absolute error
    """
    return np.mean(np.abs(y_true - y_pred))


def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate the Root Mean Squared Error (RMSE).

    RMSE = sqrt((1/n) * sum((y_true - y_pred)²))

    Args:
        y_true: Actual values
        y_pred: Predicted values

    Returns:
        Root mean squared error
    """
    return np.sqrt(np.mean((y_true - y_pred) ** 2))


def fit_linear_model(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Fit a linear regression model: y = β₀ + β₁*X

    Args:
        X: Independent variable (1D array)
        y: Dependent variable (1D array)

    Returns:
        Tuple of (coefficients [intercept, slope], predictions)
    """
    n = len(X)
    X_mean = np.mean(X)
    y_mean = np.mean(y)

    # Calculate slope: β₁ = Σ((X - X̄)(y - ȳ)) / Σ((X - X̄)²)
    numerator = np.sum((X - X_mean) * (y - y_mean))
    denominator = np.sum((X - X_mean) ** 2)

    if denominator == 0:
        slope = 0.0
    else:
        slope = numerator / denominator

    # Calculate intercept: β₀ = ȳ - β₁*X̄
    intercept = y_mean - slope * X_mean

    coefficients = np.array([intercept, slope])
    predictions = intercept + slope * X

    return coefficients, predictions


def fit_polynomial_model(X: np.ndarray, y: np.ndarray, degree: int = 2) -> Tuple[np.ndarray, np.ndarray]:
    """
    Fit a polynomial regression model: y = β₀ + β₁*X + β₂*X² + ... + βₙ*Xⁿ

    Args:
        X: Independent variable (1D array)
        y: Dependent variable (1D array)
        degree: Degree of polynomial (default: 2 for quadratic)

    Returns:
        Tuple of (coefficients, predictions)
    """
    # Use numpy's polyfit for polynomial fitting
    coefficients = np.polyfit(X, y, degree)
    predictions = np.polyval(coefficients, X)

    return coefficients, predictions


def fit_logarithmic_model(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Fit a logarithmic regression model: y = β₀ + β₁*ln(X)

    Args:
        X: Independent variable (1D array, must be > 0)
        y: Dependent variable (1D array)

    Returns:
        Tuple of (coefficients [intercept, slope], predictions)
    """
    # Filter out non-positive X values
    valid_mask = X > 0
    X_valid = X[valid_mask]
    y_valid = y[valid_mask]

    if len(X_valid) < 2:
        # Not enough valid data points, return constant model
        intercept = np.mean(y)
        slope = 0.0
        predictions = np.full(len(X), intercept)
        return np.array([intercept, slope]), predictions

    # Transform X using natural log
    log_X = np.log(X_valid)

    # Calculate slope and intercept
    log_X_mean = np.mean(log_X)
    y_mean = np.mean(y_valid)

    numerator = np.sum((log_X - log_X_mean) * (y_valid - y_mean))
    denominator = np.sum((log_X - log_X_mean) ** 2)

    if denominator == 0:
        slope = 0.0
    else:
        slope = numerator / denominator

    intercept = y_mean - slope * log_X_mean

    # Calculate predictions for all X values
    predictions = np.full(len(X), np.nan)
    predictions[valid_mask] = intercept + slope * np.log(X_valid)

    # Fill NaN predictions with mean
    predictions = np.nan_to_num(predictions, nan=np.mean(y))

    return np.array([intercept, slope]), predictions


def compute_goodness_of_fit(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_type: str,
    n_parameters: int
) -> RegressionMetrics:
    """
    Compute all goodness-of-fit metrics for a regression model.

    Args:
        y_true: Actual values
        y_pred: Predicted values
        model_type: Type of model (e.g., 'linear', 'polynomial', 'logarithmic')
        n_parameters: Number of model parameters

    Returns:
        RegressionMetrics object with all computed metrics
    """
    n_samples = len(y_true)

    # Calculate metrics
    r_squared = calculate_r_squared(y_true, y_pred)
    rss = np.sum((y_true - y_pred) ** 2)
    aic = calculate_aic(n_samples, n_parameters, rss)
    bic = calculate_bic(n_samples, n_parameters, rss)
    mae = calculate_mae(y_true, y_pred)
    rmse = calculate_rmse(y_true, y_pred)

    # Create formula string based on model type
    formula = _create_formula_string(model_type, n_parameters)

    return RegressionMetrics(
        model_type=model_type,
        r_squared=r_squared,
        aic=aic,
        bic=bic,
        mae=mae,
        rmse=rmse,
        n_samples=n_samples,
        n_parameters=n_parameters,
        formula=formula
    )


def _create_formula_string(model_type: str, n_parameters: int) -> str:
    """Create a human-readable formula string for the model."""
    if model_type == 'linear':
        return 'y = β₀ + β₁*x'
    elif model_type == 'polynomial':
        degree = n_parameters - 1
        return f'y = β₀ + β₁*x + β₂*x² + ... + β_{degree}*x^{degree}'
    elif model_type == 'logarithmic':
        return 'y = β₀ + β₁*ln(x)'
    else:
        return f'{model_type} model with {n_parameters} parameters'


def fit_regression_models(
    X: np.ndarray,
    y: np.ndarray,
    model_types: List[str] = None
) -> List[RegressionResult]:
    """
    Fit multiple regression models and compute goodness-of-fit metrics.

    Args:
        X: Independent variable (1D array)
        y: Dependent variable (1D array)
        model_types: List of model types to fit (default: ['linear', 'polynomial', 'logarithmic'])

    Returns:
        List of RegressionResult objects for each fitted model
    """
    if model_types is None:
        model_types = ['linear', 'polynomial', 'logarithmic']

    results = []

    for model_type in model_types:
        try:
            if model_type == 'linear':
                coefficients, predictions = fit_linear_model(X, y)
                n_parameters = 2  # intercept + slope
            elif model_type == 'polynomial':
                coefficients, predictions = fit_polynomial_model(X, y, degree=2)
                n_parameters = 3  # intercept + linear + quadratic
            elif model_type == 'logarithmic':
                coefficients, predictions = fit_logarithmic_model(X, y)
                n_parameters = 2  # intercept + slope
            else:
                continue

            # Compute goodness-of-fit metrics
            metrics = compute_goodness_of_fit(y, predictions, model_type, n_parameters)

            # Calculate residuals
            residuals = y - predictions

            result = RegressionResult(
                model_type=model_type,
                coefficients={f'β{i}': float(c) for i, c in enumerate(coefficients)},
                metrics=metrics,
                predictions=predictions,
                residuals=residuals,
                fitted_values=predictions
            )

            results.append(result)

        except Exception as e:
            # Log error but continue with other models
            logger = get_logger()
            logger.warning(f"Failed to fit {model_type} model: {e}")

    return results


def run_regression_analysis(
    data_path: Path,
    output_path: Path,
    x_column: str = 'crossing_number',
    y_column: str = 'hyperbolic_volume'
) -> RegressionAnalysisReport:
    """
    Run complete regression analysis on knot dataset.

    Args:
        data_path: Path to cleaned knot data CSV file
        output_path: Path to save analysis results
        x_column: Name of independent variable column
        y_column: Name of dependent variable column

    Returns:
        RegressionAnalysisReport with all results
    """
    logger = get_logger()

    # Log operation start
    log_operation(
        logger=logger,
        operation='regression_analysis',
        input_file=str(data_path),
        output_file=str(output_path),
        parameters={'x_column': x_column, 'y_column': y_column}
    )

    # Load data
    df = pd.read_csv(data_path)

    # Filter out rows with NaN values in target columns
    valid_mask = df[[x_column, y_column]].notna().all(axis=1)
    df_valid = df[valid_mask]

    # Extract arrays
    X = df_valid[x_column].values.astype(float)
    y = df_valid[y_column].values.astype(float)

    # Filter out non-positive X values for logarithmic model
  # Keep valid data for all models
  # For logarithmic, we'll handle non-positive X internally

    # Fit models
    model_results = fit_regression_models(X, y)

    # Find best model by R²
    best_model = None
    best_r_squared = -float('inf')

    for result in model_results:
        if result.metrics.r_squared > best_r_squared:
            best_r_squared = result.metrics.r_squared
            best_model = result.model_type

    # Create summary
    comparison_summary = {
        'total_models_fitted': len(model_results),
        'best_model_by_r_squared': best_model,
        'best_r_squared': best_r_squared,
        'all_metrics': {r.model_type: r.metrics.to_dict() for r in model_results}
    }

    # Create report
    report = RegressionAnalysisReport(
        analysis_timestamp=datetime.now().isoformat(),
        dataset_summary={
            'total_samples': len(df),
            'valid_samples': len(df_valid),
            'x_column': x_column,
            'y_column': y_column,
            'x_mean': float(np.mean(X)),
            'x_std': float(np.std(X)),
            'y_mean': float(np.mean(y)),
            'y_std': float(np.std(y))
        },
        model_results=model_results,
        best_model=best_model,
        best_model_r_squared=best_r_squared,
        comparison_summary=comparison_summary
    )

    # Save results
  # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save JSON report
    import json
    with open(output_path, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)

    # Log operation completion
    log_operation(
        logger=logger,
        operation='regression_analysis_complete',
        input_file=str(data_path),
        output_file=str(output_path),
        parameters={'best_model': best_model, 'best_r_squared': best_r_squared},
        status='completed'
    )

    return report


def main():
    """Main entry point for regression analysis."""
    import argparse

    parser = argparse.ArgumentParser(description='Run regression analysis on knot data')
    parser.add_argument('--input', type=str, default='data/processed/knots_cleaned.csv',
                      help='Path to input CSV file')
    parser.add_argument('--output', type=str, default='data/processed/regression_analysis.json',
                      help='Path to output JSON file')
    parser.add_argument('--x-column', type=str, default='crossing_number',
                      help='Name of independent variable column')
    parser.add_argument('--y-column', type=str, default='hyperbolic_volume',
                      help='Name of dependent variable column')

    args = parser.parse_args()

    data_path = Path(args.input)
    output_path = Path(args.output)

    if not data_path.exists():
        print(f"Error: Input file not found: {data_path}")
        return 1

    print(f"Running regression analysis on {data_path}...")
    report = run_regression_analysis(data_path, output_path, args.x_column, args.y_column)

    print(f"Analysis complete. Best model: {report.best_model} (R² = {report.best_model_r_squared:.4f})")
    print(f"Results saved to: {output_path}")

    return 0


if __name__ == '__main__':
    exit(main())
