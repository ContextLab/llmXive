import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from scipy import stats
import os
import yaml

# Import from existing project modules
from logger import get_logger
from models import validate_output_schema
from discrepancy import DiscrepancyCalculator
from simulation import fit_negative_binomial, generate_nb_null_model
from exceptions import ConfigurationError, StatisticalModelError

logger = get_logger(__name__)

# --- Existing Functions (Preserved) ---

def load_processed_discrepancies(path: str) -> pd.DataFrame:
    """Load processed discrepancy data from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data file not found: {path}")
    df = pd.read_csv(path)
    validate_output_schema(df)
    return df

def load_null_distribution(path: str) -> pd.DataFrame:
    """Load null distribution data from CSV or JSON."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Null distribution file not found: {path}")
    if path.endswith('.csv'):
        return pd.read_csv(path)
    elif path.endswith('.json'):
        return pd.read_json(path)
    else:
        raise ValueError(f"Unsupported file format: {path}")

def anderson_darling_test(observed: pd.Series, simulated: np.ndarray) -> Dict[str, float]:
    """Perform Anderson-Darling test comparing observed vs simulated."""
    try:
        result = stats.anderson_ksmp(observed, simulated)
        return {
            'statistic': float(result.statistic),
            'critical_values': [float(cv) for cv in result.critical_values],
            'p_value_approx': float(result.significance_level) if hasattr(result, 'significance_level') else 0.0
        }
    except Exception as e:
        logger.error(f"Anderson-Darling test failed: {e}")
        raise StatisticalModelError(f"Anderson-Darling test failed: {e}")

def kolmogorov_smirnov_test(observed: pd.Series, simulated: np.ndarray) -> Dict[str, float]:
    """Perform Kolmogorov-Smirnov test comparing observed vs simulated."""
    try:
        result = stats.ks_2samp(observed, simulated)
        return {
            'statistic': float(result.statistic),
            'p_value': float(result.pvalue)
        }
    except Exception as e:
        logger.error(f"KS test failed: {e}")
        raise StatisticalModelError(f"KS test failed: {e}")

def calculate_jurisdiction_p_values(df: pd.DataFrame, null_dist: pd.DataFrame) -> pd.DataFrame:
    """Calculate p-values for each jurisdiction."""
    results = []
    for _, row in df.iterrows():
        jurisdiction = row['jurisdiction']
        obs_val = row['discrepancy_abs']
        
        # Compare against null distribution for this jurisdiction or global
        # Assuming null_dist has a column 'jurisdiction' if per-jurisdiction, otherwise global
        if 'jurisdiction' in null_dist.columns:
            sim_vals = null_dist[null_dist['jurisdiction'] == jurisdiction]['simulated_value'].values
        else:
            sim_vals = null_dist['simulated_value'].values if 'simulated_value' in null_dist.columns else null_dist.values.flatten()
        
        if len(sim_vals) == 0:
            p_val = 1.0
        else:
            p_val = (np.sum(sim_vals >= obs_val) + 1) / (len(sim_vals) + 1)
        
        results.append({
            'jurisdiction': jurisdiction,
            'observed': obs_val,
            'p_value': p_val
        })
    
    return pd.DataFrame(results)

