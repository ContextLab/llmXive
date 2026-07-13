"""
T020: Hierarchical regression with covariates.

Tests whether metacognitive awareness contributes unique variance 
to reality testing accuracy after controlling for covariates.
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.env_config import load_config, setup_logging

def log_info(logger, msg):
    if logger:
        logger.info(msg)
    else:
        print(f"[INFO] {msg}")

def log_error(logger, msg):
    if logger:
        logger.error(msg)
    else:
        print(f"[ERROR] {msg}")

def load_regression_data():
    """Load data for regression analysis."""
    trial_data_path = Path("data") / "derived" / "trial_data.csv"
    if not trial_data_path.exists():
        raise FileNotFoundError(f"Trial data not found at {trial_data_path}")
    
    df = pd.read_csv(trial_data_path)
    
    # Check for working memory data
    has_working_memory = 'working_memory' in df.columns
    
    return df, has_working_memory

def compute_type2_auc_and_d_prime(df):
    """Compute Type-2 AUC and d' for each participant."""
    from src.utils.stats import compute_type2_auc, compute_sdt_metrics
    
    participants = df['participant_id'].unique()
    metrics = []
    
    for participant_id in participants:
        p_data = df[df['participant_id'] == participant_id]
        
        try:
            type2_auc = compute_type2_auc(
                p_data['source_label'],
                p_data['participant_response'],
                p_data['confidence_rating']
            )
            d_prime, _ = compute_sdt_metrics(
                p_data['source_label'],
                p_data['participant_response']
            )
        except:
            type2_auc = np.nan
            d_prime = np.nan
        
        metrics.append({
            'participant_id': participant_id,
            'type2_auc': type2_auc,
            'd_prime': d_prime,
            'age': p_data['age'].iloc[0] if 'age' in p_data.columns else np.nan,
            'gender': p_data['gender'].iloc[0] if 'gender' in p_data.columns else np.nan,
            'working_memory': p_data['working_memory'].iloc[0] if 'working_memory' in p_data.columns else np.nan
        })
    
    return pd.DataFrame(metrics)

def run_regression_analysis(metrics_df, has_working_memory):
    """Run hierarchical regression analysis."""
    # Clean data
    clean_df = metrics_df.dropna(subset=['type2_auc', 'd_prime'])
    
    if len(clean_df) < 5:
        log_info(None, "Insufficient data for regression")
        return {
            'status': 'insufficient_data',
            'message': 'Not enough participants'
        }
    
    # Prepare predictors
    predictors = ['type2_auc']
    covariates = []
    
    if 'age' in clean_df.columns:
        covariates.append('age')
    if 'gender' in clean_df.columns:
        clean_df['gender_encoded'] = clean_df['gender'].map({'M': 0, 'F': 1, 'Other': 2}).fillna(0)
        covariates.append('gender_encoded')
    
    # Step 1: Baseline model with covariates
    if covariates:
        X1 = add_constant(clean_df[covariates])
        y = clean_df['d_prime']
        model1 = OLS(y, X1).fit()
        r_squared_1 = model1.rsquared
    else:
        r_squared_1 = 0.0
        model1 = None
    
    # Step 2: Add metacognitive score
    X2 = add_constant(clean_df[covariates + predictors])
    model2 = OLS(y, X2).fit()
    r_squared_2 = model2.rsquared
    
    # Calculate delta R-squared
    delta_r2 = r_squared_2 - r_squared_1
    
    # F-change statistic (simplified)
    n = len(clean_df)
    p1 = len(covariates) + 1 if covariates else 1  # +1 for intercept
    p2 = len(covariates) + len(predictors) + 1
    
    if delta_r2 > 0 and n > p2:
        f_change = (delta_r2 / (p2 - p1)) / ((1 - r_squared_2) / (n - p2))
    else:
        f_change = 0.0
    
    # Get coefficients for metacognitive score
    coef_idx = covariates.index('type2_auc') + 1 if 'type2_auc' in covariates else len(covariates) + 1
    coef = model2.params.iloc[coef_idx] if len(model2.params) > coef_idx else 0
    std_err = model2.bse.iloc[coef_idx] if len(model2.bse) > coef_idx else 0
    t_stat = model2.tvalues.iloc[coef_idx] if len(model2.tvalues) > coef_idx else 0
    p_val = model2.pvalues.iloc[coef_idx] if len(model2.pvalues) > coef_idx else 1.0
    
    return {
        'status': 'success',
        'delta_r_squared': float(delta_r2),
        'f_change': float(f_change),
        'r_squared_1': float(r_squared_1),
        'r_squared_2': float(r_squared_2),
        'n_participants': int(n),
        'has_working_memory': has_working_memory,
        'model': {
            'coefficient': float(coef),
            'std_error': float(std_err),
            't_statistic': float(t_stat),
            'p_value': float(p_val)
        },
        'adjusted_r_squared': float(model2.rsquared_adj) if not has_working_memory else None
    }

def main():
    """Main entry point for T020."""
    config = load_config()
    logger = setup_logging(config)
    
    log_info(logger, "Starting regression analysis (T020)...")
    
    try:
        # Load data
        df, has_working_memory = load_regression_data()
        
        # Compute metrics
        metrics_df = compute_type2_auc_and_d_prime(df)
        
        # Run regression
        results = run_regression_analysis(metrics_df, has_working_memory)
        
        # Write results
        output_path = Path("data") / "results" / "regression_analysis.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        log_info(logger, f"Regression complete. Delta R²: {results['delta_r_squared']:.3f}")
        return 0
        
    except Exception as e:
        log_error(logger, f"Regression failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
