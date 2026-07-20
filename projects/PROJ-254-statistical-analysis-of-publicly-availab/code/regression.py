import os
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any, Optional
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson
from statsmodels.stats.sandwich_covariance import cov_hac

from utils import get_logger, setup_logging, set_deterministic_seed
from memory_utils import check_memory_checkpoint, trigger_garbage_collection

# Ensure deterministic behavior
set_deterministic_seed(42)

def prepare_exclusions() -> List[int]:
    """
    Read low coverage years and metadata to generate the list of excluded years.
    
    Logic:
    - Exclude years with < 1,000 unique tracks (from low_coverage_years.json).
    - Flag years with > 20% missing genre tags (log warning, add to low_coverage list with reason, 
      but DO NOT exclude from regression per Spec Edge Cases).
    
    Returns:
        List[int]: List of years to exclude from regression analysis.
    """
    logger = get_logger()
    low_coverage_path = Path("data/derived/low_coverage_years.json")
    metadata_path = Path("data/derived/metadata_mpd.parquet")
    excluded_years_path = Path("data/derived/excluded_years.json")
    
    excluded_years: List[int] = []
    
    # Load low coverage years
    if low_coverage_path.exists():
        with open(low_coverage_path, 'r') as f:
            low_coverage_data = json.load(f)
        
        for item in low_coverage_data:
            if isinstance(item, int):
                excluded_years.append(item)
            elif isinstance(item, dict) and 'year' in item:
                excluded_years.append(item['year'])
    else:
        logger.warning(f"Low coverage years file not found: {low_coverage_path}")
    
    # Check metadata for missing genre tags (if available)
    if metadata_path.exists():
        try:
            df = pd.read_parquet(metadata_path)
            if 'release_year' in df.columns and 'genre_tag' in df.columns:
                # Calculate missing genre tag percentage per year
                total_per_year = df.groupby('release_year').size()
                missing_per_year = df[df['genre_tag'].isna()].groupby('release_year').size()
                
                missing_pct = (missing_per_year / total_per_year * 100).fillna(0)
                
                for year, pct in missing_pct.items():
                    if pct > 20.0:
                        logger.warning(f"Year {year} has {pct:.1f}% missing genre tags. Flagged as LOW_COVERAGE but NOT excluded.")
                        # Update low_coverage_years.json if we were modifying it, 
                        # but per spec we just log and do not exclude.
            else:
                logger.warning("Metadata file missing required columns for coverage check.")
        except Exception as e:
            logger.error(f"Error reading metadata for coverage check: {e}")
    else:
        logger.warning(f"Metadata file not found: {metadata_path}")
    
    # Deduplicate and sort
    excluded_years = sorted(list(set(excluded_years)))
    
    # Save excluded years
    with open(excluded_years_path, 'w') as f:
        json.dump(excluded_years, f, indent=2)
    
    logger.info(f"Prepared exclusions: {len(excluded_years)} years excluded.")
    return excluded_years

