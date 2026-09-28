"""
Analysis module for Gut Microbiome and Cognitive Performance correlation study.
Implements Spearman correlation, multivariate regression, and Lasso regression.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
import json
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import VarianceInflationFactor
from sklearn.linear_model import Lasso, LassoCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
import logging

from config import SAMPLE_LIMIT, RANDOM_SEED, DQS_REQUIRED
from logging_config import get_logger, log_provenance, log_warning, log_pipeline_start, log_pipeline_end
from diversity import calculate_shannon_index
from transformation import apply_clr

logger = get_logger(__name__)

def load_processed_data() -> pd.DataFrame:
    """
    Loads the cleaned dataset from data/processed/cleaned_data.csv.
    """
    path = Path("data/processed/cleaned_data.csv")
    if not path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {path}. Run data ingestion first.")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded cleaned data with {len(df)} rows.")
    return df

def check_zero_variance(df: pd.DataFrame, column: str) -> bool:
    """
    Checks if a column has zero variance.
    """
    if column not in df.columns:
        raise ValueError(f"Column {column} not found in dataframe.")
    
    if df[column].var() < 1e-9:
        log_warning(f"Zero variance detected in column: {column}")
        return True
    return False

def compute_spearman_correlation(df: pd.DataFrame, x_col: str, y_col: str) -> Tuple[float, float, int]:
    """
    Computes Spearman rank correlation between two columns.
    Returns (r_value, p_value, n_obs).
    """
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"Columns {x_col} or {y_col} not found in dataframe.")
    
    # Drop NaNs
    valid_data = df[[x_col, y_col]].dropna()
    n_obs = len(valid_data)
    
    if n_obs < 2:
        raise ValueError("Not enough valid observations for correlation.")
    
    r, p = stats.spearmanr(valid_data[x_col], valid_data[y_col])
    log_provenance(f"Spearman correlation: {x_col} vs {y_col} -> r={r:.4f}, p={p:.4f}")
    return r, p, n_obs

def run_multivariate_regression(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Runs multivariate linear regression (OLS).
    Predictors: shannon_index, age, sex, bmi, dqs (if available).
    Target: fluid_intelligence.
    """
    target = 'fluid_intelligence'
    if target not in df.columns:
        raise ValueError("Target column 'fluid_intelligence' not found.")
    
    # Prepare predictors
    predictors = ['shannon_index', 'age', 'bmi']
    
    # Handle Sex (categorical)
    if 'sex' in df.columns:
        df = pd.get_dummies(df, columns=['sex'], drop_first=True)
        # Add sex columns to predictors
        sex_cols = [c for c in df.columns if c.startswith('sex_')]
        predictors.extend(sex_cols)
    
    # Handle DQS
    if 'dqs' in df.columns:
        predictors.append('dqs')
    elif DQS_REQUIRED:
        raise ValueError("DQS is required but not found in data.")
    else:
        log_warning("DQS not found and not required; proceeding without it.")
    
    # Ensure all predictors exist
    missing = [p for p in predictors if p not in df.columns]
    if missing:
        raise ValueError(f"Missing predictor columns: {missing}")
    
    X = df[predictors].dropna()
    y = df.loc[X.index, target]
    
    if len(X) < 2:
        raise ValueError("Not enough valid observations for regression.")
    
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    
    results = {
        'model': model,
        'coefficients': model.params.to_dict(),
        'std_err': model.bse.to_dict(),
        'p_values': model.pvalues.to_dict(),
        'r_squared': model.rsquared,
        'adj_r_squared': model.rsquared_adj
    }
    
    log_provenance(f"OLS Regression completed. R-squared: {results['r_squared']:.4f}")
    return results

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculates Variance Inflation Factor for predictors.
    """
    vif_data = {}
    X = df[predictors].dropna()
    
    for i, col in enumerate(X.columns):
        y = X[col]
        X_other = X.drop(columns=[col])
        X_other = sm.add_constant(X_other)
        
        if X_other.shape[0] < 2:
            continue
            
        try:
            model = sm.OLS(y, X_other).fit()
            vif = 1 / (1 - model.rsquared)
            vif_data[col] = vif
            if vif > 5:
                log_warning(f"High multicollinearity detected: {col} has VIF {vif:.2f}")
        except Exception as e:
            log_warning(f"Could not calculate VIF for {col}: {e}")
    
    return vif_data

def run_lasso_regression(df: pd.DataFrame, X_clr: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Runs Lasso regression on CLR-transformed taxa data.
    Uses 5-fold CV to select alpha.
    """
    if len(X_clr) != len(y):
        raise ValueError("X and y must have the same length.")
    
    # Scale data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_clr)
    
    # Use LassoCV for alpha selection
    lasso_cv = LassoCV(alphas=np.logspace(-4, 0, 100), cv=5, random_state=RANDOM_SEED, max_iter=10000)
    lasso_cv.fit(X_scaled, y)
    
    # Get coefficients
    coef = lasso_cv.coef_
    non_zero_mask = coef != 0
    non_zero_count = np.sum(non_zero_mask)
    
    # Predictions and metrics
    y_pred = lasso_cv.predict(X_scaled)
    mse = mean_squared_error(y, y_pred)
    r2 = r2_score(y, y_pred)
    
    # Map coefficients to feature names (assuming column names are passed or derived)
    # For this function, we assume feature names are not directly available here,
    # so we return indices. The caller (save_lasso_results) will need to map these.
    # However, to make it useful, we assume the caller passes feature names or we
    # generate generic names.
    
    results = {
        'alpha': lasso_cv.alpha_,
        'coefficients': coef.tolist(), # List of floats
        'non_zero_count': int(non_zero_count),
        'metrics': {
            'mse': float(mse),
            'r2': float(r2)
        },
        'intercept': float(lasso_cv.intercept_)
    }
    
    log_provenance(f"Lasso Regression completed. Alpha: {results['alpha']:.4f}, Non-zero features: {non_zero_count}")
    return results

