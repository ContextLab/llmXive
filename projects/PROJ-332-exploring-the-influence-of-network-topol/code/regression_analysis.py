import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
import logging
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import OLSInfluence

logger = logging.getLogger(__name__)

def run_ols_regression(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform OLS regression on log-transformed data.
    Returns dictionary with exponent, confidence interval, and p-value.
    """
    if len(results) < 2:
        logger.warning("Not enough data points for regression")
        return {"exponent": None, "ci_low": None, "ci_high": None, "p_value": None}

    df = pd.DataFrame(results)
    # Filter for connected graphs (percolation_flag == 1)
    df = df[df["percolation_flag"] == 1]

    if len(df) < 2:
        logger.warning("Not enough connected graphs for regression")
        return {"exponent": None, "ci_low": None, "ci_high": None, "p_value": None}

    # Log-transform
    X = np.log(df["avg_degree"].values)
    y = np.log(df["conductivity"].values)

    # Add constant for intercept
    X = sm.add_constant(X)

    try:
        model = sm.OLS(y, X)
        results_model = model.fit()

        # Extract exponent (slope), CI, and p-value
        exponent = results_model.params[1]
        conf_int = results_model.conf_int(alpha=0.05)
        p_value = results_model.pvalues[1]

        logger.info(f"Regression exponent: {exponent:.4f}, p-value: {p_value:.4f}")

        return {
            "exponent": exponent,
            "ci_low": conf_int.iloc[0, 1],
            "ci_high": conf_int.iloc[1, 1],
            "p_value": p_value,
            "r_squared": results_model.rsquared
        }
    except Exception as e:
        logger.error(f"Regression failed: {e}")
        return {"exponent": None, "ci_low": None, "ci_high": None, "p_value": None}

def calculate_correlation_matrix(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """Calculate correlation matrix for all metrics."""
    df = pd.DataFrame(results)
    numeric_cols = ["N", "p", "avg_degree", "conductivity"]
    # Filter only existing columns
    existing_cols = [c for c in numeric_cols if c in df.columns]
    if len(existing_cols) < 2:
        return pd.DataFrame()
    return df[existing_cols].corr()

def detect_percolation_threshold(results: List[Dict[str, Any]]) -> Optional[float]:
    """
    Detect percolation threshold: smallest avg_degree where >= 80% connected.
    """
    if not results:
        return None

    df = pd.DataFrame(results)
    if "percolation_flag" not in df.columns:
        return None

    # Group by avg_degree and calculate connectivity rate
    grouped = df.groupby("avg_degree").agg(
        connected=("percolation_flag", "mean"),
        count=("percolation_flag", "count")
    ).reset_index()

    # Filter for degrees with at least one sample
    grouped = grouped[grouped["count"] > 0]

    # Find smallest avg_degree where connected >= 0.8
    threshold_rows = grouped[grouped["connected"] >= 0.8]
    if threshold_rows.empty:
        return None

    return float(threshold_rows["avg_degree"].min())

def update_csv_with_percolation_threshold(csv_path: str, threshold: Optional[float]) -> None:
    """
    Update the CSV file to include the percolation_threshold value.
    This fulfills the requirement to store the threshold in the results file.
    """
    if threshold is None:
        logger.info("No percolation threshold detected, skipping CSV update")
        return

    logger.info(f"Updating CSV with percolation threshold: {threshold}")

    # Read existing CSV
    if not os.path.exists(csv_path):
        logger.warning(f"CSV file {csv_path} not found, cannot update")
        return

    df = pd.read_csv(csv_path)

    # Add column if not exists
    if "percolation_threshold" not in df.columns:
        df["percolation_threshold"] = np.nan

    # Fill with the detected threshold
    df["percolation_threshold"] = threshold

    # Write back
    df.to_csv(csv_path, index=False)
    logger.info(f"Updated {csv_path} with percolation_threshold = {threshold}")

def analyze_scaling_law(results: List[Dict[str, Any]], threshold: Optional[float]) -> Dict[str, Any]:
    """
    Analyze scaling law above percolation threshold.
    Returns significant scaling exponent if p < 0.05.
    """
    if threshold is None:
        return {"significant": False, "exponent": None, "p_value": None}

    df = pd.DataFrame(results)
    # Filter for degrees above threshold
    above_threshold = df[df["avg_degree"] > threshold]

    if len(above_threshold) < 2:
        logger.warning("Not enough data above threshold for scaling analysis")
        return {"significant": False, "exponent": None, "p_value": None}

    reg_results = run_ols_regression(above_threshold.to_dict('records'))

    if reg_results["p_value"] is not None and reg_results["p_value"] < 0.05:
        logger.info(f"Significant scaling exponent found: {reg_results['exponent']:.4f}")
        return {
            "significant": True,
            "exponent": reg_results["exponent"],
            "p_value": reg_results["p_value"],
            "ci_low": reg_results["ci_low"],
            "ci_high": reg_results["ci_high"]
        }
    else:
        logger.info("Scaling exponent not statistically significant (p >= 0.05)")
        return {
            "significant": False,
            "exponent": reg_results["exponent"],
            "p_value": reg_results["p_value"]
        }
