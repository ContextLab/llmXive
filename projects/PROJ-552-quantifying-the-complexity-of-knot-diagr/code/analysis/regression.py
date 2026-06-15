"""
Regression analysis module for knot complexity research.

Implements regression models, correlation analysis, and effect size calculations
for studying relationships between knot invariants.

Per FR-006 and Constitution Principle VII: p-values are NOT reported for census
data and are marked as 'not applicable for census data' in all output artifacts.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class RegressionMetrics:
    """Container for regression model metrics."""
    r_squared: float
    aic: float
    bic: float
    mae: float
    rmse: float
    n_samples: int
    n_parameters: int


@dataclass
class RegressionResult:
    """Container for regression model fitting results."""
    model_type: str
    coefficients: Dict[str, float]
    metrics: RegressionMetrics
    predictions: np.ndarray
    residuals: np.ndarray


@dataclass
class CorrelationResult:
    """Container for correlation analysis results.
    
    Per FR-006 and Constitution Principle VII: p-values are marked as
    'not applicable for census data' for census datasets.
    """
    correlation_type: str  # 'pearson' or 'spearman'
    coefficient: float
    p_value: str  # 'not applicable for census data' for census data
    effect_size_r: float
    interpretation: str


@dataclass
class EffectSizeResult:
    """Container for effect size calculations."""
    effect_type: str  # 'cohen_d' or 'correlation_r'
    value: float
    interpretation: str  # 'small', 'medium', 'large' per Cohen's conventions
    group1_mean: Optional[float] = None
    group2_mean: Optional[float] = None
    group1_std: Optional[float] = None
    group2_std: Optional[float] = None
    n1: Optional[int] = None
    n2: Optional[int] = None


@dataclass
class RegressionAnalysisReport:
    """Container for comprehensive regression analysis report."""
    timestamp: str
    models: List[RegressionResult]
    correlations: List[CorrelationResult]
    effect_sizes: List[EffectSizeResult]
    summary: Dict[str, Any]

# ============================================================================
# REGRESSION MODEL FUNCTIONS
# ============================================================================

def calculate_r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate R-squared (coefficient of determination).
    
    Args:
        y_true: Actual values
        y_pred: Predicted values
        
    Returns:
        R-squared value between 0 and 1
    """
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return 1 - (ss_res / ss_tot)


def calculate_aic(n: int, k: int, rss: float) -> float:
    """Calculate Akaike Information Criterion.
    
    Args:
        n: Number of samples
        k: Number of parameters
        rss: Residual sum of squares
        
    Returns:
        AIC value (lower is better)
    """
    if rss == 0:
        return float('inf')
    return n * np.log(rss / n) + 2 * k


def calculate_bic(n: int, k: int, rss: float) -> float:
    """Calculate Bayesian Information Criterion.
    
    Args:
        n: Number of samples
        k: Number of parameters
        rss: Residual sum of squares
        
    Returns:
        BIC value (lower is better)
    """
    if rss == 0:
        return float('inf')
    return n * np.log(rss / n) + k * np.log(n)


def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Mean Absolute Error.
    
    Args:
        y_true: Actual values
        y_pred: Predicted values
        
    Returns:
        MAE value
    """
    return np.mean(np.abs(y_true - y_pred))


def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Root Mean Squared Error.
    
    Args:
        y_true: Actual values
        y_pred: Predicted values
        
    Returns:
        RMSE value
    """
    return np.sqrt(np.mean((y_true - y_pred) ** 2))

# ============================================================================
# CORRELATION FUNCTIONS (T036)
# ============================================================================

