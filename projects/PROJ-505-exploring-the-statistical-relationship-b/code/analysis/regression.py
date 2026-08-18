import os
import sys
import json
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import from project modules
from utils.logging import AnalysisError, get_logger, log_duration
from utils.io import load_parquet, save_parquet
from config import get_config

logger = get_logger(__name__)

# Constants
VIF_THRESHOLD = 5.0
MIN_SAMPLES = 10

def _prepare_features(df: pd.DataFrame, coupling_cols: List[str], composition_cols: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare feature matrix (X) and target (y) for regression.
    Drops rows with NaN in any required column.
    """
    required_cols = coupling_cols + composition_cols + ['Dst', 'Kp']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise AnalysisError(f"Missing required columns for regression: {missing}")

    # Drop rows with NaN in any required column
    clean_df = df.dropna(subset=required_cols)
    
    if len(clean_df) < MIN_SAMPLES:
        raise AnalysisError(f"Insufficient data for regression after cleaning: {len(clean_df)} rows < {MIN_SAMPLES}")

    # Prepare X and y
    X_base = clean_df[coupling_cols].copy()
    X_full = clean_df[coupling_cols + composition_cols].copy()
    
    # Add constant for intercept
    X_base = sm.add_constant(X_base)
    X_full = sm.add_constant(X_full)
    
    y_dst = clean_df['Dst']
    y_kp = clean_df['Kp']

    return X_base, X_full, y_dst, y_kp, clean_df

def _calculate_vif(X: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor for each predictor.
    Returns a DataFrame with columns: 'feature', 'vif'.
    """
    vif_data = []
    # Exclude constant column from VIF calculation
    features = [c for c in X.columns if c != 'const']
    
    for feature in features:
        try:
            vif = variance_inflation_factor(X.values, X.columns.get_loc(feature))
            vif_data.append({'feature': feature, 'vif': vif})
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {feature}: {e}")
            vif_data.append({'feature': feature, 'vif': np.nan})
    
    return pd.DataFrame(vif_data)

def _fit_model(X: pd.DataFrame, y: pd.Series, model_name: str) -> Dict[str, Any]:
    """
    Fit OLS model and extract results.
    """
    try:
        model = sm.OLS(y, X).fit()
        
        # Extract coefficients and stats
        results = {
            'model_name': model_name,
            'n_obs': int(model.nobs),
            'r_squared': float(model.rsquared),
            'adj_r_squared': float(model.rsquared_adj),
            'f_statistic': float(model.fvalue),
            'f_pvalue': float(model.f_pvalue),
            'coefficients': {},
            'pvalues': {},
            'vif': None
        }

        # Extract per-coefficient stats
        for col in X.columns:
            if col == 'const':
                coef_name = 'intercept'
            else:
                coef_name = col
            
            results['coefficients'][coef_name] = float(model.params[col])
            results['pvalues'][coef_name] = float(model.pvalues[col])

        # Calculate VIF
        vif_df = _calculate_vif(X)
        results['vif'] = vif_df.to_dict('records')

        return results

    except Exception as e:
        raise AnalysisError(f"Failed to fit model {model_name}: {e}")

def _check_multicollinearity(vif_results: List[Dict], model_name: str, output_path: Path) -> None:
    """
    Check for high VIF values and write a warning artifact if VIF >= 5.
    """
    high_vif = [row for row in vif_results if row['vif'] >= VIF_THRESHOLD]
    
    if high_vif:
        warning_artifact = {
            'model': model_name,
            'threshold': VIF_THRESHOLD,
            'highly_collinear_features': high_vif,
            'message': f"WARNING: The following predictors in {model_name} have VIF >= {VIF_THRESHOLD}. "
                       "This indicates severe multicollinearity which may destabilize coefficient estimates."
        }
        
        # Write warning artifact to disk
        warning_path = output_path.parent / f"vif_warning_{model_name.replace(' ', '_')}.json"
        with open(warning_path, 'w') as f:
            json.dump(warning_artifact, f, indent=2)
        
        logger.warning(f"High multicollinearity detected in {model_name}. Warning artifact written to {warning_path}")
    else:
        logger.info(f"No features with VIF >= {VIF_THRESHOLD} found in {model_name}.")

@log_duration
def run_regression_analysis(data_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Main function to run regression analysis.
    
    Loads aligned data, fits baseline and full models, calculates VIF,
    and outputs results and warnings.
    """
    config = get_config()
    logger.info(f"Starting regression analysis with data from {data_path}")
    
    # Load data
    try:
        df = load_parquet(data_path)
    except Exception as e:
        # Fallback to CSV if parquet fails (for synthetic data compatibility)
        try:
            df = pd.read_csv(data_path)
            logger.info(f"Loaded CSV data from {data_path}")
        except Exception as csv_err:
            raise AnalysisError(f"Failed to load data from {data_path}: {csv_err}")

    # Define columns based on task description and T028 output
    # Coupling functions from T028: epsilon, newell, v_bs, v_bt (and derived)
    coupling_cols = get_coupling_function_columns()
    if not coupling_cols:
        # Hardcode expected coupling columns if the helper isn't fully populated yet
        coupling_cols = ['epsilon', 'newell', 'v_bs', 'v_bt']
    
    # Composition ratios
    composition_cols = ['O_Fe', 'He_H', 'C_O']
    
    # Validate columns exist
    missing = [c for c in coupling_cols + composition_cols if c not in df.columns]
    if missing:
        # Try to find approximate matches or warn
        available = list(df.columns)
        logger.warning(f"Expected columns missing: {missing}. Available: {available}")
        # Attempt to map common variations
        # If 'epsilon' is missing but 'Akasofu_epsilon' exists, map it
        if 'epsilon' not in coupling_cols and 'Akasofu_epsilon' in df.columns:
            coupling_cols = ['Akasofu_epsilon', 'Newell_function', 'v_bs', 'v_bt']
        elif 'epsilon' not in df.columns and 'epsilon' in coupling_cols:
            # Try to find 'epsilon' like columns
            eps_col = next((c for c in df.columns if 'epsilon' in c.lower()), None)
            if eps_col:
                coupling_cols = [eps_col] + [c for c in coupling_cols if c != 'epsilon']
    
    # Re-check after potential mapping
    missing = [c for c in coupling_cols + composition_cols if c not in df.columns]
    if missing:
        raise AnalysisError(f"Required columns still missing after mapping: {missing}. "
                            f"Available: {list(df.columns)}")

    # Prepare data
    X_base, X_full, y_dst, y_kp, clean_df = _prepare_features(
        df, coupling_cols, composition_cols
    )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {}

    # --- Dst Models ---
    logger.info("Fitting Dst models...")
    
    # Baseline Dst
    baseline_dst = _fit_model(X_base, y_dst, "Baseline_Dst")
    _check_multicollinearity(baseline_dst['vif'], "Baseline_Dst", output_path)
    results['Baseline_Dst'] = baseline_dst

    # Full Dst
    full_dst = _fit_model(X_full, y_dst, "Full_Dst")
    _check_multicollinearity(full_dst['vif'], "Full_Dst", output_path)
    results['Full_Dst'] = full_dst

    # Delta R2 for Dst
    delta_r2_dst = full_dst['r_squared'] - baseline_dst['r_squared']
    results['Delta_R2_Dst'] = delta_r2_dst
    logger.info(f"Delta R2 (Dst): {delta_r2_dst:.4f}")

    # --- Kp Models ---
    logger.info("Fitting Kp models...")
    
    # Baseline Kp
    baseline_kp = _fit_model(X_base, y_kp, "Baseline_Kp")
    _check_multicollinearity(baseline_kp['vif'], "Baseline_Kp", output_path)
    results['Baseline_Kp'] = baseline_kp

    # Full Kp
    full_kp = _fit_model(X_full, y_kp, "Full_Kp")
    _check_multicollinearity(full_kp['vif'], "Full_Kp", output_path)
    results['Full_Kp'] = full_kp

    # Delta R2 for Kp
    delta_r2_kp = full_kp['r_squared'] - baseline_kp['r_squared']
    results['Delta_R2_Kp'] = delta_r2_kp
    logger.info(f"Delta R2 (Kp): {delta_r2_kp:.4f}")

    # Save results
    results_path = output_path / "regression_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Regression results saved to {results_path}")

    # Save coefficient tables as CSV
    coeff_df = pd.DataFrame([
        {**baseline_dst['coefficients'], **baseline_dst['pvalues'], 'source': 'Baseline_Dst'},
        {**full_dst['coefficients'], **full_dst['pvalues'], 'source': 'Full_Dst'},
        {**baseline_kp['coefficients'], **baseline_kp['pvalues'], 'source': 'Baseline_Kp'},
        {**full_kp['coefficients'], **full_kp['pvalues'], 'source': 'Full_Kp'}
    ])
    # Ensure consistent columns
    all_cols = sorted(set(coeff_df.columns) - {'source'})
    coeff_df = coeff_df[['source'] + list(all_cols)]
    coeff_path = output_path / "regression_coefficients.csv"
    coeff_df.to_csv(coeff_path, index=False)
    logger.info(f"Coefficients saved to {coeff_path}")

    return results

def main():
    config = get_config()
    
    # Default paths based on project structure
    input_path = config.get('paths', {}).get('processed_data', 'data/processed/aligned_data.parquet')
    output_dir = config.get('paths', {}).get('artifacts', 'data/artifacts')
    
    # Allow CLI override
    import argparse
    parser = argparse.ArgumentParser(description='Run Regression Analysis')
    parser.add_argument('--input', '-i', type=str, default=input_path, help='Input data path')
    parser.add_argument('--output', '-o', type=str, default=output_dir, help='Output directory')
    args = parser.parse_args()

    try:
        run_regression_analysis(args.input, args.output)
        logger.info("Regression analysis completed successfully.")
    except AnalysisError as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)

# Helper to expose coupling columns if not defined in T028
def get_coupling_function_columns() -> List[str]:
    """Returns the list of coupling function columns expected by the regression model."""
    # These correspond to outputs from code/analysis/coupling_functions.py
    return ['epsilon', 'newell', 'v_bs', 'v_bt']

if __name__ == "__main__":
    main()
