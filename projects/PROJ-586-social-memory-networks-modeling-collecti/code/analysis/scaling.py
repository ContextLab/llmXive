"""Scaling analysis utilities."""
from __future__ import annotations

import pathlib
import warnings
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

def power_law(x: float, a: float, b: float) -> float:
    return a * (x ** b)

def fit_power_law(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Fit y = a * x^b using log-log linear regression."""
    if len(x) < 2 or len(y) < 2:
        raise ValueError("Need at least 2 points to fit a power law.")
    mask = (x > 0) & (y > 0)
    if not np.any(mask):
        raise ValueError("Cannot fit power law: no positive data points.")
    log_x = np.log(x[mask])
    log_y = np.log(y[mask])
    coeffs = np.polyfit(log_x, log_y, 1)
    b = coeffs[0]
    a = np.exp(coeffs[1])
    return float(a), float(b)

def fit_power_law_with_ci(x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float, float]:
    a, b = fit_power_law(x, y)
    # Simple CI estimation (mock for now, would use statsmodels in full impl)
    return a, b, 0.95, 0.95

def load_scaling_data(path: pathlib.Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Scaling data not found: {path}")
    return pd.read_csv(path)

def generate_scaling_plot(df: pd.DataFrame, output_path: pathlib.Path):
    # Deprecated: use scaling_plot_generator
    pass
