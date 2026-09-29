import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from scipy import stats
import os

from logger import get_logger
from exceptions import StatisticalModelError, ConfigurationError

logger = get_logger(__name__)

def load_processed_discrepancies(filepath: str) -> pd.DataFrame:
    """
    Load the processed discrepancies DataFrame from a CSV or Parquet file.
    Expects columns: 'jurisdiction', 'precinct_sum', 'county_reported', 'discrepancy_abs', 'discrepancy_pct', 'missing_data'.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Processed discrepancies file not found at {filepath}")
    
    if filepath.endswith('.parquet'):
        df = pd.read_parquet(filepath)
    else:
        df = pd.read_csv(filepath)
    
    required_cols = ['jurisdiction', 'precinct_sum', 'county_reported', 'discrepancy_abs', 'discrepancy_pct']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ConfigurationError(f"Processed data missing required columns: {missing}")
    
    return df

def load_null_distribution(filepath: str) -> np.ndarray:
    """
    Load the simulated null distribution from a JSON or NumPy file.
    Returns a 1D numpy array of simulated discrepancy values.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Null distribution file not found at {filepath}")
    
    if filepath.endswith('.npy'):
        return np.load(filepath)
    elif filepath.endswith('.json'):
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
            # Assume structure is {"values": [...]} or just a list
            if isinstance(data, list):
                return np.array(data)
            elif isinstance(data, dict) and 'values' in data:
                return np.array(data['values'])
            else:
                raise ConfigurationError("Null distribution JSON format unrecognized.")
    else:
        raise ConfigurationError(f"Unsupported file format for null distribution: {filepath}")

def anderson_darling_test(observed: np.ndarray, simulated: np.ndarray) -> Tuple[float, float]:
    """
    Perform Anderson-Darling test comparing observed discrepancies against simulated null.
    Returns (statistic, critical_value) or (statistic, p_value) depending on scipy version/context.
    Note: scipy.stats.anderson_ksamp is for k-samples. Here we treat simulated as the reference distribution.
    We will use the two-sample Anderson-Darling test logic if available, or fall back to KS if strict AD is needed for large N.
    For this implementation, we assume we are testing if 'observed' comes from the distribution defined by 'simulated'.
    Since scipy doesn't have a direct 'test against empirical distribution' AD function easily exposed for custom arrays,
    we will use the Kolmogorov-Smirnov two-sample test as a robust proxy for the "distribution shape" comparison,
    OR use `scipy.stats.anderson` on the observed data if we assume the simulated data defines the theoretical parameters.
    
    However, the task asks for AD test against *simulated* distributions.
    Best approach for empirical vs empirical: Two-sample Anderson-Darling.
    scipy.stats.anderson_ksamp([observed, simulated]) tests if they come from same distribution.
    """
    if len(observed) == 0 or len(simulated) == 0:
        raise StatisticalModelError("Cannot run AD test with empty data.")
    
    # Using k-sample Anderson-Darling to test if observed and simulated come from the same distribution
    result = stats.anderson_ksamp([observed, simulated])
    # result.statistic: Anderson-Kruskal statistic
    # result.pvalue: p-value
    return result.statistic, result.pvalue

def kolmogorov_smirnov_test(observed: np.ndarray, simulated: np.ndarray) -> Tuple[float, float]:
    """
    Perform Kolmogorov-Smirnov two-sample test.
    Returns (D statistic, p-value).
    """
    if len(observed) == 0 or len(simulated) == 0:
        raise StatisticalModelError("Cannot run KS test with empty data.")
    
    result = stats.ks_2samp(observed, simulated)
    return result.statistic, result.pvalue