def calculate_pearson_correlation(
    x: np.ndarray, 
    y: np.ndarray,
    is_census_data: bool = True
) -> CorrelationResult:
    """Calculate Pearson correlation coefficient.
    
    Args:
        x: First variable array
        y: Second variable array
        is_census_data: Whether this is census data (default True for knot census)
        
    Returns:
        CorrelationResult with coefficient and effect size
        
    Note: Per FR-006 and Constitution Principle VII, p-values are NOT reported
    for census data and are marked as 'not applicable for census data'.
    """
    if len(x) != len(y) or len(x) == 0:
        return CorrelationResult(
            correlation_type='pearson',
            coefficient=0.0,
            p_value='not applicable for census data',
            effect_size_r=0.0,
            interpretation='insufficient data'
        )
    
    # Remove NaN values
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        return CorrelationResult(
            correlation_type='pearson',
            coefficient=0.0,
            p_value='not applicable for census data',
            effect_size_r=0.0,
            interpretation='insufficient data'
        )
    
    # Calculate Pearson correlation
    correlation = np.corrcoef(x_clean, y_clean)[0, 1]
    if np.isnan(correlation):
        correlation = 0.0
    
    # Calculate effect size r (same as correlation coefficient for Pearson)
    effect_size_r = abs(correlation)
    
    # Interpret effect size per Cohen's conventions
    interpretation = interpret_correlation_effect_size(effect_size_r)
    
    # Per FR-006 and Constitution Principle VII: p-values NOT reported for census data
    p_value = 'not applicable for census data'
    
    return CorrelationResult(
        correlation_type='pearson',
        coefficient=float(correlation),
        p_value=p_value,
        effect_size_r=float(effect_size_r),
        interpretation=interpretation
    )


def calculate_spearman_correlation(
    x: np.ndarray, 
    y: np.ndarray,
    is_census_data: bool = True
) -> CorrelationResult:
    """Calculate Spearman rank correlation coefficient.
    
    Args:
        x: First variable array
        y: Second variable array
        is_census_data: Whether this is census data (default True for knot census)
        
    Returns:
        CorrelationResult with coefficient and effect size
        
    Note: Per FR-006 and Constitution Principle VII, p-values are NOT reported
    for census data and are marked as 'not applicable for census data'.
    """
    if len(x) != len(y) or len(x) == 0:
        return CorrelationResult(
            correlation_type='spearman',
            coefficient=0.0,
            p_value='not applicable for census data',
            effect_size_r=0.0,
            interpretation='insufficient data'
        )
    
    # Remove NaN values
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        return CorrelationResult(
            correlation_type='spearman',
            coefficient=0.0,
            p_value='not applicable for census data',
            effect_size_r=0.0,
            interpretation='insufficient data'
        )
    
    # Calculate Spearman correlation using rank data
    x_rank = pd.Series(x_clean).rank(method='average').values
    y_rank = pd.Series(y_clean).rank(method='average').values
    
    correlation = np.corrcoef(x_rank, y_rank)[0, 1]
    if np.isnan(correlation):
        correlation = 0.0
    
    # Calculate effect size r (same as correlation coefficient for Spearman)
    effect_size_r = abs(correlation)
    
    # Interpret effect size per Cohen's conventions
    interpretation = interpret_correlation_effect_size(effect_size_r)
    
    # Per FR-006 and Constitution Principle VII: p-values NOT reported for census data
    p_value = 'not applicable for census data'
    
    return CorrelationResult(
        correlation_type='spearman',
        coefficient=float(correlation),
        p_value=p_value,
        effect_size_r=float(effect_size_r),
        interpretation=interpretation
    )

# ============================================================================
# EFFECT SIZE FUNCTIONS (T036)
# ============================================================================

def calculate_cohen_d(
    group1: np.ndarray,
    group2: np.ndarray
) -> EffectSizeResult:
    """Calculate Cohen's d effect size for two groups.
    
    Args:
        group1: First group data
        group2: Second group data
        
    Returns:
        EffectSizeResult with Cohen's d value and interpretation
        
    Cohen's d interpretation:
        |d| < 0.2: negligible
        0.2 <= |d| < 0.5: small
        0.5 <= |d| < 0.8: medium
        |d| >= 0.8: large
    """
    # Remove NaN values
    g1 = group1[~np.isnan(group1)]
    g2 = group2[~np.isnan(group2)]
    
    if len(g1) < 2 or len(g2) < 2:
        return EffectSizeResult(
            effect_type='cohen_d',
            value=0.0,
            interpretation='insufficient data',
            group1_mean=np.nan if len(g1) == 0 else float(np.mean(g1)),
            group2_mean=np.nan if len(g2) == 0 else float(np.mean(g2)),
            group1_std=np.nan if len(g1) < 2 else float(np.std(g1, ddof=1)),
            group2_std=np.nan if len(g2) < 2 else float(np.std(g2, ddof=1)),
            n1=len(g1),
            n2=len(g2)
        )
    
    # Calculate means and pooled standard deviation
    mean1 = np.mean(g1)
    mean2 = np.mean(g2)
    std1 = np.std(g1, ddof=1)
    std2 = np.std(g2, ddof=1)
    
    # Pooled standard deviation
    n1, n2 = len(g1), len(g2)
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        cohens_d = 0.0
    else:
        cohens_d = (mean1 - mean2) / pooled_std
    
    # Interpret effect size
    interpretation = interpret_cohen_d(abs(cohens_d))
    
    return EffectSizeResult(
        effect_type='cohen_d',
        value=float(cohens_d),
        interpretation=interpretation,
        group1_mean=float(mean1),
        group2_mean=float(mean2),
        group1_std=float(std1),
        group2_std=float(std2),
        n1=n1,
        n2=n2
    )


