"""
Regression Analysis Module for US3.
Performs multiple regression: Cognition ~ Efficiency + Age + Sex + Education.
Includes Variance Inflation Factor (VIF) check for multicollinearity.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import local config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ensure_dirs, get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
COGNITIVE_COL = 'cognitive_score'
AGE_COL = 'age'
SEX_COL = 'sex'
EDUCATION_COL = 'education_years'
EFFICIENCY_COL = 'Global_Efficiency'  # Primary metric for regression as per task description
OUTPUT_FILE = 'data/results/regression_results.csv'
SUMMARY_FILE = 'data/results/regression_summary.json'

def load_metrics_and_demographics() -> pd.DataFrame:
    """
    Loads the network metrics CSV and merges with demographics if available.
    Expects data from T005 (download) and T008_run (metrics).
    """
    config = get_config_summary()
    metrics_path = Path(config['processed_dir']) / 'network_metrics.csv'
    
    # Handle potential path variations if T017/T019 modified location
    if not metrics_path.exists():
        # Fallback to results dir if moved there
        metrics_path = Path(config['results_dir']) / 'network_metrics.csv'
    
    if not metrics_path.exists():
        raise FileNotFoundError(f"Network metrics file not found at {metrics_path}")

    df = pd.read_csv(metrics_path)
    
    # Ensure required columns exist
    required_cols = [AGE_COL, SEX_COL, EDUCATION_COL, COGNITIVE_COL, EFFICIENCY_COL]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        # Try to be lenient if some are missing, but fail if critical ones are
        if COGNITIVE_COL not in df.columns or EFFICIENCY_COL not in df.columns:
            raise ValueError(f"Critical columns missing for regression: {missing}")
        logger.warning(f"Missing optional columns: {missing}. Proceeding with available data.")

    return df

def check_multicollinearity(df: pd.DataFrame, features: List[str]) -> Tuple[Dict[str, float], bool]:
    """
    Calculates Variance Inflation Factor (VIF) for features.
    Returns dict of VIFs and a boolean indicating if multicollinearity is severe (VIF > 5).
    """
    # Add intercept for VIF calculation (statsmodels vif usually expects X without intercept)
    X = df[features].copy()
    
    vif_data = {}
    max_vif = 0
    
    for feature in features:
        try:
            vif = variance_inflation_factor(X.values, features.index(feature))
            vif_data[feature] = vif
            if vif > max_vif:
                max_vif = vif
        except Exception as e:
            logger.error(f"Could not calculate VIF for {feature}: {e}")
            vif_data[feature] = np.nan

    is_severe = any(v > 5 for v in vif_data.values() if not np.isnan(v))
    return vif_data, is_severe

def run_regression(df: pd.DataFrame, features: List[str]) -> Dict[str, Any]:
    """
    Runs OLS regression: Cognition ~ features.
    Returns summary statistics and coefficients.
    """
    # Filter out rows with NaN in any required column
    cols_needed = features + [COGNITIVE_COL]
    clean_df = df[cols_needed].dropna()

    if len(clean_df) < 5:
        raise ValueError(f"Insufficient data points for regression after cleaning. N={len(clean_df)}")

    y = clean_df[COGNITIVE_COL]
    X = clean_df[features]

    # Add constant for intercept
    X = sm.add_constant(X)

    model = sm.OLS(y, X).fit()

    results = {
        'n_samples': len(clean_df),
        'r_squared': model.rsquared,
        'adj_r_squared': model.rsquared_adj,
        'f_pvalue': model.f_pvalue,
        'coefficients': {},
        'warnings': []
    }

    for name, param in model.params.items():
        if name != 'const':
            results['coefficients'][name] = {
                'coef': float(param),
                'std_err': float(model.bse[name]),
                't': float(model.tvalues[name]),
                'p_value': float(model.pvalues[name]),
                'conf_int_low': float(model.conf_int().loc[name, 0]),
                'conf_int_high': float(model.conf_int().loc[name, 1])
            }

    return results

def main():
    """
    Main entry point for T031.
    1. Loads data.
    2. Checks multicollinearity.
    3. Runs regression.
    4. Saves results to CSV and JSON summary.
    """
    ensure_dirs()
    config = get_config_summary()
    
    logger.info("Starting Regression Analysis (T031)...")
    
    try:
        # 1. Load Data
        logger.info("Loading metrics and demographics...")
        df = load_metrics_and_demographics()
        logger.info(f"Loaded {len(df)} records.")

        # Define features based on task description: Efficiency + Age + Sex + Education
        # We need to handle Sex and Education as categorical or numeric depending on data
        # Assuming Sex is 0/1 or M/F, Education is numeric.
        features = [EFFICIENCY_COL, AGE_COL]
        
        if SEX_COL in df.columns:
            features.append(SEX_COL)
        else:
            logger.warning(f"Column '{SEX_COL}' not found. Skipping Sex in regression.")
            
        if EDUCATION_COL in df.columns:
            features.append(EDUCATION_COL)
        else:
            logger.warning(f"Column '{EDUCATION_COL}' not found. Skipping Education in regression.")

        if COGNITIVE_COL not in df.columns:
            raise ValueError("Cognitive score column missing. Cannot run cognitive regression.")

        # 2. Multicollinearity Check
        logger.info("Checking multicollinearity (VIF)...")
        vif_results, is_severe = check_multicollinearity(df, features)
        logger.info(f"VIF Results: {vif_results}")
        
        summary_warnings = []
        if is_severe:
            summary_warnings.append("High multicollinearity detected (VIF > 5) in independent variables.")

        # 3. Run Regression
        logger.info("Running OLS Regression...")
        regression_results = run_regression(df, features)
        
        # 4. Prepare Output DataFrame
        # Create a flat dataframe for the CSV output
        output_rows = []
        for var, stats in regression_results['coefficients'].items():
            output_rows.append({
                'variable': var,
                'coef': stats['coef'],
                'std_err': stats['std_err'],
                't_stat': stats['t'],
                'p_value': stats['p_value'],
                'conf_int_low': stats['conf_int_low'],
                'conf_int_high': stats['conf_int_high']
            })
        
        # Add model level stats to the first row or a separate row? 
        # Standard practice is a summary row or separate file. 
        # We will append a row for model stats with variable='Model_Stats'
        output_rows.append({
            'variable': 'Model_Stats',
            'coef': regression_results['r_squared'],
            'std_err': regression_results['adj_r_squared'],
            't_stat': regression_results['f_pvalue'],
            'p_value': regression_results['n_samples'],
            'conf_int_low': 0.0,
            'conf_int_high': 0.0
        })

        output_df = pd.DataFrame(output_rows)
        
        # Ensure output directory exists
        output_path = Path(config['results_dir']) / OUTPUT_FILE
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_df.to_csv(output_path, index=False)
        logger.info(f"Saved regression results to {output_path}")

        # 5. Generate Summary JSON
        summary = {
            'model_summary': {
                'r_squared': regression_results['r_squared'],
                'adj_r_squared': regression_results['adj_r_squared'],
                'f_pvalue': regression_results['f_pvalue'],
                'n_samples': regression_results['n_samples']
            },
            'vif_check': {
                'values': vif_results,
                'is_severe': is_severe
            },
            'warnings': summary_warnings,
            'features_used': features
        }
        
        # Check for low power in older group (T032 dependency logic)
        # Define older group as age > 65 (standard cutoff, though not explicitly defined, using common sense)
        if AGE_COL in df.columns:
            older_count = len(df[df[AGE_COL] > 65])
            if older_count < 15:
                summary['warnings'].append('Low Power for Older Group (N < 15)')
        
        summary_path = Path(config['results_dir']) / SUMMARY_FILE
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Saved regression summary to {summary_path}")

        logger.info("Regression Analysis (T031) completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during regression: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())