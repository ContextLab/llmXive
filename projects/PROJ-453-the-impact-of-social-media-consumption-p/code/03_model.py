import os
import sys
import logging
import json
import warnings
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import local config and utils
try:
    from config import RESULTS_ROOT, DATA_ROOT, RANDOM_SEED
    from logging_config import get_logger
    from utils import causal_language_scanner
except ImportError:
    # Fallback for direct execution context if imports fail
    from code.config import RESULTS_ROOT, DATA_ROOT, RANDOM_SEED
    from code.logging_config import get_logger
    from code.utils import causal_language_scanner

logger = get_logger(__name__)

def load_schema_contract(schema_path: str) -> dict:
    """Load the output schema contract."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_output_schema(result: dict, schema: dict) -> bool:
    """Validate result structure against schema."""
    # Basic validation for now
    required_keys = ['coefficients', 'p_values', 'r_squared', 'diagnostics']
    return all(key in result for key in required_keys)

def mean_center(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Mean-center specified columns in-place."""
    for col in columns:
        if col in df.columns:
            df[col] = df[col] - df[col].mean()
    return df

def create_interaction(df: pd.DataFrame, col1: str, col2: str, output_col: str = 'interaction_term') -> pd.DataFrame:
    """Create an interaction term between two columns."""
    if col1 in df.columns and col2 in df.columns:
        df[output_col] = df[col1] * df[col2]
    else:
        logger.warning(f"Columns {col1} or {col2} not found for interaction.")
    return df

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for features."""
    vif_data = {}
    # Add constant for intercept
    X = sm.add_constant(df[features])
    for i, col in enumerate(features):
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data[col] = vif
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_data[col] = np.nan
    return vif_data

def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """Apply Benjamini-Hochberg FDR correction."""
    n = len(p_values)
    if n == 0:
        return []
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    ranks = np.arange(1, n + 1)
    corrected = sorted_p * n / ranks
    corrected = np.minimum(corrected, 1.0) # Cap at 1.0
    # Restore original order
    final_p = np.zeros(n)
    final_p[sorted_indices] = corrected
    return final_p.tolist()

def check_collinearity(df: pd.DataFrame, var1: str, var2: str, threshold: float = 0.7) -> Tuple[float, bool]:
    """Check correlation between two variables."""
    if var1 in df.columns and var2 in df.columns:
        corr = df[var1].corr(df[var2])
        if abs(corr) > threshold:
            logger.warning(f"Potential Mathematical Coupling: correlation > {threshold} ({corr:.4f})")
            return corr, True
        return corr, False
    return 0.0, False

def run_model(df: pd.DataFrame, outcome: str, predictors: List[str]) -> Dict[str, Any]:
    """Run OLS regression and return results."""
    if outcome not in df.columns:
        raise ValueError(f"Outcome variable {outcome} not found in data.")
    for p in predictors:
        if p not in df.columns:
            raise ValueError(f"Predictor {p} not found in data.")
    
    X = df[predictors]
    X = sm.add_constant(X)
    y = df[outcome]
    
    model = sm.OLS(y, X).fit()
    
    results = {
        'coefficients': model.params.to_dict(),
        'p_values': model.pvalues.to_dict(),
        'r_squared': model.rsquared,
        'adj_r_squared': model.rsquared_adj,
        'n_obs': model.nobs
    }
    return results

def run_sensitivity_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run sensitivity analysis with alternative definitions of switching index.
    Returns a DataFrame with results for main and sensitivity models.
    """
    outcome = 'cognitive_flexibility_score'
    base_predictors = ['total_screen_time', 'age']
    
    # Define operationalizations
    definitions = [
        ('main', ['switching_index'] + base_predictors),
        ('platform_count', ['num_platforms'] + base_predictors),
        ('switching_frequency', ['switching_frequency'] + base_predictors)
    ]
    
    results = []
    main_beta = None
    
    for name, predictors in definitions:
        try:
            # Filter data for this run to ensure no missing values in predictors
            valid_mask = df[predictors + [outcome]].notna().all(axis=1)
            subset = df.loc[valid_mask]
            
            if len(subset) < 10:
                logger.warning(f"Not enough data for {name} model (n={len(subset)}). Skipping.")
                continue
                
            res = run_model(subset, outcome, predictors)
            
            # Extract beta for the primary switching variable
            primary_var = predictors[0] # First predictor is the switching variable
            beta = res['coefficients'].get(primary_var, 0.0)
            p_val = res['p_values'].get(primary_var, 1.0)
            n = res['n_obs']
            sign = np.sign(beta)
            
            if name == 'main':
                main_beta = beta
            
            results.append({
                'definition': name,
                'beta': beta,
                'p_value': p_val,
                'n': n,
                'sign': sign,
                'primary_var': primary_var
            })
            
        except Exception as e:
            logger.error(f"Error running sensitivity model {name}: {e}")
            continue
    
    if not results:
        raise ValueError("No sensitivity models could be run.")
    
    df_res = pd.DataFrame(results)
    
    # Calculate delta_beta
    if main_beta is not None:
        df_res['delta_beta'] = (df_res['beta'] - main_beta).abs()
    else:
        # Fallback if main wasn't found (shouldn't happen if logic is correct)
        df_res['delta_beta'] = 0.0
    
    # FDR Correction on p-values
    p_vals = df_res['p_value'].tolist()
    fdr_p_vals = benjamini_hochberg(p_vals)
    df_res['fdr_p_value'] = fdr_p_vals
    
    return df_res

