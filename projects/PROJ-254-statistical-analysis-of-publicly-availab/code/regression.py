import os
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any

import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import OLSInfluence

from utils import get_logger, setup_logging

# Ensure logging is configured for the module
setup_logging()
logger = get_logger()

def flag_low_coverage(
    df: pd.DataFrame,
    min_tracks: int = 1000,
    max_missing_genre_rate: float = 0.2
) -> Tuple[pd.DataFrame, Dict[int, str]]:
    """
    Identify years with <1,000 unique tracks (flag for exclusion) and
    years with >20% missing genre tags (log warning).
    
    Returns:
        filtered_df: The original dataframe (logic is applied in regression fitting).
        flags: Dict mapping year to reason for exclusion.
    """
    flags = {}
    logger.info("Starting low coverage flagging process.")
    
    # Group by year to analyze coverage
    yearly_stats = df.groupby('year').agg(
        unique_tracks=('track_id', 'nunique'),
        missing_genres=('genre', lambda x: x.isna().sum()),
        total_tracks=('genre', 'count')
    ).reset_index()

    for _, row in yearly_stats.iterrows():
        year = row['year']
        unique_count = row['unique_tracks']
        missing_count = row['missing_genres']
        total_count = row['total_tracks']
        
        missing_rate = missing_count / total_count if total_count > 0 else 0.0

        if missing_rate > max_missing_genre_rate:
            flags[year] = f"High missing genre rate: {missing_rate:.2%}"
            logger.warning(f"Year {year}: High missing genre rate ({missing_rate:.2%}). Logged for exclusion.")
        
        if unique_count < min_tracks:
            if year in flags:
                flags[year] += f"; Low unique track count ({unique_count} < {min_tracks})"
            else:
                flags[year] = f"Low unique track count: {unique_count} < {min_tracks}"
            logger.warning(f"Year {year}: Low unique track count ({unique_count} < {min_tracks}). Flagged for exclusion.")

    logger.info(f"Flagging complete. Excluded years: {list(flags.keys())}")
    return df, flags

def get_filtered_years_for_regression(
    df: pd.DataFrame,
    min_tracks: int = 1000,
    max_missing_genre_rate: float = 0.2
) -> List[int]:
    """
    Returns a list of years that are valid for regression analysis.
    """
    _, flags = flag_low_coverage(df, min_tracks, max_missing_genre_rate)
    excluded_years = set(flags.keys())
    all_years = set(df['year'].unique())
    valid_years = list(all_years - excluded_years)
    valid_years.sort()
    return valid_years

def fit_linear_regression(
    df: pd.DataFrame,
    min_tracks: int = 1000,
    max_missing_genre_rate: float = 0.2
) -> sm.OLSResults:
    """
    Load similarity data, filter out flagged low-coverage years,
    and fit a linear regression model (year vs. mean_off_diagonal_similarity).
    
    Returns:
        OLSResults object from statsmodels.
    """
    logger.info("Fitting linear regression model.")
    
    valid_years = get_filtered_years_for_regression(
        df, min_tracks, max_missing_genre_rate
    )
    
    if len(valid_years) < 2:
        raise ValueError("Not enough valid years to perform regression.")

    filtered_df = df[df['year'].isin(valid_years)]
    
    # Prepare data
    X = filtered_df['year'].values
    y = filtered_df['mean_off_diagonal_similarity'].values
    
    # Add constant for intercept
    X = sm.add_constant(X)
    
    # Fit model with robust standard errors
    model = sm.OLS(y, X)
    results = model.fit(cov_type='HC3') # Robust standard errors
    
    logger.info(f"Regression model fitted. R-squared: {results.rsquared:.4f}")
    logger.info(f"Slope: {results.params[1]:.6f}, Intercept: {results.params[0]:.6f}")
    
    return results

def calculate_cooks_distance(
    df: pd.DataFrame,
    results: sm.OLSResults,
    min_tracks: int = 1000,
    max_missing_genre_rate: float = 0.2
) -> pd.DataFrame:
    """
    Calculate Cook's Distance for outliers using the provided regression model.
    
    Returns:
        DataFrame with year, similarity, and cooks_distance.
    """
    logger.info("Calculating Cook's Distance for outlier detection.")
    
    valid_years = get_filtered_years_for_regression(
        df, min_tracks, max_missing_genre_rate
    )
    filtered_df = df[df['year'].isin(valid_years)]
    
    X = filtered_df['year'].values
    X = sm.add_constant(X)
    y = filtered_df['mean_off_diagonal_similarity'].values
    
    influence = OLSInfluence(results)
    cooks_d = influence.cooks_distance[0]
    
    report = filtered_df.copy()
    report['cooks_distance'] = cooks_d
    
    # Sort by Cook's distance descending
    report = report.sort_values(by='cooks_distance', ascending=False)
    
    outlier_count = int((cooks_d > (4 / len(cooks_d))).sum())
    logger.info(f"Cook's Distance calculation complete. Outliers identified: {outlier_count}")
    
    return report[['year', 'mean_off_diagonal_similarity', 'cooks_distance']]

