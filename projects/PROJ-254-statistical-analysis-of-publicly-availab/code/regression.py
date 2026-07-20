"""
Regression module for fitting linear models and performing robustness checks.
"""
import os
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any, Optional
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_white

from utils import setup_logging, get_logger, set_deterministic_seed

logger = setup_logging()

DATA_DERIVED_DIR = Path(__file__).resolve().parent.parent / "data" / "derived"

def setup_logging_module():
    """
    Setup logging for regression module.
    """
    logger.info("Regression module logging setup complete.")

def read_low_coverage_years() -> List[int]:
    """
    Read low coverage years from JSON file.
    """
    path = DATA_DERIVED_DIR / "low_coverage_years.json"
    if not path.exists():
        return []
    with open(path, 'r') as f:
        return json.load(f)

def prepare_exclusions() -> List[int]:
    """
    Prepare list of years to exclude based on low coverage and missing tags.
    Logs exclusion criteria explicitly to pipeline_log.txt.
    """
    low_cov_years = read_low_coverage_years()
    excluded = set(low_cov_years)
    
    low_cov_count = len(low_cov_years)
    missing_tag_count = 0
    missing_tag_years = []

    # Check metadata for missing tags
    path = DATA_DERIVED_DIR / "metadata_mpd.parquet"
    if path.exists():
        df = pd.read_parquet(path)
        if 'year' in df.columns and 'genre' in df.columns:
            # Calculate ratio of missing genres per year
            year_counts = df.groupby('year')['genre'].apply(lambda x: x.isna().sum() / len(x))
            for year, ratio in year_counts.items():
                if ratio > 0.2: # 20% missing threshold
                    excluded.add(int(year))
                    missing_tag_years.append(int(year))
                    missing_tag_count += 1
                    logger.warning(f"Year {year} has >20% missing genre tags. Excluding.")
        else:
            logger.warning("Metadata file exists but lacks 'year' or 'genre' columns. Cannot check missing tags.")
    else:
        logger.warning("metadata_mpd.parquet not found. Skipping missing tag exclusion check.")

    # Log explicit summary of exclusion criteria
    logger.info("=== EXCLUSION CRITERIA SUMMARY ===")
    logger.info(f"Years excluded due to low coverage (<1,000 tracks): {low_cov_count}")
    if low_cov_years:
        logger.info(f"   Years: {sorted(low_cov_years)}")
    logger.info(f"Years excluded due to >20% missing genre tags: {missing_tag_count}")
    if missing_tag_years:
        logger.info(f"   Years: {sorted(missing_tag_years)}")
    logger.info(f"Total unique years excluded: {len(excluded)}")
    logger.info("=================================")

    return sorted(list(excluded))

def flag_low_coverage(year: int) -> bool:
    """
    Flag if a year is low coverage.
    """
    return year in read_low_coverage_years()

def get_filtered_years_for_regression(years: List[int], excluded: List[int]) -> List[int]:
    """
    Filter years based on exclusions.
    """
    return [y for y in years if y not in excluded]

def fit_linear_regression(df: pd.DataFrame) -> sm.RegressionResultsWrapper:
    """
    Fit linear regression with Newey-West HAC standard errors.
    """
    if 'year' not in df.columns or 'mean_off_diagonal_similarity' not in df.columns:
        raise ValueError("DataFrame missing required columns.")
    
    X = df['year']
    y = df['mean_off_diagonal_similarity']
    
    X = sm.add_constant(X)
    model = sm.OLS(y, X)
    results = model.fit()
    
    # HAC Standard Errors
    cov_type = 'HAC'
    cov_kwds = {'maxlags': 1, 'kernel': 'Bartlett'}
    results_hac = results.get_robustcov_results(cov_type=cov_type, **cov_kwds)
    
    logger.info("Regression fit complete.")
    return results_hac

def calculate_cooks_distance(results: sm.RegressionResultsWrapper, df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Cook's Distance for outliers.
    """
    from statsmodels.stats.outliers_influence import OLSInfluence
    influence = OLSInfluence(results.model, results.params)
    cooks_d = influence.cooks_distance[0]
    
    df_cooks = pd.DataFrame({
        'year': df['year'],
        'cooks_distance': cooks_d
    })
    return df_cooks

def output_regression_results(results: sm.RegressionResultsWrapper, df: pd.DataFrame):
    """
    Output regression results to JSON.
    """
    slope = results.params[1]
    intercept = results.params[0]
    p_value = results.pvalues[1]
    conf_int = results.conf_int().loc[1].tolist()
    
    output = {
        "slope": slope,
        "intercept": intercept,
        "p_value": p_value,
        "confidence_interval": conf_int,
        "r_squared": results.rsquared
    }
    
    path = DATA_DERIVED_DIR / "regression_results.json"
    with open(path, 'w') as f:
        json.dump(output, f, indent=2)
    logger.info(f"Saved regression results to {path}")

def main():
    """
    Main entry point for regression.
    """
    set_deterministic_seed(42)
    setup_logging_module()
    
    try:
        # Load similarity data
        path = DATA_DERIVED_DIR / "yearly_similarity.csv"
        if not path.exists():
            raise FileNotFoundError(f"Similarity CSV not found: {path}")
        df = pd.read_csv(path)
        
        # Prepare exclusions (includes logging of criteria)
        excluded_years = prepare_exclusions()
        
        # Save exclusions
        with open(DATA_DERIVED_DIR / "excluded_years.json", 'w') as f:
            json.dump(excluded_years, f)
        
        # Filter
        filtered_years = get_filtered_years_for_regression(df['year'].tolist(), excluded_years)
        df_filtered = df[df['year'].isin(filtered_years)]
        
        if len(df_filtered) < 2:
            logger.error("Not enough data points for regression after exclusion.")
            return
        
        # Fit
        results = fit_linear_regression(df_filtered)
        
        # Output
        output_regression_results(results, df_filtered)
        
        # Cook's Distance
        cooks_df = calculate_cooks_distance(results, df_filtered)
        cooks_df.to_csv(DATA_DERIVED_DIR / "cooks_distance_report.csv", index=False)
        
        logger.info("Regression pipeline complete.")
        
    except Exception as e:
        logger.error(f"Regression pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()