def calculate_correlation_effect_size(r: float) -> EffectSizeResult:
    """Calculate effect size interpretation for correlation coefficient.
    
    Args:
        r: Correlation coefficient value
        
    Returns:
        EffectSizeResult with interpretation
        
    Cohen's conventions for correlation r:
        |r| < 0.1: negligible
        0.1 <= |r| < 0.3: small
        0.3 <= |r| < 0.5: medium
        |r| >= 0.5: large
    """
    abs_r = abs(r)
    interpretation = interpret_correlation_effect_size(abs_r)
    
    return EffectSizeResult(
        effect_type='correlation_r',
        value=float(r),
        interpretation=interpretation
    )

# ============================================================================
# INTERPRETATION FUNCTIONS
# ============================================================================

def interpret_cohen_d(abs_d: float) -> str:
    """Interpret Cohen's d effect size magnitude.
    
    Args:
        abs_d: Absolute value of Cohen's d
        
    Returns:
        Interpretation string
    """
    if abs_d < 0.2:
        return 'negligible'
    elif abs_d < 0.5:
        return 'small'
    elif abs_d < 0.8:
        return 'medium'
    else:
        return 'large'


def interpret_correlation_effect_size(abs_r: float) -> str:
    """Interpret correlation coefficient effect size magnitude.
    
    Args:
        abs_r: Absolute value of correlation coefficient
        
    Returns:
        Interpretation string
    """
    if abs_r < 0.1:
        return 'negligible'
    elif abs_r < 0.3:
        return 'small'
    elif abs_r < 0.5:
        return 'medium'
    else:
        return 'large'

# ============================================================================
# REGRESSION MODEL FITTING (existing functions preserved)
# ============================================================================

def fit_linear_model(x: np.ndarray, y: np.ndarray) -> RegressionResult:
    """Fit a simple linear regression model.
    
    Args:
        x: Independent variable
        y: Dependent variable
        
    Returns:
        RegressionResult with model parameters and metrics
    """
    # Remove NaN values
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        return RegressionResult(
            model_type='linear',
            coefficients={'intercept': 0.0, 'slope': 0.0},
            metrics=RegressionMetrics(
                r_squared=0.0, aic=0.0, bic=0.0, mae=0.0, rmse=0.0,
                n_samples=0, n_parameters=2
            ),
            predictions=np.array([]),
            residuals=np.array([])
        )
    
    # Fit linear model
    slope, intercept = np.polyfit(x_clean, y_clean, 1)
    predictions = slope * x_clean + intercept
    residuals = y_clean - predictions
    
    # Calculate metrics
    r_squared = calculate_r_squared(y_clean, predictions)
    rss = np.sum(residuals ** 2)
    n = len(x_clean)
    k = 2  # intercept + slope
    
    aic = calculate_aic(n, k, rss)
    bic = calculate_bic(n, k, rss)
    mae = calculate_mae(y_clean, predictions)
    rmse = calculate_rmse(y_clean, predictions)
    
    return RegressionResult(
        model_type='linear',
        coefficients={'intercept': float(intercept), 'slope': float(slope)},
        metrics=RegressionMetrics(
            r_squared=float(r_squared),
            aic=float(aic),
            bic=float(bic),
            mae=float(mae),
            rmse=float(rmse),
            n_samples=n,
            n_parameters=k
        ),
        predictions=predictions,
        residuals=residuals
    )


