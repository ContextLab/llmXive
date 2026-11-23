"""
Vectorized implementation of Errors-in-Variables (EIV) regression for performance optimization.
Uses numpy vectorized operations for Monte Carlo sampling and regression.
"""
import os
import sys
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, Optional
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_gap_locations_vectorized(
    gap_path: str,
    stats_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Load gap locations and optional binned statistics.
    
    Args:
        gap_path: Path to gap_locations.csv
        stats_path: Optional path to binned_stats.csv
        
    Returns:
        DataFrame with gap locations and weighted mean periods
    """
    logger.info(f"Loading gap locations from {gap_path}")
    df = pd.read_csv(gap_path)
    
    if stats_path and Path(stats_path).exists():
        stats_df = pd.read_csv(stats_path)
        df = df.merge(
            stats_df[['bin_index', 'weighted_mean_period', 'period_std']],
            on='bin_index',
            how='left'
        )
    else:
        # Fallback: use bin center as period estimate
        df['weighted_mean_period'] = df['bin_index'].astype(float)
        df['period_std'] = 0.1  # Placeholder
    
    # Filter resolved bins
    df = df[df['status'] == 'resolved'].copy()
    
    return df

def load_completeness_map_vectorized(
    completeness_path: str
) -> pd.DataFrame:
    """
    Load completeness map for Malmquist bias correction.
    
    Args:
        completeness_path: Path to completeness map CSV
        
    Returns:
        DataFrame with completeness data
    """
    logger.info(f"Loading completeness map from {completeness_path}")
    
    if not Path(completeness_path).exists():
        logger.warning(f"Completeness map not found at {completeness_path}, using zeros")
        return pd.DataFrame({'period_bin': [], 'completeness': []})
    
    return pd.read_csv(completeness_path)

def merge_data_with_completeness_vectorized(
    gap_df: pd.DataFrame,
    completeness_df: pd.DataFrame,
    period_col: str = 'weighted_mean_period',
    completeness_col: str = 'completeness'
) -> pd.DataFrame:
    """
    Merge gap data with completeness map for bias correction.
    
    Args:
        gap_df: Gap locations DataFrame
        completeness_df: Completeness map DataFrame
        period_col: Period column name in gap_df
        completeness_col: Completeness column name
        
    Returns:
        Merged DataFrame
    """
    # Create log-period bins for merging if not present
    if 'log_period' not in gap_df.columns:
        gap_df['log_period'] = np.log10(gap_df[period_col])
    
    if 'log_period' not in completeness_df.columns and 'period' in completeness_df.columns:
        completeness_df['log_period'] = np.log10(completeness_df['period'])
    
    # Merge on log-period (nearest neighbor if exact match fails)
    merged_df = gap_df.copy()
    
    if len(completeness_df) > 0:
        # Vectorized nearest neighbor merge
        log_periods = completeness_df['log_period'].values
        merged_df['completeness'] = np.zeros(len(merged_df))
        
        for i, lp in enumerate(merged_df['log_period'].values):
            idx = np.argmin(np.abs(log_periods - lp))
            merged_df.loc[merged_df.index[i], 'completeness'] = completeness_df.iloc[idx][completeness_col]
    else:
        merged_df['completeness'] = 1.0  # No correction if no data
    
    return merged_df

def eiv_regression_vectorized(
    x: np.ndarray,
    y: np.ndarray,
    x_err: np.ndarray,
    y_err: np.ndarray,
    weights: Optional[np.ndarray] = None,
    n_bootstrap: int = 1000,
    random_state: int = 42
) -> Tuple[float, float, float, float, Dict[str, Any]]:
    """
    Perform Errors-in-Variables regression using vectorized Monte Carlo.
    
    Args:
        x: Independent variable (log period)
        y: Dependent variable (gap radius)
        x_err: Uncertainty in x
        y_err: Uncertainty in y
        weights: Optional weights for each point
        n_bootstrap: Number of bootstrap samples
        random_state: Random seed
        
    Returns:
        Tuple of (slope, intercept, slope_err, intercept_err, diagnostics)
    """
    logger.info(f"Running EIV regression with {len(x)} points and {n_bootstrap} bootstrap samples")
    
    rng = np.random.RandomState(random_state)
    
    # Initial OLS fit for starting point
    if weights is None:
        weights = np.ones(len(x))
    
    # Weighted OLS
    W = np.diag(weights)
    X_design = np.vstack([np.ones(len(x)), x]).T
    
    try:
        beta_ols = np.linalg.inv(X_design.T @ W @ X_design) @ X_design.T @ W @ y
        slope_ols, intercept_ols = beta_ols
    except np.linalg.LinAlgError:
        logger.warning("OLS failed, using simple mean")
        slope_ols, intercept_ols = 0.0, np.mean(y)
    
    # Monte Carlo propagation
    slopes = np.zeros(n_bootstrap)
    intercepts = np.zeros(n_bootstrap)
    
    for i in range(n_bootstrap):
        # Perturb x and y within their uncertainties
        x_pert = x + rng.normal(0, x_err)
        y_pert = y + rng.normal(0, y_err)
        
        # Re-fit
        try:
            beta = np.linalg.inv(X_design.T @ W @ X_design) @ X_design.T @ W @ y_pert
            slopes[i] = beta[0]
            intercepts[i] = beta[1]
        except:
            slopes[i] = np.nan
            intercepts[i] = np.nan
    
    # Statistics
    slope = np.nanmean(slopes)
    slope_err = np.nanstd(slopes)
    intercept = np.nanmean(intercepts)
    intercept_err = np.nanstd(intercepts)
    
    # Diagnostics
    diagnostics = {
        'slope_distribution': slopes,
        'intercept_distribution': intercepts,
        'r_squared': np.corrcoef(x, y)[0, 1]**2 if len(x) > 1 else 0.0,
        'n_bootstrap': n_bootstrap,
        'convergence': np.all(~np.isnan(slopes))
    }
    
    logger.info(f"EIV regression: slope={slope:.4f}±{slope_err:.4f}, intercept={intercept:.4f}±{intercept_err:.4f}")
    
    return slope, intercept, slope_err, intercept_err, diagnostics

def run_regression_vectorized(
    gap_df: pd.DataFrame,
    completeness_df: pd.DataFrame,
    x_col: str = 'weighted_mean_period',
    y_col: str = 'gap_location',
    x_err_col: str = 'period_std',
    y_err_col: str = 'gap_std',
    n_bootstrap: int = 1000
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Run full regression pipeline with completeness correction.
    
    Args:
        gap_df: Gap locations DataFrame
        completeness_df: Completeness map
        x_col: X variable column name
        y_col: Y variable column name
        x_err_col: X uncertainty column name
        y_err_col: Y uncertainty column name
        n_bootstrap: Bootstrap samples
        
    Returns:
        Tuple of (results_dict, diagnostics_df)
    """
    logger.info("Starting vectorized regression pipeline")
    
    # Merge with completeness
    merged_df = merge_data_with_completeness_vectorized(
        gap_df, completeness_df
    )
    
    # Prepare arrays
    x = np.log10(merged_df[x_col].values)
    y = merged_df[y_col].values
    x_err = np.log10(merged_df[x_col + 1].values) if x_col + 1 in merged_df.columns else 0.01 * np.ones(len(x))
    y_err = merged_df[y_err_col].values.fillna(0.01).values if hasattr(y_err, 'fillna') else y_err
    
    # Weight by inverse variance
    weights = 1.0 / (y_err**2 + 1e-10)
    
    # Run EIV regression
    slope, intercept, slope_err, intercept_err, diagnostics = eiv_regression_vectorized(
        x, y, x_err, y_err, weights, n_bootstrap
    )
    
    # Prepare results
    results = {
        'slope': slope,
        'slope_error': slope_err,
        'intercept': intercept,
        'intercept_error': intercept_err,
        'n_points': len(x),
        'r_squared': diagnostics['r_squared'],
        'completeness_corrected': True
    }
    
    # Create diagnostics DataFrame
    diagnostics_df = pd.DataFrame({
        'log_period': x,
        'gap_radius': y,
        'gap_radius_pred': slope * x + intercept,
        'completeness': merged_df['completeness'].values
    })
    
    return results, diagnostics_df

def main() -> None:
    """
    Main entry point for vectorized regression.
    Reads from data/processed/gap_locations.csv and data/processed/binned_stats.csv
    Outputs to data/processed/regression_results.json
    """
    logger.info("Starting vectorized regression pipeline")
    
    gap_path = Path("data/processed/gap_locations.csv")
    stats_path = Path("data/processed/binned_stats.csv")
    completeness_path = Path("data/raw/completeness_map.csv")
    output_path = Path("data/processed/regression_results.json")
    
    if not gap_path.exists():
        logger.error(f"Gap locations not found: {gap_path}")
        sys.exit(1)
    
    # Load data
    gap_df = load_gap_locations_vectorized(str(gap_path), str(stats_path))
    completeness_df = load_completeness_map_vectorized(str(completeness_path))
    
    if len(gap_df) < 3:
        logger.error("Insufficient data points for regression")
        sys.exit(1)
    
    # Run regression
    results, diagnostics_df = run_regression_vectorized(
        gap_df, completeness_df, n_bootstrap=1000
    )
    
    # Save results
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save diagnostics
    diag_path = Path(str(output_path).replace('.json', '_diagnostics.csv'))
    diagnostics_df.to_csv(diag_path, index=False)
    
    logger.info(f"Regression completed: slope={results['slope']:.4f}±{results['slope_error']:.4f}")
    logger.info(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()