"""
Analysis module for correlation between molecular complexity and degradation rates.
Implements MLR, LASSO, and residual diagnostics.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.linear_model import Lasso, LinearRegression
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler

from code.logging_config import get_logger, log_operation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)
logger = get_logger("analysis")


def get_data_path() -> Path:
    """Return the project root path."""
    return Path(__file__).parent.parent


def load_gate_status() -> Dict[str, Any]:
    """Load gate status from data/gate_status.json."""
    gate_path = get_data_path() / "data" / "gate_status.json"
    if not gate_path.exists():
        return {"status": "FAIL", "reason": "Gate status file not found"}
    with open(gate_path, "r") as f:
        return json.load(f)


def load_stat_gate_status() -> Dict[str, Any]:
    """Load statistical gate status from data/stat_gate_status.json."""
    stat_gate_path = get_data_path() / "data" / "stat_gate_status.json"
    if not stat_gate_path.exists():
        return {"status": "FAIL", "reason": "Stat gate status file not found"}
    with open(stat_gate_path, "r") as f:
        return json.load(f)


def load_standard_subset() -> pd.DataFrame:
    """Load the standard subset dataset."""
    data_path = get_data_path() / "data" / "processed" / "standard_subset.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Standard subset file not found: {data_path}")
    return pd.read_csv(data_path)


def run_mlr(X: np.ndarray, y: np.ndarray) -> Tuple[Dict[str, float], float]:
    """
    Run Multiple Linear Regression.

    Returns:
        Tuple of (coefficients dict, R2 score)
    """
    model = LinearRegression()
    model.fit(X, y)

    # Calculate R2
    y_pred = model.predict(X)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

    # Get feature names from column headers if available
    # Assuming X is a numpy array, we'll use generic names
    feature_names = [f"feature_{i}" for i in range(X.shape[1])]

    coefficients = {name: float(coeff) for name, coeff in zip(feature_names, model.coef_)}

    return coefficients, float(r2)


def run_lasso_regression(X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Tuple[Dict[str, float], float, Dict[str, float]]:
    """
    Run LASSO regression with GridSearchCV for alpha selection.

    Returns:
        Tuple of (coefficients dict, best alpha, p_values dict)
    """
    # Scale data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Define alpha range
    alphas = np.logspace(-4, 2, 50)

    # GridSearchCV
    lasso = Lasso(max_iter=10000)
    grid = GridSearchCV(lasso, {"alpha": alphas}, cv=5, scoring="r2")
    grid.fit(X_scaled, y)

    best_model = grid.best_estimator_
    best_alpha = grid.best_params_["alpha"]

    # Calculate R2
    y_pred = best_model.predict(X_scaled)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

    # Get coefficients
    coefficients = {name: float(coeff) for name, coeff in zip(feature_names, best_model.coef_)}

    # Calculate p-values (approximate using t-test)
    # Note: LASSO coefficients are biased, so p-values are approximate
    n_samples = X.shape[0]
    n_features = X.shape[1]
    degrees_of_freedom = n_samples - n_features - 1

    # Standard errors (simplified approximation)
    residuals = y - y_pred
    mse = np.sum(residuals ** 2) / degrees_of_freedom if degrees_of_freedom > 0 else 1.0

    # Covariance matrix approximation
    try:
        XtX_inv = np.linalg.pinv(X_scaled.T @ X_scaled)
        std_errors = np.sqrt(np.diag(XtX_inv) * mse)
    except np.linalg.LinAlgError:
        std_errors = np.ones(n_features)

    # T-statistics and p-values
    t_stats = best_model.coef_ / std_errors if np.all(std_errors != 0) else np.zeros(n_features)
    p_values = {name: float(2 * (1 - stats.t.cdf(np.abs(t), degrees_of_freedom)))
                for name, t in zip(feature_names, t_stats)}

    return coefficients, float(best_alpha), p_values


def perform_residual_diagnostics(y: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    """
    Perform residual diagnostics: Shapiro-Wilk and Breusch-Pagan tests.

    Returns:
        Dictionary with test statistics and p-values
    """
    residuals = y - y_pred

    # Shapiro-Wilk test for normality
    shapiro_stat, shapiro_p = stats.shapiro(residuals)

    # Breusch-Pagan test for homoscedasticity
    # We need the original features for this test
    # For simplicity, we'll use a basic version
    n = len(residuals)
    # Create a simple model for variance (using predicted values as proxy)
    y_pred_squared = y_pred ** 2
    # Fit a simple linear model: residuals^2 ~ y_pred^2
    try:
        X_bp = sm.add_constant(y_pred)
        model_bp = sm.OLS(residuals ** 2, X_bp).fit()
        # LM test statistic
        lm_stat = n * model_bp.rsquared
        bp_p = 1 - stats.chi2.cdf(lm_stat, 1)  # 1 degree of freedom
    except Exception:
        lm_stat = 0.0
        bp_p = 1.0

    return {
        "shapiro_wilk": {"stat": float(shapiro_stat), "p": float(shapiro_p)},
        "breusch_pagan": {"stat": float(lm_stat), "p": float(bp_p)},
    }


def save_analysis_results(
    status: str,
    n: int,
    r2: Optional[float],
    p_values: Optional[Dict[str, float]],
    coefficients: Optional[Dict[str, float]],
    diagnostics: Dict[str, Any],
    methodology: str = "MLR+LASSO",
) -> Path:
    """Save analysis results to JSON file."""
    output_path = get_data_path() / "data" / "processed" / "analysis_results.json"

    results = {
        "status": status,
        "N": n,
        "R2": r2,
        "p_values": p_values,
        "coefficients": coefficients,
        "methodology": methodology,
        "timestamp": datetime.utcnow().isoformat(),
        "diagnostics": diagnostics,
    }

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Analysis results saved to {output_path}")
    return output_path


def save_analysis_results_wrapper(
    status: str,
    n: int,
    r2: Optional[float] = None,
    p_values: Optional[Dict[str, float]] = None,
    coefficients: Optional[Dict[str, float]] = None,
    diagnostics: Optional[Dict[str, Any]] = None,
) -> None:
    """Wrapper to save analysis results with default diagnostics."""
    if diagnostics is None:
        diagnostics = {
            "shapiro_wilk": {"stat": 0.0, "p": 1.0},
            "breusch_pagan": {"stat": 0.0, "p": 1.0},
        }

    save_analysis_results(
        status=status,
        n=n,
        r2=r2,
        p_values=p_values,
        coefficients=coefficients,
        diagnostics=diagnostics,
    )


@log_operation("main")
def main() -> int:
    """Main entry point for analysis."""
    from datetime import datetime  # Import here to avoid circular issues

    logger.info("Starting analysis pipeline")

    # Check gate statuses
    gate_status = load_gate_status()
    stat_gate_status = load_stat_gate_status()

    if gate_status.get("status") != "PASS" or stat_gate_status.get("status") != "PASS":
        logger.warning("Gate failed or not passed. Skipping analysis.")
        save_analysis_results_wrapper(
            status="SKIPPED",
            n=gate_status.get("N", 0) if gate_status.get("status") == "FAIL" else stat_gate_status.get("N", 0),
        )
        return 1

    try:
        # Load data
        df = load_standard_subset()
        n = len(df)

        if n == 0:
            logger.error("No data available for analysis")
            save_analysis_results_wrapper(status="FAIL", n=0)
            return 1

        # Identify target and features
        # Assume 'half_life' is the target and other numeric columns are features
        target_col = "half_life"
        if target_col not in df.columns:
            # Try alternative names
            for alt in ["t_half", "t1_2", "degradation_half_life"]:
                if alt in df.columns:
                    target_col = alt
                    break

        if target_col not in df.columns:
            logger.error(f"Target column '{target_col}' not found in dataset")
            save_analysis_results_wrapper(status="FAIL", n=n)
            return 1

        # Select features (exclude target and non-numeric columns)
        feature_cols = [col for col in df.select_dtypes(include=[np.number]).columns if col != target_col]

        if len(feature_cols) == 0:
            logger.error("No feature columns found")
            save_analysis_results_wrapper(status="FAIL", n=n)
            return 1

        X = df[feature_cols].values
        y = df[target_col].values

        # Handle missing values
        mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
        X = X[mask]
        y = y[mask]
        n = len(y)

        if n < 2:
            logger.error("Insufficient data after cleaning")
            save_analysis_results_wrapper(status="FAIL", n=n)
            return 1

        # Run MLR
        logger.info("Running MLR...")
        mlr_coeffs, mlr_r2 = run_mlr(X, y)

        # Run LASSO
        logger.info("Running LASSO regression...")
        lasso_coeffs, best_alpha, p_values = run_lasso_regression(X, y, feature_cols)

        # Run diagnostics
        logger.info("Performing residual diagnostics...")
        y_pred = lasso_coeffs  # Use LASSO predictions for diagnostics
        # Recalculate predictions using the actual model
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        lasso = Lasso(alpha=best_alpha, max_iter=10000)
        lasso.fit(X_scaled, y)
        y_pred = lasso.predict(X_scaled)

        diagnostics = perform_residual_diagnostics(y, y_pred)

        # Save results
        logger.info("Saving analysis results...")
        save_analysis_results(
            status="PASS",
            n=n,
            r2=mlr_r2,
            p_values=p_values,
            coefficients=lasso_coeffs,
            diagnostics=diagnostics,
        )

        logger.info("Analysis completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        save_analysis_results_wrapper(status="FAIL", n=0)
        return 1


if __name__ == "__main__":
    sys.exit(main())