def fit_polynomial_model(x: np.ndarray, y: np.ndarray, degree: int = 2) -> RegressionResult:
    """Fit a polynomial regression model.
    
    Args:
        x: Independent variable
        y: Dependent variable
        degree: Polynomial degree
        
    Returns:
        RegressionResult with model parameters and metrics
    """
    # Remove NaN values
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < degree + 1:
        return RegressionResult(
            model_type=f'polynomial_degree_{degree}',
            coefficients={},
            metrics=RegressionMetrics(
                r_squared=0.0, aic=0.0, bic=0.0, mae=0.0, rmse=0.0,
                n_samples=0, n_parameters=degree + 1
            ),
            predictions=np.array([]),
            residuals=np.array([])
        )
    
    # Fit polynomial model
    coefficients = np.polyfit(x_clean, y_clean, degree)
    predictions = np.polyval(coefficients, x_clean)
    residuals = y_clean - predictions
    
    # Calculate metrics
    r_squared = calculate_r_squared(y_clean, predictions)
    rss = np.sum(residuals ** 2)
    n = len(x_clean)
    k = degree + 1
    
    aic = calculate_aic(n, k, rss)
    bic = calculate_bic(n, k, rss)
    mae = calculate_mae(y_clean, predictions)
    rmse = calculate_rmse(y_clean, predictions)
    
    coef_dict = {f'coeff_{i}': float(coeff) for i, coeff in enumerate(coefficients)}
    
    return RegressionResult(
        model_type=f'polynomial_degree_{degree}',
        coefficients=coef_dict,
        metrics=RegressionMetrics(
            r_squared=float(r_squared),
            aic=float(aic),
            bic=float(bic),
            mae=float(mae),
            rmse=float(rmse),
            n_samples=n,
            n_parameters=k
        ),
        predictions=predictions,
        residuals=residuals
    )


def fit_logarithmic_model(x: np.ndarray, y: np.ndarray) -> RegressionResult:
    """Fit a logarithmic regression model (y = a + b * log(x)).
    
    Args:
        x: Independent variable (must be positive)
        y: Dependent variable
        
    Returns:
        RegressionResult with model parameters and metrics
    """
    # Remove NaN and non-positive x values
    mask = ~(np.isnan(x) | np.isnan(y) | (x <= 0))
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        return RegressionResult(
            model_type='logarithmic',
            coefficients={'intercept': 0.0, 'log_coeff': 0.0},
            metrics=RegressionMetrics(
                r_squared=0.0, aic=0.0, bic=0.0, mae=0.0, rmse=0.0,
                n_samples=0, n_parameters=2
            ),
            predictions=np.array([]),
            residuals=np.array([])
        )
    
    # Transform x to log scale
    log_x = np.log(x_clean)
    
    # Fit linear model on log-transformed x
    slope, intercept = np.polyfit(log_x, y_clean, 1)
    predictions = slope * log_x + intercept
    residuals = y_clean - predictions
    
    # Calculate metrics
    r_squared = calculate_r_squared(y_clean, predictions)
    rss = np.sum(residuals ** 2)
    n = len(x_clean)
    k = 2
    
    aic = calculate_aic(n, k, rss)
    bic = calculate_bic(n, k, rss)
    mae = calculate_mae(y_clean, predictions)
    rmse = calculate_rmse(y_clean, predictions)
    
    return RegressionResult(
        model_type='logarithmic',
        coefficients={'intercept': float(intercept), 'log_coeff': float(slope)},
        metrics=RegressionMetrics(
            r_squared=float(r_squared),
            aic=float(aic),
            bic=float(bic),
            mae=float(mae),
            rmse=float(rmse),
            n_samples=n,
            n_parameters=k
        ),
        predictions=predictions,
        residuals=residuals
    )

# ============================================================================
# COMPREHENSIVE ANALYSIS FUNCTIONS
# ============================================================================