def verify_robustness(df_sensitivity: pd.DataFrame, threshold: float = 0.10) -> Dict[str, Any]:
    """
    Verify robustness per SC-003:
    - Beta sign does not flip.
    - p < 0.10 for all variants (or at least stable sign if p > 0.10).
    """
    status = "PASS"
    details = []
    message = ""
    
    signs = df_sensitivity['sign'].tolist()
    p_vals = df_sensitivity['p_value'].tolist()
    
    # Check sign stability
    unique_signs = set(signs)
    if len(unique_signs) > 1:
        status = "FAIL"
        details.append("Sign instability detected: signs flipped across operationalizations.")
        message = "SC-003 FAIL: Sign instability detected."
    else:
        # Check p-values
        high_p = [i for i, p in enumerate(p_vals) if p >= threshold]
        if high_p:
            # If signs are stable but p > 0.10, we might still pass but with warning
            # The spec says: "IF signs flip: ... set status to FAIL". 
            # "If p > 0.10 ... log Warning ... robustness maintained."
            # So status remains PASS if signs are stable, even if p > 0.10?
            # Re-reading: "SC-003 Met: p < 0.10 across operationalizations"
            # "SC-003 FAIL: Sign instability or p > 0.10 detected"
            # The failure condition includes "p > 0.10 detected".
            # So if ANY p >= 0.10, it is FAIL.
            status = "FAIL"
            details.append(f"P-values >= {threshold} detected for {len(high_p)} variant(s).")
            message = f"SC-003 FAIL: p > {threshold} detected."
        else:
            message = f"SC-003 Met: p < {threshold} across operationalizations."
    
    # Log specific warnings
    for i, row in df_sensitivity.iterrows():
        if row['p_value'] >= threshold and status == "PASS":
            logger.warning(f"Variant {row['definition']}: p > {threshold} but sign stable; robustness maintained.")
        if row['p_value'] >= threshold and status == "FAIL":
             details.append(f"Variant {row['definition']}: p={row['p_value']:.4f}")

    return {
        'sc003_status': status,
        'details': details,
        'message': message,
        'signs': signs,
        'p_values': p_vals
    }

def main():
    """Main entry point for T026: Sensitivity Analysis & FDR."""
    logger.info("Starting Sensitivity Analysis & FDR (T026).")
    
    # 1. Load Data
    cleaned_path = Path(DATA_ROOT) / 'processed' / 'participants_cleaned.csv'
    if not cleaned_path.exists():
        logger.error(f"Cleaned data not found at {cleaned_path}.")
        raise FileNotFoundError(f"Cleaned data not found: {cleaned_path}")
    
    df = pd.read_csv(cleaned_path)
    logger.info(f"Loaded {len(df)} records from {cleaned_path}")
    
    # 2. Check for Residuals (T025 output)
    residuals_path = Path(RESULTS_ROOT) / 'models' / 'residuals.csv'
    # Ensure path is Path object for .exists() check
    if isinstance(residuals_path, str):
        residuals_path = Path(residuals_path)
        
    if residuals_path.exists():
        logger.info(f"Residuals found at {residuals_path}. Using residualized approach if needed.")
        # Note: T026 spec says "Check if residuals.csv exists". 
        # The sensitivity analysis itself doesn't strictly need residuals unless we are residualizing the switching index.
        # The task description says: "Run regression with alternative definitions: platform_count only, switching_frequency only."
        # It does not explicitly say to use residuals for sensitivity, but we acknowledge the file exists.
    else:
        logger.info("No residuals found. Proceeding with standard variables.")
    
    # 3. Run Sensitivity Analysis
    try:
        sensitivity_df = run_sensitivity_analysis(df)
        logger.info(f"Sensitivity analysis complete. {len(sensitivity_df)} models run.")
    except Exception as e:
        logger.error(f"Failed to run sensitivity analysis: {e}")
        raise
    
    # 4. Write Sensitivity Results
    sensitivity_output_path = Path(RESULTS_ROOT) / 'sensitivity_comparison.csv'
    sensitivity_df.to_csv(sensitivity_output_path, index=False)
    logger.info(f"Wrote sensitivity results to {sensitivity_output_path}")
    
    # 5. Verify Robustness (SC-003)
    robustness_result = verify_robustness(sensitivity_df)
    
    # 6. Write Robustness Evidence
    robustness_path = Path(RESULTS_ROOT) / 'robustness_evidence.json'
    with open(robustness_path, 'w') as f:
        json.dump(robustness_result, f, indent=2)
    logger.info(f"Wrote robustness evidence to {robustness_path}")
    
    if robustness_result['sc003_status'] == 'FAIL':
        logger.critical(f"SC-003 Violation: {robustness_result['message']}")
    
    logger.info("T026 Sensitivity Analysis & FDR completed.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
