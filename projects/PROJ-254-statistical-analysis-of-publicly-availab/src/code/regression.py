import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd

from utils import get_logger, setup_logging, set_deterministic_seed
from memory_utils import monitor_and_maybe_gc

try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logging.warning("statsmodels not installed. Regression functions will fail.")

def flag_low_coverage(
    metadata_path: str = "data/derived/metadata_mpd.parquet",
    min_tracks: int = 1000,
    max_missing_genre_rate: float = 0.2
) -> Tuple[List[int], List[int], Dict[int, float]]:
    """
    Identify years with low track coverage or high missing genre rates.

    Args:
        metadata_path: Path to metadata file.
        min_tracks: Minimum unique tracks required.
        max_missing_genre_rate: Maximum allowed missing genre rate.

    Returns:
        Tuple of (flagged_years, warning_years, missing_genre_rates)
    """
    logger = get_logger()
    logger.info("Flagging low coverage years...")

    try:
        df = pd.read_parquet(metadata_path)

        flagged_years = []
        warning_years = []
        missing_genre_rates = {}

        for year in sorted(df['year'].dropna().unique()):
            year_df = df[df['year'] == year]

            # Calculate missing genre rate
            total_tracks = len(year_df)
            missing_genre = year_df['genre'].isna().sum()
            missing_rate = missing_genre / total_tracks if total_tracks > 0 else 1.0
            missing_genre_rates[year] = missing_rate

            if missing_rate > max_missing_genre_rate:
                warning_years.append(year)
                logger.warning(f"Year {year} has {missing_rate:.1%} missing genre tags")

            # Count unique tracks
            unique_tracks = year_df['track_id'].nunique()
            if unique_tracks < min_tracks:
                flagged_years.append(year)
                logger.info(f"Year {year} flagged for low coverage: {unique_tracks} tracks")

            monitor_and_maybe_gc()

        return flagged_years, warning_years, missing_genre_rates

    except Exception as e:
        logger.error(f"Error flagging low coverage: {str(e)}")
        return [], [], {}

def fit_linear_regression(
    similarity_path: str = "data/derived/yearly_similarity.csv",
    excluded_years: List[int] = None
) -> Dict[str, Any]:
    """
    Fit linear regression to similarity trend.

    Args:
        similarity_path: Path to similarity CSV.
        excluded_years: Years to exclude from regression.

    Returns:
        Regression results dictionary.
    """
    if not STATSMODELS_AVAILABLE:
        logger = get_logger()
        logger.error("statsmodels not installed.")
        return {}

    logger = get_logger()
    logger.info("Fitting linear regression...")

    try:
        df = pd.read_csv(similarity_path)

        if excluded_years:
            initial_len = len(df)
            df = df[~df['year'].isin(excluded_years)]
            excluded_count = initial_len - len(df)
            logger.info(f"Excluded {excluded_count} years from regression")

        if len(df) < 2:
            logger.error("Not enough data points for regression")
            return {}

        # Prepare data
        X = sm.add_constant(df['year'])
        y = df['mean_off_diagonal_similarity']

        # Fit model with robust standard errors
        model = sm.OLS(y, X).fit(cov_type='HC3')

        results = {
            'slope': float(model.params['year']),
            'intercept': float(model.params['const']),
            'r_squared': float(model.rsquared),
            'p_value': float(model.pvalues['year']),
            'confidence_interval_95': list(model.conf_int().loc['year']),
            'years_included': len(df),
            'years_excluded': len(excluded_years) if excluded_years else 0,
            'excluded_years': excluded_years or []
        }

        logger.info(f"Regression slope: {results['slope']:.6f} (p={results['p_value']:.4f})")
        return results

    except Exception as e:
        logger.error(f"Error fitting regression: {str(e)}")
        return {}

def calculate_cooks_distance(
    similarity_path: str = "data/derived/yearly_similarity.csv",
    regression_results: Dict[str, Any] = None
) -> pd.DataFrame:
    """
    Calculate Cook's Distance for outlier detection.

    Args:
        similarity_path: Path to similarity CSV.
        regression_results: Pre-computed regression results.

    Returns:
        DataFrame with Cook's Distance values.
    """
    if not STATSMODELS_AVAILABLE:
        logger = get_logger()
        logger.error("statsmodels not installed.")
        return pd.DataFrame()

    logger = get_logger()
    logger.info("Calculating Cook's Distance...")

    try:
        df = pd.read_csv(similarity_path)

        # Prepare data
        X = sm.add_constant(df['year'])
        y = df['mean_off_diagonal_similarity']

        # Fit model
        model = sm.OLS(y, X).fit()

        # Calculate Cook's Distance
        cooks_d = model.get_influence().cooks_distance[0]

        # Create report
        report = pd.DataFrame({
            'year': df['year'],
            'similarity': df['mean_off_diagonal_similarity'],
            'cooks_distance': cooks_d,
            'is_outlier': cooks_d > 4 / len(df),  # Common threshold
            'leverage': model.get_influence().hat_matrix_diag
        })

        outlier_count = report['is_outlier'].sum()
        logger.info(f"Found {outlier_count} outliers using Cook's Distance")

        return report

    except Exception as e:
        logger.error(f"Error calculating Cook's Distance: {str(e)}")
        return pd.DataFrame()

def main() -> int:
    """Main entry point for regression analysis."""
    set_deterministic_seed(42)
    setup_logging("pipeline_log.txt")
    logger = get_logger()

    try:
        # Flag low coverage years
        flagged, warnings, rates = flag_low_coverage()

        # Fit regression
        regression_results = fit_linear_regression(excluded_years=flagged)
        if not regression_results:
            logger.error("Regression failed")
            return 1

        # Save regression results
        output_path = Path("data/derived/regression_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        import json
        with open(output_path, 'w') as f:
            json.dump(regression_results, f, indent=2)
        logger.info(f"Saved regression results to {output_path}")

        # Calculate Cook's Distance
        cooks_report = calculate_cooks_distance()
        if not cooks_report.empty:
            cooks_path = Path("data/derived/cooks_distance_report.csv")
            cooks_report.to_csv(cooks_path, index=False)
            logger.info(f"Saved Cook's Distance report to {cooks_path}")

        logger.info("Regression analysis completed")
        return 0

    except Exception as e:
        logger.error(f"Regression analysis failed: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())