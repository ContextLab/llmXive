from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

@dataclass
class RegressionMetrics:
    r_squared: float
    aic: float
    bic: float
    mae: float

@dataclass
class LinearModelResult:
    coefficients: List[float]
    intercept: float
    metrics: RegressionMetrics

@dataclass
class ResidualEntry:
    index: int
    residual: float
    family: str

def fit_linear_model(
    data: Any,
    response: str,
    predictors: List[str],
    *,
    add_constant: bool = True,
) -> LinearModelResult: ...

def fit_polynomial_model(
    data: Any,
    response: str,
    predictors: List[str],
    degree: int,
    *,
    add_constant: bool = True,
) -> LinearModelResult: ...

def fit_logarithmic_model(
    data: Any,
    response: str,
    predictors: List[str],
    *,
    add_constant: bool = True,
) -> LinearModelResult: ...

def identify_residual_families(
    residuals: List[float],
    *,
    threshold: float = 2.0,
) -> List[ResidualEntry]: ...

def write_regression_metrics_report(
    metrics: RegressionMetrics,
    output_path: str,
) -> None: ...

def write_residual_analysis_report(
    residuals: List[ResidualEntry],
    output_path: str,
) -> None: ...

def main() -> None: ...