def calculate_jurisdiction_p_values(
    df: pd.DataFrame,
    null_dist: np.ndarray,
    method: str = 'empirical_cdf'
) -> pd.DataFrame:
    """
    Calculate p-values for each jurisdiction individually against the null distribution.
    
    Logic:
    1. Group data by 'jurisdiction'.
    2. For each jurisdiction, aggregate the discrepancies (e.g., mean or sum of absolute discrepancies)
       to form a single test statistic per jurisdiction.
       *Assumption*: The null distribution represents the distribution of this aggregated statistic.
       If the null distribution was generated per-precinct, we must aggregate observed data similarly.
       Given the context of "jurisdiction individually", we calculate a summary statistic for the jurisdiction
       and compare it to the null distribution of that same summary statistic.
    
    3. Calculate the empirical p-value:
       p = (count(null >= observed_stat) + 1) / (len(null) + 1)  (Two-tailed or one-tailed logic applies here)
       Since discrepancies can be positive or negative, but we often care about magnitude:
       If using absolute discrepancies, we look at the tail.
       
    Args:
        df: Processed discrepancies DataFrame.
        null_dist: 1D array of simulated null statistics.
        method: 'empirical_cdf' (default) or 'gaussian_fit'.
    
    Returns:
        DataFrame with jurisdiction and calculated p-value.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty.")
        return pd.DataFrame(columns=['jurisdiction', 'p_value', 'observed_statistic'])

    if null_dist.size == 0:
        raise StatisticalModelError("Null distribution is empty.")

    # Define the aggregation function for the jurisdiction
    # We assume the null distribution was generated by aggregating precinct-level discrepancies
    # into a jurisdiction-level metric (e.g., mean absolute discrepancy).
    agg_func = np.mean 
    col_to_agg = 'discrepancy_abs' 
    
    # Group by jurisdiction and calculate the statistic
    jurisdiction_stats = df.groupby('jurisdiction')[col_to_agg].agg(agg_func).reset_index()
    jurisdiction_stats.columns = ['jurisdiction', 'observed_statistic']

    p_values = []
    
    logger.info(f"Calculating p-values against null distribution (size={len(null_dist)}) for {len(jurisdiction_stats)} jurisdictions.")

    for _, row in jurisdiction_stats.iterrows():
        obs_val = row['observed_statistic']
        
        if method == 'empirical_cdf':
            # Two-sided p-value logic for magnitude:
            # How likely is it to see a value as extreme or more extreme than obs_val?
            # Since null_dist might be centered around 0 or a small positive bias,
            # we check the tail probability.
            
            # If the null distribution represents absolute discrepancies, we look at the right tail.
            # p = P(X >= obs_val)
            count_extreme = np.sum(null_dist >= obs_val)
            p_val = (count_extreme + 1) / (len(null_dist) + 1)
            
            # If the user wants two-tailed for signed discrepancies, logic would differ,
            # but 'discrepancy_abs' implies one-tailed (upper).
        
        elif method == 'gaussian_fit':
            # Fit a Gaussian to the null distribution
            mean, std = np.mean(null_dist), np.std(null_dist)
            if std == 0:
                p_val = 1.0 if obs_val == mean else 0.0
            else:
                z = (obs_val - mean) / std
                # Survival function for one-tailed
                p_val = stats.norm.sf(abs(z))
        else:
            raise ConfigurationError(f"Unknown p-value method: {method}")
        
        p_values.append({
            'jurisdiction': row['jurisdiction'],
            'observed_statistic': obs_val,
            'p_value': p_val
        })

    result_df = pd.DataFrame(p_values)
    return result_df

def run_analysis(
    processed_data_path: str,
    null_distribution_path: str,
    output_path: str
) -> pd.DataFrame:
    """
    Orchestrates the full analysis: loading data, running tests, calculating p-values, and saving results.
    """
    logger.info(f"Starting analysis with processed data: {processed_data_path}")
    
    # Load data
    df = load_processed_discrepancies(processed_data_path)
    null_dist = load_null_distribution(null_distribution_path)
    
    # Global tests
    observed_vals = df['discrepancy_abs'].values
    ad_stat, ad_p = anderson_darling_test(observed_vals, null_dist)
    ks_stat, ks_p = kolmogorov_smirnov_test(observed_vals, null_dist)
    
    logger.info(f"Global AD Test: stat={ad_stat:.4f}, p={ad_p:.4f}")
    logger.info(f"Global KS Test: stat={ks_stat:.4f}, p={ks_p:.4f}")
    
    # Jurisdiction-level p-values
    jurisdiction_results = calculate_jurisdiction_p_values(df, null_dist)
    
    # Save results
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    jurisdiction_results.to_csv(output_path, index=False)
    logger.info(f"Jurisdiction p-values saved to {output_path}")
    
    return jurisdiction_results

def calculate_vif_for_predictors(df: pd.DataFrame, predictor_cols: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for given predictors.
    SC-006: If predictors exist, check VIF > 5.
    """
    if not predictor_cols or len(predictor_cols) < 2:
        logger.info("Not enough predictors to calculate VIF.")
        return {}
    
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    from statsmodels.tools.tools import add_constant
    
    # Filter to available columns
    available_cols = [c for c in predictor_cols if c in df.columns]
    if len(available_cols) < 2:
        logger.warning(f"Only {len(available_cols)} predictors found in data. Cannot calculate VIF.")
        return {}
    
    X = df[available_cols]
    X = add_constant(X)
    
    vif_data = {}
    for i, col in enumerate(available_cols):
        vif = variance_inflation_factor(X.values, i+1) # +1 because of constant
        vif_data[col] = vif
        if vif > 5:
            logger.warning(f"High VIF detected for {col}: {vif:.2f}")
    
    return vif_data

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run statistical analysis on election discrepancies.")
    parser.add_argument("--processed-data", required=True, help="Path to processed discrepancies CSV")
    parser.add_argument("--null-dist", required=True, help="Path to null distribution JSON/NPY")
    parser.add_argument("--output", required=True, help="Path to save jurisdiction p-values CSV")
    parser.add_argument("--method", default="empirical_cdf", choices=["empirical_cdf", "gaussian_fit"], help="Method for p-value calculation")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logger = get_logger(__name__)
    setup_logger.info("Running main analysis pipeline.")
    
    # We need to call the run_analysis function which uses the specific method
    # But run_analysis doesn't take method arg. Let's adapt or call calculate directly.
    # Re-implementing main to be flexible:
    
    df = load_processed_discrepancies(args.processed_data)
    null_dist = load_null_distribution(args.null_dist)
    
    results = calculate_jurisdiction_p_values(df, null_dist, method=args.method)
    
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else '.', exist_ok=True)
    results.to_csv(args.output, index=False)
    print(f"Analysis complete. Results saved to {args.output}")

if __name__ == "__main__":
    main()