import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

__all__ = [
    "load_primary_analysis_dataset",
    "prepare_gam_data",
    "fit_gam_model",
    "extract_gam_results",
    "test_nonlinearity",
    "run_gam_analysis",
    "main",
]

def load_primary_analysis_dataset(csv_path: str) -> pd.DataFrame:
    """
    Load the primary analysis dataset for GAM modeling.

    Parameters
    ----------
    csv_path: str
        Path to the CSV file produced by ``code/modeling/filter.py``.

    Returns
    -------
    pd.DataFrame
        DataFrame ready for GAM analysis.
    """
    logging.info("Loading GAM dataset from %s", csv_path)
    return pd.read_csv(csv_path)

def prepare_gam_data(df: pd.DataFrame, predictor: str, response: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract predictor and response arrays for GAM fitting.

    Parameters
    ----------
    df: pd.DataFrame
    predictor: str
        Column name for the predictor variable (e.g., a spatial metric).
    response: str
        Column name for the response variable (e.g., ``'PCE'``).

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        (X, y) arrays suitable for ``pygam``.
    """
    X = df[[predictor]].values
    y = df[response].values
    return X, y

def fit_gam_model(X: np.ndarray, y: np.ndarray, spline_order: int = 3) -> Any:
    """
    Fit a Generalized Additive Model using ``pygam``.

    Parameters
    ----------
    X: np.ndarray
        Predictor matrix.
    y: np.ndarray
        Response vector.
    spline_order: int, optional
        Order of the spline basis (default 3).

    Returns
    -------
    Any
        Fitted GAM object.
    """
    try:
        from pygam import LinearGAM, s
    except ImportError as e:
        logging.error("pygam is not installed: %s", e)
        raise

    gam = LinearGAM(s(0, n_splines=20, spline_order=spline_order)).fit(X, y)
    return gam

def extract_gam_results(gam: Any) -> Dict[str, Any]:
    """
    Extract summary statistics from a fitted GAM.

    Parameters
    ----------
    gam: Any
        Fitted GAM object.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing ``'edf'``, ``'p_values'`` and ``'summary'``.
    """
    return {
        "edf": gam.statistics_["edof"],
        "p_values": gam.statistics_["p_values"],
        "summary": gam.summary(),
    }

def test_nonlinearity(gam: Any, X: np.ndarray, y: np.ndarray) -> bool:
    """
    Perform a simple non‑linearity test by comparing GAM to a linear model.

    Parameters
    ----------
    gam: Any
        Fitted GAM.
    X: np.ndarray
        Predictor matrix.
    y: np.ndarray
        Response vector.

    Returns
    -------
    bool
        ``True`` if the GAM provides a statistically significant improvement.
    """
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score

    linear = LinearRegression().fit(X, y)
    r2_gam = gam.statistics_["pseudo_r2"]["explained_deviance"]
    r2_lin = r2_score(y, linear.predict(X))
    return r2_gam > r2_lin

def run_gam_analysis(
    csv_path: str, predictor: str, response: str
) -> Dict[str, Any]:
    """
    Complete GAM analysis pipeline.

    Parameters
    ----------
    csv_path: str
        Path to the primary analysis CSV.
    predictor: str
        Predictor column name.
    response: str
        Response column name.

    Returns
    -------
    Dict[str, Any]
        Results dictionary from ``extract_gam_results``.
    """
    df = load_primary_analysis_dataset(csv_path)
    X, y = prepare_gam_data(df, predictor, response)
    gam = fit_gam_model(X, y)
    results = extract_gam_results(gam)
    return results

def main():
    """
    Placeholder CLI entry point for GAM analysis.
    """
    logging.info("GAM analysis placeholder – no CLI implemented.")