def flag_low_coverage(year: int, reason: str) -> None:
    """
    Log a warning for a low coverage year and optionally update low_coverage_years.json.
    (Note: Per Spec, this does NOT exclude the year from regression).
    """
    logger = get_logger()
    low_coverage_path = Path("data/derived/low_coverage_years.json")
    
    data = []
    if low_coverage_path.exists():
        with open(low_coverage_path, 'r') as f:
            data = json.load(f)
    
    # Check if year already exists
    year_exists = False
    for item in data:
        if (isinstance(item, int) and item == year) or (isinstance(item, dict) and item.get('year') == year):
            year_exists = True
            break
    
    if not year_exists:
        data.append({"year": year, "reason": reason})
        with open(low_coverage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    logger.warning(f"Year {year} flagged as LOW_COVERAGE: {reason}")

def get_filtered_years_for_regression(excluded_years: List[int]) -> List[int]:
    """
    Load similarity data and filter out excluded years.
    
    Args:
        excluded_years: List of years to exclude.
        
    Returns:
        List of years remaining for regression.
    """
    logger = get_logger()
    similarity_path = Path("data/derived/yearly_similarity.csv")
    
    if not similarity_path.exists():
        raise FileNotFoundError(f"Similarity data not found: {similarity_path}")
    
    df = pd.read_csv(similarity_path)
    if 'year' not in df.columns:
        raise ValueError("Similarity CSV missing 'year' column.")
    
    excluded_set = set(excluded_years)
    filtered_df = df[~df['year'].isin(excluded_set)]
    
    logger.info(f"Filtered years: {len(df)} total -> {len(filtered_df)} after excluding {len(excluded_set)}.")
    return filtered_df['year'].tolist()

def fit_linear_regression() -> Dict[str, Any]:
    """
    Fit a linear regression model (year vs. mean_off_diagonal_similarity) 
    using statsmodels with Newey-West HAC standard errors.
    
    Returns:
        Dict containing slope, intercept, p-value, confidence interval, and r-squared.
    """
    logger = get_logger()
    similarity_path = Path("data/derived/yearly_similarity.csv")
    excluded_path = Path("data/derived/excluded_years.json")
    
    # Load data
    if not similarity_path.exists():
        raise FileNotFoundError(f"Similarity data not found: {similarity_path}")
    
    df = pd.read_csv(similarity_path)
    if 'year' not in df.columns or 'mean_off_diagonal_similarity' not in df.columns:
        raise ValueError("Similarity CSV missing required columns.")
    
    # Load exclusions
    excluded_years = []
    if excluded_path.exists():
        with open(excluded_path, 'r') as f:
            excluded_years = json.load(f)
    else:
        logger.warning(f"Excluded years file not found: {excluded_path}. Proceeding without exclusions.")
    
    # Filter data
    excluded_set = set(excluded_years)
    filtered_df = df[~df['year'].isin(excluded_set)]
    
    if len(filtered_df) < 2:
        raise ValueError("Insufficient data points for regression after filtering.")
    
    X = filtered_df['year'].values
    y = filtered_df['mean_off_diagonal_similarity'].values
    
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    # Fit OLS
    model = sm.OLS(y, X_with_const)
    results = model.fit()
    
    # Calculate HAC standard errors (Newey-West)
    # Note: statsmodels' cov_hac requires specific inputs, often used with results.get_robustcov_results
    # Using a simpler approach for HAC if available, or fallback to standard errors if not
    try:
        # Attempt to get HAC robust covariance
        # lag is the number of lags to consider; for time series, often floor(n^(1/3)) or similar
        # Here we use a default or estimate based on data length
        n_obs = len(y)
        lag = max(1, int(n_obs ** (1/3)))
        robust_results = results.get_robustcov_results(cov_type='HAC', maxlags=lag)
        
        slope = robust_results.params[1]
        intercept = robust_results.params[0]
        p_value = robust_results.pvalues[1]
        conf_int = robust_results.conf_int(alpha=0.05)[1] # 95% CI for slope
        r_squared = robust_results.rsquared
    except Exception as e:
        logger.warning(f"HAC robust covariance calculation failed: {e}. Falling back to OLS standard errors.")
        slope = results.params[1]
        intercept = results.params[0]
        p_value = results.pvalues[1]
        conf_int = results.conf_int(alpha=0.05)[1]
        r_squared = results.rsquared
    
    # Durbin-Watson test for autocorrelation
    try:
        dw_stat = durbin_watson(results.resid)
    except Exception:
        dw_stat = None
    
    # Log completion
    logger.info("Regression fit complete.")
    
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "p_value": float(p_value),
        "ci_lower": float(conf_int[0]),
        "ci_upper": float(conf_int[1]),
        "r_squared": float(r_squared),
        "durbin_watson": float(dw_stat) if dw_stat is not None else None,
        "n_observations": int(n_obs),
        "excluded_years": excluded_years
    }