def run_analysis(
    processed_data_path: str,
    null_distribution_path: str,
    output_path: str,
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """Run full analysis pipeline."""
    logger.info(f"Loading processed data from {processed_data_path}")
    df = load_processed_discrepancies(processed_data_path)
    
    logger.info(f"Loading null distribution from {null_distribution_path}")
    null_dist = load_null_distribution(null_distribution_path)
    
    # Calculate p-values
    p_values_df = calculate_jurisdiction_p_values(df, null_dist)
    
    # Run statistical tests
    observed_vals = df['discrepancy_abs'].dropna()
    if 'simulated_value' in null_dist.columns:
        simulated_vals = null_dist['simulated_value'].values
    else:
        simulated_vals = null_dist.values.flatten()
    
    ad_result = anderson_darling_test(observed_vals, simulated_vals)
    ks_result = kolmogorov_smirnov_test(observed_vals, simulated_vals)
    
    # VIF Calculation (New for T035)
    vif_result = calculate_vif_for_predictors(df, config_path)
    
    # Compile results
    results = {
        'jurisdiction_p_values': p_values_df.to_dict(orient='records'),
        'anderson_darling': ad_result,
        'kolmogorov_smirnov': ks_result,
        'vif_analysis': vif_result,
        'summary': {
            'total_jurisdictions': len(df),
            'flagged_at_0_05': len(p_values_df[p_values_df['p_value'] < 0.05]),
            'flagged_at_0_01': len(p_values_df[p_values_df['p_value'] < 0.01])
        }
    }
    
    # Save results
    output_df = pd.DataFrame(results['jurisdiction_p_values'])
    output_df.to_csv(output_path, index=False)
    logger.info(f"Analysis results saved to {output_path}")
    
    return results

def main():
    """Main entry point for analysis."""
    import argparse
    parser = argparse.ArgumentParser(description="Run statistical analysis on election discrepancies")
    parser.add_argument("--processed-data", required=True, help="Path to processed discrepancy data CSV")
    parser.add_argument("--null-dist", required=True, help="Path to null distribution data")
    parser.add_argument("--output", required=True, help="Path for output results CSV")
    parser.add_argument("--config", help="Path to configuration YAML file")
    args = parser.parse_args()
    
    results = run_analysis(args.processed_data, args.null_dist, args.output, args.config)
    print(f"Analysis complete. Flagged jurisdictions (p<0.05): {results['summary']['flagged_at_0_05']}")

# --- New Function for T035: VIF Calculation ---

def calculate_vif_for_predictors(
    df: pd.DataFrame, 
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate Variance Inflation Factor (VIF) for predictors if regression is extended.
    
    Checks config for 'population density' and 'precinct size'.
    If present, calculates VIF. Flags if VIF > 5.
    If not present, marks SC-006 as 'Not Applicable'.
    
    Args:
        df: DataFrame containing discrepancy data and potential predictors.
        config_path: Path to config YAML file.
    
    Returns:
        Dict containing VIF results or 'Not Applicable' status.
    """
    target_predictors = ['population_density', 'precinct_size']
    result = {
        'status': 'Not Applicable',
        'reason': 'Predictors not found in data or config',
        'vif_values': {},
        'high_vif_flags': []
    }
    
    # Load config if provided
    config_predictors = []
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            # Check for predictors in config
            if 'predictors' in config:
                config_predictors = config['predictors']
            elif 'regression' in config and 'predictors' in config['regression']:
                config_predictors = config['regression']['predictors']
        except Exception as e:
            logger.warning(f"Could not load config for predictors: {e}")
    
    # Determine which predictors to check
    # Priority: Explicitly requested in config, otherwise check standard names in data
    predictors_to_check = []
    
    if config_predictors:
        # If config explicitly lists predictors, use them
        for pred in config_predictors:
            if pred in target_predictors and pred in df.columns:
                predictors_to_check.append(pred)
    else:
        # Check standard names
        for pred in target_predictors:
            if pred in df.columns:
                predictors_to_check.append(pred)
    
    if not predictors_to_check:
        logger.info("No relevant predictors found for VIF calculation. SC-006 marked as Not Applicable.")
        return result
    
    # Prepare data for VIF calculation
    # VIF requires a matrix of predictors. We use the found predictors.
    X = df[predictors_to_check].dropna()
    
    if X.shape[0] < len(predictors_to_check) + 1:
        logger.warning("Insufficient data points for VIF calculation.")
        result['status'] = 'Not Applicable'
        result['reason'] = 'Insufficient data points'
        return result
    
    # Add intercept for VIF calculation (standard practice)
    X_with_intercept = sm.add_constant(X)
    
    vif_values = {}
    high_vif_flags = []
    
    try:
        import statsmodels.api as sm
    except ImportError:
        logger.warning("statsmodels not installed. Cannot calculate VIF. Marking as Not Applicable.")
        result['status'] = 'Not Applicable'
        result['reason'] = 'statsmodels library not available'
        return result
    
    for i, col in enumerate(X.columns):
        # VIF for col is 1 / (1 - R^2) where R^2 is from regressing col on other predictors
        y = X[col]
        X_other = X.drop(columns=[col])
        X_other_with_const = sm.add_constant(X_other)
        
        model = sm.OLS(y, X_other_with_const).fit()
        r_squared = model.rsquared
        
        if r_squared == 1.0:
            vif = np.inf
        else:
            vif = 1.0 / (1.0 - r_squared)
        
        vif_values[col] = float(vif)
        
        if vif > 5.0:
            high_vif_flags.append({
                'predictor': col,
                'vif': float(vif),
                'threshold': 5.0,
                'flag': 'High VIF'
            })
    
    result['status'] = 'Calculated'
    result['vif_values'] = vif_values
    result['high_vif_flags'] = high_vif_flags
    
    if high_vif_flags:
        result['reason'] = f"Found {len(high_vif_flags)} predictors with VIF > 5"
        logger.warning(f"High VIF detected: {high_vif_flags}")
    else:
        result['reason'] = "All predictors have VIF <= 5"
        logger.info("VIF calculation complete. No high multicollinearity detected.")
    
    return result

# Note: statsmodels import is handled inside the function to avoid hard dependency
# unless VIF calculation is actually triggered.
try:
    import statsmodels.api as sm
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False