def compute_goodness_of_fit(result: RegressionResult) -> Dict[str, float]:
    """Compute goodness-of-fit metrics summary.
    
    Args:
        result: RegressionResult object
        
    Returns:
        Dictionary of metric names to values
    """
    return {
        'r_squared': result.metrics.r_squared,
        'aic': result.metrics.aic,
        'bic': result.metrics.bic,
        'mae': result.metrics.mae,
        'rmse': result.metrics.rmse,
        'n_samples': result.metrics.n_samples
    }


def fit_regression_models(
    x: np.ndarray,
    y: np.ndarray,
    model_types: List[str] = None
) -> List[RegressionResult]:
    """Fit multiple regression models and return results.
    
    Args:
        x: Independent variable
        y: Dependent variable
        model_types: List of model types to fit ('linear', 'polynomial', 'logarithmic')
        
    Returns:
        List of RegressionResult objects
    """
    if model_types is None:
        model_types = ['linear', 'polynomial', 'logarithmic']
    
    results = []
    
    if 'linear' in model_types:
        results.append(fit_linear_model(x, y))
    
    if 'polynomial' in model_types:
        results.append(fit_polynomial_model(x, y, degree=2))
    
    if 'logarithmic' in model_types:
        results.append(fit_logarithmic_model(x, y))
    
    return results


def run_regression_analysis(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
    model_types: List[str] = None,
    is_census_data: bool = True
) -> RegressionAnalysisReport:
    """Run comprehensive regression analysis including correlations and effect sizes.
    
    Args:
        df: DataFrame containing knot data
        x_column: Name of independent variable column
        y_column: Name of dependent variable column
        model_types: List of regression model types to fit
        is_census_data: Whether this is census data (default True)
        
    Returns:
        RegressionAnalysisReport with all results
        
    Note: Per FR-006 and Constitution Principle VII, p-values are marked as
    'not applicable for census data' for census datasets.
    """
    x = df[x_column].values
    y = df[y_column].values
    
    # Fit regression models
    regression_results = fit_regression_models(x, y, model_types)
    
    # Calculate Pearson correlation
    pearson_result = calculate_pearson_correlation(x, y, is_census_data)
    
    # Calculate Spearman correlation
    spearman_result = calculate_spearman_correlation(x, y, is_census_data)
    
    # Calculate effect sizes
    effect_sizes = [
        calculate_correlation_effect_size(pearson_result.coefficient),
        calculate_correlation_effect_size(spearman_result.coefficient)
    ]
    
    # Add Cohen's d for alternating vs non-alternating comparison if applicable
    if 'is_alternating' in df.columns:
        alt_knots = df[df['is_alternating'] == True][y_column].values
        non_alt_knots = df[df['is_alternating'] == False][y_column].values
        
        if len(alt_knots) >= 2 and len(non_alt_knots) >= 2:
            cohen_d_result = calculate_cohen_d(alt_knots, non_alt_knots)
            effect_sizes.append(cohen_d_result)
    
    # Build summary
    best_model = min(regression_results, key=lambda r: r.metrics.aic) if regression_results else None
    
    summary = {
        'n_samples': len(x),
        'n_models': len(regression_results),
        'best_model': best_model.model_type if best_model else None,
        'best_aic': best_model.metrics.aic if best_model else None,
        'pearson_correlation': pearson_result.coefficient,
        'spearman_correlation': spearman_result.coefficient,
        'p_value_status': 'not applicable for census data'
    }
    
    return RegressionAnalysisReport(
        timestamp=datetime.now().isoformat(),
        models=regression_results,
        correlations=[pearson_result, spearman_result],
        effect_sizes=effect_sizes,
        summary=summary
    )

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for regression analysis module."""
    import sys
    
    # Example usage demonstration
    print("Regression Analysis Module for Knot Complexity Research")
    print("=" * 60)
    print()
    print("Available functions:")
    print("  - calculate_pearson_correlation(x, y, is_census_data=True)")
    print("  - calculate_spearman_correlation(x, y, is_census_data=True)")
    print("  - calculate_cohen_d(group1, group2)")
    print("  - calculate_correlation_effect_size(r)")
    print("  - fit_regression_models(x, y, model_types)")
    print("  - run_regression_analysis(df, x_column, y_column)")
    print()
    print("Note: Per FR-006 and Constitution Principle VII, p-values are")
    print("marked as 'not applicable for census data' for census datasets.")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())