def calculate_cooks_distance(results_dict: Dict[str, Any]) -> pd.DataFrame:
    """
    Calculate Cook's Distance for outliers using the regression model.
    (Note: This is a placeholder implementation as the actual model object is not returned by fit_linear_regression.
     In a full pipeline, we would pass the fitted model object or re-fit here).
    """
    logger = get_logger()
    similarity_path = Path("data/derived/yearly_similarity.csv")
    excluded_path = Path("data/derived/excluded_years.json")
    
    if not similarity_path.exists():
        raise FileNotFoundError(f"Similarity data not found: {similarity_path}")
    
    df = pd.read_csv(similarity_path)
    excluded_years = []
    if excluded_path.exists():
        with open(excluded_path, 'r') as f:
            excluded_years = json.load(f)
    
    excluded_set = set(excluded_years)
    filtered_df = df[~df['year'].isin(excluded_set)]
    
    if len(filtered_df) < 4:
        logger.warning("Not enough data points to calculate Cook's Distance.")
        return pd.DataFrame()
    
    X = filtered_df['year'].values
    y = filtered_df['mean_off_diagonal_similarity'].values
    X_with_const = sm.add_constant(X)
    
    model = sm.OLS(y, X_with_const)
    results = model.fit()
    
    # Calculate Cook's Distance
    # Formula: D_i = (r_i^2 / (p * MSE)) * (h_ii / (1 - h_ii)^2)
    # where r_i is residual, p is number of parameters, MSE is mean squared error, h_ii is leverage
    
    residuals = results.resid
    leverage = results.get_influence().hat_matrix_diag
    mse = results.mse_resid
    p = results.df_model + 1  # number of parameters (intercept + slope)
    
    cooks_d = (residuals**2 / (p * mse)) * (leverage / (1 - leverage)**2)
    
    report_df = pd.DataFrame({
        "year": filtered_df['year'],
        "similarity": filtered_df['mean_off_diagonal_similarity'],
        "residual": residuals,
        "leverage": leverage,
        "cooks_distance": cooks_d
    })
    
    # Sort by Cook's Distance descending
    report_df = report_df.sort_values(by='cooks_distance', ascending=False)
    
    return report_df

def output_regression_results(results_dict: Dict[str, Any]) -> None:
    """
    Save regression results to JSON and print to console.
    """
    logger = get_logger()
    output_path = Path("data/derived/regression_results.json")
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(results_dict, f, indent=2)
    
    # Print to console
    print(f"Regression Results:")
    print(f"  Slope: {results_dict['slope']:.6f}")
    print(f"  Intercept: {results_dict['intercept']:.6f}")
    print(f"  P-value: {results_dict['p_value']:.6f}")
    print(f"  95% CI: [{results_dict['ci_lower']:.6f}, {results_dict['ci_upper']:.6f}]")
    print(f"  R-squared: {results_dict['r_squared']:.6f}")
    print(f"  Durbin-Watson: {results_dict['durbin_watson']:.4f if results_dict['durbin_watson'] else 'N/A'}")
    print(f"  Observations: {results_dict['n_observations']}")
    print(f"  Excluded Years: {results_dict['excluded_years']}")

def main() -> None:
    """
    Main entry point for the regression pipeline.
    """
    logger = setup_logging()
    logger.info("Starting regression analysis.")
    
    try:
        # 1. Prepare exclusions
        excluded_years = prepare_exclusions()
        
        # 2. Fit linear regression
        results = fit_linear_regression()
        
        # 3. Output results
        output_regression_results(results)
        
        # 4. Calculate Cook's Distance
        cooks_df = calculate_cooks_distance(results)
        if not cooks_df.empty:
            cooks_path = Path("data/derived/cooks_distance_report.csv")
            cooks_df.to_csv(cooks_path, index=False)
            logger.info(f"Cook's Distance report saved to {cooks_path}")
        
        logger.info("Regression analysis complete.")
        
    except Exception as e:
        logger.error(f"Regression analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()