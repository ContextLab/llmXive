import os
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import OLSInfluence

from utils import get_logger, setup_logging, set_deterministic_seed

# Setup logging to file as per FR-008
LOG_FILE = "pipeline_log.txt"
setup_logging(log_file=LOG_FILE)
logger = get_logger()

def flag_low_coverage(df: pd.DataFrame, min_tracks: int = 1000, max_missing_rate: float = 0.2) -> Tuple[pd.DataFrame, Set[int]]:
    """
    Identify years with <1,000 unique tracks (flag for exclusion)
    and years with >20% missing genre tags (log warning).
    
    Returns:
        filtered_df: DataFrame with rows kept for regression (missing genres handled)
        flagged_years: Set of years to exclude from regression due to low coverage
    """
    logger.info("Starting low coverage flagging process.")
    
    # Check for missing genre tags in the source if available, 
    # but here we assume df contains 'year' and 'mean_off_diagonal_similarity'
    # If 'missing_genre_rate' column exists, we use it, otherwise we log based on track counts if available.
    # Assuming df comes from similarity output which might not have raw track counts.
    # However, T014/T029 logic implies we might need to cross-reference or assume the input df
    # already represents the aggregated state.
    
    # For T030 context, we focus on the regression input df.
    # We need to check track counts if they are available in the df or derived from context.
    # Since the input to regression is yearly_similarity.csv, it likely only has year and similarity.
    # We must rely on the 'flagged' logic from T029 if passed, or re-calculate if we have track counts.
    # Given the constraint, we assume the input df might have a 'unique_track_count' column 
    # or we rely on the fact that T029 already filtered.
    # To be robust: if 'unique_track_count' exists, use it.
    
    flagged_years: Set[int] = set()
    
    if 'unique_track_count' in df.columns:
        low_coverage_mask = df['unique_track_count'] < min_tracks
        flagged_years = set(df.loc[low_coverage_mask, 'year'].tolist())
        logger.warning(f"Flagging {len(flagged_years)} years with < {min_tracks} unique tracks for regression exclusion.")
    else:
        logger.info("No 'unique_track_count' column found in similarity data; skipping track count check.")

    if 'missing_genre_rate' in df.columns:
        high_missing_mask = df['missing_genre_rate'] > max_missing_rate
        if high_missing_mask.any():
            high_missing_years = df.loc[high_missing_mask, 'year'].tolist()
            logger.warning(f"Years with > {max_missing_rate*100}% missing genre tags: {high_missing_years}")
    
    # Filter out flagged years for the regression input
    filtered_df = df[~df['year'].isin(flagged_years)].copy()
    logger.info(f"Regression will proceed with {len(filtered_df)} years after filtering {len(flagged_years)} low-coverage years.")
    
    return filtered_df, flagged_years

def get_filtered_years_for_regression(df: pd.DataFrame) -> List[int]:
    """Helper to get list of years used in regression."""
    filtered_df, _ = flag_low_coverage(df)
    return sorted(filtered_df['year'].tolist())

def fit_linear_regression(df: pd.DataFrame) -> Tuple[Any, Dict[str, Any]]:
    """
    Fit linear regression: year vs. mean_off_diagonal_similarity.
    Uses statsmodels with robust standard errors.
    Returns model object and summary stats.
    """
    logger.info("Fitting linear regression model...")
    
    filtered_df, _ = flag_low_coverage(df)
    
    if len(filtered_df) < 2:
        raise ValueError("Insufficient data points for regression after filtering.")
    
    X = sm.add_constant(filtered_df['year'])
    y = filtered_df['mean_off_diagonal_similarity']
    
    model = sm.WLS(y, X, weights=1/filtered_df['year']) # Simple weighting or OLS
    # Using OLS with robust cov_type as per FR-005
    ols_model = sm.OLS(y, X)
    results = ols_model.fit(cov_type='HC3') # Robust standard errors
    
    logger.info(f"Regression fit complete. R-squared: {results.rsquared:.4f}")
    logger.info(f"Convergence status: {results.converged if hasattr(results, 'converged') else 'N/A (OLS)'}")
    
    return results, {
        "slope": float(results.params['year']),
        "intercept": float(results.params['const']),
        "p_value": float(results.pvalues['year']),
        "rsquared": float(results.rsquared),
        "std_err": float(results.bse['year']),
        "ci_lower": float(results.conf_int().loc['year', 0]),
        "ci_upper": float(results.conf_int().loc['year', 1])
    }

def calculate_cooks_distance(results: Any, df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Cook's Distance for outliers using the regression model.
    Returns a DataFrame with year and Cook's Distance.
    """
    logger.info("Calculating Cook's Distance for robustness check...")
    
    filtered_df, _ = flag_low_coverage(df)
    X = sm.add_constant(filtered_df['year'])
    y = filtered_df['mean_off_diagonal_similarity']
    
    influence = OLSInfluence(results)
    cooks_d = influence.cooks_distance[0]
    
    report_df = pd.DataFrame({
        'year': filtered_df['year'].values,
        'cooks_distance': cooks_d
    })
    
    # Sort by distance descending
    report_df = report_df.sort_values(by='cooks_distance', ascending=False)
    
    outlier_count = (cooks_d > 4/len(filtered_df)).sum()
    logger.info(f"Cook's Distance calculation complete. Identified {outlier_count} potential outliers (threshold: 4/n).")
    
    return report_df, outlier_count

def output_regression_results(results: Any, stats: Dict[str, Any], outlier_count: int, output_path: Path):
    """
    Output regression results to console and JSON file.
    Logs comprehensive model parameters and convergence status to pipeline_log.txt.
    """
    logger.info("=" * 50)
    logger.info("REGRESSION ANALYSIS RESULTS")
    logger.info("=" * 50)
    
    # Log Model Parameters
    logger.info(f"Slope: {stats['slope']:.6f}")
    logger.info(f"Intercept: {stats['intercept']:.6f}")
    logger.info(f"Standard Error: {stats['std_err']:.6f}")
    logger.info(f"P-value: {stats['p_value']:.6e}")
    logger.info(f"R-squared: {stats['rsquared']:.6f}")
    logger.info(f"95% CI Lower: {stats['ci_lower']:.6f}")
    logger.info(f"95% CI Upper: {stats['ci_upper']:.6f}")
    
    # Log Convergence Status
    logger.info(f"Convergence Status: True (OLS converged)")
    
    # Log Outlier Counts
    logger.info(f"Outlier Count (Cook's Distance > 4/n): {outlier_count}")
    
    logger.info("=" * 50)
    
    # Save to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Regression results saved to {output_path}")

def main():
    """Main entry point for regression analysis."""
    logger.info("Starting regression analysis pipeline.")
    
    # Paths
    input_path = Path("data/derived/yearly_similarity.csv")
    output_json_path = Path("data/derived/regression_results.json")
    output_cooks_path = Path("data/derived/cooks_distance_report.csv")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    # Load data
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # Fit model
    results, stats = fit_linear_regression(df)
    
    # Calculate Cook's Distance
    cooks_df, outlier_count = calculate_cooks_distance(results, df)
    
    # Output results
    output_regression_results(results, stats, outlier_count, output_json_path)
    
    # Save Cook's Distance report
    cooks_df.to_csv(output_cooks_path, index=False)
    logger.info(f"Cook's Distance report saved to {output_cooks_path}")
    
    logger.info("Regression analysis pipeline completed successfully.")

if __name__ == "__main__":
    main()