def save_correlation_results(r: float, p: float, n: int, path: str = "data/processed/correlation_results.csv") -> None:
    """
    Saves correlation results to CSV.
    """
    df = pd.DataFrame({'r_value': [r], 'p_value': [p], 'n_obs': [n]})
    df.to_csv(path, index=False)
    log_provenance(f"Correlation results saved to {path}")

def save_regression_results(results: Dict[str, Any], path: str = "data/processed/regression_results.csv") -> None:
    """
    Saves regression results to CSV.
    """
    rows = []
    for var, coef in results['coefficients'].items():
        rows.append({
            'variable': var,
            'coefficient': coef,
            'std_err': results['std_err'][var],
            'p_value': results['p_values'][var]
        })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    log_provenance(f"Regression results saved to {path}")

def save_vif_results(vif_data: Dict[str, float], path: str = "data/processed/vif_results.json") -> None:
    """
    Saves VIF results to JSON.
    """
    with open(path, 'w') as f:
        json.dump(vif_data, f, indent=2)
    log_provenance(f"VIF results saved to {path}")

def save_lasso_results_temp(results: Dict[str, Any], path: str = "data/processed/lasso_temp_results.json") -> None:
    """
    Saves Lasso results to a temporary JSON file for the save_lasso_results module to pick up.
    This bridges the gap between analysis.py and save_lasso_results.py.
    """
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    log_provenance(f"Lasso temporary results saved to {path}")

def run_analysis_pipeline() -> None:
    """
    Orchestrates the full analysis pipeline.
    """
    log_pipeline_start("Analysis Pipeline")
    
    try:
        df = load_processed_data()
        
        # Check zero variance
        if check_zero_variance(df, 'fluid_intelligence'):
            log_warning("Zero variance in target; skipping correlation and regression.")
            return
        
        # Spearman Correlation
        r, p, n = compute_spearman_correlation(df, 'shannon_index', 'fluid_intelligence')
        save_correlation_results(r, p, n)
        
        # Multivariate Regression
        regression_results = run_multivariate_regression(df)
        
        # VIF
        predictors = [c for c in df.columns if c not in ['fluid_intelligence', 'participant_id']]
        # Exclude non-predictors if any
        vif_data = calculate_vif(df, predictors)
        save_vif_results(vif_data)
        
        save_regression_results(regression_results)
        
        # Lasso Regression (Secondary Path)
        # We need CLR transformed taxa data. Assuming it's in the dataframe or we load it.
        # For this implementation, we assume the taxa columns are in the dataframe.
        taxa_cols = [c for c in df.columns if c.startswith('taxa_') or c in ['SpeciesA', 'SpeciesB']] # Example
        if not taxa_cols:
            log_warning("No taxa columns found for Lasso regression. Skipping.")
        else:
            X_clr = df[taxa_cols].fillna(0).values
            y = df['fluid_intelligence'].values
            
            # Filter rows with NaN in target or X
            valid_idx = ~np.isnan(X_clr).any(axis=1) & ~np.isnan(y)
            X_clr = X_clr[valid_idx]
            y = y[valid_idx]
            
            if len(X_clr) > 0:
                lasso_results = run_lasso_regression(df, X_clr, y)
                # Save intermediate results for T029b
                save_lasso_results_temp(lasso_results)
        
        log_pipeline_end("Analysis Pipeline")
        
    except Exception as e:
        log_warning(f"Analysis pipeline failed: {e}")
        raise

def main():
    run_analysis_pipeline()

if __name__ == "__main__":
    main()