def output_regression_results(
    results: sm.OLSResults,
    output_path: Path
) -> None:
    """
    Output regression results (slope, 95% CI, p-value) to JSON.
    """
    logger.info("Writing regression results to JSON.")
    
    slope = results.params[1]
    intercept = results.params[0]
    p_value = results.pvalues[1]
    conf_int = results.conf_int().iloc[1].tolist()
    
    data = {
        "slope": float(slope),
        "intercept": float(intercept),
        "p_value": float(p_value),
        "confidence_interval_95": conf_int,
        "r_squared": float(results.rsquared),
        "num_observations": int(results.nobs)
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Regression results saved to {output_path}")

def main():
    """
    Main entry point for the regression analysis task T030.
    Performs regression, calculates Cook's Distance, and logs comprehensive model parameters.
    """
    logger.info("Starting Regression Analysis (T030).")
    
    # Paths
    base_path = Path("data/derived")
    similarity_path = base_path / "yearly_similarity.csv"
    results_path = base_path / "regression_results.json"
    cooks_path = base_path / "cooks_distance_report.csv"
    
    if not similarity_path.exists():
        logger.error(f"Input file not found: {similarity_path}")
        raise FileNotFoundError(f"Required input file missing: {similarity_path}")
    
    # Load data
    df = pd.read_csv(similarity_path)
    
    # 1. Flag low coverage and log warnings (T029 logic)
    _, flags = flag_low_coverage(df)
    logger.info(f"Excluded years due to coverage: {flags}")
    
    # 2. Fit Regression (T026)
    results = fit_linear_regression(df)
    
    # 3. Output Results (T027)
    output_regression_results(results, results_path)
    
    # 4. Calculate Cook's Distance (T036)
    cooks_report = calculate_cooks_distance(df, results)
    cooks_report.to_csv(cooks_path, index=False)
    
    # 5. Comprehensive Logging for T030 (FR-008)
    logger.info("=" * 50)
    logger.info("REGRESSION MODEL PARAMETERS & STATUS")
    logger.info("=" * 50)
    logger.info(f"Convergence Status: {results.converged if hasattr(results, 'converged') else 'N/A (OLS usually converges)'}")
    logger.info(f"Number of Observations Used: {results.nobs}")
    logger.info(f"Model Formula: mean_off_diagonal_similarity ~ year")
    logger.info(f"Covariance Type: HC3 (Robust)")
    logger.info(f"R-squared: {results.rsquared:.6f}")
    logger.info(f"Adj. R-squared: {results.rsquared_adj:.6f}")
    logger.info(f"F-statistic: {results.fvalue:.6f}")
    logger.info(f"F-statistic p-value: {results.f_pvalue:.6e}")
    logger.info("-" * 50)
    logger.info("COEFFICIENTS:")
    logger.info(f"  Intercept: {results.params[0]:.6f} (p={results.pvalues[0]:.6e})")
    logger.info(f"  Slope (Year): {results.params[1]:.6f} (p={results.pvalues[1]:.6e})")
    logger.info("-" * 50)
    logger.info("OUTLIER ANALYSIS (Cook's Distance):")
    outlier_threshold = 4 / len(cooks_report)
    logger.info(f"  Threshold used: {outlier_threshold:.6f}")
    outliers = cooks_report[cooks_report['cooks_distance'] > outlier_threshold]
    logger.info(f"  Total outliers identified: {len(outliers)}")
    if len(outliers) > 0:
        logger.info("  Outlier years:")
        for _, row in outliers.iterrows():
            logger.info(f"    - Year {int(row['year'])}: Cook's D = {row['cooks_distance']:.6f}")
    else:
        logger.info("  No significant outliers detected.")
    logger.info("=" * 50)
    logger.info("Regression Analysis (T030) completed successfully.")

if __name__ == "__main__":
    main()