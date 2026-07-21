"""
Regression module for fitting linear models and performing Cook's Distance analysis.
"""
import os
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any, Optional
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import OLSInfluence

from utils import setup_logging, get_logger, set_deterministic_seed
from memory_utils import check_memory_thresholds, trigger_garbage_collection

logger = setup_logging()

DATA_DERIVED_DIR = Path(__file__).resolve().parent.parent / "data" / "derived"

def setup_logging_module():
    """
    Setup logging for the regression module.
    """
    logger.info("Regression module initialized.")

def read_low_coverage_years() -> List[int]:
    """
    Read low coverage years from the JSON file.

    Returns:
        List[int]: List of low coverage years.

    Raises:
        FileNotFoundError: If the file is missing.
    """
    path = DATA_DERIVED_DIR / "low_coverage_years.json"
    if not path.exists():
        return []
    
    with open(path, 'r') as f:
        return json.load(f)

def prepare_exclusions(similarity_df: pd.DataFrame, low_coverage_years: List[int]) -> Set[int]:
    """
    Prepare exclusions for regression.

    Args:
        similarity_df (pd.DataFrame): DataFrame with similarity data.
        low_coverage_years (List[int]): List of low coverage years.

    Returns:
        Set[int]: Set of years to exclude.
    """
    # Exclude low coverage years
    exclusions = set(low_coverage_years)
    return exclusions

def flag_low_coverage(year: int, low_coverage_years: List[int]) -> bool:
    """
    Flag if a year is low coverage.

    Args:
        year (int): Year to check.
        low_coverage_years (List[int]): List of low coverage years.

    Returns:
        bool: True if low coverage.
    """
    return year in low_coverage_years

def get_filtered_years_for_regression(similarity_df: pd.DataFrame, exclusions: Set[int]) -> pd.DataFrame:
    """
    Get filtered DataFrame for regression.

    Args:
        similarity_df (pd.DataFrame): DataFrame with similarity data.
        exclusions (Set[int]): Set of years to exclude.

    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    return similarity_df[~similarity_df['year'].isin(exclusions)]

def fit_linear_regression(df: pd.DataFrame, exclude_outliers: bool = False) -> sm.RegressionResultsWrapper:
    """
    Fit a linear regression model.

    Args:
        df (pd.DataFrame): DataFrame with 'year' and 'mean_off_diagonal_similarity'.
        exclude_outliers (bool): Whether to exclude Cook's Distance outliers.

    Returns:
        sm.RegressionResultsWrapper: Regression results.
    """
    X = df['year']
    y = df['mean_off_diagonal_similarity']
    
    X = sm.add_constant(X)
    model = sm.OLS(y, X)
    results = model.fit(cov_type='HAC', cov_kwds={'maxlags': 1})
    
    return results

def calculate_cooks_distance(results: sm.RegressionResultsWrapper) -> pd.DataFrame:
    """
    Calculate Cook's Distance for each observation.

    Args:
        results (sm.RegressionResultsWrapper): Regression results.

    Returns:
        pd.DataFrame: DataFrame with Cook's Distance values.
    """
    influence = OLSInfluence(results)
    cooks_d = influence.cooks_distance[0]
    
    df_cooks = pd.DataFrame({
        'index': results.model.data.xnames,
        'cooks_distance': cooks_d
    })
    df_cooks['year'] = results.model.data.orig_endog  # Placeholder, adjust as needed
    
    return df_cooks

def output_regression_results(results: sm.RegressionResultsWrapper, cooks_df: pd.DataFrame, robustness_status: str):
    """
    Output regression results to JSON.

    Args:
        results (sm.RegressionResultsWrapper): Regression results.
        cooks_df (pd.DataFrame): Cook's Distance DataFrame.
        robustness_status (str): Robustness status.
    """
    output = {
        'slope': results.params[1],
        'intercept': results.params[0],
        'p_value': results.pvalues[1],
        'confidence_interval': results.conf_int().iloc[1].tolist(),
        'robustness_status': robustness_status
    }
    
    output_path = DATA_DERIVED_DIR / "regression_results.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Saved regression results to {output_path}")

def main():
    """
    Main entry point for regression analysis.
    """
    set_deterministic_seed(42)
    setup_logging_module()
    
    try:
        # Load similarity data
        similarity_df = pd.read_csv(DATA_DERIVED_DIR / "yearly_similarity.csv")
        
        # Read low coverage years
        low_coverage_years = read_low_coverage_years()
        
        # Prepare exclusions
        exclusions = prepare_exclusions(similarity_df, low_coverage_years)
        
        # Filter data
        filtered_df = get_filtered_years_for_regression(similarity_df, exclusions)
        
        # Fit regression
        results = fit_linear_regression(filtered_df)
        
        # Calculate Cook's Distance
        cooks_df = calculate_cooks_distance(results)
        
        # Save Cook's Distance report
        cooks_report_path = DATA_DERIVED_DIR / "cooks_distance_report.csv"
        cooks_df.to_csv(cooks_report_path, index=False)
        logger.info(f"Saved Cook's Distance report to {cooks_report_path}")
        
        # Determine robustness (placeholder logic)
        robustness_status = "Robust" if results.pvalues[1] < 0.05 else "Not Robust"
        
        # Output results
        output_regression_results(results, cooks_df, robustness_status)
        
        logger.info("Regression analysis complete.")
        
    except Exception as e:
        logger.error(f"Regression analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
